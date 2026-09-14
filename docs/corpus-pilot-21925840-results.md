# First 180-orbit corpus pilot: results and independent checks

Reviewed September 12, 2026. Slurm **21925840** completed normally. Results were returned through Horizon to [results/corpus-21925840](https://github.com/wssswsws/erdos-86/tree/results/corpus-21925840) and fetched locally. Original output is in [pilot-seed-8601](../artifacts/experiments/slurm-21925840/pilot-seed-8601/); computed statistics and checks are in [analysis.json](../artifacts/experiments/slurm-21925840/analysis/analysis.json).

**No 305-edge construction was found.** Raw generation reached 286 edges and local repair reached 290. The saved overall best of 304 came from the existing training population. Initial loss fell substantially, but this did not translate into competitive construction quality.

## Execution and provenance

- Slurm `COMPLETED`, exit code `0:0`, **19 min 39 sec**, one A100 80GB PCIe, four CPUs, and 16 GB RAM: **0.3275 GPU hours**. Program time was 1173.19 seconds; startup and shutdown account for the difference.
- Code `46dd29801eef68c54151241805462fe4eb83977e`, source working tree recorded clean. The eight Python source hashes matched the local files at review time.
- Initial corpus: 180 audited 304-edge orbit representatives, seed 8601. Population and audit hashes matched the report.
- **11,000 training steps and three rounds of 4,096 samples** completed, totaling **12,288**. The stopping reason was `completed`, not timeout.
- Peak allocated CUDA tensor memory was 543,417,856 bytes, approximately 0.506 GiB; this is not total process memory.
- The remote candidate JSONL and approximately 16 MB checkpoint were retained. GitHub transfer included losslessly compressed `candidates.jsonl.gz`, not model weights.

## Candidate quality

| Round | Raw mean edges | Raw maximum | Repaired mean | Repaired maximum | Paired classical search |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 275.29 | 286 | 279.35 | **290** | All 304 |
| 2 | 274.28 | 285 | 279.39 | 288 | All 304 |
| 3 | 270.04 | 281 | 278.09 | 287 | All 304 |

The classical comparison started from 304-edge references and used the same number of repair kicks. The model generated from an empty prefix. Starting states differed, and total compute including training was not matched. This is therefore not a controlled equal-budget method ranking. It does show that the generated starting points did not improve the available 304-edge references, and later rounds did not improve generation quality.

All repaired model candidates were below 304. The [best repaired model graph](../artifacts/experiments/slurm-21925840/analysis/best-model-repaired.json) is saved separately; it is not a new Q7 record.

## Loss did decrease during initial training

The console printed the current batch's loss every 100 steps. This review used all 11,000 recorded losses, smoothing them and normalizing by the number of non-forced decisions.

| Initial training window | Mean reported loss | Non-forced BCE | Non-forced fraction |
| --- | ---: | ---: | ---: |
| Steps 1–500 | 0.3883 | 0.4585 | 84.68% |
| Steps 4501–5000 | 0.1550 | 0.1816 | 85.38% |

Loss decreased on the unchanged initial population, including after normalization. It cannot be explained merely by more forced-zero decisions. This supports improved fitting of the training distribution, not held-out generalization or improved full-graph generation.

After generated candidates entered the training pool, loss rose to roughly 0.23–0.24 and stayed near that level. Dashed lines in the plot mark population rebuilds, where the target distribution changes.

![Training loss and candidate quality](../artifacts/experiments/slurm-21925840/analysis/diagnostics.png)

## Reference dilution

The original feedback rule merged old and generated graphs and retained the top 512 by edge count. After round one this meant:

- 180 existing 304-edge reference graphs;
- 332 generated and repaired graphs with 283–290 edges.

Uniform sampling reduced the reference share from 100% to **180/512 = 35.16%**. The remaining **64.84%** of samples came from lower-edge-count graphs. Later pools still contained only 180 references; the lowest retained generated count became 284. Mean pool edge counts were 291.11, 291.57, and 291.62.

Lower-quality graphs may add structural variety, but they also change what the network imitates. Pool dilution coincided with the loss jump and declining raw generation quality. At this stage no controlled experiment had established it as the sole or main cause. The later [diagnostic suite](graphgps-diagnostic-suite-results.md) tested protected reference sampling.

Another hypothesis is prefix-distribution mismatch: training receives correct reference prefixes, whereas generation receives its own decisions over 448 steps. This pilot lacked fixed-prefix and rollout-prefix diagnostics, so that explanation remained a hypothesis.

## Time and verification scope

| Stage | Measured time |
| --- | ---: |
| Training | 358.43 sec, approximately 5.97 min |
| Autoregressive generation | 583.17 sec, approximately 9.72 min |
| Model-candidate repair | 92.58 sec |
| Paired classical local search | 88.41 sec |
| Other program overhead | Approximately 50.60 sec |

All **12,288 saved repaired edge lists** were independently checked for cube-edge validity, duplicates, square constraints, and common neighbors. All passed and had distinct exact labelings. The final `best.json` passed and was confirmed to belong to the initial population. Per-round counts matched the report, and each training pool was reconstructed with the recorded elite rule.

Complete raw-generation and paired-baseline edge lists were not saved. Their logged statistics can be cross-checked, but those individual graphs cannot all be reverified locally. Distinct labels are not necessarily distinct symmetry orbits; no new-candidate orbit census was performed.

The error log contained three PyTorch warnings about missing NumPy. The job completed normally and the executed path did not require NumPy conversion. Future NumPy-dependent analysis would require installing it.

## Iteris and reproduction

The pilot task was marked `done` because the agreed experiment and report review were complete. This did not complete the 305-edge research goal. The computational result is `reviewed`, not a Lean proof or an Iteris agent-panel certification.

The review recommended fixed evaluation, averaged logs, protected reference sampling, and saving raw/baseline objects. Those changes were later implemented in the [diagnostic plan](graphgps-pilot-diagnostic-plan.md).

```bash
MPLCONFIGDIR=/tmp/erdos86-mpl python3 scripts/analyze_graphgps_pilot.py \
  --run artifacts/experiments/slurm-21925840/pilot-seed-8601 \
  --output artifacts/experiments/slurm-21925840/analysis --plot
```
