"""Independent certificate verifier. Reads data only, standard library only."""
from pathlib import Path
from collections import Counter
from itertools import combinations
import json, hashlib
ROOT = Path(__file__).resolve().parent
results = []
for name, n, expected in [("q8_odd_square_682.json", 8, 682), ("selected_edges_best.json", 7, 304)]:
    raw = (ROOT / ("86-" + name)).read_bytes()
    obj = json.loads(raw)
    edges = obj["edges"]
    assert obj["n"] == n and len(edges) == expected
    norm = []
    adj = [set() for _ in range(1 << n)]
    for e in edges:
        assert len(e) == 2
        a,b = e
        assert type(a) is int and type(b) is int
        assert 0 <= a < 1 << n and 0 <= b < 1 << n
        d = a ^ b
        assert d > 0 and d & (d-1) == 0
        norm.append(tuple(sorted((a,b))))
        adj[a].add(b); adj[b].add(a)
    E = set(norm)
    assert len(E) == expected
    # Independent graph-theoretic test: no vertex pair has two common neighbors.
    pairs = set()
    for neighbors in adj:
        for pair in combinations(sorted(neighbors),2):
            assert pair not in pairs, ("C4", pair)
            pairs.add(pair)
    # Also enumerate all cube squares, recording the stronger odd-square property.
    hist = Counter()
    for i,j in combinations(range(n),2):
        mask = (1 << i) | (1 << j)
        for x in range(1 << n):
            if x & mask: continue
            a,b,c,d = x,x^(1<<i),x^mask,x^(1<<j)
            hist[sum(tuple(sorted(e)) in E for e in [(a,b),(b,c),(c,d),(d,a)])] += 1
    assert hist[4] == 0
    assert sum(hist.values()) == n*(n-1)//2 * (1 << (n-2))
    if n == 8: assert set(hist).issubset({1,3})
    digest = hashlib.sha256(raw).hexdigest()
    if n == 8:
        manifest = (ROOT/"86-ODDSQUARE_BRIDGE_SHA256SUMS.txt").read_text()
        assert digest + "  " + name in manifest
    results.append({"file": name, "n":n, "edges":len(E), "sha256":digest,
                    "cube_squares":sum(hist.values()), "square_edge_histogram":dict(sorted(hist.items())),
                    "degree_histogram":dict(sorted(Counter(map(len,adj)).items())),
                    "C4_violations":0, "common_neighbor_pair_collisions":0})
print(json.dumps(results, indent=2))
