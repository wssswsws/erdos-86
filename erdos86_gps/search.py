"""Bounded classical baseline / local phase. No upstream search code imported."""
import random
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


def local_search(cube, bits, *, seed, kicks=16, kick_min=4, kick_max=12):
    rng = random.Random(seed)
    best = current = repair(cube, bits, rng)
    for _ in range(kicks):
        present = [i for i, value in enumerate(current) if value]
        proposal = current.copy()
        k = min(len(present), rng.randint(kick_min, kick_max))
        for e in rng.sample(present, k):
            proposal[e] = 0
        candidate = repair(cube, proposal, rng)
        # Accept plateau movement; best witness is kept separately.
        if sum(candidate) >= sum(current):
            current = candidate
        if sum(candidate) > sum(best):
            best = candidate
    verify_edges(cube.n, cube.decode(best))
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
