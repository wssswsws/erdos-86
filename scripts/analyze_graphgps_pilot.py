#!/usr/bin/env python3
"""Audit saved repaired graphs and summarize one completed GraphGPS pilot."""
import argparse
from collections import Counter
import gzip
from hashlib import sha256
import json
from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from erdos86_gps.cube import Cube
from erdos86_gps.verify import verify_edges


def describe(values):
    return {'n': len(values), 'min': min(values), 'mean': statistics.mean(values),
            'median': statistics.median(values), 'max': max(values),
            'histogram': dict(sorted(Counter(values).items()))}


def loss_window(rows):
    return {'first_step': rows[0]['step'], 'last_step': rows[-1]['step'],
            'mean_loss': statistics.mean(r['loss'] for r in rows),
            'mean_trainable_fraction': statistics.mean(r['trainable_fraction'] for r in rows),
            'conditional_BCE_nonforced': sum(r['loss'] for r in rows) / sum(r['trainable_fraction'] for r in rows)}


def analyze(run, output):
    started = time.monotonic()
    output.mkdir(parents=True, exist_ok=True)
    report = json.loads((run / 'report.json').read_text())
    assert report['stopping_reason'] == 'completed'
    assert (run / 'exit-code.txt').read_text().strip() == '0'
    config = report['config']
    assert report['training_steps_this_run'] == config['pretrain_steps'] + config['rounds'] * config['round_train_steps']
    assert report['sampled_graphs'] == config['rounds'] * config['samples_per_round']
    for name, digest in report['provenance']['source_sha256'].items():
        assert sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    population_path = ROOT / report['population_source']['path']
    assert sha256(population_path.read_bytes()).hexdigest() == report['population_source']['sha256']
    audit_path = ROOT / report['population_source']['audit_path']
    assert sha256(audit_path.read_bytes()).hexdigest() == report['population_source']['audit_sha256']
    cube = Cube.build(7)
    initial = {bytes(cube.encode(json.loads(line)['edges'])) for line in population_path.read_text().splitlines()}
    population = set(initial)
    best = json.loads((run / 'best.json').read_text())
    best_check = verify_edges(7, best['edges'])
    assert best_check == report['best_validation'] or json.dumps(best_check, sort_keys=True) == json.dumps(report['best_validation'], sort_keys=True)
    rows_by_round = [[] for _ in range(config['rounds'])]
    seen_pairs, all_unique = set(), set()
    best_model = None
    hashes = {}
    for path in sorted(run.iterdir()):
        if path.is_file() and path.suffix != '.pt':
            hashes[path.name] = sha256(path.read_bytes()).hexdigest()
    with gzip.open(run / 'candidates.jsonl.gz', 'rt') as stream:
        for line in stream:
            row = json.loads(line)
            key = (row['round'], row['index'])
            assert key not in seen_pairs
            seen_pairs.add(key)
            validation = verify_edges(7, row['edges'])
            # JSON round-trip normalizes integer histogram keys to strings.
            assert json.loads(json.dumps(validation)) == row['repaired_validation']
            bits = bytes(cube.encode(row['edges']))
            if best_model is None or validation['edges'] > best_model['validation']['edges']:
                best_model = {'n': 7, 'edges': row['edges'], 'validation': validation,
                              'round': row['round'] + 1, 'index': row['index'], 'source': 'repaired_model_sample'}
            all_unique.add(bits)
            rows_by_round[row['round']].append((row, bits))
    rounds = []
    for i, rows in enumerate(rows_by_round):
        rows.sort(key=lambda pair: pair[0]['index'])
        assert [r['index'] for r, _ in rows] == list(range(config['samples_per_round']))
        raw = [r['raw_validation']['edges'] for r, _ in rows]
        repaired = [sum(bits) for _, bits in rows]
        baseline = [r['paired_baseline_edges'] for r, _ in rows]
        assert raw == report['rounds'][i]['raw_edge_counts']
        assert repaired == report['rounds'][i]['repaired_edge_counts']
        assert baseline == report['rounds'][i]['paired_baseline_edge_counts']
        population.update(bits for _, bits in rows)
        population = set(sorted(population, key=lambda bits: (-sum(bits), bits))[:config['elite_size']])
        assert len(population) == report['rounds'][i]['elite_exact_label_unique']
        rounds.append({'round': i + 1, 'raw': describe(raw), 'repaired': describe(repaired),
                       'paired_baseline': describe(baseline),
                       'repaired_unique_labels': len({bits for _, bits in rows}),
                       'beat_baseline_count': sum(a > b for a, b in zip(repaired, baseline)),
                       'tie_baseline_count': sum(a == b for a, b in zip(repaired, baseline)),
                       'elite_score_distribution': describe([sum(bits) for bits in population])})
    assert len(seen_pairs) == report['sampled_graphs']
    (output / 'best-model-repaired.json').write_text(json.dumps(best_model, indent=2) + '\n')
    losses = report['losses']
    assert [r['step'] for r in losses] == list(range(1, report['training_steps_this_run'] + 1))
    stages = []
    start = 0
    for length in [config['pretrain_steps']] + [config['round_train_steps']] * config['rounds']:
        rows = losses[start:start + length]
        stages.append({'all': loss_window(rows), 'first_500': loss_window(rows[:500]),
                       'last_500': loss_window(rows[-500:])})
        start += length
    result = {'schema': 'erdos86.pilot.audit.v1', 'run_directory': str(run.relative_to(ROOT)),
              'input_sha256': hashes, 'source_hashes_match': True, 'population_and_audit_hashes_match': True,
              'verified_saved_repaired_graphs': len(seen_pairs), 'repaired_unique_labels': len(all_unique),
              'best_validation': best_check, 'best_is_in_initial_population': bytes(cube.encode(best['edges'])) in initial,
              'best_source': report['best_source'], 'training_steps': len(losses), 'rounds': rounds,
              'best_model_repaired': {k: v for k, v in best_model.items() if k != 'edges'},
              'loss_stages': stages,
              'timing_seconds': {k: report[k] for k in ['wall_seconds', 'training_seconds', 'generation_seconds', 'repair_seconds', 'baseline_seconds']},
              'peak_cuda_allocated_bytes': report['peak_cuda_allocated_bytes'],
              'audit_seconds': time.monotonic() - started,
              'verification_scope': 'All saved repaired edge lists and final best reverified. Raw and paired-baseline edge lists were not saved; their counts are cross-checked against reports, not independently reverified.',
              'comparison_scope': report['comparison_scope'], 'held_out_evaluation': False}
    (output / 'analysis.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ['input_sha256', 'rounds', 'loss_stages']}, indent=2))
    print(json.dumps({'rounds': [{k: ({kk: vv for kk, vv in v.items() if kk != 'histogram'} if isinstance(v, dict) else v)
                                 for k, v in row.items()} for row in rounds], 'loss_stages': stages}, indent=2))
    return report, result


def plot(report, output):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    rows = report['losses']
    values = np.array([r['loss'] for r in rows])
    eligible = np.array([r['trainable_fraction'] for r in rows])
    smooth = np.convolve(values, np.ones(100), mode='valid') / 100
    conditional = smooth / (np.convolve(eligible, np.ones(100), mode='valid') / 100)
    fig, axs = plt.subplots(2, 1, figsize=(10, 7), constrained_layout=True)
    axs[0].plot(np.arange(100, len(rows) + 1), smooth, label='100-step mean loss', linewidth=1)
    axs[0].plot(np.arange(100, len(rows) + 1), conditional, label='BCE on non-forced decisions', linewidth=1, alpha=.85)
    for step in [5000, 7000, 9000]:
        axs[0].axvline(step, color='grey', linestyle=':', linewidth=1)
    axs[0].set(title='Training diagnostics (changing elite pools after dotted lines)', xlabel='Training step', ylabel='Binary cross-entropy')
    axs[0].legend()
    rounds = report['rounds']
    for shift, key, color, name in [(-.14, 'raw_edge_counts', '#5b7fa3', 'Raw model samples'),
                                   (.14, 'repaired_edge_counts', '#19846b', 'After local repair')]:
        data = [r[key] for r in rounds]
        box = axs[1].boxplot(data, positions=np.arange(1, 4) + shift, widths=.24, patch_artist=True,
                            showfliers=False, manage_ticks=False)
        for patch in box['boxes']: patch.set(facecolor=color, alpha=.7)
        axs[1].plot([], [], color=color, linewidth=8, label=name)
        axs[1].scatter(np.arange(1, 4) + shift, [max(d) for d in data], color=color, marker='*', s=90)
    axs[1].axhline(304, color='#b05340', linestyle='--', label='Initial pool / paired baseline: 304')
    axs[1].set(title='Candidate quality by round (stars: maxima; boxes: quartiles)', xlabel='Generation round', ylabel='Edges', xticks=[1, 2, 3])
    axs[1].legend(loc='upper center', ncol=3, fontsize=9)
    fig.savefig(output / 'diagnostics.png', dpi=170)
    plt.close(fig)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--plot', action='store_true')
    args = parser.parse_args()
    report, result = analyze(args.run.resolve(), args.output.resolve())
    if args.plot: plot(report, args.output.resolve())
