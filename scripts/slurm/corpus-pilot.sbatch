#!/usr/bin/env bash
#SBATCH --job-name=erdos86-corpus
#SBATCH --partition=gpuq
#SBATCH --account=hpcusers
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err
#SBATCH --no-requeue

set -euo pipefail
: "${SLURM_JOB_ID:?Submit with sbatch, not bash on the login node}"
cd "${ERDOS86_PROJECT_ROOT:-$SLURM_SUBMIT_DIR}"
export ERDOS86_CONFIG=configs/graphgps/corpus-pilot.json
srun --ntasks=1 bash scripts/slurm/run_graphgps.sh pilot cuda:0 "${1:-8601}"
