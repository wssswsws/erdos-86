"""Bounded smoke, GPU calibration, training loop, and CPU baseline commands."""
import argparse
from collections import Counter
from hashlib import sha256
import json
import math
from pathlib import Path
import platform
import subprocess
import time
import torch
from .cube import Cube
from .engine import BudgetExpired, Trainer, check_deadline, precision_context, sample, synchronize
from .model import Generator, ModelConfig, prefix_states
from .search import bootstrap, local_search
from .verify import verify_edges

ROOT = Path(__file__).resolve().parents[1]


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    temp.replace(path)


def load_config(path):
    config = json.loads(Path(path).read_text())
    positive = ['batch_size', 'initial_population', 'elite_size', 'sample_batch_size', 'max_wall_seconds']
    nonnegative = ['pretrain_steps', 'rounds', 'samples_per_round', 'round_train_steps', 'repair_kicks']
    if any(config[k] <= 0 for k in positive) or any(config[k] < 0 for k in nonnegative):
        raise ValueError('Invalid run limits')
    if config['model']['n'] != 7:
        raise ValueError('Project workflow expects Q7; components support smaller test cubes')
    return config


def known_seed(cube):
    path = ROOT / 'references/baselines/86-selected_edges_best.json'
    raw = path.read_bytes()
    data = json.loads(raw)
    verify_edges(data['n'], data['edges'])
    return cube.encode(data['edges']), {'path': str(path.relative_to(ROOT)), 'sha256': sha256(raw).hexdigest()}


def provenance():
    files = {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest()
             for p in sorted((ROOT / 'erdos86_gps').glob('*.py'))}
    revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True, capture_output=True)
    return {'python': platform.python_version(), 'torch': str(torch.__version__), 'platform': platform.platform(),
            'git_head': revision.stdout.strip(), 'source_sha256': files,
            'cuda_version': torch.version.cuda}


def read_population(path, cube, *, audit_path=None):
    raw = Path(path).read_bytes()
    population = set()
    rows = 0
    for line in raw.decode().splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get('n', cube.n) != cube.n:
            raise ValueError('Population dimension mismatch')
        verify_edges(cube.n, record['edges'])
        population.add(tuple(cube.encode(record['edges'])))
        rows += 1
    if not population:
        raise ValueError('Empty training population')
    meta = {'path': str(path), 'sha256': sha256(raw).hexdigest(),
            'rows': rows, 'exact_label_unique': len(population), 'orbit_dedup': False}
    if audit_path:
        audit_raw = Path(audit_path).read_bytes()
        audit = json.loads(audit_raw)
        if (audit.get('schema') != 'erdos86.corpus.audit.v1'
                or audit.get('population_sha256') != meta['sha256']
                or audit.get('representatives') != rows or rows != len(population)
                or audit.get('canonical_minimality_verified') is not True
                or cube.n != 7 or any(sum(bits) != 304 for bits in population)):
            raise ValueError('Population audit mismatch or incomplete orbit verification')
        meta.update(orbit_dedup=True, audit_path=str(audit_path),
                    audit_sha256=sha256(audit_raw).hexdigest(), source_commit=audit['source_commit'],
                    orbit_scope='Initial population only; later elite updates use exact-label dedup.',
                    held_out_evaluation=False)
    return [list(bits) for bits in sorted(population)], meta


def run_loop(config, output, *, device='cpu', checkpoint=None, population_path=None, population_audit=None, smoke=False):
    output = Path(output)
    if (output / 'report.json').exists() or (output / 'candidates.jsonl').exists():
        raise ValueError('Output already contains a run; choose a fresh directory')
    output.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(config['seed'])
    started = time.monotonic()
    deadline = started + config['max_wall_seconds']
    cube = Cube.build(config['model']['n'])
    seed_bits, source = known_seed(cube)
    population_source = None
    if checkpoint and population_path:
        raise ValueError('Use either a checkpoint population or --population, not both')
    if population_audit and not population_path:
        raise ValueError('Population audit requires --population')
    if checkpoint:
        trainer, population, _ = Trainer.load(checkpoint, device=device)
        if trainer.model.config != ModelConfig(**config['model']):
            raise ValueError('Checkpoint architecture and run config differ')
    else:
        if population_path:
            population, population_source = read_population(population_path, cube, audit_path=population_audit)
        else:
            population = bootstrap(cube, seed_bits, config['initial_population'], config['seed'])
        trainer = Trainer(Generator(ModelConfig(**config['model'])), device=device, seed=config['seed'])
    for bits in population:
        verify_edges(cube.n, cube.decode(bits))
    baseline_population = [bits.copy() for bits in population]
    initial_steps = trainer.steps
    initial_population_size = len(population)
    best = max(population, key=sum)
    report = {'schema': 'erdos86_gps.run.v1', 'mode': 'smoke' if smoke else 'gpu_pilot',
              'config': config, 'device': str(device), 'provenance': provenance(), 'seed_source': source,
              'parameters': trainer.model.parameter_count(), 'initial_best': sum(best),
              'population_source': population_source,
              'best_source': 'initial_population',
              'initial_population': initial_population_size,
              'data_scope': 'Training population; see population_source for initial orbit audit. Later elites use exact-label dedup. No held-out generalization claim.',
              'resume_semantics': 'Restores trainer and population; this invocation starts a new bounded set of rounds.',
              'training_seconds': 0.0, 'generation_seconds': 0.0, 'repair_seconds': 0.0,
              'baseline_seconds': 0.0, 'sampled_graphs': 0, 'losses': [], 'rounds': [],
              'stopping_reason': 'completed', 'comparison_scope': 'Paired repair counts only; NOT equal total compute.',
              'local_branch_gradient_seen': False if smoke else None,
              'global_branch_gradient_seen': False if smoke else None}
    write_json(output / 'config.json', config)
    if torch.device(device).type == 'cuda':
        torch.cuda.reset_peak_memory_stats(device)

    def train(steps):
        for _ in range(steps):
            check_deadline(deadline)
            synchronize(device)
            t0 = time.monotonic()
            stats = trainer.train_step(population, config['batch_size'])
            synchronize(device)
            report['training_seconds'] += time.monotonic() - t0
            report['losses'].append({'step': trainer.steps, **stats})
            if smoke:
                for name, param in trainer.model.named_parameters():
                    if param.grad is not None and bool(torch.any(param.grad != 0)):
                        if 'factor_update' in name or 'variable_update' in name:
                            report['local_branch_gradient_seen'] = True
                        if 'qkv' in name:
                            report['global_branch_gradient_seen'] = True
            if trainer.steps % 100 == 0:
                print(json.dumps({'phase': 'train', 'step': trainer.steps, 'loss': stats['loss']}), flush=True)

    try:
        train(config['pretrain_steps'])
        trainer.save(output / 'checkpoint.pt', population, {'phase': 'pretrained'})
        for round_id in range(config['rounds']):
            new_graphs, baseline_scores, raw_scores = [], [], []
            for offset in range(0, config['samples_per_round'], config['sample_batch_size']):
                check_deadline(deadline)
                size = min(config['sample_batch_size'], config['samples_per_round'] - offset)
                synchronize(device)
                t0 = time.monotonic()
                graphs, sampling = sample(trainer.model, size, seed=config['seed'] + 100000 * (round_id + 1) + offset,
                                          deadline=deadline)
                synchronize(device)
                report['generation_seconds'] += time.monotonic() - t0
                for j, bits in enumerate(graphs):
                    check_deadline(deadline)
                    validation = verify_edges(cube.n, cube.decode(bits))
                    raw_scores.append(sum(bits))
                    t0 = time.monotonic()
                    repaired = local_search(cube, bits, seed=config['seed'] + offset + j + 17,
                                            kicks=config['repair_kicks'])
                    report['repair_seconds'] += time.monotonic() - t0
                    repaired_validation = verify_edges(cube.n, cube.decode(repaired))
                    t0 = time.monotonic()
                    baseline = local_search(cube, baseline_population[(offset + j) % len(baseline_population)],
                                            seed=config['seed'] + offset + j + 17, kicks=config['repair_kicks'])
                    report['baseline_seconds'] += time.monotonic() - t0
                    baseline_scores.append(sum(baseline))
                    candidate = {'round': round_id, 'index': offset + j, 'raw_validation': validation,
                                 'repaired_validation': repaired_validation, 'edges': cube.decode(repaired),
                                 'forced_zero_decisions': sampling['forced_zero_decisions'][j],
                                 'paired_baseline_edges': sum(baseline)}
                    with (output / 'candidates.jsonl').open('a') as f:
                        f.write(json.dumps(candidate) + '\n')
                    new_graphs.append(repaired)
                    report['sampled_graphs'] += 1
                    if sum(repaired) > sum(best):
                        best = repaired
                        report['best_source'] = 'repaired_model_sample'
                    if sum(baseline) > sum(best):
                        best = baseline
                        report['best_source'] = 'paired_local_baseline'
                    if sum(best) >= 305:
                        report['stopping_reason'] = 'verified_target_candidate'
                        break
                print(json.dumps({'phase': 'sample_repair', 'round': round_id,
                                  'samples': report['sampled_graphs'], 'best': sum(best)}), flush=True)
                if sum(best) >= 305:
                    break
            unique = {tuple(bits) for bits in population + new_graphs}
            population = [list(bits) for bits in sorted(unique, key=lambda bits: (-sum(bits), bits))[:config['elite_size']]]
            report['rounds'].append({'round': round_id, 'raw_edge_counts': raw_scores,
                                     'repaired_edge_counts': [sum(bits) for bits in new_graphs],
                                     'paired_baseline_edge_counts': baseline_scores,
                                     'elite_exact_label_unique': len(population)})
            if sum(best) >= 305:
                break
            train(config['round_train_steps'])
            trainer.save(output / 'checkpoint.pt', population, {'round_completed': round_id})
    except BudgetExpired:
        report['stopping_reason'] = 'wall_budget'
    except (Exception, KeyboardInterrupt) as exc:
        report['stopping_reason'] = 'interrupted' if isinstance(exc, KeyboardInterrupt) else 'error'
        report['error'] = f'{type(exc).__name__}: {exc}'
        raise
    finally:
        report['training_steps_this_run'] = trainer.steps - initial_steps
        report['training_steps_total'] = trainer.steps
        report['best_validation'] = verify_edges(cube.n, cube.decode(best))
        report['best_is_original_seed'] = best == seed_bits
        report['wall_seconds'] = time.monotonic() - started
        report['peak_cuda_allocated_bytes'] = torch.cuda.max_memory_allocated(device) if torch.device(device).type == 'cuda' else None
        trainer.save(output / 'checkpoint.pt', population, {'stopping_reason': report['stopping_reason']})
        write_json(output / 'best.json', {'n': cube.n, 'edges': cube.decode(best), 'validation': report['best_validation']})
        if smoke:
            restored, restored_population, _ = Trainer.load(output / 'checkpoint.pt', device=device)
            report['checkpoint_reload_equal'] = trainer.steps == restored.steps and population == restored_population and all(
                torch.equal(v, restored.model.state_dict()[k]) for k, v in trainer.model.state_dict().items())
            report['smoke_passed'] = (report['stopping_reason'] == 'completed' and report['sampled_graphs'] == config['samples_per_round'] * config['rounds']
                                      and report['local_branch_gradient_seen'] and report['global_branch_gradient_seen']
                                      and report['checkpoint_reload_equal'])
        write_json(output / 'report.json', report)
    print(json.dumps({'report': str(output / 'report.json'), 'best': sum(best),
                      'stop': report['stopping_reason'], 'smoke_passed': report.get('smoke_passed')}), flush=True)
    if smoke and not report['smoke_passed']:
        raise RuntimeError('Smoke did not complete successfully; inspect report')
    return report


def benchmark(config, *, device, steps, output):
    """Measure actual model/batch timing; CPU results never imply GPU throughput."""
    if steps < 1:
        raise ValueError('Benchmark steps must be positive')
    torch.manual_seed(config['seed'])
    cube = Cube.build(config['model']['n'])
    known, _ = known_seed(cube)
    trainer = Trainer(Generator(ModelConfig(**config['model'])), device=device, seed=config['seed'])
    for _ in range(2):
        trainer.train_step([known], config['batch_size'])
    synchronize(device)
    if torch.device(device).type == 'cuda':
        torch.cuda.reset_peak_memory_stats(device)
    t0 = time.monotonic()
    for _ in range(steps):
        trainer.train_step([known], config['batch_size'])
    synchronize(device)
    train_seconds = (time.monotonic() - t0) / steps
    targets = torch.tensor([known] * config['sample_batch_size'], device=device)
    ranks = torch.arange(len(cube.edges), device=device).expand_as(targets)
    prefix_length = torch.full((len(targets),), 224, device=device, dtype=torch.long)
    states = prefix_states(targets, ranks, prefix_length)
    trainer.model.eval()
    with torch.no_grad(), precision_context(device):
        for _ in range(2):
            trainer.model(states, ranks, prefix_length)
        synchronize(device)
        t0 = time.monotonic()
        for _ in range(steps):
            trainer.model(states, ranks, prefix_length)
        synchronize(device)
    forward_seconds = (time.monotonic() - t0) / steps
    # Small full sampling run measures Python/mask overhead and all prefix lengths.
    synchronize(device)
    t0 = time.monotonic()
    graphs, _ = sample(trainer.model, config['sample_batch_size'], seed=config['seed'] + 1)
    synchronize(device)
    sample_batch_seconds = time.monotonic() - t0
    for bits in graphs:
        verify_edges(cube.n, cube.decode(bits))
    t0 = time.monotonic()
    for i, bits in enumerate(graphs):
        local_search(cube, bits, seed=i, kicks=config['repair_kicks'])
    repair_seconds = (time.monotonic() - t0) / len(graphs)
    result = {'device': str(device), 'hardware': torch.cuda.get_device_name(device) if torch.device(device).type == 'cuda' else platform.processor(),
              'provenance': provenance(), 'config': config, 'steps': steps,
              'parameters': trainer.model.parameter_count(), 'train_step_seconds': train_seconds,
              'forward_seconds': forward_seconds, 'sample_batch_seconds': sample_batch_seconds,
              'repair_graph_seconds': repair_seconds,
              'peak_cuda_allocated_bytes': torch.cuda.max_memory_allocated(device) if torch.device(device).type == 'cuda' else None}
    write_json(output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def estimate(config, *, calibration=None):
    steps = config['pretrain_steps'] + config['rounds'] * config['round_train_steps']
    graphs = config['rounds'] * config['samples_per_round']
    batches = config['rounds'] * math.ceil(config['samples_per_round'] / config['sample_batch_size'])
    result = {'training_steps': steps, 'generated_graphs': graphs, 'sample_batches': batches,
              'full_graph_forward_calls': batches * 448, 'configured_wall_cap_hours': config['max_wall_seconds'] / 3600}
    d, layers = config['model']['width'], config['model']['layers']
    # Dense matmul-only estimate: factor/variable MLPs, QKV/out, FFN, QK and AV.
    ff_mult = config['model'].get('ff_mult', 4)
    per_forward = 2 * layers * (4 * 672 * d * d + (8 + 2 * ff_mult) * 448 * d * d + 2 * 448 * 448 * d)
    result['approx_forward_gflops_per_graph_prefix'] = per_forward / 1e9
    result['approx_total_matmul_pflops'] = (per_forward * graphs * 448 + 3 * per_forward * config['batch_size'] * steps) / 1e15
    result['flops_scope'] = 'Matmul estimate only; assumes full local+global architecture, backward about 2x forward; excludes gather, norms, masking and Python overhead.'
    if calibration:
        if not calibration['device'].startswith('cuda'):
            raise ValueError('A CPU calibration cannot estimate GPU hours')
        for key in ['model', 'batch_size', 'sample_batch_size', 'repair_kicks']:
            if calibration['config'][key] != config[key]:
                raise ValueError(f'Calibration does not match config field {key}')
        train = steps * calibration['train_step_seconds']
        generation = batches * calibration['sample_batch_seconds']
        cpu = graphs * calibration['repair_graph_seconds']
        result.update({'basis': 'Actual CUDA calibration; sequential repairs keep an allocated GPU idle.',
                       'train_gpu_hours': train / 3600, 'generation_gpu_hours': generation / 3600,
                       'sequential_repair_cpu_hours': cpu / 3600,
                       'estimated_allocated_hours_excluding_paired_baseline_and_startup': (train + generation + cpu) / 3600,
                       'estimated_allocated_hours_with_paired_baseline': (train + generation + 2 * cpu) / 3600})
    else:
        scenarios = []
        for label, train_ms, forward_ms, repair_ms in [('optimistic_assumption', 15, 5, 20), ('conservative_assumption', 80, 25, 200)]:
            train = steps * train_ms / 1000
            generation = batches * 448 * forward_ms / 1000
            cpu = graphs * repair_ms / 1000
            scenarios.append({'label': label, 'train_step_ms': train_ms, 'sample_step_batch_ms': forward_ms,
                              'repair_graph_ms': repair_ms, 'active_gpu_hours': (train + generation) / 3600,
                              'allocated_hours_with_sequential_repair_and_paired_baseline': (train + generation + 2 * cpu) / 3600})
        result.update({'basis': 'Planning assumptions, NOT measured GPU performance. No guarantee for any GPU model.',
                       'scenarios': scenarios, 'suggested_initial_reservation_hours': [2, 4],
                       'note': 'Calibrate external GPU first; cap may stop an unfinished run. Sampling has 448 full forwards and no KV cache.'})
    return result


def baseline(config, *, output, wall_seconds):
    cube = Cube.build(7)
    known, source = known_seed(cube)
    started = time.monotonic()
    deadline = started + wall_seconds
    best, trials, counts = known, 0, Counter()
    while time.monotonic() < deadline:
        start = best if trials % 2 == 0 else [0] * len(cube.edges)
        candidate = local_search(cube, start, seed=config['seed'] + trials, kicks=config['repair_kicks'])
        counts[sum(candidate)] += 1
        if sum(candidate) > sum(best):
            best = candidate
        trials += 1
        if sum(best) >= 305:
            break
    write_json(output, {'mode': 'cpu_local_search_baseline', 'trials': trials, 'edge_count_histogram': dict(counts),
                        'wall_seconds': time.monotonic() - started, 'seed_source': source,
                        'provenance': provenance(), 'config': config,
                        'best': {'n': 7, 'edges': cube.decode(best), 'validation': verify_edges(7, cube.decode(best))}})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['smoke', 'run', 'benchmark', 'estimate', 'baseline', 'verify'])
    parser.add_argument('--config')
    parser.add_argument('--output')
    parser.add_argument('--device', default='cpu')
    parser.add_argument('--threads', type=int, default=2)
    parser.add_argument('--checkpoint')
    parser.add_argument('--population', help='Optional verified JSONL edge-list training population')
    parser.add_argument('--population-audit', help='Audit JSON binding the initial orbit representatives by SHA-256')
    parser.add_argument('--calibration')
    parser.add_argument('--steps', type=int, default=20)
    parser.add_argument('--wall-seconds', type=float, default=60)
    parser.add_argument('--execute', action='store_true', help='Explicitly start the external GPU pilot')
    parser.add_argument('--candidate')
    args = parser.parse_args()
    torch.set_num_threads(args.threads)
    name = 'smoke' if args.command == 'smoke' else 'pilot'
    config = load_config(args.config or ROOT / f'configs/graphgps/{name}.json')
    if args.command == 'verify':
        if not args.candidate:
            parser.error('--candidate required')
        data = json.loads(Path(args.candidate).read_text())
        print(json.dumps(verify_edges(data['n'], data['edges']), indent=2))
        return
    if args.device.startswith('cuda') and not torch.cuda.is_available():
        parser.error('CUDA is unavailable; connect the external GPU first')
    if args.command == 'run':
        if not args.execute or not args.device.startswith('cuda'):
            parser.error('The research pilot requires --execute --device cuda after external GPU connection')
        if not args.output:
            parser.error('Choose a fresh --output directory')
    if args.command == 'smoke':
        if args.device != 'cpu':
            parser.error('This local smoke is CPU-only; use benchmark for external CUDA')
        run_loop(config, args.output or ROOT / 'artifacts/experiments/graphgps-smoke', device='cpu', smoke=True)
    elif args.command == 'run':
        run_loop(config, args.output, device=args.device, checkpoint=args.checkpoint,
                 population_path=args.population, population_audit=args.population_audit)
    elif args.command == 'benchmark':
        benchmark(config, device=args.device, steps=args.steps, output=args.output or 'graphgps-benchmark.json')
    elif args.command == 'estimate':
        result = estimate(config, calibration=json.loads(Path(args.calibration).read_text()) if args.calibration else None)
        if args.output:
            write_json(args.output, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.command == 'baseline':
        if args.wall_seconds <= 0:
            parser.error('A positive --wall-seconds is required')
        baseline(config, output=args.output or 'graphgps-baseline.json', wall_seconds=args.wall_seconds)


if __name__ == '__main__':
    main()
