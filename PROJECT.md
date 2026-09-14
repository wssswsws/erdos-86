# Erdős #86 research project

The original problem asks for the asymptotic maximum number of edges in a C4-free subgraph of a hypercube. Our initial finite target is to understand the known 304-edge subgraphs of Q7 and either construct a verified 305-edge example or obtain a precisely scoped structural result.

The current project-reviewed interval is **304 ≤ ex(Q7,C4) ≤ 305**. An elementary [facet-congruence proof](docs/q7-upper-bound-305.md) establishes the upper bound. No 305-edge construction has been found, and historical novelty has not been established.

The source intake, Q7–Q15 certificate checks, 180-orbit training-corpus audit, GraphGPS implementation, CPU smoke tests, A100 calibration, and two GPU experiments are complete. The latest six-run experiment reached a verified maximum of 294 edges from the model; it did not demonstrate a competitive search advantage. Its complete candidate archive and checkpoints still require transfer and batch review.

Start with the [research overview](docs/existing-research.md), [four directions toward 305](docs/toward-305.md), [model architecture](docs/graphgps-route4.md), and [latest experiment results](docs/graphgps-diagnostic-suite-results.md). Mathematical definitions and acceptance criteria are in [sources/erdos-86.tex](sources/erdos-86.tex).

Research is paused. A future restart must preserve the scope of incomplete searches, pending reviews, and existing evidence. Documentation maintenance and publication do not authorize new computation or training.
