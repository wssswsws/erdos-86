# Erdős Problem #86: C₄-free subgraphs of hypercubes

A computational mathematics research workspace for [Erdős Problem #86](https://www.erdosproblems.com/86), combining exact graph verification, finite construction searches, and a GraphGPS-style learning experiment. [Iteris](https://github.com/frenzymath/iteris) organizes sources, tasks, and evidence; the Lean project is a scaffold for future formalization.

## The problem

The vertices of the hypercube $Q_n$ are binary strings of length $n$. Two vertices are adjacent when they differ in exactly one bit. How many edges can we retain without creating a cycle of length four?

Write $f(n)=\operatorname{ex}(Q_n,C_4)$. The original conjecture asks whether

$$f(n)=\left(\frac12+o(1)\right)n2^{n-1}.$$

Our finite target is $Q_7$: 128 vertices, 448 possible edges, and 672 square faces. A known construction retains **304 edges**. We are investigating whether **305 edges** are possible. Resolving this finite question would not settle the asymptotic conjecture.

## Current results

Updated September 13, 2026. Further research and GPU training are paused pending an explicit restart.

| Area | Result | Evidence and limits |
| --- | --- | --- |
| Finite mathematical bound | $304\le f(7)\le305$ | [Project-reviewed counting proof](docs/q7-upper-bound-305.md); no 305-edge construction and no proof that 304 is optimal. Historical novelty has not been established. |
| Known constructions | Q7: 304 edges; Q8: 682 edges | [Imported certificates and independent verifier](references/baselines/README.md). These are existing results. |
| Training corpus | 180 distinct symmetry-orbit representatives, all with 304 edges | [Audit](references/corpora/q7-304-orbits/README.md) of the published 19,866-graph catalogue. This is not a classification of all 304-edge graphs. |
| First GPU pilot | Best raw sample: 286; best repaired sample: 290 | [11,000 steps on one A100](docs/corpus-pilot-21925840-results.md), 19 min 39 sec. All 12,288 saved repaired candidates independently rechecked. |
| Six-run diagnostic suite | Best repaired model sample: 294 | [114,000 total steps on one A100](docs/graphgps-diagnostic-suite-results.md), 2 hr 4 min 42 sec. No model sample reached 300. The best graph was rechecked locally; the full archive audit is pending. |

The learning experiments have not established a competitive advantage over classical constructions or search. A reported overall best of 304 includes an existing reference graph; it must not be attributed to the model.

## Start here

- [Research overview and source boundaries](docs/existing-research.md)
- [Four research directions toward 305](docs/toward-305.md)
- [GraphGPS architecture and experiment workflow](docs/graphgps-route4.md)
- [Deep cross-entropy and PatternBoost explained](docs/ml-methods-from-lectures.md)
- [Slurm / A100 setup and submission](docs/slurm-guide.md)
- [Optional Modal setup and historical cost estimates](docs/modal-guide.md)
- [Research conventions](docs/OPERATOR.md), [roadmap](ROADMAP.md), and [status](STATUS.md)

## Verify the known constructions

From the repository root, using Python 3:

```bash
python3 references/baselines/86-verify.py
python3 scripts/verify_wrona_certificates.py
```

These checks use integer arithmetic and the Python standard library. The first verifies the Q7/Q8 certificates; the second checks the imported Q9–Q15 certificates. Do not use `python -O`, which disables assertions in the baseline verifier.

## Run a small local smoke test

Install the pinned GraphGPS dependencies in a virtual environment. The smoke test runs on CPU and checks the pipeline; it is not a meaningful construction-search benchmark.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-graphgps.txt
python -m pytest -q tests/graphgps
python -m erdos86_gps smoke --output artifacts/experiments/my-cpu-smoke
```

Use a fresh output directory for every experiment. GPU runs require an explicit execution flag and a budget; follow the [Slurm guide](docs/slurm-guide.md) and [diagnostic experiment plan](docs/graphgps-pilot-diagnostic-plan.md). The repository does not automatically resume paused experiments.

## Use Iteris

Iteris is installed separately. The wrapper looks for `ITERIS_BIN`, then an `iteris` executable on `PATH`, then the original workspace layout at `../../tools/iteris/.venv/bin/iteris`.

```bash
./scripts/iteris doctor
./scripts/iteris status
./scripts/iteris tool memory search --query 'PatternBoost'
```

The recorded setup used Iteris 0.2.0 at commit `a82213ef6247b551ddd19b413b06266e841d2375`. Research execution consumes the configured model's resources; inspect the execution configuration before starting `iteris run`. Keep the current pause in force until research is explicitly resumed.

## Repository layout

| Path | Purpose |
| --- | --- |
| `docs/` | Maintained English research notes and operating guides |
| `erdos86_gps/` | Constraint-graph message passing, global attention, sampling, repair, and verification |
| `configs/graphgps/` | Smoke, pilot, and diagnostic configurations |
| `scripts/` | Corpus audit, analysis, Iteris wrapper, and cloud launchers |
| `references/` | Versioned sources, upstream licenses, and known certificates |
| `artifacts/` | Selected configurations, reports, and verifiable graph data |
| `memory/`, `tasks/`, `.iteris/` | Iteris evidence and workflow records |
| `sources/erdos-86.tex` | Mathematical scope and evidence requirements |

Source snapshots and historical machine records retain their original contents and may include Chinese. They are provenance records, not the maintained English documentation. Large local search archives and model checkpoints are not all distributed in Git.

A `reviewed` record means the stated project checks were performed, with the scope described in that record. It does not mean external peer review, formal verification, or a new result. The Lean scaffold currently contains no formal proof of Problem #86. Upstream materials retain their original licenses and attribution.
