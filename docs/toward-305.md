# Four research directions toward 305 edges in Q7

Originally proposed September 12, 2026; updated for the September 13 project status. This note assumes undergraduate graph theory. It records research directions and elementary reductions, not estimates of the probability of solving the problem.

The target is a C4-free selection of 305 of Q7's 448 edges. The project-reviewed interval is now **304–305**, with a [direct upper-bound proof](q7-upper-bound-305.md). A verified example would settle this fixed-dimensional value, but would not settle the original asymptotic problem. Its existence is still unknown.

Route 4 was prioritized and implemented. The [completed GPU diagnostics](graphgps-diagnostic-suite-results.md) did not reach 300 edges from the model. Structural searches have also produced separate local records; the elementary conditions below should not be mistaken for the strongest conditions now available. Further research is paused.

## Constraints shared by the routes

An improvement must leave the odd-square class, whose Q7 maximum is 304. Merely permitting two-edge squares is insufficient: a 305-edge graph must contain empty squares.

Let $m$ be the edge count, $N_0$ the number of empty squares, and $P$ the number of squares retaining exactly two opposite edges. Then

$$N_0-P\ge2(m-304).$$

In particular, $m=305$ requires $N_0\ge P+2\ge2$. Appendix A proves this elementary necessary condition. It does not justify imposing **exactly** two empty squares. The [later facet argument](q7-upper-bound-305.md) also requires every vertex of a 305-edge graph to have degree 3, 4, or 5, with at most two degree-3 vertices on either bipartition side.

For the fixed imported 304-edge seed, the original diagnostic found 36 one-edge, 120 two-edge, and 516 three-edge squares. All two-edge squares use adjacent edges. Of its 144 missing edges, 60 individually create three C4s and 84 create four. For a given missing edge, those squares have disjoint sets of the other three edges. Consequently, reaching a 305-edge graph from that seed requires deleting at least three old edges and adding at least four new ones. This initial bound concerns that seed only and does not assert that such a small repair succeeds.

## Route 1: reconstruct a local region

Temporarily let a solver reselect the edges in one region, aiming to replace $r$ edges with at least $r+1$. Introduce binary variables $x_e$ and, for every square $S$, impose

$$\sum_{e\in S}x_e\le3.$$

Freeze variables outside the chosen region, retain all boundary-square constraints, and maximize $\sum_e x_e$ or require at least 305 edges.

The initial proposed pilot compared random regions with regions suggested by the missing-edge obstruction lists, releasing 32, 64, or 128 variables. Ten instances per setting with ten seconds per instance was a proposed starting budget, not a report that these jobs completed.

AI can propose region-selection rules, analyze recurrent obstructions, implement incremental updates, and turn successful exchanges into reusable moves. Useful intermediate outputs include a reproducible repairer, a complete exclusion for a specified region around a specified seed, or structurally distinct high-edge-count seeds. Additional 304-edge graphs require orbit comparison before claiming structural novelty.

Shallow repair is not an unexplored idea: [Wrona, Section 6.2](https://github.com/rafalwronapl/erdos86-hypercube-c4/blob/7b8554bf3e7562a4bc1fb217757e709ba63c3e26/PAPER_V2.md) reports unsuccessful Q7 local repair. Record the actual region, solver status, and output so the scope can be compared.

Iteris task: `task-q7-local-repair-pilot`.

## Route 2: align two Q6 slices

View Q7 as two Q6 layers joined at corresponding vertices. Put C4-free graphs $A$ and $B$ in the layers. A new cross-layer C4 occurs precisely when an edge $uv$ appears in both layers and both vertical edges at $u,v$ are selected. Thus the selected vertical vertices must form an independent set in $H=A\cap B$.

Since $H$ is bipartite, its maximum independent-set size is $64-\nu(H)$, where $\nu$ is the maximum matching size. The optimal lift for fixed layers has

$$|E(A)|+|E(B)|+64-\nu(A\cap B)$$

edges. This extends the same-parent formula in [Wrona's paper](https://github.com/rafalwronapl/erdos86-hypercube-c4/blob/7b8554bf3e7562a4bc1fb217757e709ba63c3e26/PAPER_V2.md) to two different parents.

If 305 is possible, at least one coordinate cut has one of these unordered layer-size pairs, using the historical bound $f(6)=132$:

| Layer edges | Intersection matching needed for at least 305 |
| --- | --- |
| 132 + 132 | $\nu\le23$ |
| 132 + 131 | $\nu\le22$ |
| 132 + 130 | $\nu\le21$ |
| 131 + 131 | $\nu\le21$ |

Appendix B gives the reduction. A first implementation can cut known Q7 seeds, verify the matching score, and then search diverse 130–132-edge Q6 parents. For a fixed pair there are at most $2^6\cdot6!=46080$ relative cube automorphisms. Benchmark before committing to exhaustive enumeration.

AI can search for dense parents with an unusually small intersection matching and use matching bottlenecks to suggest joint modifications. Intermediate results include an exact optimum for an explicitly listed parent library, a reproducible lift generator, or a structural lemma guaranteeing a small matching.

The two-slice representation itself loses no generality, but an incomplete parent library does. Do not assume every 130/131-edge Q6 graph can be obtained by deleting edges from an available 132-edge sample.

Iteris task: `task-q7-two-slice-pilot`.

## Route 3: solve for 305 edges directly

One heuristic keeps exactly 305 edges while allowing temporary C4s and searches for exchanges that reduce their number to zero. An exact alternative uses all 448 variables, 672 square constraints, and $\sum_e x_e=305$, supplemented only by proved necessary conditions.

First check that a 304-edge version accepts a known certificate. Save formulas and logs. Since a 305-edge graph must have an empty square, a global model may fix one designated square empty by cube symmetry without losing existence coverage. Relative positions of further empty squares can be classified, but the classification must be checked for completeness.

This normalization cannot be transferred unchanged to a fixed-seed neighborhood: moving a square without also transforming the seed changes that neighborhood. Nor may the global model assume exactly two empty squares or only degrees 4 and 5. The reviewed degree restriction allows degree 3 as well.

AI can derive pruning inequalities, choose cardinality encodings, analyze difficult branches, and propose coordinated edge moves. Incremental heuristic C4 counts should periodically be checked from the full edge list. A near-feasible 305-edge graph is an intermediate object, not a legal construction.

[Minamoto v5, Appendix A](https://arxiv.org/html/2603.29127v5#A1) already reports unresolved direct SAT/MIP attempts. A different solver is not a reason to expect success. Only complete mathematical coverage together with valid exact certificates can turn exclusions into a general upper bound; UNKNOWN and timeouts cannot.

Iteris task: `task-q7-defect-model`.

## Route 4: learn candidate starting points

Alternate local improvement, selection of good graphs, model training, and generation of new starting points. Original PatternBoost uses a sequence Transformer; Wagner's deep cross-entropy implementation uses a fully connected network. Our [GraphGPS-style adaptation](graphgps-route4.md) combines local constraint-graph messages with global edge-variable attention.

Potential learning targets include promising starting graphs, repair regions, or modifications inferred from search trajectories. Any benefit should be measured against a classical search baseline using a declared total-cost budget, including training. Useful intermediate results would improve a prespecified metric such as high-quality verified candidates per unit cost or repair success rate.

The catalogue's 19,866 labels represent only 180 cube-symmetry orbits. Splitting raw rows can leak symmetric copies. Imitating known 304-edge graphs may also return to known structures rather than introduce the required defects productively. Obtaining an existing 304-edge graph faster does not by itself imply progress toward 305.

The implemented imitation-and-repair pipeline reached 294 edges in its [latest experiment](graphgps-diagnostic-suite-results.md). That result does not support simply increasing the training budget. A next controlled test could reuse the saved checkpoints with the same stronger repairer used for classical starting points.

Iteris tasks: `task-patternboost-q7-design` and `task-q7-training-corpus-audit`, followed by the recorded implementation and GPU tasks.

## Acceptance and prioritization

The original recommendation was to build a reliable repairer first, pursue the two-slice approach separately, and use exact models to produce necessary conditions and bounded exclusions before evaluating learning. This was a judgment about cost and verifiability, not a probability ranking; the project subsequently prioritized route 4.

Record code versions, input hashes, seeds, parameters, time or evaluation counts, complete best edge lists, and stopping reasons. A 305-edge candidate must pass all 672 square checks and the independent common-neighbor check. Preserve the fixed baseline verifier; the generic new-candidate checker is `erdos86_gps/verify.py`.

## Appendix A: why empty squares are necessary

Let $T=\sum_v\binom{d(v)}2$ count two-edge paths with a specified center. Each belongs to exactly one square. For every integer degree,

$$\binom d2-(4d-10)=\frac{(d-4)(d-5)}2\ge0.$$

Using 128 vertices and degree sum $2m$ gives $T\ge8m-1280$.

For a square, subtract its retained-edge count from its centered two-edge-path count and add one. The contribution is 1 for an empty square, −1 for two opposite edges, and 0 for one edge, two adjacent edges, or three edges. Four retained edges are forbidden. Each cube edge belongs to six squares, so

$$T-6m+672=N_0-P\ge2m-608.$$

At $m=305$, this gives $N_0\ge P+2\ge2$. This necessary condition agrees with the split-deficit discussion in [Minamoto v5, Remark 10 and Section 10](https://arxiv.org/html/2603.29127v5#S10). The elementary presentation does not depend on $f(6)=132$ and carries no priority claim.

## Appendix B: the four layer-size pairs

A graph with more than 305 edges can be reduced to 305 by deletion without introducing C4s. For a 305-edge graph, let $c_i$ be the number of edges in direction $i$, and $a_i,b_i$ the edge counts of the two layers obtained by cutting that direction. Since $a_i,b_i\le132$,

$$c_i=305-a_i-b_i\ge41,\qquad\sum_{i=1}^7c_i=305.$$

Some direction satisfies $41\le c_i\le43$. Its two layer counts sum to 264, 263, or 262; with each at most 132, only $(132,132),(132,131),(132,130),(131,131)$ are possible.

Also,

$$41\le c_i\le59,\qquad\sum_i(c_i-41)=18.$$

These are count restrictions, not a classification of the layer graphs. The matching thresholds follow from $a+b+64-\nu\ge305$. See the [research overview](existing-research.md) for the historical bound used here.
