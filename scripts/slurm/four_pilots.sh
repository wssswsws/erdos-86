#!/usr/bin/env bash
# Four independent experiments, not DDP. Preserve Slurm's CUDA_VISIBLE_DEVICES mapping.
set -euo pipefail
: "${SLURM_JOB_ID:?This worker must run inside a Slurm allocation}"
project_root="${ERDOS86_PROJECT_ROOT:-${SLURM_SUBMIT_DIR:-}}"
cd "$project_root"
python_bin="${ERDOS86_PYTHON:-$project_root/.venv/bin/python}"
"$python_bin" - <<'PY'
import torch
if torch.cuda.device_count() != 4:
    raise SystemExit(f'Expected exactly four assigned GPUs, got {torch.cuda.device_count()}.')
PY
mkdir -p "logs/slurm-${SLURM_JOB_ID}"
pids=()
trap 'kill "${pids[@]}" 2>/dev/null || true; exit 130' INT TERM
for rank in 0 1 2 3; do
    seed=$((8601 + rank))
    bash scripts/slurm/run_graphgps.sh pilot "cuda:$rank" "$seed" \
        > "logs/slurm-${SLURM_JOB_ID}/seed-${seed}.log" 2>&1 &
    pids+=("$!")
    echo "Started seed=$seed on logical cuda:$rank; log=logs/slurm-${SLURM_JOB_ID}/seed-${seed}.log"
done
result=0
for pid in "${pids[@]}"; do
    if ! wait "$pid"; then result=1; fi
done
echo "Four independent experiments finished; aggregate exit=$result"
exit "$result"
