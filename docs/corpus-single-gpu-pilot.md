# Audited 304-edge corpus and first single-GPU pilot

The September 12 experiment integrated verified diverse 304-edge constructions and submitted one single-A100 pilot.

**Slurm 21925840 completed normally:** one A100 80GB PCIe, 19 min 39 sec (**0.3275 GPU hours**), 11,000 training steps, and 12,288 generated candidates. The best raw model graph had 286 edges; repair reached 290. The overall 304-edge best came from the initial training set; no 305-edge graph was found. All saved repaired candidates were independently checked locally. See the [full results](corpus-pilot-21925840-results.md).

Code: `46dd29801eef68c54151241805462fe4eb83977e`. The original [submission record](../artifacts/experiments/q7-corpus-pilot-preparation/submission.json) preserves the submitted configuration.

## Data and initialization

The initial training population changed from one known graph and uneven bootstrap data to **180 verified representatives of distinct cube-symmetry orbits**, each with 304 edges. Sources and audit scope are in the [corpus README](../references/corpora/q7-304-orbits/README.md).

Representatives were sampled uniformly and augmented by random cube automorphisms. Network weights were initialized randomly. Each generated graph began with all 448 edge decisions undecided. Local constraint-graph messages, global attention, exact C4 masking, and repair remained in place.

Slurm pilot launchers require both the representative file and its audit record and stop on missing data or a hash mismatch. Reports preserve the population and audit hashes, source revision, and initial audit scope. Later elite pools used exact-label deduplication; this pilot had no held-out evaluation set.

## Submitted configuration

| Item | Setting |
| --- | --- |
| Launcher | `scripts/slurm/corpus-pilot.sbatch` |
| Configuration | `configs/graphgps/corpus-pilot.json` |
| Resources | `gpuq` / `hpcusers`; one A100, four CPUs, 16 GB RAM |
| Seed | 8601 |
| Model | Width 128, four layers, eight heads; random initial weights |
| Training | 5,000 initial steps, then 2,000 steps after each of three rounds |
| Generation | 4,096 per round, 12,288 total; batch 32 |
| Repair and comparison | 16 kicks per graph; paired classical search used the same count |
| Limits | 55-minute program soft limit; one-hour Slurm hard limit; no automatic retry |
| Runtime | Calibration estimate 0.316 GPU hours; observed 0.3275 GPU hours |
| Target behavior | Save and stop on an independently verified graph with at least 305 edges |

For a separately authorized reproduction, submit once from the repository root:

```bash
mkdir -p logs
sbatch scripts/slurm/corpus-pilot.sbatch 8601
```

Output: `artifacts/experiments/slurm-JOB_ID/pilot-seed-8601/`. Logs: `logs/erdos86-corpus-JOB_ID.out` and `.err`. If submission output is interrupted, check `squeue` and `sacct` before retrying.

## Validation boundary

Before submission, checks covered the corpus, 16 model/data tests, Bash syntax, single-GPU launch arguments, and a CPU smoke using the new data. Review `population_source`, initial population size, stopping reason, candidate distributions, and elapsed time in the real report.

An inherited 304-edge best is not a model discovery. The classical comparison matched repair counts, not total compute including training. Failure to find 305 in this bounded run does not prove nonexistence or rule out every learning approach. Further training is paused.
