#!/usr/bin/env bash
#SBATCH --job-name=erdos86-diag
#SBATCH --partition=gpuq
#SBATCH --account=hpcusers
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err
#SBATCH --no-requeue

set -euo pipefail
: "${SLURM_JOB_ID:?Submit with sbatch, not bash on the login node}"
cd "${ERDOS86_PROJECT_ROOT:-$SLURM_SUBMIT_DIR}"
python_bin="${ERDOS86_PYTHON:-$PWD/.venv/bin/python}"
[[ -x "$python_bin" ]] || { echo 'Prepare the tested Python environment first.' >&2; exit 2; }
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONUNBUFFERED=1
export OMP_NUM_THREADS=2
export MKL_NUM_THREADS=2
out="artifacts/experiments/slurm-${SLURM_JOB_ID}/diagnostics"
[[ ! -e "$out" ]] || { echo 'Output exists; refusing to repeat a suite.' >&2; exit 2; }
git diff --quiet HEAD -- erdos86_gps scripts/run_graphgps_diagnostics.py scripts/slurm/diagnostics.sbatch configs/graphgps/diagnostics.json || {
    echo 'Training sources differ from the submitted commit.' >&2; exit 2;
}
# Fail fast on the allocated node; never install packages or fall back to CPU training.
srun --ntasks=1 "$python_bin" -m pytest -q tests/graphgps
srun --ntasks=1 "$python_bin" scripts/run_graphgps_diagnostics.py --execute --device cuda:0 --output "$out"
