# Explicit C4-Free Subgraphs of Hypercubes Q9 Through Q15

R. Wrona

Independent researcher

Contact: rafalwronapl@gmail.com

Draft v2, 2026-05-11

2020 Mathematics Subject Classification: 05C35, 05C62, 05C50.

Keywords: hypercube, C4-free subgraph, extremal graph theory, computational construction, certificate verification.

## Abstract

Let `ex(Q_n,C4)` denote the maximum number of edges in a C4-free subgraph of the `n`-dimensional hypercube. We give explicit edge-list certificates establishing

\[
\begin{aligned}
\mathrm{ex}(Q_9,C_4)&\ge 1505, &
\mathrm{ex}(Q_{10},C_4)&\ge 3304, &
\mathrm{ex}(Q_{11},C_4)&\ge 7164,\\
\mathrm{ex}(Q_{12},C_4)&\ge 15372, &
\mathrm{ex}(Q_{13},C_4)&\ge 32856, &
\mathrm{ex}(Q_{14},C_4)&\ge 69909,\\
\mathrm{ex}(Q_{15},C_4)&\ge 148126.
\end{aligned}
\]

These extend the explicit certificate table beyond the values `ex(Q7,C4) >= 304` and `ex(Q8,C4) >= 680` reported by Minamoto. Each construction is supplied as a JSON edge-list certificate and was verified by exhaustive enumeration of all 4-cycles in the corresponding hypercube. The constructions were found by a two-stage computational pipeline: a product lift using automorphisms of the hypercube, followed by a local ILP repair step on C4-incidence neighborhoods. We make no exactness claims for `n >= 7`.

## 1. Introduction

The hypercube `Q_n` has vertex set `{0,1}^n`; two vertices are adjacent when they differ in exactly one coordinate. Thus

```text
|V(Q_n)| = 2^n,        |E(Q_n)| = n 2^(n-1).
```

The C4-free extremal problem for the hypercube asks for

```text
ex(Q_n,C4) = max {|E(H)| : H subgraph Q_n and H contains no C4}.
```

This is problem #86 in the Erdos Problems database. The standard asymptotic conjecture is

```text
ex(Q_n,C4) = (1/2 + o(1)) n 2^(n-1).
```

Balogh, Hu, Lidicky and Liu proved that a C4-free subgraph of `Q_n` has at most `0.6068 |E(Q_n)|` edges for sufficiently large `n` in their flag-algebra framework. Baber improved the asymptotic upper-bound constant to `0.60318`.

For small dimensions, Brouwer and Etzion determined the exact values up to `n=6`. Minamoto recently gave explicit constructions with 304 edges in `Q7` and 680 edges in `Q8`, together with edge lists and verification code. We are not aware of a previously published explicit certificate table for `ex(Q_n,C4)` for `n >= 9`.

The main contribution of this note is a certified lower-bound table for `9 <= n <= 15`. Compared with the commonly cited Brass-Harborth-Nienborg general estimate `0.5 * (n + 0.9 sqrt(n)) * 2^(n-1)`, the certificates improve the numerical lower bound for `Q9`, `Q10`, and `Q11`; for `Q12` through `Q15` they should be viewed as explicit certificate-level constructions rather than improvements over that general estimate.

## 2. Preliminaries

We identify vertices of `Q_n` with integers `0,...,2^n-1` via binary expansion. An edge is an unordered pair `{u,v}` such that `u xor v` is a power of two.

Every 4-cycle in `Q_n` is determined uniquely by a base vertex `b` and two dimensions `i < j` such that the `i`-th and `j`-th bits of `b` are zero. The cycle has vertices

```text
b, b + 2^i, b + 2^j, b + 2^i + 2^j.
```

Therefore the number of 4-cycles in `Q_n` is

```text
2^(n-2) * binom(n,2).
```

The automorphism group of `Q_n` is the semidirect product `S_n lt (Z/2Z)^n`, acting by coordinate permutations followed by xor with a fixed flip mask.

If `G` is a subgraph of `Q_n`, then `G` is bipartite. Hence for the independence number of any subgraph `F subseteq Q_n`, Konig's theorem gives

```text
alpha(F) = |V(Q_n)| - nu(F),
```

where `nu(F)` is the maximum matching size.

## 3. Construction Method

### 3.1 Product Lift

Let `G subseteq Q_n` be C4-free with `m` edges. We construct a subgraph of `Q_{n+1}` by using two copies of `Q_n`.

Choose an automorphism `g in Aut(Q_n)`. Put `G` in slice 0 and `gG` in slice 1. Then add cross edges `(v, v+2^n)` for vertices `v` in a set `I subseteq V(Q_n)`.

The only new 4-cycles not contained in a slice use one old dimension and the new dimension. Such a 4-cycle appears exactly when `{u,v}` is an edge of both `G` and `gG`, and both `u` and `v` are selected for cross edges. Therefore the construction is C4-free precisely when `I` is an independent set in the intersection graph

```text
G cap gG.
```

Since this graph is bipartite, we compute a maximum independent set exactly through maximum matching. The lifted graph has

```text
2m + alpha(G cap gG)
```

edges.

For `Q9` and `Q10`, the automorphism search used simulated annealing/local search over coordinate permutations and flip masks. For `Q11` through `Q15`, we used random automorphism search with exact matching evaluation for each candidate automorphism; the successful runs used 400, 300, 150, 100 and 50 random trials respectively.

### 3.2 Local ILP Repair

The second step is a local repair procedure that starts from a certified C4-free graph `H subseteq Q_n`. It is important that this is not a fixed subcube-window search. The implemented repair neighborhood is adaptive and is built from the C4-incidence structure of a candidate absent edge.

For an absent hypercube edge `e`, define its conflict count to be the number of 4-cycles containing `e` in which the other three edges are already present in `H`. Adding `e` alone would close exactly these conflicts.

For each candidate absent edge, ordered by increasing conflict count, the repair step does the following.

1. Force the absent edge `e` to be selected.
2. Form an initial seed consisting of `e` and all edges in the conflicting 4-cycles.
3. Expand this seed for radius `r` in the edge-C4 incidence graph: at each expansion step, add every edge lying in a 4-cycle with a frontier edge.
4. Freeze all selected edges outside the resulting neighborhood.
5. Solve a binary ILP on the neighborhood edges:
   - the forced edge `e` must be selected;
   - for every 4-cycle, the number of selected variable edges plus fixed selected outside edges is at most 3;
   - maximize the total number of selected edges.
6. If the resulting graph has more edges and verifies as C4-free, keep it.

The default implementation uses three passes with radii `1,2,3`, testing only the lowest-conflict candidates in each pass. All ILP subproblems were solved with SCIP through PySCIPOpt.

This repair step can move the construction outside the product-lift family. It was essential for all final values in the table below.

## 4. Results

### Theorem 1

The following lower bounds hold.

| n | lower bound for `ex(Q_n,C4)` | density `|E|/(n2^(n-1))` | C4 cycles checked | certificate |
|---:|---:|---:|---:|---|
| 9 | 1505 | 0.6532 | 4608 | `q9_edges_repair_from1503_iter2.json` |
| 10 | 3304 | 0.6453 | 11520 | `q10_edges_repair_from3302_iter5.json` |
| 11 | 7164 | 0.6360 | 28160 | `q11_edges_repair_from7160_probe_fast2.json` |
| 12 | 15372 | 0.6255 | 67584 | `q12_edges_repair_from15366_iter3.json` |
| 13 | 32856 | 0.6170 | 159744 | `q13_edges_repair_from32842_iter2.json` |
| 14 | 69909 | 0.6096 | 372736 | `q14_edges_repair_from69895_iter2.json` |
| 15 | 148126 | 0.6028 | 860160 | `q15_edges_repair_from148111_iter1.json` |

Proof. Each listed certificate is an explicit edge list in `Q_n`. The verification routine in Section 5 checks that every listed edge is a valid hypercube edge and then enumerates all `2^(n-2) binom(n,2)` 4-cycles of `Q_n`. In every case the number of 4-cycles whose four edges are all present is zero. Therefore each certificate gives a C4-free subgraph of `Q_n` with the listed number of edges. This proves the stated lower bounds.

### 4.1 Construction Chain

The actual chain of constructions was as follows.

```text
Q8 = 680  (Minamoto)
  -> lift to Q9 = 1501
  -> repair to Q9 = 1505

Q9 = 1501
  -> lift to Q10 = 3292
  -> repair to Q10 = 3304

Q10 = 3304
  -> lift to Q11 = 7142
  -> repair to Q11 = 7164

Q11 = 7151
  -> lift to Q12 = 15350
  -> repair to Q12 = 15372

Q12 = 15366
  -> lift to Q13 = 32829
  -> repair to Q13 = 32856

Q13 = 32856
  -> lift to Q14 = 69883
  -> repair to Q14 = 69909

Q14 = 69909
  -> lift to Q15 = 148111
  -> repair to Q15 = 148126
```

The transition from `Q9` to `Q10` is exceptional: the repaired `Q9=1505` certificate was not the best parent for the next lift in our tests. Re-lifting from `Q9=1505` produced only `Q10=3285`, while lifting from the earlier `Q9=1501` certificate and then repairing gave `Q10=3304`. For later dimensions, the parent used for the next lift was a repaired certificate, though not always the final latest repair iteration.

This is an empirical observation about compatibility with the next automorphism search, not a theorem.

### 4.2 Upper-Bound Context

The following elementary subcube counting lemma provides a useful upper-bound context.

Lemma 2. For `n >= 2`,

```text
(n-1) ex(Q_n,C4) <= 2n ex(Q_{n-1},C4).
```

Proof. The graph `Q_n` has `2n` codimension-one subcubes, each isomorphic to `Q_{n-1}`. Every edge of `Q_n` lies in exactly `n-1` such subcubes. If `H` is a C4-free subgraph of `Q_n`, then each intersection of `H` with a codimension-one subcube has at most `ex(Q_{n-1},C4)` edges. Summing over all codimension-one subcubes gives

```text
(n-1)|E(H)| <= 2n ex(Q_{n-1},C4).
```

Maximizing over `H` proves the lemma.

The table below separates rigorous upper bounds from conditional ones. The conditional column assumes the unproved equalities `ex(Q7,C4)=304` and `ex(Q8,C4)=680`.

| n | lower bound | rigorous UB by Lemma 2 | conditional UB |
|---:|---:|---:|---:|
| 7 | 304 | 308 | 308 |
| 8 | 680 | 704 | 694 |
| 9 | 1505 | 1584 | 1530 |
| 10 | 3304 | 3520 | 3400 |
| 11 | 7164 | 7744 | 7480 |
| 12 | 15372 | 16896 | 16320 |
| 13 | 32856 | 36608 | 35360 |
| 14 | 69909 | 78848 | 76160 |
| 15 | 148126 | 168960 | 163200 |

For example, the rigorous chain uses `ex(Q6,C4)=132`, giving `Q7 <= floor((14/6)132)=308`, then `Q8 <= floor((16/7)308)=704`, and so on. The conditional chain replaces `Q7 <= 308` by `Q7=304` and `Q8 <= 704` by `Q8=680`.

We do not claim that the subcube lemma is new.

### 4.3 Lower-Bound Context

The Brass-Harborth-Nienborg construction gives the commonly cited general estimate

```text
0.5 * (n + 0.9 sqrt(n)) * 2^(n-1)
```

for general `n >= 9`. The comparison is:

| n | certificate | BHN general estimate | difference |
|---:|---:|---:|---:|
| 9 | 1505 | 1497.6 | +7.4 |
| 10 | 3304 | 3288.6 | +15.4 |
| 11 | 7164 | 7160.3 | +3.7 |
| 12 | 15372 | 15480.5 | -108.5 |
| 13 | 32856 | 33269.8 | -413.8 |
| 14 | 69909 | 71137.2 | -1228.2 |
| 15 | 148126 | 151434.7 | -3308.7 |

Thus the `Q9`, `Q10`, and `Q11` certificates improve this general numerical estimate. The remaining certificates are still valid explicit lower-bound witnesses, but should not be presented as improving the BHN estimate.

## 5. Verification and Certificates

Each certificate is a JSON file containing integer vertex pairs. SHA-256 hashes in this paper are computed over the raw JSON file bytes.

The following standalone verifier captures the check used for the certificates.

```python
def verify_c4_free(n, edges):
    edge_set = {tuple(sorted(e)) for e in edges}
    for u, v in edges:
        assert 0 <= u < 2**n and 0 <= v < 2**n
        assert bin(u ^ v).count("1") == 1

    violations = 0
    for base in range(1 << n):
        for d1 in range(n):
            if (base >> d1) & 1:
                continue
            for d2 in range(d1 + 1, n):
                if (base >> d2) & 1:
                    continue
                a = base
                b = base | (1 << d1)
                c = base | (1 << d2)
                d = base | (1 << d1) | (1 << d2)
                square = [(a, b), (a, c), (b, d), (c, d)]
                if all(tuple(sorted(e)) in edge_set for e in square):
                    violations += 1
    return violations
```

The cycle counts checked were:

| n | number of 4-cycles |
|---:|---:|
| 9 | 4608 |
| 10 | 11520 |
| 11 | 28160 |
| 12 | 67584 |
| 13 | 159744 |
| 14 | 372736 |
| 15 | 860160 |

Summed across the seven independent verifications, 1,504,512 4-cycles were enumerated and checked.

A fresh local run of this verifier on the seven final certificate files is recorded in `VERIFY_ALL_CERTIFICATES.log`.

### 5.1 Independent Cross-Check

After publication of the certificate repository, Minamo Minamoto independently checked the seven certificates, including the improved Q11 certificate with 7164 edges, using a separate sparse cherry-counting verifier. This verifier uses the equivalent condition that a graph is C4-free if and only if no unordered vertex pair has two common neighbours. This is a different algorithm from the exhaustive four-cycle enumeration above.

That independent check found matching SHA-256 hashes, the stated edge counts, no invalid hypercube edges, no loops or duplicates, full vertex support, and no C4 in all seven certificates. The cross-check report and verifier are included as `independent_crosscheck.md` and `c4_sparse_verifier.py`.

## 6. Computational Notes

### 6.1 Lift Parameters

The product-lift automorphisms used for the lift-stage certificates were:

In the first row, "Minamoto run 1 / run 2" refers to the two 680-edge `Q8` certificates distributed in Minamoto's repository.

| lift | parent file | result | permutation | flip | alpha | search budget |
|---|---|---:|---|---:|---:|---:|
| Q8 -> Q9 | Minamoto run 1 / run 2 | 1501 | `[3,2,4,1,5,0,6,7]` | 25 | 141 | 4 base pairs x 20 restarts x 1500 moves |
| Q9 -> Q10 | `q9_edges_v6_local.json` | 3292 | `[0,1,2,8,4,5,6,7,3]` | 8 | 290 | 3 parent pairs x 15 restarts x 800 moves |
| Q10 -> Q11 | `q10_edges_repair_from3302_iter5.json` | 7142 | `[6,8,2,4,7,0,5,3,1,9]` | 484 | 534 | 400 random trials |
| Q11 -> Q12 | `q11_edges_repair_from7146_iter2.json` | 15350 | `[8,2,1,10,9,6,3,7,4,5,0]` | 1092 | 1048 | 300 random trials |
| Q12 -> Q13 | `q12_edges_repair_from15358_iter2.json` | 32829 | `[7,0,10,2,9,6,8,4,11,5,3,1]` | 67 | 2097 | 150 random trials |
| Q13 -> Q14 | `q13_edges_repair_from32842_iter2.json` | 69883 | `[0,10,1,11,4,6,7,3,5,12,9,8,2]` | 7162 | 4171 | 100 random trials |
| Q14 -> Q15 | `q14_edges_repair_from69895_iter2.json` | 148111 | `[13,2,7,8,0,4,3,1,9,5,6,11,10,12]` | 5091 | 8293 | 50 random trials |

These parameters were found computationally; no theoretical significance is claimed for them.

### 6.2 Negative Results

Several natural variants did not improve the main construction.

1. A `Q8 x Q2` four-slice construction for `Q10` reached only `Q10 >= 3248`.
2. Multi-parent twin lifts for `Q10`, using different `Q9` parents in the two slices, were worse than the best same-parent lift in our tests.
3. Re-lifting the repaired `Q9=1505` certificate produced only `Q10=3285`, worse than the `Q10=3304` certificate obtained from `Q9=1501` followed by repair.
4. Applying the local repair procedure to Minamoto's `Q8=680` certificates did not find a 681-edge construction. Minamoto's analysis already shows that no single-edge addition to the 680-edge construction is C4-free, so any 681-edge improvement would require deleting and adding edges rather than a pure local extension.
5. Applying the local repair procedure to a `Q7=304` certificate did not find a 305-edge construction. This gives no proof of exactness; it only indicates that a possible improvement is not a shallow local repair.

### 6.3 Asymptotic Consistency

The densities of the seven certificates are:

```text
0.6532, 0.6453, 0.6360, 0.6255, 0.6170, 0.6096, 0.6028.
```

This decreasing sequence is consistent with the conjecture `ex(Q_n,C4) = (1/2+o(1)) |E(Q_n)|`. Finite-dimensional values above `1/2` do not contradict the asymptotic conjecture.

The `n=15` density `0.6028` is below Baber's asymptotic upper-bound constant `0.60318`; the `n=14` density `0.6096` is still slightly above it. This comparison is only contextual, since the `0.60318` bound is asymptotic.

## 7. Reproducibility

The lower-bound claim in this note is reproducible from the public certificates alone: run the standalone verifier on the seven JSON files and check that every listed edge is a valid hypercube edge and that no enumerated 4-cycle is fully selected.

The search pipeline that found the certificates used random product lifts and local ILP repair, as described above. Those search scripts are not needed to verify the theorem and are not part of the minimal certificate repository. The lift parameters are included only as computational provenance, not as an independent proof.

The total search time for the table was on the order of several CPU-hours on a single workstation, with no GPU.

## 8. Open Problems

1. Determine whether `ex(Q7,C4)=304`. A SAT or pseudo-Boolean UNSAT certificate for the nonexistence of a 305-edge construction appears to be the most direct computational route.
2. Determine whether `ex(Q8,C4)=680`. The failure of single-edge addition and shallow repair suggests that any improvement would require a more global modification.
3. Improve the lower bounds in the table by deeper local repair or by improving the low-dimensional parents.
4. Find non-computational structure explaining why local repair improves edge count while sometimes reducing compatibility with the next product lift.

## References

[BE11] A. E. Brouwer and T. Etzion, "Equitable colorings and the maximum number of edges in C4-free subgraphs of the n-cube", Discrete Mathematics 311 (2011).

[BHLL14] J. Balogh, P. Hu, B. Lidicky, H. Liu, "Upper bounds on the size of 4- and 6-cycle-free subgraphs of the hypercube", European Journal of Combinatorics 35 (2014), 75--85. arXiv:1201.0209.

[Ba12] R. Baber, "Turan densities of hypercubes", arXiv:1201.3587, 2012.

[E84] P. Erdos, "On some problems in graph theory, combinatorial analysis and combinatorial number theory", in Graph Theory and Combinatorics, Cambridge 1983, Academic Press, 1984, 1--17.

[Min26] Minamo Minamoto, "New Lower Bounds for C4-Free Subgraphs of the Hypercubes Q6, Q7, and Q8: Constructions, Structure, and Computational Method", arXiv:2603.29127, 2026.

[ErdosProblems] T. Bloom et al., "Erdos Problems: Problem #86", https://www.erdosproblems.com/86.

## Appendix A. Certificate Hashes

SHA-256 hashes are over raw JSON file bytes.

```text
Q9   q9_edges_repair_from1503_iter2.json    0994be825ec39d115b65eb1436eace7c1be324448a6ec116d69c8a7e2a75d338
Q10  q10_edges_repair_from3302_iter5.json   24317cb0f821a7e39688d1376ac58c466779fc21d3628085270ddc468ae27c09
Q11  q11_edges_repair_from7160_probe_fast2.json a396680dd00bd3b86fff26920c5345cebeff4dde3d7dd411fd8ea97ac269274b
Q12  q12_edges_repair_from15366_iter3.json  f1e952df4c40e10418f52b9c778fd8d1313efb1ab41bc8e45266d645a368a2f5
Q13  q13_edges_repair_from32842_iter2.json  f3214c05e66d45a3a300d2a96ee3f3a77982d091990ff5457f1852e98a389dd2
Q14  q14_edges_repair_from69895_iter2.json  78d7ca75e720f920637d72134c7749f9680f7c4c60d31ac67e8948a1fa0d7e32
Q15  q15_edges_repair_from148111_iter1.json 9c98dc35a87d2a2fde9ee115f628144d2851e1dbdf57096ad6e6003d97b8f575
```
