# Optional Modal workflow for route 4

This guide preserves the setup and pricing review of **September 12, 2026**. Recheck account credits and current prices before using them for a new purchase. The Modal backend has not been executed on the cloud; the project's completed GPU measurements come from a lab A100 using Slurm.

At the recorded rates, an unused $30 monthly compute credit was expected to cover calibration and one small pilot, with room for limited repetitions. That is a compute-budget estimate, not a prediction that the experiment will find 305 edges.

Modal executes Python functions on cloud machines. Code editing and Iteris records remain local; reports, edge lists, and checkpoints can be downloaded afterward. The entrypoint is [scripts/modal_graphgps.py](../scripts/modal_graphgps.py). It is separate from the tested Slurm diagnostic workflow.

The original local checks used Modal SDK 1.5.3: definition loading, argument parsing, syntax, and 15 tests in an isolated copy of the upload bundle passed. Cloud image construction and CUDA execution on Modal remain untested. [Modal guide](https://modal.com/docs/guide).

## Historical credit and cost estimate

The September 12 review recorded Starter with no monthly subscription fee and $30 monthly compute credit. The table uses standard **Functions** pricing with two physical CPU cores and 8 GiB host memory, adding approximately $0.1583/hour. GPU VRAM is separate from host memory.

| GPU | VRAM | GPU $/hour | With CPU and RAM $/hour | Theoretical hours for $30 | Compute cost for 2–4 hours |
| --- | ---: | ---: | ---: | ---: | ---: |
| L4 | 24 GiB | 0.7992 | 0.9575 | 31.3 | $1.91–3.83 |
| A10 | 24 GiB | 1.1016 | 1.2599 | 23.8 | $2.52–5.04 |
| L40S | 48 GiB | 1.9512 | 2.1095 | 14.2 | $4.22–8.44 |
| A100 40GB | 40 GiB | 2.0988 | 2.2571 | 13.3 | $4.51–9.03 |

Sources from that review: [pricing](https://modal.com/pricing), [GPU types](https://modal.com/blog/gpu-types), and [resource billing](https://modal.com/docs/guide/resources). The GPU comparison article's older prices were not used.

```text
Hourly rate = GPU price per second × 3600
            + 2 × 0.0000131 × 3600
            + 8 × 0.00000222 × 3600
```

CPU and RAM billing use the larger of requested and actual usage; this entrypoint also sets limits. Image building, startup, shutdown, storage, and other overhead are excluded. The recorded Volume price was $0.09/GiB/month; account rules determine which noncompute charges credits cover. Notebook/Sandbox resource prices differ.

The original plan was to calibrate L4, optionally compare A10, and reserve $5 for one L4 pilot. Three 2–4-hour L4 pilots would cost about $5.7–11.5 in compute; twelve such runs would cost about $23–46 and could exceed the credit. These are equal-duration estimates, not measured cross-GPU runtimes. Lab A100 timings do not directly establish L4 timings.

The original [pilot](../configs/graphgps/pilot.json) plans 11,000 steps and 12,288 generated graphs. Its roughly 1.32 million parameters do not imply cheap generation: each graph requires 448 full-network decisions.

## 1. Configure the account and spending limits

Use [Modal signup](https://modal.com/signup), and check the current [billing rules](https://modal.com/docs/guide/billing). At the recorded review, a payment method was required. Credits alone did not imply that paid usage would stop when they ran out.

In Settings → Usage & Billing, check the actual balance and distinguish:

- **Workspace budget / usage limit:** total usage before credits. For a $30 credit allowance, the original recommendation was $30.
- **Spend limit:** out-of-pocket usage after credits. To use credits only, the original recommendation was **$0**, with the saved setting confirmed in the interface.

A $30 spend limit would allow additional paid usage. Starter used workspace-level budgets; environment budgets were a paid-plan feature. Recheck the [budget documentation](https://modal.com/docs/guide/budgets) and current account controls before launching.

## 2. Install and authenticate locally

From the repository root, in the Python environment intended for Modal:

```bash
python3 -m pip install modal==1.5.3
python3 -m modal setup
```

Authentication stays on the local machine. It does not belong in the repository. [Installation and authentication](https://modal.com/docs/guide).

An offline definition check is available:

```bash
python3 scripts/modal_graphgps.py
```

`Offline definition check passed` does not validate a cloud image or CUDA. `modal run` is a cloud operation, not an offline check.

## 3. Calibrate an L4

The following command consumes cloud resources when explicitly run:

```bash
python3 -m modal run scripts/modal_graphgps.py \
  --mode benchmark --run-id l4-calibration-001 --execute
```

It runs tests, times 20 full-size training steps, generates a complete batch of 32 graphs, and estimates the pilot. It does not launch full training. The image installs Python 3.13, PyTorch 2.10.0 CUDA 12.8, and pytest, following the pinned [PyTorch wheel](https://pytorch.org/get-started/previous-versions/).

Output is stored in Volume `erdos86-graphgps-results`, under the run ID. Existing directories are refused; choose a new ID for each run.

```bash
python3 -m modal volume get erdos86-graphgps-results l4-calibration-001 \
  artifacts/experiments/modal-l4-calibration-001
```

Inspect `benchmark.json` and `estimate.json`: actual hardware, training-step time, full-batch sampling time, peak PyTorch-allocated memory, and `estimated_allocated_hours_with_paired_baseline`. Allocated tensor memory is not total process GPU memory. The estimated hours omit some startup and saving overhead.

If the estimate exceeds the budget or memory fails, revise and recalibrate. To compare A10:

```bash
ERDOS86_MODAL_GPU=A10 python3 -m modal run scripts/modal_graphgps.py \
  --mode benchmark --run-id a10-calibration-001 --execute
```

## 4. Launch a separately authorized pilot

After reviewing calibration, tests, and cost:

```bash
python3 -m modal run --detach scripts/modal_graphgps.py \
  --mode pilot --run-id l4-pilot-001 --execute
```

`--detach` lets the cloud task survive local disconnection. Save its App ID and dashboard link. [Run reference](https://modal.com/docs/cli/latest/run).

The default is one GPU with no schedule or automatic parameter sweep. Training has a four-hour soft limit; the function limit is four hours five minutes. Image building is outside the training soft limit. `max_containers=1` does not cap aggregate use across independently launched Apps.

To stop an App:

```bash
python3 -m modal app stop YOUR_APP_ID
```

A forced stop may precede checkpoint saving. The entrypoint writes and commits a run marker before computation; replay into an existing directory fails rather than silently consuming another full budget. It is not an automatic resume system. Inspect saved files before arranging a continuation. [Preemption reference](https://modal.com/docs/guide/preemption).

## 5. Download and verify

```bash
python3 -m modal volume get erdos86-graphgps-results l4-pilot-001 \
  artifacts/experiments/modal-l4-pilot-001
python3 -m erdos86_gps verify \
  --candidate artifacts/experiments/modal-l4-pilot-001/training/best.json
```

The run includes `training/report.json`, `training/best.json`, `training/candidates.jsonl`, and `training/checkpoint.pt`. Volume data persists independently of a container's temporary filesystem. [Volumes](https://modal.com/docs/guide/volumes) and [download CLI](https://modal.com/docs/cli/latest/volume).

Record calibration, the experiment report, actual billed usage, and verification in Iteris locally. The Modal upload bundle contains model code, configurations, relevant tests, and one public 304-edge seed; it does not upload `.git`, so `git_head` may be absent while source hashes remain available.

**This original Modal entrypoint still uses the seed/bootstrap population.** It does not upload the audited 180-orbit corpus or reproduce the later Slurm diagnostic suite. Keep that distinction when comparing results. A retained overall best of 304 may be the initial reference, and a training run finishing is not mathematical progress. Further project training remains paused.
