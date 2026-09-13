"""Bounded classical baseline / local phase. No upstream search code imported."""
import random
import math
from .verify import verify_edges


def repair(cube, bits, rng):
    bits = list(map(int, bits))
    counts = [sum(bits[e] for e in face) for face in cube.faces]
    # General repair supports imported invalid candidates too.
    while max(counts) == 4:
        bad = [f for f, count in enumerate(counts) if count == 4]
        candidates = list({e for f in bad for e in cube.faces[f]})
        rng.shuffle(candidates)
        e = max(candidates, key=lambda e: sum(counts[f] == 4 for f in cube.edge_faces[e]))
        bits[e] = 0
        for f in cube.edge_faces[e]:
            counts[f] -= 1
    missing = [e for e, keep in enumerate(bits) if not keep]
    rng.shuffle(missing)
    for e in missing:
        if all(counts[f] < 3 for f in cube.edge_faces[e]):
            bits[e] = 1
            for f in cube.edge_faces[e]:
                counts[f] += 1
    return bits


def local_search(cube, bits, *, seed, kicks=16, kick_min=4, kick_max=12,
                 temperature_start=0.0, temperature_end=0.0, kick_mode='random', stats=None):
    if (kicks < 0 or kick_min < 1 or kick_max < kick_min
            or temperature_start < 0 or temperature_end < 0
            or kick_mode not in {'random', 'mixed'}):
        raise ValueError('Invalid local search configuration')
    rng = random.Random(seed)
    best = current = repair(cube, bits, rng)
    if stats is not None:
        stats.update(accepted_downhill=0, accepted_plateau=0, best_edges=sum(best))
    for step in range(kicks):
        present = [i for i, value in enumerate(current) if value]
        proposal = current.copy()
        k = min(len(present), rng.randint(kick_min, kick_max))
        if kick_mode == 'mixed' and k and rng.random() < 0.5:
            # Grow a region through shared square constraints, then fill if disconnected.
            chosen = {rng.choice(present)}
            while len(chosen) < k:
                adjacent = {j for e in chosen for f in cube.edge_faces[e] for j in cube.faces[f]
                            if current[j] and j not in chosen}
                chosen.add(rng.choice(sorted(adjacent or (set(present) - chosen))))
        else:
            chosen = rng.sample(present, k)
        for e in chosen:
            proposal[e] = 0
        candidate = repair(cube, proposal, rng)
        delta = sum(candidate) - sum(current)
        temperature = temperature_start + (temperature_end - temperature_start) * step / max(kicks - 1, 1)
        accept = delta >= 0 or (temperature > 0 and rng.random() < math.exp(delta / temperature))
        # Current may move downhill; the independently checked best is never lost.
        if accept:
            current = candidate
            if stats is not None:
                stats['accepted_downhill'] += int(delta < 0)
                stats['accepted_plateau'] += int(delta == 0)
        if sum(candidate) > sum(best):
            best = candidate
    verify_edges(cube.n, cube.decode(best))
    if stats is not None:
        stats['best_edges'] = sum(best)
    return best


def bootstrap(cube, known_bits, count, seed):
    """Functional starting population, NOT an audited independent orbit corpus."""
    rng = random.Random(seed)
    graphs = {tuple(known_bits)}
    for i in range(max(0, count - 1)):
        if i % 2:
            start = [0] * len(cube.edges)
        else:
            start = known_bits.copy()
            for e in rng.sample([e for e, x in enumerate(start) if x], min(32, sum(start))):
                start[e] = 0
        graphs.add(tuple(local_search(cube, start, seed=seed + i + 1, kicks=2)))
    return [list(g) for g in sorted(graphs)]
