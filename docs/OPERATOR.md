# Research conventions

## Scope and evidence

- Mathematical source: `sources/erdos-86.tex`; intended final research artifact: `results/erdos-86/answer.md`.
- Write maintained repository documentation in English. Explain mathematical statements using basic undergraduate graph theory, and state what was checked, what the evidence supports, and what remains open.
- Read `docs/existing-research.md`, `docs/ml-methods-from-lectures.md`, and relevant `memory/facts/` records before starting a new line of work. Preserve source versions and evidence boundaries.
- Known baseline constructions have 304 edges in Q7 and 682 in Q8. They are not discoveries of this project.
- The project-reviewed Q7 interval is now 304–305; see `docs/q7-upper-bound-305.md`. A 305-edge graph must have degrees 3–5 and at most two degree-3 vertices on each bipartition side. Historical priority and external review remain separate questions.
- The odd-square subclass, in which every square retains one or three edges, cannot improve these Q7/Q8 baselines. Searches for 305 or 683 must permit squares with zero or two edges.
- Distinguish the asymptotic problem, unrestricted fixed-dimensional optima, restricted-class optima, and individual candidate constructions.
- Timeouts, local optima, and unsuccessful heuristic searches are not nonexistence proofs. Exact exclusions must state their complete parameter and symmetry coverage.
- Retain the Lean scaffold. It currently contains no formal proof of Problem #86.

## Verification

`references/baselines/86-verify.py` is an independent standard-library verifier, not an upstream search program. It checks all squares and common-neighbor pairs. Do not use `python -O`.

Keep the fixed verifier as an acceptance reference. If it needs modification, preserve the previous version and explain why; never weaken the mathematical conditions to accept a candidate. `erdos86_gps/verify.py` supplies an additional independent dual check for new candidates. `scripts/verify_wrona_certificates.py` checked the seven imported Q9–Q15 certificates; outputs are in `artifacts/experiments/literature-intake-20260912/`.

An initialization record marked `accepted` refers to source-structure validation. A fact marked `reviewed` has the specific source or computational checks stated in its body. Neither label establishes external peer review, Lean certification, or approval by an Iteris review panel.

## Search and training

The four original directions are in `docs/toward-305.md`. Elementary necessary conditions, fixed-seed repair barriers, and slice reductions must retain their assumptions. In particular, a constraint on one seed or an incomplete parent catalogue does not establish a general exclusion.

The GraphGPS implementation hides every future edge label before constructing GNN inputs, square features, or global attention. It forbids only actions that complete a C4; it does not force odd-square structure. Do not train on full target-graph labels as visible input.

The corpus contains 180 verified representatives of the published catalogue's symmetry orbits. Augmentation changes labels, not orbits. The first pilot used all 180 for training. The diagnostic suite used 144 training and 36 held-out orbits, with all generated graphs having at least 304 edges excluded from feedback. This holdout was new to the diagnostic runs, not to the project as a whole.

Checkpoint restoration recovers model, optimizer, random state, and population, but a new invocation restarts the configured round budget. It does not resume an interrupted sampling position exactly. Use a fresh output directory and a separately specified continuation budget.

## Latest route-4 result

Slurm 21925840 completed in 19 min 39 sec on one A100. Its best raw sample had 286 edges and its best repaired sample had 290; the overall 304-edge best came from the reference population.

Slurm 21929229 completed with exit code `0:0` in 2 hr 4 min 42 sec on one A100. All six runs completed 19,000 steps, totaling 114,000 steps. The reference80 maxima were 293, 292, and 294; the comparison maxima were 291, 290, and 291. Final fixed repaired means averaged 281.375 versus 280.2083. No model sample reached 300.

The 294-edge graph occurred before the first feedback update, so its maximum cannot be credited to the 80% reference-weight policy. It was transferred as an exact bit encoding and independently checked locally. See `docs/graphgps-diagnostic-suite-results.md` and `artifacts/experiments/slurm-21929229/observed-review/`.

The diagnostic task remains in `review`: execution and the final-summary review are complete; full candidate streams and checkpoints still require transfer and batch audit. Classical baselines already reach 304, so any further learning claim requires a controlled comparison.

## Pause and coordination

Research and further GPU training are paused pending an explicit restart. Documentation updates do not restart them. Preserve task-specific review states and the disabled compute gate used by the structural-search work.

Externally managed collaboration tasks may appear orphaned to Iteris. Do not run recovery or reset them on that basis. Before resuming, read their saved checkpoints, check disk space and resource limits, and keep incomplete or UNKNOWN results at their recorded evidence level.

Long searches and training runs require a concrete task and resource budget. Do not automatically launch `iteris run`, retrain, or resubmit a completed job.
