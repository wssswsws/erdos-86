"""Independent integer-only audit of the seven published Wrona certificates.

This program reads JSON data, never imports upstream code, and checks both
cube faces and common-neighbor pairs. Run from any working directory.
"""
from collections import Counter
from itertools import combinations
from pathlib import Path
import argparse
import hashlib
import json
import time

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {9: 1505, 10: 3304, 11: 7164, 12: 15372,
            13: 32856, 14: 69909, 15: 148126}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify(path, n, expected, expected_digest):
    started = time.monotonic()
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    require(digest == expected_digest, f'{path.name}: SHA-256 mismatch')
    obj = json.loads(raw)
    require(obj['n'] == n and obj['num_edges'] == expected, 'metadata mismatch')
    edges = obj['edges']
    require(len(edges) == expected, 'edge count mismatch')
    vertices = 1 << n
    adjacency = [set() for _ in range(vertices)]
    codes = set()
    for edge in edges:
        require(isinstance(edge, list) and len(edge) == 2, 'invalid edge format')
        u, v = edge
        require(type(u) is int and type(v) is int, 'noninteger endpoint')
        require(0 <= u < vertices and 0 <= v < vertices, 'endpoint out of range')
        delta = u ^ v
        require(delta > 0 and delta & (delta - 1) == 0, 'not a cube edge')
        a, b = sorted((u, v))
        code = a * vertices + b
        require(code not in codes, 'duplicate edge')
        codes.add(code)
        adjacency[u].add(v)
        adjacency[v].add(u)

    seen_pairs = set()
    for neighbors in adjacency:
        for a, b in combinations(sorted(neighbors), 2):
            code = a * vertices + b
            require(code not in seen_pairs, f'C4 detected via common neighbors {a,b}')
            seen_pairs.add(code)
    cherries = len(seen_pairs)
    del seen_pairs

    face_hist = Counter()
    for i, j in combinations(range(n), 2):
        si, sj = 1 << i, 1 << j
        mask = si | sj
        for x in range(vertices):
            if x & mask:
                continue
            a, b, c, d = x, x | si, x | si | sj, x | sj
            count = ((b in adjacency[a]) + (c in adjacency[b])
                     + (d in adjacency[c]) + (a in adjacency[d]))
            require(count <= 3, f'C4 detected on face {(x,i,j)}')
            face_hist[count] += 1
    face_count = n * (n - 1) // 2 * (1 << (n - 2))
    require(sum(face_hist.values()) == face_count, 'incomplete face enumeration')
    return {'file': path.name, 'n': n, 'edges': len(codes), 'sha256': digest,
            'vertex_support': sum(bool(s) for s in adjacency),
            'cube_squares': face_count, 'square_edge_histogram': dict(sorted(face_hist.items())),
            'common_neighbor_pairs_checked': cherries, 'C4_violations': 0,
            'common_neighbor_pair_collisions': 0,
            'elapsed_seconds': round(time.monotonic() - started, 3)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-dir', type=Path,
                        default=ROOT / 'references/user/source-pack/wrona')
    args = parser.parse_args()
    hashes = {}
    for line in (args.source_dir / 'SHA256SUMS').read_text().splitlines():
        if line.strip():
            digest, name = line.split(maxsplit=1)
            hashes[name.lstrip('*')] = digest
    results = []
    for n, expected in EXPECTED.items():
        matches = list(args.source_dir.glob(f'q{n}_edges_*.json'))
        require(len(matches) == 1, f'expected exactly one current Q{n} certificate')
        results.append(verify(matches[0], n, expected, hashes[matches[0].name]))
    print(json.dumps({'schema_version': 'erdos86.independent_certificate_audit.v1',
                      'upstream_commit': '7b8554bf3e7562a4bc1fb217757e709ba63c3e26',
                      'results': results, 'passed': True}, indent=2))


if __name__ == '__main__':
    main()
