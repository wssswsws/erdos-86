#!/usr/bin/env python3
"""Run a fixed, bounded, sequential two-arm / three-seed diagnostic suite."""
import argparse
import gc
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import torch
from erdos86_gps.cli import write_json
from erdos86_gps.diagnostics import run_diagnostic


def validate(config):
    if config['arms'] != ['reference80', 'legacy_topk']:
        raise ValueError('Expected the prespecified two-arm comparison')
    if len(set(config['seeds'])) != len(config['seeds']) or not config['seeds']:
        raise ValueError('Expected distinct seeds')
    if not 0 < config['max_wall_seconds'] <= 1800 or not 0 < config['suite_wall_seconds'] <= 12600:
        raise ValueError('Exceeded bounded diagnostic budget')
    if config['model']['n'] != 7 or not 0 < config['heldout_orbits'] < 180 or config['elite_size'] < 180:
        raise ValueError('Invalid audited Q7 corpus configuration')
    for key in ['pretrain_steps', 'rounds', 'round_train_steps', 'samples_per_round', 'eval_samples', 'eval_prefixes', 'batch_size', 'sample_batch_size']:
        if not isinstance(config[key], int) or config[key] <= 0:
            raise ValueError(f'Invalid {key}')
    if config['reference_fraction'] != .8:
        raise ValueError('reference80 must reserve 80% reference probability')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', default='configs/graphgps/diagnostics.json')
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--device', default='cuda:0')
    p.add_argument('--execute', action='store_true')
    p.add_argument('--smoke', action='store_true')
    args = p.parse_args()
    config = json.loads(Path(args.config).read_text())
    if args.smoke:
        config.update(model={'n': 7, 'width': 16, 'layers': 2, 'heads': 4}, seeds=[8611],
                      pretrain_steps=2, rounds=1, round_train_steps=1, samples_per_round=2,
                      eval_samples=2, eval_prefixes=8, batch_size=2, sample_batch_size=2,
                      max_wall_seconds=120, suite_wall_seconds=300)
    validate(config)
    if not args.execute:
        print(json.dumps(config, indent=2)); return
    if args.output.exists():
        raise SystemExit('Output exists; refusing to replay or overwrite a suite.')
    args.output.mkdir(parents=True)
    torch.set_num_threads(2)
    hardware = {'device': args.device, 'python': platform.python_version(), 'torch': str(torch.__version__)}
    if args.device.startswith('cuda'):
        if not torch.cuda.is_available():
            raise SystemExit('CUDA unavailable; no CPU fallback for a GPU submission.')
        torch.cuda.set_device(torch.device(args.device))
        if torch.__version__.split('+')[0] != '2.10.0':
            raise SystemExit('This profile requires the tested PyTorch 2.10.0 environment.')
        hardware.update(gpu=torch.cuda.get_device_name(), visible_gpu_count=torch.cuda.device_count(),
                        total_gpu_memory_bytes=torch.cuda.get_device_properties(torch.device(args.device)).total_memory,
                        bf16_supported=torch.cuda.is_bf16_supported())
    write_json(args.output / 'hardware.json', hardware)
    write_json(args.output / 'suite-config.json', config)
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    (args.output / 'git-revision.txt').write_text(revision + '\n')
    started = time.monotonic()
    report = {'schema': 'erdos86.diagnostic.suite.v1', 'status': 'running', 'runs': [], 'config': config,
              'smoke': args.smoke, 'hardware': hardware, 'git_revision': revision}
    write_json(args.output / 'suite-report.json', report)
    exit_code = 0
    try:
        for i, seed in enumerate(config['seeds']):
            arms = config['arms'] if i % 2 == 0 else list(reversed(config['arms']))
            for arm in arms:
                remaining = config['suite_wall_seconds'] - (time.monotonic() - started)
                if remaining < config['max_wall_seconds'] + 30:
                    report['status'] = 'suite_budget'; return
                run_config = {**config, 'seed': seed, 'arm': arm}
                entry = {'seed': seed, 'arm': arm, 'directory': f'{arm}-seed-{seed}', 'status': 'running'}
                report['runs'].append(entry)
                write_json(args.output / 'suite-report.json', report)
                print(json.dumps({'phase': 'suite_run', **entry}), flush=True)
                result = run_diagnostic(run_config, args.output / entry['directory'], device=args.device,
                                        population_path=config['population'], population_audit=config['population_audit'])
                entry.update(status=result['stopping_reason'], training_steps=result['training_steps'],
                             sampled_graphs=result['sampled_graphs'], wall_seconds=result['wall_seconds'],
                             best=result['best_validation']['edges'],
                             best_model=result['best_model_validation']['edges'] if result['best_model_validation'] else None)
                write_json(args.output / 'suite-report.json', report)
                del result
                gc.collect()
                if args.device.startswith('cuda'):
                    torch.cuda.empty_cache()
                if entry['status'] == 'verified_target_candidate':
                    report['status'] = 'verified_target_candidate'; return
        report['status'] = ('completed' if all(r['status'] == 'completed' for r in report['runs'])
                            else 'completed_with_run_limits')
    except (Exception, KeyboardInterrupt) as exc:
        exit_code = 1
        report['status'] = 'interrupted' if isinstance(exc, KeyboardInterrupt) else 'error'
        report['error'] = f'{type(exc).__name__}: {exc}'
        if report['runs'] and report['runs'][-1]['status'] == 'running':
            report['runs'][-1]['status'] = report['status']
        raise
    finally:
        report['wall_seconds'] = time.monotonic() - started
        write_json(args.output / 'suite-report.json', report)
        (args.output / 'exit-code.txt').write_text(str(exit_code) + '\n')
        print(json.dumps({'phase': 'suite_end', 'status': report['status'], 'runs': len(report['runs']),
                          'wall_seconds': report['wall_seconds']}), flush=True)


if __name__ == '__main__':
    main()
