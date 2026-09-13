#!/usr/bin/env bash
# Call once from the login-node repository. Snapshot code before allocating a GPU.
set -euo pipefail
project_root=$(git rev-parse --show-toplevel)
cd "$project_root"
python_bin="${ERDOS86_PYTHON:-$project_root/.venv/bin/python}"
[[ -x "$python_bin" ]] || { echo 'Python environment missing.' >&2; exit 2; }
git diff --quiet HEAD -- erdos86_gps configs/graphgps/diagnostics.json scripts/run_graphgps_diagnostics.py scripts/slurm || {
    echo 'Commit the training sources before submission.' >&2; exit 2;
}
revision=$(git rev-parse HEAD)
snapshot="$project_root/.runs/diagnostics-${revision:0:12}"
receipt="$project_root/artifacts/experiments/diagnostics-submissions/${revision:0:12}"
mkdir -p "$(dirname "$receipt")" "$project_root/.runs"
mkdir "$receipt" || { echo 'A submission attempt already exists. Inspect its receipt and Slurm before retrying.' >&2; exit 2; }
printf '%s\n' "$revision" > "$receipt/git-revision.txt"
git worktree add --detach "$snapshot" "$revision"
mkdir -p "$snapshot/logs"
export ERDOS86_PROJECT_ROOT="$snapshot"
export ERDOS86_PYTHON="$python_bin"
job_id=$(sbatch --parsable --chdir="$snapshot" --job-name="erdos86-diag-${revision:0:8}" "$snapshot/scripts/slurm/diagnostics.sbatch")
printf '%s\n' "$job_id" > "$receipt/job-id.txt"
"$python_bin" - "$receipt" "$snapshot" "$job_id" "$revision" <<'PY'
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
receipt, snapshot, job, revision = sys.argv[1:]
data = {'job_id': job.split(';')[0], 'submitted_at': datetime.now(timezone.utc).isoformat(),
        'code_revision': revision, 'snapshot_directory': snapshot, 'status': 'submitted',
        'gpu_count': 1, 'slurm_hours': 4, 'runs': 6, 'automatic_requeue': False,
        'output_directory': f'{snapshot}/artifacts/experiments/slurm-{job.split(";")[0]}/diagnostics'}
(Path(receipt) / 'submission.json').write_text(json.dumps(data, indent=2) + '\n')
print(json.dumps(data, indent=2))
PY
