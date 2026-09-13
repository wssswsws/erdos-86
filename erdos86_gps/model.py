"""GPS-style local variable/factor messages + global variable self-attention.

Each forward pass sees ONLY an already-decided prefix. Attention is global,
not triangular: future VALUES are absent everywhere, including factor features.
"""
from dataclasses import asdict, dataclass
import torch
from torch import nn
from torch.nn import functional as F
from .cube import Cube


@dataclass
class ModelConfig:
    n: int = 7
    width: int = 128
    layers: int = 4
    heads: int = 8
    ff_mult: int = 4
    local: bool = True
    global_attention: bool = True


def mlp(width, multiple=2):
    return nn.Sequential(nn.Linear(width, multiple * width), nn.GELU(), nn.Linear(multiple * width, width))


class GPSBlock(nn.Module):
    def __init__(self, config):
        super().__init__()
        d = config.width
        self.heads = config.heads
        self.use_local, self.use_global = config.local, config.global_attention
        self.pre_norm = nn.LayerNorm(d)
        if self.use_local:
            self.factor_update = mlp(d)
            self.variable_update = mlp(d)
        if self.use_global:
            self.qkv = nn.Linear(d, 3 * d)
            self.attention_out = nn.Linear(d, d)
        self.post_norm = nn.LayerNorm(d)
        self.ff = mlp(d, config.ff_mult)

    def forward(self, h, factor_features, faces, edge_faces):
        z = self.pre_norm(h)
        update = torch.zeros_like(h)
        if self.use_local:
            # Gather implements variable -> constraint -> variable message passing.
            factors = self.factor_update(z[:, faces].mean(dim=2) + factor_features)
            update = update + self.variable_update(factors[:, edge_faces].mean(dim=2))
        if self.use_global:
            batch, edges, width = z.shape
            qkv = self.qkv(z).view(batch, edges, 3, self.heads, width // self.heads)
            q, k, v = qkv.permute(2, 0, 3, 1, 4).unbind(0)
            attended = F.scaled_dot_product_attention(q, k, v, dropout_p=0.0)
            update = update + self.attention_out(attended.transpose(1, 2).reshape(batch, edges, width))
        h = h + update
        return h + self.ff(self.post_norm(h))


class Generator(nn.Module):
    def __init__(self, config=ModelConfig()):
        super().__init__()
        if config.width % config.heads or config.layers < 1:
            raise ValueError('Width must divide into heads; layers must be positive')
        self.config = config
        cube = Cube.build(config.n)
        self.register_buffer('faces', torch.tensor(cube.faces), persistent=False)
        self.register_buffer('edge_faces', torch.tensor(cube.edge_faces), persistent=False)
        # Labeled coordinates break initial symmetry. Training uses cube relabeling;
        # exact equivariance is NOT claimed for these positional features.
        coordinates = [[2 * ((u >> j) & 1) - 1 for j in range(config.n)] +
                       [int((u ^ v) == 1 << j) for j in range(config.n)] for u, v in cube.edges]
        self.register_buffer('coordinates', torch.tensor(coordinates, dtype=torch.float32), persistent=False)
        self.input = nn.Linear(2 * config.n + 6, config.width)
        self.factor_input = nn.Linear(3, config.width)
        self.blocks = nn.ModuleList([GPSBlock(config) for _ in range(config.layers)])
        self.output = nn.Sequential(nn.LayerNorm(config.width), nn.Linear(config.width, 1))

    def forward(self, states, ranks, steps):
        # states: 0=undecided, 1=decided absent, 2=decided present.
        batch, count = states.shape
        encoding = F.one_hot(states, num_classes=3).float()
        rank = ranks.float() / max(count - 1, 1)
        progress = steps.float()[:, None].expand(-1, count) / count
        current = ranks == steps[:, None]
        h = self.input(torch.cat([self.coordinates[None].expand(batch, -1, -1), encoding,
                                 rank[..., None], progress[..., None], current.float()[..., None]], dim=-1))
        face_states = states[:, self.faces]
        selected = (face_states == 2).sum(-1).float()
        unknown = (face_states == 0).sum(-1).float()
        factor_features = self.factor_input(torch.stack([selected / 4, unknown / 4, (3 - selected) / 3], dim=-1))
        for block in self.blocks:
            h = block(h, factor_features, self.faces, self.edge_faces)
        return self.output(h).squeeze(-1)

    def parameter_count(self):
        return sum(p.numel() for p in self.parameters())

    def config_dict(self):
        return asdict(self.config)


def prefix_states(targets, ranks, steps):
    """Unknown values are replaced before ANY neural or factor computation."""
    return torch.where(ranks < steps[:, None], targets.long() + 1, torch.zeros_like(targets, dtype=torch.long))


def allowed_additions(states, faces, edge_faces):
    selected = (states[:, faces] == 2).sum(-1)
    return (selected[:, edge_faces] < 3).all(-1) & (states == 0)
