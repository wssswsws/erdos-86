# A simple deterministic 294-edge Q7 construction

A model score of 293 is below a simple classical baseline: **294 edges can be obtained deterministically, without training, random search, or reading a known 304-edge graph**. A small extension using random majority updates reached 302, with mean 298.347 over 1,000 starts.

These are baseline constructions and finite experiments, not new edge-count records or established novelty claims. They do not negate a narrower claim that training improves a model relative to its own untrained initialization.

## The 294-edge construction

Write a vertex as $x=(x_0,\ldots,x_6)$, with bit $i$ corresponding to integer $2^i$. Define

$$p_i(x)=x_0+\cdots+x_{i-1}\pmod2,\qquad p_0(x)=0.$$

Initially retain the direction-$i$ edge $\{x,x\oplus2^i\}$ when $p_i(x)=0$. The rule is independent of the endpoint's bit $i$, so it defines undirected edges consistently.

There are **256 edges**: all 64 direction-0 edges and half the edges in each of the other six directions. Every square has one or three retained edges. For directions $i<j$, the two $i$ edges have the same prefix parity and the two $j$ edges have opposite prefix parity.

Now visit only the 64 even-weight vertices. If such a vertex has degree at most 3, complement all seven of its incident cube edges. Otherwise leave it unchanged.

Complementing a vertex star toggles two edges in each incident square, preserving square-edge parity. Thus every square still has one or three edges and no C4 appears. Stars at distinct even vertices are edge-disjoint, so their gains add independently.

On the even side, the six prefix values $p_1,\ldots,p_6$ range freely over all bit strings. If $k$ are one, the initial degree is $7-k$, with $\binom6k$ vertices of that type. The complemented low-degree vertices contribute:

| Initial degree | Number of even vertices | Gain per vertex | Total gain |
| --- | ---: | ---: | ---: |
| 1 | 1 | 5 | 5 |
| 2 | 6 | 3 | 18 |
| 3 | 15 | 1 | 15 |

The result has $256+5+18+15=\boxed{294}$ edges. Equivalently,

$$\sum_{k=0}^6\binom6k\max(k,7-k)=294.$$

```python
edges = {
    (x, x ^ (1 << i))
    for x in range(128) for i in range(7)
    if not (x >> i) & 1
    and (x & ((1 << i) - 1)).bit_count() % 2 == 0
}
for v in range(128):
    if v.bit_count() % 2 == 0:
        star = {tuple(sorted((v, v ^ (1 << i)))) for i in range(7)}
        if len(edges & star) < 4:
            edges ^= star
assert len(edges) == 294
```

Independent checks of the saved certificate found 126 one-edge squares, 546 three-edge squares, zero C4s by both verifiers, and degree histogram $4:70,5:42,6:14,7:2$.

## Small extensions and their scope

Use prefix signs $J_i(x)=(-1)^{p_i(x)}$ and vertex labels $s(x)\in\{-1,+1\}$. Retain an edge when $J_i(x)s(x)s(x\oplus2^i)=+1$. This is the same square-parity-preserving switching framework.

| Family or search | Best edge count | Scope |
| --- | ---: | --- |
| Whole Hamming-weight layers | 224 | All 128 layer masks enumerated; 34 legal |
| Prefix rule, all vertex labels positive | 256 | Direct count above |
| Odd labels positive, one majority update on even vertices | 294 | Deterministic proof above |
| At most three negative odd labels; optimize even labels | 297 | All 43,745 possibilities enumerated |
| Random labels and alternating majority updates | 302 | 1,000 starts, seed 8611; mean 298.347 |

For the whole-layer family, adjacent selected layers create a C4. The seven layer sizes are $7,42,105,140,105,42,7$. Selecting the middle layer allows at most 42 on each side, giving 224; omitting it allows at most $7+105=112$ on each side. This proves 224 only for that restricted family.

For sparse negative odd labels, fixing the odd side lets every even label be optimized independently. Exhaustive results were:

| Negative odd labels | Possibilities | Maximum | First maximizing set of integer vertices |
| --- | ---: | ---: | --- |
| 0 | 1 | 294 | Empty |
| 1 | 64 | 294 | {1} |
| 2 | 2,016 | 295 | {1,19} |
| 3 | 41,664 | 297 | {7,69,79} |

The 297-edge certificate has 117 one-edge and 555 three-edge squares. No claim is made about larger negative-label sets.

## Random majority updates

Sample all 128 labels in vertex order with Python `random.Random(8611)` and `choice((-1, 1))`. Update the even side, then the odd side, choosing the sign of each vertex's signed neighbor sum; repeat until a full sweep makes no changes. Seven neighbors prevent ties. Every changed label strictly increases the edge count, so the process terminates and remains in the odd-square class.

All 1,000 starts share a continuous RNG stream. A sweep includes both sides and the final unchanged check. Results:

| Final edges | Frequency |
| --- | ---: |
| 294 | 1 |
| 295 | 10 |
| 296 | 42 |
| 297 | 186 |
| 298 | 305 |
| 299 | 290 |
| 300 | 139 |
| 301 | 25 |
| 302 | 2 |

There were 535 two-sweep, 463 three-sweep, and two four-sweep starts. The first maximum occurred at zero-based start 421. The saved best certificate has 102 one-edge and 570 three-edge squares and degree histogram $4:40,5:84,6:4$.

Scores and sweep counts for every start were saved. Full edge lists were not saved and externally rechecked for all 1,000 outcomes; their legality follows from the uniform construction argument. The saved representative certificates were independently checked.

One local reproduction took approximately 0.00019 seconds for the deterministic construction, 0.127 CPU seconds for sparse enumeration, and 0.380 CPU seconds / 0.429 wall seconds for the 1,000 random starts. Including file output and four independent certificate checks, the script took approximately 0.807 CPU seconds / 0.976 wall seconds. These are local measurements, not a controlled CPU/GPU speed comparison.

## Evidence and publication scope

The short Python construction above is self-contained and reproduces the deterministic 294-edge graph. It can be checked using the published generic verifier in `erdos86_gps/verify.py`.

The additional majority-search script, full trial records, and saved 294/297/302 certificates remain in the local research workspace under `scripts/analyze_simple_293_baselines.py` and `artifacts/experiments/simple-293-baselines/`. They are not included in this documentation-only publication. The numerical extensions above report the local experiment and its recorded checks; this page does not provide its complete reproducibility archive.

The prefix-sign and vertex-switching framework is existing mathematics: [Minamoto v5, Section 6.1](https://arxiv.org/html/2603.29127v5#S6.SS1) describes the correspondence, and [Section 6.3](https://arxiv.org/html/2603.29127v5#S6.SS3) gives the prefix formula and traces it to Marinari–Parisi–Ritort (1995), equation (4). A limited search did not locate this exact one-pass 294 statement; that is not evidence of novelty. No known 304-edge block construction was used to generate these certificates.
