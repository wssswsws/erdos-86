# Audited Q7 training representatives with 304 edges

Source: [Minamoto, pinned commit b94577f](https://github.com/minamominamoto/c4free-hypercube/tree/b94577fd5e06e62e1c6895b7e4d2b0abeaea411b). The upstream license is in `../minamoto-b94577f/LICENSE`. These are published constructions, not discoveries of this project.

`representatives.jsonl` contains 180 C4-free Q7 graphs with 304 edges, one representative per orbit in the published catalogue. Initial uniform representative sampling followed by coordinate permutations and XOR translations gives each catalogue orbit equal expected weight. Augmentation changes labels, not orbits.

## Audit scope

`audit.json` binds the source revision and the hashes of input and representative files:

- `scripts/build_q7_corpus.py` used the fixed independent integer verifier on all 19,866 original constructions: vertex ranges, cube edges, duplicates, all squares, and common-neighbor conditions. Every graph had exactly 304 edges, with no duplicate exact labelings.
- A separately written mapping check verified all 19,866 coordinate-permutation/XOR witnesses from an orbit representative to its catalogue graph.
- The pinned upstream `q7_orbit_witness_check.py --canonical` was read and rerun over all 645,120 cube symmetries for each of the 180 representatives, confirming recorded minima and their distinctness. See `canonical-check.log`. This is a complete rerun of the upstream canonicalization algorithm, not a second independently designed algorithm.

The catalogue contains 389 odd-square labeled graphs, corresponding to six representative orbits. The other 174 representatives are outside that class. The generator still permits empty and two-edge squares.

Training explicitly loads `--population representatives.jsonl --population-audit audit.json`. A mismatched hash, representative count, edge count, or incomplete audit stops loading. The record binds previously audited files; startup does not repeat the entire orbit census.

## Training and holdout boundaries

The first corpus pilot used all 180 representatives without a holdout and made no unseen-orbit generalization claim. Subsequent elite pools were selected by edge count and deduplicated by exact labeling, not kept uniformly weighted by orbit.

The later diagnostic suite splits 144 training and 36 held-out representatives before augmentation and excludes generated 304-edge-or-larger graphs from feedback. See the [diagnostic plan](../../../docs/graphgps-pilot-diagnostic-plan.md). This holdout is specific to those runs; the project had previously used all 180.

The 180 orbits describe the published catalogue only. They are not a complete classification of all possible 304-edge Q7 graphs.

## Reproduce the audit

The full original catalogue is approximately 64 MB and is excluded from Git. Download `q7_edges_304.jsonl.part1`, `.part2`, and `.part3` from the pinned upstream commit into `references/corpora/minamoto-b94577f/`. The checkers, witnesses, and license are included locally. Then run from the repository root:

```bash
python3 scripts/build_q7_corpus.py --canonical
```

Graph and mapping checks use the Python standard library; complete canonicalization additionally requires NumPy. Without `--canonical`, the resulting audit remains incomplete and cannot authorize production training.
