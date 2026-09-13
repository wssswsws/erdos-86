"""Explicit, bounded Modal entrypoints for route 4. Direct Python execution is offline."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

import modal

LOCAL_ROOT = Path(__file__).resolve().parents[1]
REMOTE_ROOT = Path('/workspace')
VOLUME_NAME = 'erdos86-graphgps-results'
GPU = os.environ.get('ERDOS86_MODAL_GPU', 'L4')
if GPU not in {'L4', 'A10', 'L40S', 'A100-40GB'}:
    raise ValueError('ERDOS86_MODAL_GPU must be L4, A10, L40S, or A100-40GB')

app = modal.App('erdos86-graphgps')
volume = modal.Volume.from_name(VOLUME_NAME, create_if_missing=True)
image = (
    modal.Image.debian_slim(python_version='3.13')
    .apt_install('git')
    .pip_install('torch==2.10.0', index_url='https://download.pytorch.org/whl/cu128')
    .pip_install('pytest>=8,<10')
    .env({'PYTHONPATH': str(REMOTE_ROOT), 'PYTHONUNBUFFERED': '1',
          'ERDOS86_MODAL_GPU': GPU, 'OMP_NUM_THREADS': '2', 'MKL_NUM_THREADS': '2'})
    .workdir(REMOTE_ROOT)
    .add_local_dir(LOCAL_ROOT / 'erdos86_gps', '/workspace/erdos86_gps',
                   ignore=['**/__pycache__/**', '**/*.pyc'])
    .add_local_dir(LOCAL_ROOT / 'configs/graphgps', '/workspace/configs/graphgps')
    .add_local_dir(LOCAL_ROOT / 'tests/graphgps', '/workspace/tests/graphgps',
                   ignore=['**/__pycache__/**', '**/*.pyc'])
    .add_local_file(LOCAL_ROOT / 'references/baselines/86-selected_edges_best.json',
                    '/workspace/references/baselines/86-selected_edges_best.json')
)

resources = dict(image=image, gpu=GPU, cpu=(2.0, 2.0), memory=(8192, 8192),
                 volumes={'/results': volume}, max_containers=1,
                 min_containers=0, scaledown_window=2, retries=0)


def validate_run_id(run_id):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,79}', run_id):
        raise ValueError('run-id must be 1–80 ASCII letters/digits/dots/dashes/underscores')


def execute_job(mode, run_id):
    validate_run_id(run_id)
    if mode not in {'benchmark', 'pilot'}:
        raise ValueError('Unknown mode')
    output = Path('/results') / run_id
    # Persist a claim before computing. A preemption replay must not start a new full budget.
    output.mkdir(parents=True, exist_ok=False)
    record = {'mode': mode, 'run_id': run_id, 'requested_gpu': GPU,
              'modal_sdk': modal.__version__, 'status': 'started',
              'started_utc': datetime.now(timezone.utc).isoformat(), 'commands': []}
    record_path = output / 'modal-run.json'
    record_path.write_text(json.dumps(record, indent=2) + '\n')
    volume.commit()
    started = time.monotonic()

    def command(*args):
        record['commands'].append(list(args))
        subprocess.run([sys.executable, *args], cwd=REMOTE_ROOT, check=True)

    try:
        if mode == 'benchmark':
            command('-m', 'pytest', '-q', 'tests/graphgps',
                    f'--junitxml={output / "tests.xml"}')
            command('-m', 'erdos86_gps', 'benchmark', '--device', 'cuda', '--steps', '20',
                    '--output', str(output / 'benchmark.json'))
            command('-m', 'erdos86_gps', 'estimate',
                    '--calibration', str(output / 'benchmark.json'),
                    '--output', str(output / 'estimate.json'))
            result = json.loads((output / 'estimate.json').read_text())
        else:
            config = json.loads((REMOTE_ROOT / 'configs/graphgps/pilot.json').read_text())
            if not 0 < config['max_wall_seconds'] <= 14400:
                raise ValueError('Modal pilot requires a positive wall cap of at most 4 hours')
            command('-m', 'erdos86_gps', 'run', '--execute', '--device', 'cuda',
                    '--output', str(output / 'training'))
            report = json.loads((output / 'training/report.json').read_text())
            result = {key: report.get(key) for key in
                      ['stopping_reason', 'sampled_graphs', 'best_source', 'best_validation']}
        record['status'] = 'completed'
        return {'run_id': run_id, 'volume': VOLUME_NAME, 'result': result}
    except BaseException as exc:
        record.update(status='interrupted_or_failed', error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        record['elapsed_seconds'] = time.monotonic() - started
        record_path.write_text(json.dumps(record, indent=2) + '\n')
        volume.commit()


@app.function(timeout=900, **resources)
def calibrate(run_id: str):
    return execute_job('benchmark', run_id)


@app.function(timeout=14700, **resources)
def pilot(run_id: str):
    return execute_job('pilot', run_id)


@app.local_entrypoint()
def main(mode: str = 'benchmark', run_id: str = '', execute: bool = False):
    if mode not in {'benchmark', 'pilot'}:
        raise ValueError('--mode must be benchmark or pilot')
    validate_run_id(run_id)
    if not execute:
        raise ValueError('Add --execute to request cloud compute; plain Python checks this file offline')
    function = calibrate if mode == 'benchmark' else pilot
    print(json.dumps(function.remote(run_id), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    print(f'Offline definition check passed: Modal {modal.__version__}, GPU={GPU}.')
    print('No cloud calls made. See docs/modal-guide.md for explicit launch commands.')
