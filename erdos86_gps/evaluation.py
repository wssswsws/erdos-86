"""Fixed random-prefix evaluation, isolated from every training RNG."""
from hashlib import sha256
import json
import random

import torch
from torch.nn import functional as F

from .engine import check_deadline, precision_context
from .model import allowed_additions, prefix_states


def fixed_prefixes(cube, population, count, seed):
    rng = random.Random(seed)
    torch_rng = torch.Generator().manual_seed(seed)
    rows = []
    for _ in range(count):
        perm = list(range(cube.n))
        rng.shuffle(perm)
        rows.append(cube.relabel(rng.choice(population), perm, rng.randrange(1 << cube.n)))
    targets = torch.tensor(rows, dtype=torch.long)
    edges = targets.shape[1]
    orders = torch.stack([torch.randperm(edges, generator=torch_rng) for _ in rows])
    ranks = orders.argsort(1)
    steps = torch.randint(edges, (count,), generator=torch_rng)
    query = orders.gather(1, steps[:, None])
    data = {'states': prefix_states(targets, ranks, steps), 'ranks': ranks, 'steps': steps,
            'query': query, 'labels': targets.gather(1, query).squeeze(1).float()}
    digest = sha256(json.dumps({k: v.tolist() for k, v in data.items()}, separators=(',', ':')).encode()).hexdigest()
    return data, {'seed': seed, 'count': count, 'sha256': digest}


@torch.no_grad()
def evaluate_prefixes(model, data, batch_size, deadline=None):
    was_training = model.training
    model.eval()
    device = next(model.parameters()).device
    totals = [{'examples': 0, 'nonforced': 0, 'nll_sum': 0.0, 'correct_nonforced': 0} for _ in range(4)]
    count = len(data['steps'])
    try:
        for offset in range(0, count, batch_size):
            check_deadline(deadline)
            b = {k: v[offset:offset + batch_size].to(device) for k, v in data.items()}
            allowed = allowed_additions(b['states'], model.faces, model.edge_faces).gather(1, b['query']).squeeze(1)
            if torch.any((~allowed) & (b['labels'] == 1)):
                raise ValueError('Invalid evaluation target')
            with precision_context(device):
                logits = model(b['states'], b['ranks'], b['steps']).gather(1, b['query']).squeeze(1)
            loss = F.binary_cross_entropy_with_logits(logits.float(), b['labels'], reduction='none') * allowed
            if not torch.isfinite(loss).all():
                raise FloatingPointError('Non-finite evaluation loss')
            bins = (4 * b['steps'] // b['states'].shape[1]).clamp(max=3)
            for i, total in enumerate(totals):
                mask = bins == i
                total['examples'] += int(mask.sum())
                total['nonforced'] += int((allowed & mask).sum())
                total['nll_sum'] += float(loss[mask].sum())
                total['correct_nonforced'] += int((((logits >= 0) == b['labels'].bool()) & allowed & mask).sum())
    finally:
        model.train(was_training)

    def finish(row):
        return {**row, 'mean_nll': row['nll_sum'] / row['examples'] if row['examples'] else None,
                'conditional_bce_nonforced': row['nll_sum'] / row['nonforced'] if row['nonforced'] else None,
                'accuracy_nonforced': row['correct_nonforced'] / row['nonforced'] if row['nonforced'] else None}
    overall = {key: sum(row[key] for row in totals) for key in totals[0]}
    return {**finish(overall), 'prefix_quartiles': [finish(row) for row in totals]}
