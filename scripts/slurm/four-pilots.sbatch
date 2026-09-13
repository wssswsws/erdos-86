#!/usr/bin/env bash
#SBATCH --job-name=erdos86-four-seeds
#SBATCH --partition=gpuq
#SBATCH --account=hpcusers
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:a100:4
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=04:15:00
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err
#SBATCH --no-requeue

set -euo pipefail
: "${SLURM_JOB_ID:?Submit this file with sbatch, not bash on the login node}"
cd "${ERDOS86_PROJECT_ROOT:-$SLURM_SUBMIT_DIR}"
# A single Slurm task owns four assigned GPUs; its four workers each use one logical device.
srun --ntasks=1 bash scripts/slurm/four_pilots.sh
