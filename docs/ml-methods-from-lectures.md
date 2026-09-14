# Machine-learning methods for graph construction in the lectures

The source is the supplied 157-page *Lectures on AI for Mathematics*. PDF page numbers and printed page numbers agree on the relevant pages. Selected page text and the original PDF hash are preserved in [lecture-selected-pages.txt](../references/user/source-pack/lecture-selected-pages.txt).

| Location | Method | Original work |
| --- | --- | --- |
| Section 5.2, approximately pp. 103–110; core algorithm on pp. 104–105 | Deep cross-entropy method | Adam Zsolt Wagner, [Constructions in combinatorics via neural networks](https://arxiv.org/abs/2104.14516), 2021 |
| Section 5.3, pp. 110–116; graph results on pp. 114–115 | PatternBoost | François Charton, Jordan S. Ellenberg, Adam Zsolt Wagner, and Geordie Williamson, [PatternBoost](https://arxiv.org/abs/2411.00566), 2024 |

## Deep cross-entropy: imitate successful choices

Encode a graph as a sequence of zeros and ones, one decision per possible edge. A neural network supplies probabilities for successive choices. Generate many graphs, score them, keep an elite fraction, and train the network to imitate those choices. Repeating this may improve the probability of generating a good graph.

For example, to disprove a proposed inequality $A(G)\ge c$, use score $-A(G)$. A score above $-c$ identifies a candidate counterexample that still requires rigorous verification. Wagner applies this approach to matching numbers, adjacency and distance spectra, and matrix permanents. Not every case was the first counterexample to its conjecture.

The 19-vertex tree in Section 2.2 has two centers, each with eight leaves, connected through one additional intermediate vertex. Its matching number is 2 and its adjacency spectral radius is $\sqrt{10}$, so

$$\sqrt{10}+2<\sqrt{18}+1.$$

Figure 4 on page 7 of the original paper confirms the intermediate vertex. The lecture's description of a single edge joining the centers is imprecise. The paper also credits Stevanović with an earlier disproof; this example supplies a smaller explicit counterexample.

The original deep cross-entropy implementation uses a fully connected neural network, not a GNN. The optimization method itself does not require that particular architecture.

## PatternBoost: alternate learning and local search

```text
candidate graphs -> local improvement -> retain good graphs
       ^                                      |
       |                                      v
new candidates <- sample the model <- train a small Transformer
```

Local search adds, deletes, and repairs edges. The model learns patterns in encodings of good graphs and proposes new starting points. A local optimum only means that the permitted moves no longer improve it; it need not be globally optimal.

The lecture's C4-free example on page 114 matches Section 3.1 of the paper: on general 33-vertex graphs, 50 million pure local-search calls reached 89 edges; initial model experiments reached 91; a larger model and improved encoding eventually reached the known optimum of 96 after roughly 116.5 million local-search calls. These are the authors' reported results, not experiments reproduced here.

Section 3.3 gives a different hypercube task: retain all vertices of Q6 and diameter 6 while minimizing edges. Its 81-edge construction beat a conjectured minimum of 82. That diameter problem differs from #86, which maximizes edges subject to excluding C4s.

The original PatternBoost implementation uses a sequence Transformer, not a GNN. Neither its examples nor Wagner's establish a success probability for the present Q7 target.

## Adaptation to this project

Our implementation is a [GraphGPS-style variant](graphgps-route4.md): a local constraint-graph GNN plus global attention between edge variables, followed by sequential sampling. It is independently written, not an installation or reproduction of either original machine-learning codebase.

- Represent only the 448 cube edges, rather than all $\binom{128}{2}=8128$ vertex pairs.
- Train on audited legal constructions with symmetry-aware sampling. Augmentation changes labels; it does not create new structural orbits.
- Preserve legality during generation, then improve candidates with bounded local search.
- Allow empty and two-edge square faces. Remaining in the odd-square class cannot exceed 304.
- Compare against classical search with a declared total-cost budget and fixed metrics: edge counts, target-hit rates, verified candidates, orbit diversity, and runtime.
- Independently check every accepted candidate. A bit string containing 305 ones is insufficient unless its selected edges are C4-free.

The CPU implementation, A100 calibration, corpus pilot, and six-run diagnostic suite are complete. The [latest result](graphgps-diagnostic-suite-results.md) was a verified repaired model sample with 294 edges; no model sample reached 300. This validates the pipeline but has not established competitive search performance. Further training is paused.

Iteris records source data, parameters, code versions, unsuccessful paths, and verification results. It does not supply PatternBoost automatically.

## Original code and papers

- [Wagner's paper](https://arxiv.org/abs/2104.14516) and [official code](https://github.com/zawagner22/cross-entropy-for-combinatorics).
- [PatternBoost paper](https://arxiv.org/html/2411.00566) and [official code](https://github.com/zawagner22/transformers_math_experiments).

Both papers were saved during intake. Their original training projects have not been installed or rerun here.
