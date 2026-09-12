# Independent Cross-Check of Q9-Q15 Certificates

Date: 2026-05-22

Source repository: `github.com/rafalwronapl/erdos86-hypercube-c4`

Checked by: independent reviewer, Minamoto side, not the certificate author.

Context: R. Wrona requested certificate-level verification before public posting
on Erdos Problems #86. The Q11 certificate was first checked at 7156 edges and
then re-checked after a local repair improvement to 7164 edges. The current
repository uses the 7164-edge Q11 certificate in the main certificate table and
keeps the earlier 7156-edge Q11 file in `archive/`.

## Method

The repository's `verify_c4_free.py` verifies C4-freeness by enumerating all
`binom(n,2) * 2^(n-2)` four-cycles of `Q_n` and checking that no square is fully
present.

This independent review instead used sparse cherry counting:

```text
C4-free <=> no unordered vertex pair has at least two common neighbours
```

Equivalently, no length-2 path endpoint pair may occur through two different
centres. This is a different algorithm and a separate implementation from the
repository's full four-cycle enumeration verifier.

Each file's SHA-256 hash was also matched against `SHA256SUMS`.

## Result

All seven certificates passed.

| n | claimed bound | SHA-256 | unique edges | invalid range/dist/loop/dup | C4-free | support | degree range |
|---:|---:|---|---:|---|---|---:|---|
| 9 | 1505 | match | 1505 | 0/0/0/0 | yes | 512/512 | 4-7 |
| 10 | 3304 | match | 3304 | 0/0/0/0 | yes | 1024/1024 | 5-9 |
| 11 | 7164 | match | 7164 | 0/0/0/0 | yes | 2048/2048 | 5-10 |
| 12 | 15372 | match | 15372 | 0/0/0/0 | yes | 4096/4096 | 5-11 |
| 13 | 32856 | match | 32856 | 0/0/0/0 | yes | 8192/8192 | 5-12 |
| 14 | 69909 | match | 69909 | 0/0/0/0 | yes | 16384/16384 | 5-13 |
| 15 | 148126 | match | 148126 | 0/0/0/0 | yes | 32768/32768 | 5-14 |

The lower bounds therefore hold at the certificate level.

## Scope

Established:

- each listed edge is a valid hypercube edge in the stated `Q_n`;
- there are no loops or duplicate edges;
- the edge counts match the claimed bounds;
- no C4 was detected by the independent cherry-counting verifier;
- SHA-256 hashes matched the repository's `SHA256SUMS`.

Not established by this check:

- optimality;
- novelty against every possible unpublished or published construction;
- correctness or reproducibility of the search pipeline that found the edge
  lists.

The check verifies the certificates, not a claim of exactness or best possible
values.

## Reproduce

Run:

```bash
python c4_sparse_verifier.py q9_edges_repair_from1503_iter2.json --n 9 --expected-edges 1505
python c4_sparse_verifier.py q10_edges_repair_from3302_iter5.json --n 10 --expected-edges 3304
python c4_sparse_verifier.py q11_edges_repair_from7160_probe_fast2.json --n 11 --expected-edges 7164
python c4_sparse_verifier.py q12_edges_repair_from15366_iter3.json --n 12 --expected-edges 15372
python c4_sparse_verifier.py q13_edges_repair_from32842_iter2.json --n 13 --expected-edges 32856
python c4_sparse_verifier.py q14_edges_repair_from69895_iter2.json --n 14 --expected-edges 69909
python c4_sparse_verifier.py q15_edges_repair_from148111_iter1.json --n 15 --expected-edges 148126
```
