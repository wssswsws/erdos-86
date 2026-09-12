# Explicit C4-Free Subgraphs of Hypercubes Q9 Through Q15

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3](https://img.shields.io/badge/Python-3-blue.svg)](verify_c4_free.py)

This repository contains explicit edge-list certificates for C4-free subgraphs
of hypercubes `Q9` through `Q15`.

The result was posted as a certificate-verification request on the Erdos
Problems forum:

https://www.erdosproblems.com/forum/thread/86

For the Erdos Problems #86 notation `ex(Q_n, C4)`, the certificates establish
the following lower bounds:

| n | certified lower bound | C4 violations | SHA-256 | certificate |
|---:|---:|---:|---|---|
| 9 | 1505 | 0 | `0994be825ec39d115b65eb1436eace7c1be324448a6ec116d69c8a7e2a75d338` | `q9_edges_repair_from1503_iter2.json` |
| 10 | 3304 | 0 | `24317cb0f821a7e39688d1376ac58c466779fc21d3628085270ddc468ae27c09` | `q10_edges_repair_from3302_iter5.json` |
| 11 | 7164 | 0 | `a396680dd00bd3b86fff26920c5345cebeff4dde3d7dd411fd8ea97ac269274b` | `q11_edges_repair_from7160_probe_fast2.json` |
| 12 | 15372 | 0 | `f1e952df4c40e10418f52b9c778fd8d1313efb1ab41bc8e45266d645a368a2f5` | `q12_edges_repair_from15366_iter3.json` |
| 13 | 32856 | 0 | `f3214c05e66d45a3a300d2a96ee3f3a77982d091990ff5457f1852e98a389dd2` | `q13_edges_repair_from32842_iter2.json` |
| 14 | 69909 | 0 | `78d7ca75e720f920637d72134c7749f9680f7c4c60d31ac67e8948a1fa0d7e32` | `q14_edges_repair_from69895_iter2.json` |
| 15 | 148126 | 0 | `9c98dc35a87d2a2fde9ee115f628144d2851e1dbdf57096ad6e6003d97b8f575` | `q15_edges_repair_from148111_iter1.json` |

The claim is only that these are explicit certified lower bounds. No exactness
claim is made for `n >= 7`, and these finite-dimensional constructions do not
contradict the asymptotic conjecture.

## Why This Matters

For finite extremal graph problems, a useful public result needs more than a
number. It needs the certificate, a verifier, hashes, and a precise statement of
what is and is not being claimed.

This repository is structured around that standard: explicit edge lists,
SHA-256 checksums, a direct verifier, an independent sparse cross-check, and a
conservative lower-bound framing.

## Relation To The BHN General Estimate

The Brass-Harborth-Nienborg general estimate gives a useful comparison point.
Using the commonly cited general form
`0.5 * (n + 0.9 * sqrt(n)) * 2^(n-1)`, the present certificates exceed that
estimate for `Q9`, `Q10`, and `Q11`, but not for `Q12` through `Q15`.

| n | certificate | BHN general estimate | certificate - estimate |
|---:|---:|---:|---:|
| 9 | 1505 | 1497.6 | +7.4 |
| 10 | 3304 | 3288.6 | +15.4 |
| 11 | 7164 | 7160.3 | +3.7 |
| 12 | 15372 | 15480.5 | -108.5 |
| 13 | 32856 | 33269.8 | -413.8 |
| 14 | 69909 | 71137.2 | -1228.2 |
| 15 | 148126 | 151434.7 | -3308.7 |

So the strongest conservative framing is: explicit certificate-level lower
bounds for `Q9` through `Q15`, with small numerical improvements over the BHN
general estimate in `Q9`, `Q10`, and `Q11`.

## Verification

Run:

```bash
python verify_c4_free.py
```

The verifier checks that every listed edge is a valid hypercube edge and then
enumerates every 4-cycle in `Q_n`. A certificate passes only if no 4-cycle has
all four edges selected.

Expected verification summary:

```text
q9_edges_repair_from1503_iter2.json: n=9, edges=1505, cycles=4608, violations=0
q10_edges_repair_from3302_iter5.json: n=10, edges=3304, cycles=11520, violations=0
q11_edges_repair_from7160_probe_fast2.json: n=11, edges=7164, cycles=28160, violations=0
q12_edges_repair_from15366_iter3.json: n=12, edges=15372, cycles=67584, violations=0
q13_edges_repair_from32842_iter2.json: n=13, edges=32856, cycles=159744, violations=0
q14_edges_repair_from69895_iter2.json: n=14, edges=69909, cycles=372736, violations=0
q15_edges_repair_from148111_iter1.json: n=15, edges=148126, cycles=860160, violations=0
```

An earlier local verification run is recorded in
`VERIFY_ALL_CERTIFICATES.log`.

On a local workstation, a fresh verification of all seven bundled certificates
takes a few seconds.

## Independent Cross-Check

The certificate set, including the improved `Q11 >= 7164` certificate, was
independently checked by Minamo Minamoto using a separate sparse cherry-counting
verifier. This verifier does not enumerate the 4-cycles of the hypercube
directly. Instead, it checks the equivalent condition that no unordered pair of
vertices has two common neighbours.

All seven certificates passed that independent check:

- SHA-256 hashes matched `SHA256SUMS`;
- edge counts matched the claimed values;
- all edges were valid hypercube edges;
- no loops or duplicates were found;
- no C4 was detected.

See `independent_crosscheck.md` and `c4_sparse_verifier.py`.

## Contents

- `verify_c4_free.py` - standalone verifier.
- `c4_sparse_verifier.py` - independent sparse cherry-counting verifier.
- `independent_crosscheck.md` - independent certificate-level cross-check.
- `q*_edges_*.json` - edge-list certificates.
- `archive/` - old Q11=7156 certificate retained for the independent
  cross-check record.
- `PAPER_V2.md` - draft note explaining the construction and verification.
- `lift_params.json` - product-lift parameters used in the search stage.
- `SHA256SUMS` - raw file hashes for the certificates.
- `CLAIM_BOUNDARY.md` - precise statement of what is and is not claimed.
- `REPRODUCE.md` - short reproduction instructions.
- `HDF_STATUS.md` - Hard Discovery Factory classification.
- `FORUM_POST_DRAFT_V3.md` - draft forum post for Erdos Problems.

## Disclosure

This was an AI-assisted computational discovery. The result should be judged by
the explicit edge-list certificates and the independent verifier, not by
authorship.
