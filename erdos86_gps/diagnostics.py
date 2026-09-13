"""Audited-corpus experiments with protected reference sampling and fixed evaluation."""
from collections import Counter
import gzip
from hashlib import sha256
import json
from pathlib import Path
import random
import statistics
import time

import torch

from .cli import provenance, read_population, write_json
from .cube import Cube
from .engine import BudgetExpired, Trainer, check_deadline, sample, synchronize
from .evaluation import evaluate_prefixes, fixed_prefixes
from .model import Generator, ModelConfig
from .search import local_search
from .verify import verify_edges


class TargetFound(RuntimeError):
    pass


def split_corpus(population, heldout_count, seed):
    """Input is already audited as one representative per distinct cube orbit."""
    if not 0 < heldout_count < len(population):
        raise ValueError('Holdout must be nonempty and leave training representatives')
    ids = list(range(len(population)))
    random.Random(seed).shuffle(ids)
    heldout_ids = sorted(ids[:heldout_count])
    training_ids = sorted(ids[heldout_count:])
    return ([population[i] for i in training_ids], [population[i] for i in heldout_ids],
            {'seed': seed, 'training_indices': training_ids, 'heldout_indices': heldout_ids,
             'index_order': 'lexicographically sorted edge-incidence vectors from read_population'})


def update_exploration(archive, new_graphs, capacity):
    # All holdout graphs have 304 edges. Excluding EVERY generated 304+ graph from
    # feedback gives an exact no-orbit-leakage guarantee without heuristic hashes.
    unique = {tuple(bits) for bits in archive + new_graphs if sum(bits) < 304}
    return [list(bits) for bits in sorted(unique, key=lambda x: (-sum(x), x))[:capacity]]


def sampling_weights(reference_count, exploration_count, arm, reference_fraction):
    if reference_count < 1 or exploration_count < 0:
        raise ValueError('Invalid pool sizes')
    if arm not in {'reference80', 'legacy_topk'} or not 0 < reference_fraction <= 1:
        raise ValueError('Invalid training arm or reference fraction')
    if not exploration_count:
        return [1 / reference_count] * reference_count
    if arm == 'legacy_topk':
        return [1 / (reference_count + exploration_count)] * (reference_count + exploration_count)
    return ([reference_fraction / reference_count] * reference_count
            + [(1 - reference_fraction) / exploration_count] * exploration_count)


def score_summary(scores):
    if not scores:
        return {'samples': 0}
    ordered = sorted(scores)
    return {'samples': len(scores), 'mean': statistics.mean(scores), 'min': min(scores), 'max': max(scores),
            'p90': ordered[int(.9 * (len(scores) - 1))], 'p99': ordered[int(.99 * (len(scores) - 1))],
            'at_least_300': sum(x >= 300 for x in scores), 'at_least_304': sum(x >= 304 for x in scores),
            'at_least_305': sum(x >= 305 for x in scores), 'histogram': dict(sorted(Counter(scores).items()))}


def run_diagnostic(config, output, *, device, population_path, population_audit):
    output = Path(output)
    if output.exists():
        raise ValueError('Diagnostic output must be a fresh directory')
    output.mkdir(parents=True)
    started = time.monotonic()
    deadline = started + config['max_wall_seconds']
    cube = Cube.build(7)
    all_graphs, source = read_population(population_path, cube, audit_path=population_audit)
    if not source['orbit_dedup']:
        raise ValueError('Orbit-audited source required')
    reference, heldout, split = split_corpus(all_graphs, config['heldout_orbits'], config['split_seed'])
    split.update(source_sha256=source['sha256'], training_orbits=len(reference), heldout_orbits=len(heldout),
                 generated_304_plus_excluded_from_training=True,
                 scope='Heldout from this run, not a historically untouched benchmark; the prior pilot used all 180.')
    write_json(output / 'split.json', split)
    torch.manual_seed(config['seed'])
    trainer = Trainer(Generator(ModelConfig(**config['model'])), device=device, seed=config['seed'])
    initial_weight_sha256 = sha256(b''.join(bytes(v.detach().cpu().contiguous().view(torch.uint8).flatten().tolist())
                                           for v in trainer.model.state_dict().values())).hexdigest()
    archive = []
    best = reference[0]
    best_generated = None
    report = {'schema': 'erdos86.diagnostic.run.v1', 'config': config, 'provenance': provenance(),
              'population_source': source, 'split': split, 'initial_weight_sha256': initial_weight_sha256,
              'parameters': trainer.model.parameter_count(), 'best_source': 'initial_reference',
              'stopping_reason': 'completed', 'training_seconds': 0., 'generation_seconds': 0.,
              'repair_seconds': 0., 'baseline_seconds': 0., 'evaluation_seconds': 0.,
              'sampled_graphs': 0, 'evaluation_graphs': 0, 'losses': [], 'rounds': [], 'evaluations': [],
              'pool_history': [], 'checkpoints': [],
              'comparison_scope': 'Arms share configuration except sampling weights; 3 paired seeds. Classical baselines match repair kicks, NOT total compute.',
              'novelty_scope': 'Exact labeled hashes are recorded; no new-orbit claim without a separate symmetry audit.'}
    write_json(output / 'config.json', config)
    if torch.device(device).type == 'cuda':
        torch.cuda.reset_peak_memory_stats(device)
    local_config = config['local_search']
    fixed = {}

    def snapshot(stage):
        name = f'checkpoints/{trainer.steps:06d}-{stage}.pt'
        trainer.save(output / name, reference + archive,
                     {'stage': stage, 'reference_count': len(reference), 'split': split,
                      'arm': config['arm'], 'resume_scope': 'Saved for evaluation; diagnostic suite does not auto-resume.'})
        report['checkpoints'].append({'stage': stage, 'step': trainer.steps, 'path': name})
        write_json(output / 'report.json', report)

    def update_best(bits, origin, is_model):
        nonlocal best, best_generated
        validation = verify_edges(7, cube.decode(bits))
        if is_model and (best_generated is None or sum(bits) > sum(best_generated)):
            best_generated = bits.copy()
            write_json(output / 'best-model.json', {'n': 7, 'edges': cube.decode(bits),
                                                   'source': origin, 'validation': validation})
        if sum(bits) > sum(best):
            best = bits.copy()
            report['best_source'] = origin
        if sum(bits) >= 305:
            write_json(output / 'target-305.json', {'n': 7, 'edges': cube.decode(bits),
                                                   'source': origin, 'validation': validation})
            raise TargetFound(origin)

    def improve(bits, seed):
        stats = {}
        result = local_search(cube, bits, seed=seed, stats=stats, **local_config)
        return result, stats

    def evaluate(stage, stream):
        t0 = time.monotonic()
        item = {'stage': stage, 'step': trainer.steps, 'prefixes': {}}
        for label, (data, meta) in fixed.items():
            item['prefixes'][label] = {**evaluate_prefixes(trainer.model, data, config['batch_size'], deadline),
                                      'cases': meta}
        # Same sampling seed at every stage, separate from training and online generation.
        scores, repaired_scores = [], []
        for offset in range(0, config['eval_samples'], config['sample_batch_size']):
            size = min(config['sample_batch_size'], config['eval_samples'] - offset)
            graphs, _ = sample(trainer.model, size, seed=config['eval_seed'] + config['seed'] + offset, deadline=deadline)
            for j, bits in enumerate(graphs):
                check_deadline(deadline)
                repaired, stats = improve(bits, config['eval_seed'] + config['seed'] + offset + j + 17)
                raw_v = verify_edges(7, cube.decode(bits))
                repaired_v = verify_edges(7, cube.decode(repaired))
                scores.append(sum(bits)); repaired_scores.append(sum(repaired))
                stream.write(json.dumps({'stage': stage, 'index': offset + j, 'raw_edges': cube.decode(bits),
                                         'edges': cube.decode(repaired), 'raw_validation': raw_v,
                                         'repaired_validation': repaired_v, 'repair_stats': stats,
                                         'raw_sha256': sha256(bytes(bits)).hexdigest(),
                                         'repaired_sha256': sha256(bytes(repaired)).hexdigest()}) + '\n')
                report['evaluation_graphs'] += 1
                update_best(repaired, 'evaluation_model_sample', True)
        item.update(raw=score_summary(scores), repaired=score_summary(repaired_scores))
        report['evaluations'].append(item)
        report['evaluation_seconds'] += time.monotonic() - t0
        print(json.dumps({'phase': 'evaluation', **item}), flush=True)
        write_json(output / 'report.json', report)

    def train(steps):
        population = reference + archive
        weights = sampling_weights(len(reference), len(archive), config['arm'], config['reference_fraction'])
        report['pool_history'].append({'step': trainer.steps, 'reference_count': len(reference),
                                       'exploration_count': len(archive), 'reference_probability': sum(weights[:len(reference)]),
                                       'exploration_scores': score_summary([sum(x) for x in archive])})
        for _ in range(steps):
            check_deadline(deadline)
            synchronize(device)
            t0 = time.monotonic()
            stats = trainer.train_step(population, config['batch_size'], sample_weights=weights)
            synchronize(device)
            report['training_seconds'] += time.monotonic() - t0
            report['losses'].append({'step': trainer.steps, **stats})
            if trainer.steps % 100 == 0:
                window = report['losses'][-100:]
                eligible = sum(x['trainable_fraction'] for x in window)
                print(json.dumps({'phase': 'train', 'step': trainer.steps,
                                  'mean_loss_100': statistics.mean(x['loss'] for x in window),
                                  'conditional_bce_100': sum(x['loss'] for x in window) / eligible if eligible else None,
                                  'reference_probability': sum(weights[:len(reference)])}), flush=True)

    try:
        check_deadline(deadline)
        fixed = {label: fixed_prefixes(cube, population, config['eval_prefixes'], config['eval_seed'] + i)
                 for i, (label, population) in enumerate([('train', reference), ('heldout', heldout)])}
        write_json(output / 'fixed-evaluation.json', {k: v[1] for k, v in fixed.items()})
        with gzip.open(output / 'candidates.jsonl.gz', 'wt') as candidates, gzip.open(output / 'evaluation-candidates.jsonl.gz', 'wt') as eval_stream:
            snapshot('untrained')
            evaluate('untrained', eval_stream)
            train(config['pretrain_steps'])
            snapshot('pretrained')
            evaluate('pretrained', eval_stream)
            for round_id in range(config['rounds']):
                current = {'round': round_id, 'raw': [], 'repaired': [], 'seed_baseline': [], 'empty_baseline': []}
                report['rounds'].append(current)
                new_graphs = []
                for offset in range(0, config['samples_per_round'], config['sample_batch_size']):
                    check_deadline(deadline)
                    size = min(config['sample_batch_size'], config['samples_per_round'] - offset)
                    synchronize(device); t0 = time.monotonic()
                    sample_seed = config['seed'] + 100000 * (round_id + 1) + offset
                    graphs, sampling = sample(trainer.model, size, seed=sample_seed, deadline=deadline)
                    synchronize(device); report['generation_seconds'] += time.monotonic() - t0
                    for j, bits in enumerate(graphs):
                        check_deadline(deadline)
                        search_seed = sample_seed + j + 17
                        t0 = time.monotonic()
                        repaired, stats = improve(bits, search_seed)
                        report['repair_seconds'] += time.monotonic() - t0
                        t0 = time.monotonic()
                        seed_baseline, seed_stats = improve(reference[(offset + j) % len(reference)], search_seed)
                        empty_baseline, empty_stats = improve([0] * 448, search_seed)
                        report['baseline_seconds'] += time.monotonic() - t0
                        row = {'round': round_id, 'index': offset + j, 'sample_seed': sample_seed, 'search_seed': search_seed,
                               'forced_zero_decisions': sampling['forced_zero_decisions'][j],
                               'raw_edges': cube.decode(bits), 'edges': cube.decode(repaired),
                               'seed_baseline_edges': cube.decode(seed_baseline), 'empty_baseline_edges': cube.decode(empty_baseline),
                               'repair_stats': stats, 'seed_baseline_stats': seed_stats, 'empty_baseline_stats': empty_stats}
                        for label, graph in [('raw', bits), ('repaired', repaired), ('seed_baseline', seed_baseline), ('empty_baseline', empty_baseline)]:
                            row[label + '_validation'] = verify_edges(7, cube.decode(graph))
                            row[label + '_sha256'] = sha256(bytes(graph)).hexdigest()
                            current[label].append(sum(graph))
                        candidates.write(json.dumps(row) + '\n')
                        new_graphs.append(repaired)
                        report['sampled_graphs'] += 1
                        update_best(repaired, 'repaired_model_sample', True)
                        update_best(seed_baseline, 'known_seed_baseline', False)
                        update_best(empty_baseline, 'empty_graph_baseline', False)
                    print(json.dumps({'phase': 'sample_repair', 'round': round_id, 'samples': report['sampled_graphs'],
                                      'best_model': sum(best_generated) if best_generated is not None else None,
                                      'best_overall': sum(best)}), flush=True)
                archive = update_exploration(archive, new_graphs, config['elite_size'] - len(reference))
                current['summary'] = {key: score_summary(current[key]) for key in ['raw', 'repaired', 'seed_baseline', 'empty_baseline']}
                current['generated_304_plus_excluded'] = sum(sum(x) >= 304 for x in new_graphs)
                train(config['round_train_steps'])
                stage = f'round-{round_id + 1}'
                snapshot(stage)
                evaluate(stage, eval_stream)
    except TargetFound:
        report['stopping_reason'] = 'verified_target_candidate'
    except BudgetExpired:
        report['stopping_reason'] = 'wall_budget'
    except (Exception, KeyboardInterrupt) as exc:
        report['stopping_reason'] = 'interrupted' if isinstance(exc, KeyboardInterrupt) else 'error'
        report['error'] = f'{type(exc).__name__}: {exc}'
        raise
    finally:
        report['training_steps'] = trainer.steps
        report['best_validation'] = verify_edges(7, cube.decode(best))
        report['best_model_validation'] = verify_edges(7, cube.decode(best_generated)) if best_generated is not None else None
        report['wall_seconds'] = time.monotonic() - started
        report['peak_cuda_allocated_bytes'] = torch.cuda.max_memory_allocated(device) if torch.device(device).type == 'cuda' else None
        trainer.save(output / 'checkpoint.pt', reference + archive, {'reference_count': len(reference), 'split': split, 'stopping_reason': report['stopping_reason']})
        write_json(output / 'best.json', {'n': 7, 'edges': cube.decode(best), 'source': report['best_source'], 'validation': report['best_validation']})
        write_json(output / 'report.json', report)
    return report
