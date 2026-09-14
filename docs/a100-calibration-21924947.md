# A100 calibration: Slurm 21924947

Reviewed September 12, 2026. **Calibration succeeded.** The short A100 80GB PCIe measurement predicted approximately **0.316 allocated GPU hours, or 19 minutes**, for the original complete pilot. The earlier 2–4 hours was a premeasurement reservation; four hours was a stopping limit, not a required runtime.

This calibration measured execution and throughput, not trained search quality. The later [corpus pilot](corpus-pilot-21925840-results.md) completed in 19 min 39 sec.

## Provenance and transfer

- Results branch: [results/calibration-21924947](https://github.com/wssswsws/erdos-86/tree/results/calibration-21924947).
- Report commit: [74db31c](https://github.com/wssswsws/erdos-86/commit/74db31c6dba00acce5d4fcf48b84fe828cfdd9cf), containing eight files. They were fetched and copied into the matching local artifact directory; bytes matched that commit.
- Experiment code: `252466d29e6c67ace2640c1ccfd45f64fa22657a`; its source working tree was recorded as clean. All eight Python source hashes matched the local files **at the time of review**.
- Slurm accounting was read through Horizon: `COMPLETED`, exit code `0:0`, elapsed `00:00:25`, one GPU, four CPUs, and 16 GB memory. This was a terminal observation; the original eight-file report did not include an accounting export.
- [Exit code](../artifacts/experiments/slurm-21924947/benchmark-seed-8601/exit-code.txt): 0. [Tests](../artifacts/experiments/slurm-21924947/benchmark-seed-8601/tests.xml): 15 passed, no failures, errors, or skips; 5.72 seconds. This does not mean each test specifically ran on CUDA.

## Measurements

Sources: [hardware.json](../artifacts/experiments/slurm-21924947/benchmark-seed-8601/hardware.json) and [benchmark.json](../artifacts/experiments/slurm-21924947/benchmark-seed-8601/benchmark.json).

| Item | Measurement |
| --- | --- |
| GPU | NVIDIA A100 80GB PCIe; one visible GPU |
| Environment | Python 3.13.13; PyTorch 2.10.0+cu126; CUDA 12.6; bf16 supported |
| Model | Four layers, width 128, eight heads, 1,324,033 parameters |
| Training / sampling batch | 32 / 32 |
| Training step | 32.88 ms; 20 timed steps after two warmup steps |
| Full-network forward pass | 3.13 ms at batch 32 |
| Generate 32 complete graphs | 1.533 sec, including 448 sequential decisions |
| CPU repair per graph | Mean 7.65 ms with 16 kicks |
| Peak PyTorch-allocated CUDA memory | 543,417,856 bytes, approximately 0.506 GiB |

The memory measure includes allocated tensors, not total process or device memory. It indicates no obvious tensor-memory pressure at this configuration; it does not identify the optimal larger batch size.

## Pilot extrapolation

The [estimate](../artifacts/experiments/slurm-21924947/benchmark-seed-8601/estimate.json) uses 11,000 training steps and 12,288 graphs in 384 batches.

| Stage | Estimated duration |
| --- | ---: |
| Training | 6.03 min |
| Sequential generation | 9.81 min |
| CPU repair of model candidates | 1.57 min |
| Paired classical local search | Approximately 1.57 min |
| Total | **18.98 min / 0.316 GPU hours** |

Serial CPU repair counts toward GPU allocation time because the GPU remains reserved. Baseline time was approximated from candidate-repair time, not independently measured for high-quality starting graphs.

Only 20 training steps and one batch were timed. Population initialization, independent verification, checkpoint saving, candidate writes, and changing graph structures add uncertainty. The original recommendation was a one-hour allocation for the first complete single-GPU pilot; it was subsequently run and reviewed separately.

Four independent equal-sized seeds on four A100s would ideally consume about 1.27 GPU hours while taking roughly 19 minutes of wall time, plus overhead. This is not a fourfold speedup of one experiment, and concurrent CPU/I/O contention was not measured.

## Interpretation

The CUDA training and sampling path worked, and measured throughput made bounded multi-seed experiments affordable in allocation time. Calibration used one known 304-edge graph for short training and did not establish a new construction or an advantage over classical search.

At calibration time, the pilot still used bootstrap data. The subsequent corpus work added and audited 180 diverse 304-edge orbit representatives; see the [corpus note](../references/corpora/q7-304-orbits/README.md). This historical calibration report should not be read as the current data configuration or as authorization to launch another job.
