#!/usr/bin/env bash
# Shared single-GPU worker. No downloads or installations on a compute node.
set -euo pipefail
: "${SLURM_JOB_ID:?This worker must run inside a Slurm allocation}"
project_root="${ERDOS86_PROJECT_ROOT:-${SLURM_SUBMIT_DIR:-}}"
[[ -d "$project_root/erdos86_gps" ]] || { echo 'Submit from the erdos-86 repository root.' >&2; exit 2; }
cd "$project_root"
python_bin="${ERDOS86_PYTHON:-$project_root/.venv/bin/python}"
[[ -x "$python_bin" ]] || { echo "Python not found: $python_bin. Prepare .venv or set ERDOS86_PYTHON." >&2; exit 2; }
mode="${1:-benchmark}"
device="${2:-cuda:0}"
seed="${3:-8601}"
[[ "$mode" == benchmark || "$mode" == pilot ]] || { echo 'Expected benchmark or pilot.' >&2; exit 2; }
[[ "$device" =~ ^cuda:[0-9]+$ && "$seed" =~ ^[0-9]+$ ]] || { echo 'Invalid device or seed.' >&2; exit 2; }
export PYTHONPATH="$project_root${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONUNBUFFERED=1
export OMP_NUM_THREADS=2
export MKL_NUM_THREADS=2
run_dir="$project_root/artifacts/experiments/slurm-${SLURM_JOB_ID}/${mode}-seed-${seed}"
mkdir -p "$(dirname "$run_dir")"
mkdir "$run_dir"  # Refuse to overwrite/replay an existing experiment.
trap 'worker_exit=$?; printf "%s\n" "$worker_exit" > "$run_dir/exit-code.txt"' EXIT
git rev-parse HEAD > "$run_dir/git-revision.txt"
if git diff --quiet HEAD -- erdos86_gps configs/graphgps scripts/slurm; then
    echo clean > "$run_dir/source-working-tree.txt"
else
    echo modified > "$run_dir/source-working-tree.txt"
fi
"$python_bin" - "$device" "$run_dir" "$seed" <<'PY'
import json
from pathlib import Path
import platform
import sys
import torch
device, output, seed = sys.argv[1], Path(sys.argv[2]), int(sys.argv[3])
if not torch.cuda.is_available():
    raise SystemExit('CUDA unavailable inside allocation; check GPU request and the PyTorch environment.')
index = int(device.split(':')[1])
if index >= torch.cuda.device_count():
    raise SystemExit(f'{device} is not visible; only {torch.cuda.device_count()} GPUs are assigned.')
torch.cuda.set_device(index)
hardware = {'device': device, 'gpu': torch.cuda.get_device_name(index),
            'visible_gpu_count': torch.cuda.device_count(), 'python': platform.python_version(),
            'torch': str(torch.__version__), 'cuda': torch.version.cuda,
            'total_gpu_memory_bytes': torch.cuda.get_device_properties(index).total_memory,
            'bf16_supported': torch.cuda.is_bf16_supported()}
(output / 'hardware.json').write_text(json.dumps(hardware, indent=2) + '\n')
print(json.dumps(hardware, indent=2), flush=True)
if torch.__version__.split('+')[0] != '2.10.0':
    raise SystemExit('This launch profile requires tested PyTorch 2.10.0; prepare the pinned environment first.')
config = json.loads(Path('configs/graphgps/pilot.json').read_text())
config['seed'] = seed
if not 0 < config['max_wall_seconds'] <= 14400:
    raise SystemExit('Pilot wall cap must be positive and at most 4 hours.')
(output / 'run-config.json').write_text(json.dumps(config, indent=2) + '\n')
PY
config="$run_dir/run-config.json"
echo "Output directory: $run_dir"
if [[ "$mode" == benchmark ]]; then
    "$python_bin" -m pytest -q tests/graphgps --junitxml="$run_dir/tests.xml"
    "$python_bin" -m erdos86_gps benchmark --device "$device" --config "$config" \
        --steps 20 --output "$run_dir/benchmark.json"
    "$python_bin" -m erdos86_gps estimate --config "$config" \
        --calibration "$run_dir/benchmark.json" --output "$run_dir/estimate.json"
else
    "$python_bin" -m erdos86_gps run --execute --device "$device" \
        --config "$config" --output "$run_dir"
    "$python_bin" -m erdos86_gps verify --candidate "$run_dir/best.json"
fi
