"""Candidate acceptance: standard-library checks independent of model topology."""
from collections import Counter
from itertools import combinations


def verify_edges(n, edges):
    if type(n) is not int or n < 2:
        raise ValueError('Invalid dimension')
    selected = set()
    adjacency = [set() for _ in range(1 << n)]
    for edge in edges:
        if len(edge) != 2:
            raise ValueError('Malformed edge')
        u, v = edge
        if type(u) is not int or type(v) is not int or not (0 <= u < 1 << n and 0 <= v < 1 << n):
            raise ValueError('Invalid vertex')
        xor = u ^ v
        if xor == 0 or xor & (xor - 1):
            raise ValueError('Not a hypercube edge')
        key = tuple(sorted(edge))
        if key in selected:
            raise ValueError('Duplicate edge')
        selected.add(key)
        adjacency[u].add(v)
        adjacency[v].add(u)
    pairs = Counter(pair for ns in adjacency for pair in combinations(sorted(ns), 2))
    collisions = sum(k * (k - 1) // 2 for k in pairs.values())
    hist = Counter()
    opposite = 0
    for i, j in combinations(range(n), 2):
        for u in range(1 << n):
            if u & ((1 << i) | (1 << j)):
                continue
            a, b, c, d = u, u ^ (1 << i), u ^ (1 << i) ^ (1 << j), u ^ (1 << j)
            present = [tuple(sorted(e)) in selected for e in [(a, b), (b, c), (c, d), (d, a)]]
            hist[sum(present)] += 1
            opposite += sum(present) == 2 and present[0] == present[2] and present[1] == present[3]
    if hist[4] or collisions:
        raise ValueError(f'C4 found: faces={hist[4]}, common-neighbor collisions={collisions}')
    if sum(hist.values()) != n * (n - 1) // 2 * (1 << (n - 2)):
        raise ValueError('Incomplete face enumeration')
    return {'n': n, 'edges': len(selected), 'C4_violations': hist[4],
            'common_neighbor_pair_collisions': collisions,
            'square_histogram': dict(sorted(hist.items())),
            'empty_squares': hist[0], 'opposite_two_edge_squares': opposite,
            'degree_histogram': dict(sorted(Counter(map(len, adjacency)).items()))}
