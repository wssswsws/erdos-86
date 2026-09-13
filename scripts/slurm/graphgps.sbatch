#!/usr/bin/env bash
#SBATCH --job-name=erdos86-calibrate
#SBATCH --partition=gpuq
#SBATCH --account=hpcusers
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:20:00
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err
#SBATCH --no-requeue

set -euo pipefail
: "${SLURM_JOB_ID:?Submit this file with sbatch, not bash on the login node}"
cd "${ERDOS86_PROJECT_ROOT:-$SLURM_SUBMIT_DIR}"
mode="${1:-benchmark}"
if [[ "$mode" != benchmark && "$mode" != pilot ]]; then
    echo 'Usage: sbatch [resource options] scripts/slurm/graphgps.sbatch benchmark|pilot [seed]' >&2
    exit 2
fi
if [[ "$mode" == pilot ]]; then
    echo 'Pilot requires sbatch --time=04:15:00; the program itself has a 4-hour soft cap.'
fi
srun --ntasks=1 bash scripts/slurm/run_graphgps.sh "$mode" cuda:0 "${2:-8601}"
