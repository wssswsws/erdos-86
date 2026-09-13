"""Random-prefix likelihood training and exact masked autoregressive sampling."""
from contextlib import nullcontext
from pathlib import Path
import os
import random
import time
import torch
from torch.nn import functional as F
from .cube import Cube
from .model import Generator, ModelConfig, allowed_additions, prefix_states


class BudgetExpired(RuntimeError):
    pass


def check_deadline(deadline):
    if deadline is not None and time.monotonic() >= deadline:
        raise BudgetExpired('Configured wall-clock budget reached')


def synchronize(device):
    if torch.device(device).type == 'cuda':
        torch.cuda.synchronize(device)


def precision_context(device):
    if torch.device(device).type == 'cuda' and torch.cuda.is_bf16_supported():
        return torch.autocast('cuda', dtype=torch.bfloat16)
    return nullcontext()


class Trainer:
    def __init__(self, model, *, device='cpu', seed=86, lr=3e-4):
        self.device = torch.device(device)
        self.model = model.to(self.device)
        self.cube = Cube.build(model.config.n)
        self.optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
        self.rng = torch.Generator().manual_seed(seed)
        self.augment_rng = random.Random(seed + 1)
        self.steps = 0

    def batch(self, population, batch_size, *, augment=True):
        ids = torch.randint(len(population), (batch_size,), generator=self.rng).tolist()
        rows = []
        for index in ids:
            bits = population[index]
            if augment:
                perm = list(range(self.cube.n))
                self.augment_rng.shuffle(perm)
                bits = self.cube.relabel(bits, perm, self.augment_rng.randrange(1 << self.cube.n))
            rows.append(bits)
        targets = torch.tensor(rows, dtype=torch.long, device=self.device)
        count = targets.shape[1]
        orders = torch.stack([torch.randperm(count, generator=self.rng) for _ in ids]).to(self.device)
        ranks = orders.argsort(dim=1)
        steps = torch.randint(count, (batch_size,), generator=self.rng).to(self.device)
        states = prefix_states(targets, ranks, steps)
        query = orders.gather(1, steps[:, None])
        labels = targets.gather(1, query).squeeze(1).float()
        return states, ranks, steps, query, labels

    def train_step(self, population, batch_size, *, augment=True):
        self.model.train()
        states, ranks, steps, query, labels = self.batch(population, batch_size, augment=augment)
        allowed = allowed_additions(states, self.model.faces, self.model.edge_faces).gather(1, query).squeeze(1)
        if torch.any((~allowed) & (labels == 1)):
            raise ValueError('Training example violates a square constraint')
        self.optimizer.zero_grad(set_to_none=True)
        with precision_context(self.device):
            logits = self.model(states, ranks, steps).gather(1, query).squeeze(1)
            # Forced-zero decisions have exactly zero conditional NLL, no gradient.
            loss = (F.binary_cross_entropy_with_logits(logits.float(), labels, reduction='none') * allowed).mean()
        if not torch.isfinite(loss):
            raise FloatingPointError('Non-finite training loss')
        loss.backward()
        grad_norm = torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
        if not torch.isfinite(grad_norm):
            raise FloatingPointError('Non-finite gradients')
        self.optimizer.step()
        self.steps += 1
        return {'loss': float(loss.detach()), 'grad_norm': float(grad_norm),
                'trainable_fraction': float(allowed.float().mean())}

    def save(self, path, population, extra=None):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {'schema': 'erdos86_gps.v1', 'config': self.model.config_dict(),
                   'model': self.model.state_dict(), 'optimizer': self.optimizer.state_dict(),
                   'steps': self.steps, 'rng': self.rng.get_state(),
                   'augment_rng': self.augment_rng.getstate(), 'population': population,
                   'extra': extra or {}}
        temp = path.with_suffix(path.suffix + '.tmp')
        torch.save(payload, temp)
        os.replace(temp, path)

    @classmethod
    def load(cls, path, *, device='cpu'):
        # Only checkpoints made by this program are intended as inputs.
        data = torch.load(path, map_location='cpu', weights_only=True)
        if data.get('schema') != 'erdos86_gps.v1':
            raise ValueError('Unsupported checkpoint')
        trainer = cls(Generator(ModelConfig(**data['config'])), device=device)
        trainer.model.load_state_dict(data['model'])
        trainer.optimizer.load_state_dict(data['optimizer'])
        trainer.steps = data['steps']
        trainer.rng.set_state(data['rng'])
        trainer.augment_rng.setstate(data['augment_rng'])
        return trainer, data['population'], data['extra']


@torch.no_grad()
def sample(model, batch_size, *, seed, temperature=1.0, deadline=None):
    if temperature <= 0:
        raise ValueError('Temperature must be positive')
    model.eval()
    device = next(model.parameters()).device
    count = model.coordinates.shape[0]
    rng = torch.Generator().manual_seed(seed)
    order = torch.stack([torch.randperm(count, generator=rng) for _ in range(batch_size)]).to(device)
    ranks = order.argsort(1)
    uniforms = torch.rand(batch_size, count, generator=rng).to(device)
    states = torch.zeros(batch_size, count, dtype=torch.long, device=device)
    rows = torch.arange(batch_size, device=device)
    forced = torch.zeros(batch_size, dtype=torch.long, device=device)
    for t in range(count):
        check_deadline(deadline)
        steps = torch.full((batch_size,), t, device=device, dtype=torch.long)
        query = order[:, t]
        permitted = allowed_additions(states, model.faces, model.edge_faces)[rows, query]
        with precision_context(device):
            logits = model(states, ranks, steps)[rows, query]
        choose = (uniforms[:, t] < torch.sigmoid(logits.float() / temperature)) & permitted
        forced += ~permitted
        states[rows, query] = choose.long() + 1
    return (states - 1).cpu().tolist(), {'forced_zero_decisions': forced.cpu().tolist(),
                                       'forward_calls': count, 'batch_size': batch_size}
