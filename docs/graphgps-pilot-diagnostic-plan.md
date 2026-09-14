# Second GraphGPS experiment: protected reference-weight diagnostics

This is the design record for **Slurm 21929229**, now completed. Six runs executed sequentially on one A100 80GB PCIe using code `51bfea0cccf024553a28dd43662082161bb3e6c8`. The [final results](graphgps-diagnostic-suite-results.md) replace earlier startup observations as the current status. No further training is automatically scheduled.

The architecture retains local constraint-graph message passing and global edge-variable attention. The experiment changes population sampling, local search, and evaluation to test the suspected dilution of high-quality references.

## Testable question

Does preserving the training weight of 304-edge references reduce deterioration after generated graphs enter the pool and increase the frequency of high-quality generated candidates? This bounded experiment does not assume that 305 exists or is reachable by the model.

| Setting | reference80 | legacy_topk |
| --- | --- | --- |
| Initial reference set | 144 audited 304-edge orbit representatives | Same |
| Fixed holdout | Remaining 36 orbits | Same |
| Reference sampling after feedback | 80% when exploration data exists | Uniform over the pool; 144/512 = 28.125% when full |
| Exploration pool | Up to 368 generated graphs below 304 edges, selected by edge count | Same |
| Seeds | 8611, 8612, 8613 | Paired seed labels |
| Model / optimizer | Width 128, four layers, eight heads; AdamW | Same |
| Training | 10,000 initial steps plus three blocks of 3,000: 19,000 total | Same |
| Main generation | Three rounds of 2,048: 6,144 total | Same |

The configured treatment difference is population sampling weight. `legacy_topk` retains the old uniform-feedback idea but uses the new split, searcher, evaluation, and budget; it is not an exact reproduction of the first pilot. Run order alternates between arms across seeds.

Training and validation orbits are split before separate symmetry augmentation. Each run begins from random weights, not an old checkpoint. The earlier pilot used all 180 representatives, so this is a holdout for these runs, not a historically unseen project test set.

To prevent symmetric validation examples from returning through feedback, **every generated graph with at least 304 edges is excluded from training feedback**, even if it happens to belong to a training orbit. A graph with fewer edges cannot be isomorphic to a 304-edge validation graph. Generated 304-edge graphs would still be saved for orbit review; an independently verified 305-edge graph would stop the suite.

## Search and evaluation

- Local perturbations delete 8–24 edges, mixing uniformly selected edges and regions expanded through shared squares. Repaired states may decrease in edge count under an annealed acceptance rule, with temperature falling from 2.0 to 0.25. The best verified certificate is retained separately.
- Each main model candidate is paired with classical search from a reference graph and from an empty graph. Both use the same search parameters and save complete edge lists. This matches search settings, not total compute including neural training.
- Checkpoints are saved before training and at 10,000, 13,000, 16,000, and 19,000 steps. Each stage evaluates 1,024 fixed training-prefix decisions and 1,024 fixed validation-prefix decisions, with an evaluation RNG independent of training.
- Each stage also generates and repairs 256 graphs with fixed sampling seeds: 1,280 evaluation samples per run, excluded from feedback. Thus the final checkpoint is actually sampled rather than merely saved after the last training block.
- Logs report 100-step mean loss, non-forced BCE, and actual reference-sampling probability. Reports include means, 90th/99th percentiles, and counts reaching 300, 304, and 305.
- Main and stage evaluation preserve raw/repaired edge lists, validation results, and exact-label hashes. Main search also preserves both classical baselines. Gzip streams keep the original objects without losing raw graphs as in the first pilot. Different labels do not establish different orbits.

All candidates may contain empty squares. No separate reward for the number of empty squares was added: lower-edge-count candidates already had them, so the challenge is maintaining high edge count at the same time.

This experiment did not implement a learned repair-region selector or learned SAT/MIP action policy. Nor does it isolate the value of the GNN or attention branch.

## Budget and stopping rules

The planned allocation was **2–3 A100 hours**, extrapolated from previous throughput and local repair measurements. The actual completed allocation was **2.0783 GPU hours**.

- One A100, four CPUs, and 16 GB RAM; six sequential runs.
- Per-run program limit: 30 minutes. Suite soft limit: 3.5 hours. Slurm hard limit: four hours.
- A timed-out run saves a partial report and is labeled accordingly; it cannot be counted as completing all planned training.
- An independently verified graph with at least 305 edges stops the suite after saving provenance and the edge list.
- Errors stop execution without automatic retry. Training does not run on the login node.

## Submission and artifacts

For an explicitly authorized new reproduction, submit once from the main checkout:

```bash
bash scripts/slurm/submit_diagnostics.sh
```

The launcher creates `.runs/diagnostics-SHORT_COMMIT/` for the current revision and uses the main checkout's `.venv`. The receipt is written to `artifacts/experiments/diagnostics-submissions/SHORT_COMMIT/`. An existing receipt directory blocks duplicate submission. If submission output is interrupted, inspect the receipt and Slurm before retrying.

Actual output is under the worktree's `artifacts/experiments/slurm-JOB_ID/diagnostics/`, containing `suite-report.json` and six arm/seed directories. Slurm logs are in that worktree's `logs/`. The [original receipt](../artifacts/experiments/diagnostics-submissions/51bfea0cccf0/submission.json) and [startup observation](../artifacts/experiments/diagnostics-submissions/51bfea0cccf0/observed-startup.json) preserve historical locations.

Local preparation records are in `artifacts/experiments/diagnostics-preparation/`: 21 tests, a two-arm CPU smoke, and validation outputs. Initial checks compared paired initial-weight hashes, fixed-evaluation hashes, and the 80% versus 28.125% sampling weights. The final statistical interpretation must also account for the fact that the full GPU runs did not branch from one identical pretrained checkpoint.
