# Run the GraphGPS experiments on Slurm / A100

Prepared September 12, 2026; updated after the completed GPU experiments. The supplied lab profile uses partition `gpuq`, account `hpcusers`, and GPU resource `gpu:a100`. Other clusters must use their own account, partition, and resource names. The observed cluster also advertised `a100-40g`; do not assume that resource name is interchangeable with `a100`.

Submit jobs from the repository root on the login node. Training runs inside the resulting compute-node allocation. Further project experiments are currently paused; the commands below are for an explicitly requested reproduction or restart.

## Completed runs and entrypoints

- [Calibration 21924947](a100-calibration-21924947.md): A100 80GB PCIe; successful CUDA/bf16 and throughput checks.
- [Corpus pilot 21925840](corpus-single-gpu-pilot.md): 180 audited reference orbits; one A100; 19 min 39 sec.
- [Diagnostic suite 21929229](graphgps-pilot-diagnostic-plan.md): six sequential runs on one A100; 2 hr 4 min 42 sec. See the [results](graphgps-diagnostic-suite-results.md).

Slurm pilot launchers require the audited corpus and its audit file. They do not silently fall back to bootstrap data. The original generic pilot retains a four-hour program budget; the corpus-specific pilot uses a one-hour Slurm allocation.

## 1. Get the repository

For a newly created, empty directory:

```bash
cd "$HOME/erdos-86"
git clone https://github.com/wssswsws/erdos-86.git .
git log -1 --oneline
mkdir -p logs
```

The final `.` clones into the current directory. If it is already a checkout, use `git pull --ff-only` when no running job depends on that checkout's files. Inspect a nonempty directory rather than deleting files to force a clone.

Public HTTPS cloning does not require GitHub authentication. Pushing results does: use a configured credential manager, a supported token workflow, or an SSH key. An SSH remote is `git@github.com:wssswsws/erdos-86.git`. Do not embed a token in a remote URL or commit it. See [GitHub command-line authentication](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/about-authentication-to-github#authenticating-with-the-command-line).

## 2. Prepare Python

Create an isolated environment rather than changing the shared lab installation:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install torch==2.10.0 --index-url https://download.pytorch.org/whl/cu126
python -m pip install 'pytest>=8,<10'
python -c "import torch; print(torch.__version__, torch.version.cuda)"
```

The [official PyTorch 2.10.0 CUDA 12.6 wheel](https://pytorch.org/get-started/previous-versions/) was validated on the recorded A100 allocation. A different host still needs a compatible driver. CUDA being unavailable on the login node does not imply it is unavailable on the compute node.

If package downloads are unavailable, use the lab's matching environment or internal wheel mirror. Point the launcher to an executable accessible on the compute node:

```bash
export ERDOS86_PYTHON=/absolute/path/to/environment/bin/python
```

Otherwise it uses `.venv/bin/python` under the project root. Load required lab modules before submission. The worker checks the PyTorch version and does not install dependencies on a compute node. Modal, Iteris, PyG, and Lean are not required for these jobs.

## 3. Calibrate one A100

A submission check does not reserve a GPU or run the job:

```bash
sbatch --test-only scripts/slurm/graphgps.sbatch benchmark
```

To request the calibration:

```bash
sbatch scripts/slurm/graphgps.sbatch benchmark
```

It requests one A100, four Slurm CPUs, 16 GiB system memory, and 20 minutes. It checks hardware, runs the model tests, times 20 training steps at the full model size, generates a complete batch of 32 graphs, and estimates the pilot duration. It does not launch the pilot afterward.

Replace `JOB_ID` with the returned number:

```bash
squeue -u "$USER"
tail -f logs/erdos86-calibrate-JOB_ID.out
```

Ctrl+C exits `tail`; it does not cancel the job. Errors are in the corresponding `.err` file. After completion:

```bash
sacct -j JOB_ID --format=JobID,JobName,State,Elapsed,AllocTRES,MaxRSS,ExitCode
cat artifacts/experiments/slurm-JOB_ID/benchmark-seed-8601/exit-code.txt
cat artifacts/experiments/slurm-JOB_ID/benchmark-seed-8601/hardware.json
cat artifacts/experiments/slurm-JOB_ID/benchmark-seed-8601/estimate.json
```

Check the exit code, Slurm state, and report together. `estimated_allocated_hours_with_paired_baseline` includes CPU repair and a paired baseline, but not all startup and saving costs. A returned job ID means submission was accepted; the job may still be queued. [Slurm submission reference](https://slurm.schedmd.com/sbatch.html).

## 4. Choose one experiment

For the first corpus pilot's configuration:

```bash
sbatch scripts/slurm/corpus-pilot.sbatch 8601
```

It uses a 55-minute program soft limit and one-hour Slurm hard limit. Details are in the [corpus pilot note](corpus-single-gpu-pilot.md).

To reproduce the six-run diagnostic design, submit once from the main checkout:

```bash
bash scripts/slurm/submit_diagnostics.sh
```

This creates a commit-pinned worktree, writes a submission receipt, and refuses duplicate submission for that revision. It runs six experiments sequentially on one A100. Outputs belong to that worktree, not the original pilot directory. See the [diagnostic plan](graphgps-pilot-diagnostic-plan.md).

The older generic single-seed pilot is also available:

```bash
sbatch --job-name=erdos86-pilot --time=04:15:00 \
  scripts/slurm/graphgps.sbatch pilot 8601
```

Keep `--time=04:15:00`: otherwise the calibration script's 20-minute limit applies. The program has a four-hour soft limit; the extra 15 minutes allow startup and saving. A time limit does not guarantee all planned rounds finish.

### Four independent seeds on four GPUs

For an explicitly budgeted four-seed experiment:

```bash
sbatch scripts/slurm/four-pilots.sbatch
```

This requests one node, four A100s, 16 Slurm CPUs, and 64 GiB system memory. Four independent processes use seeds 8601–8604 and the allocated logical devices `cuda:0`–`cuda:3`. They respect Slurm's `CUDA_VISIBLE_DEVICES`; these are not assumed to be physical GPU numbers. [Slurm GPU allocation](https://slurm.schedmd.com/gres.html).

Each process has its own output directory and log:

```text
artifacts/experiments/slurm-JOB_ID/pilot-seed-8601/
artifacts/experiments/slurm-JOB_ID/pilot-seed-8602/
artifacts/experiments/slurm-JOB_ID/pilot-seed-8603/
artifacts/experiments/slurm-JOB_ID/pilot-seed-8604/
logs/slurm-JOB_ID/seed-8601.log
```

Four GPUs allocated for four hours consume approximately 16 GPU hours, plus allocation overhead. This is four independent models, not distributed training of one model. They do not share elite pools; one finding 305 does not stop the other three automatically. Four-GPU concurrency has not been validated on the cluster.

## 5. Stop or troubleshoot

```bash
scancel JOB_ID
```

Forced termination may occur before the latest state is saved. Checkpoints are written at stage boundaries and normal timeout; exact restoration of a partially sampled batch is not promised. Jobs disable requeue and output overwriting. Inspect saved work before defining a continuation budget.

| Symptom | Check |
| --- | --- |
| No logs | Create `logs/` before submission; queued jobs may not have produced output yet. |
| Python not found | Prepare `.venv` or set `ERDOS86_PYTHON` to a shared absolute executable path. |
| CUDA unavailable / insufficient driver | Inspect `.err` and `hardware.json`; check the compute-node driver and wheel. |
| Invalid account / partition / GRES | Check `sinfo -o '%P %G %l %a'` and your lab's allocation settings. |
| Out of memory | Distinguish host RAM from GPU memory; recalibrate after changing resources or batch size. |

## 6. Return results through GitHub

After inspecting the output, create a results branch and stage only the intended reports and certificates:

```bash
git switch -c results/slurm-JOB_ID
git add artifacts/experiments/slurm-JOB_ID
git diff --cached --stat
git commit -m "Record Slurm JOB_ID GraphGPS results [skip ci]"
git push -u origin HEAD
```

Review the actual files before committing. Checkpoints (`.pt`), ordinary terminal logs, and environments are ignored. Avoid `git add .`. `report.json` records source hashes and candidate provenance; `best.json` contains a full edge list. The overall best may be an inherited 304-edge reference.

For diagnostics, inspect the receipt for the separate worktree path and collect the files from there. Large candidate streams may need lossless compression; model checkpoints need a separate transfer mechanism if they are required for review.

After returning results, independently verify certificates and record measured allocation time and conclusions in Iteris. Switch back to `main` before pulling future code. Do not change the source checkout used by a running job.

## Validation boundary

Initial preparation checked 15 model tests, shell syntax, login-node execution guards, device/seed/output isolation with a fake worker, and overwrite rejection. [Preparation evidence](../artifacts/experiments/slurm-preparation/validation.json) concerns that local orchestration check. Later single-A100 calibration and experiments validated the actual CUDA path. They do not establish four-GPU performance.
