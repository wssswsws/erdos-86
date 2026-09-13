#!/usr/bin/env python3
"""Read published data only; independently validate graphs and orbit witnesses.

Canonical minimality is checked separately by the reviewed upstream checker.
No executable code from the downloaded data is imported here.
"""
import argparse
from collections import Counter
from hashlib import sha256
from itertools import permutations
import json
from pathlib import Path
import sys
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from erdos86_gps.verify import verify_edges

COMMIT = 'b94577fd5e06e62e1c6895b7e4d2b0abeaea411b'
PART_HASHES = [
    'c6ab51d185047b2352406e88d498d9d606a1afadd6cdd1809791e3fc8d2b8c34',
    'bf67e1b6c8779688787f6c919eceeea593855e333ff8199a15e84bd39050f791',
    'b3b8fc36d71a17c2c47bfc60baf7f561d884fef73b362db31189669ff177afb6',
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def transform(edges, perm, xor):
    require(sorted(perm) == list(range(7)) and type(xor) is int and 0 <= xor < 128,
            'Invalid cube automorphism')
    vertices = [sum(((v >> d) & 1) << perm[d] for d in range(7)) ^ xor for v in range(128)]
    return frozenset(tuple(sorted((vertices[u], vertices[v]))) for u, v in edges)


def build(source, output, *, canonical=False):
    started = time.monotonic()
    witnesses = json.loads((source / 'q7_orbit_witnesses.json').read_text())
    census = json.loads((source / 'q7_orbit_census.json').read_text())
    graphs, validations, inputs = [], [], {}
    for number, expected in enumerate(PART_HASHES, 1):
        name = f'q7_edges_304.jsonl.part{number}'
        raw = (source / name).read_bytes()
        require(sha256(raw).hexdigest() == expected, f'Hash mismatch: {name}')
        inputs[name] = {'sha256': expected, 'bytes': len(raw)}
        for line in raw.decode().splitlines():
            data = json.loads(line)
            require(data.get('n', 7) == 7, 'Wrong dimension')
            validation = verify_edges(7, data['edges'])
            require(validation['edges'] == 304, 'Not a 304-edge graph')
            graphs.append(frozenset(tuple(sorted(e)) for e in data['edges']))
            validations.append(validation)
        print(f'Validated {len(graphs)} graphs', flush=True)
    require(len(graphs) == len(set(graphs)) == 19866, 'Unexpected catalogue size or exact duplicate')
    reps, rows = witnesses['reps'], witnesses['witness']
    require(witnesses['orbits'] == len(reps) == census['orbits'] == 180, 'Wrong orbit count')
    require(len(rows) == len(graphs), 'Incomplete witnesses')
    assignment = [row[0] for row in rows]
    require(assignment == census['assignment'], 'Census assignment mismatch')
    require([assignment.count(i) for i in range(180)] == census['catalogue_sizes'], 'Orbit sizes mismatch')
    perms = list(permutations(range(7)))
    for i, (orbit, permutation, xor) in enumerate(rows):
        require(type(orbit) is int and 0 <= orbit < 180, 'Bad orbit id')
        require(type(permutation) is int and 0 <= permutation < len(perms), 'Bad permutation id')
        require(transform(graphs[reps[orbit]], perms[permutation], xor) == graphs[i],
                f'Invalid representative-to-member witness at index {i}')
    # This certifies coverage by at most 180 orbits. Distinctness requires the
    # separate exhaustive canonical-minimality check recorded in audit.json.
    output.mkdir(parents=True, exist_ok=True)
    records = []
    for orbit, index in enumerate(reps):
        require(index == assignment.index(orbit), 'Representative is not first member')
        records.append({'n': 7, 'edges': sorted(graphs[index]), 'source_index': index,
                        'published_orbit_id': orbit})
    payload = ''.join(json.dumps(record, separators=(',', ':')) + '\n' for record in records).encode()
    (output / 'representatives.jsonl').write_bytes(payload)
    for name in ['q7_orbit_census.json', 'q7_orbit_witnesses.json', 'q7_orbit_witness_check.py',
                 'LICENSE', 'ORIGINAL_DATA_SHA256SUMS.txt']:
        raw = (source / name).read_bytes()
        inputs[name] = {'sha256': sha256(raw).hexdigest(), 'bytes': len(raw)}
    audit = {
        'schema': 'erdos86.corpus.audit.v1', 'source_commit': COMMIT,
        'source_url': f'https://github.com/minamominamoto/c4free-hypercube/tree/{COMMIT}',
        'inputs': inputs, 'catalogue_rows': len(graphs), 'exact_label_unique': len(set(graphs)),
        'independently_verified_304_C4_free': len(graphs), 'witnesses_verified': len(rows),
        'representatives': len(records), 'canonical_minimality_verified': False,
        'catalogue_odd_square_count': sum(set(v['square_histogram']) <= {1, 3} for v in validations),
        'representative_odd_square_count': sum(set(validations[i]['square_histogram']) <= {1, 3} for i in reps),
        'square_histogram_classes': len({tuple(v['square_histogram'].items()) for v in validations}),
        'population_sha256': sha256(payload).hexdigest(),
        'verification_seconds': time.monotonic() - started,
        'verifier_sha256': sha256((ROOT / 'erdos86_gps/verify.py').read_bytes()).hexdigest(),
        'builder_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
        'scope': 'Released catalogue only; no completeness claim for all 304-edge graphs; no held-out evaluation.',
    }
    if canonical:
        require(inputs['q7_orbit_witness_check.py']['sha256'] ==
                '496c165a5e9b26f927eb1ef8e777705df11a5be875390175d47f556a42070ac5',
                'Upstream canonical checker differs from the reviewed version')
        result = subprocess.run([sys.executable, '-u', 'q7_orbit_witness_check.py', '--canonical'],
                                cwd=source, text=True, capture_output=True, check=True)
        log = result.stdout + result.stderr
        require('canonical minimality re-verified for orbits 0..179: 0 failures' in log
                and 'RESULT: certificate verifies' in log, 'Canonical check incomplete')
        (output / 'canonical-check.log').write_text(log)
        audit.update(canonical_minimality_verified=True,
                     canonical_check={'checker': 'q7_orbit_witness_check.py --canonical',
                                      'exit_code': result.returncode, 'representatives_checked': 180,
                                      'group_elements_per_representative': 645120,
                                      'log_sha256': sha256(log.encode()).hexdigest(),
                                      'implementation': 'Reviewed upstream checker; complete rerun, not a second independent canonical algorithm.'})
    (output / 'audit.json').write_text(json.dumps(audit, indent=2) + '\n')
    print(json.dumps({k: v for k, v in audit.items() if k != 'inputs'}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / 'references/corpora/minamoto-b94577f')
    parser.add_argument('--output', type=Path, default=ROOT / 'references/corpora/q7-304-orbits')
    parser.add_argument('--canonical', action='store_true', help='Also rerun the pinned upstream exhaustive canonical checker')
    args = parser.parse_args()
    build(args.source, args.output, canonical=args.canonical)
