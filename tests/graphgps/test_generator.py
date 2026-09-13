import json
from pathlib import Path
import random

import pytest
import torch

from erdos86_gps.cube import Cube
from erdos86_gps.engine import Trainer, sample
from erdos86_gps.model import Generator, ModelConfig, allowed_additions, prefix_states
from erdos86_gps.search import local_search, repair
from erdos86_gps.verify import verify_edges
from erdos86_gps.cli import estimate, load_config, read_population, run_loop

ROOT = Path(__file__).resolve().parents[2]
torch.set_num_threads(2)


def tiny_model(n=3):
    return Generator(ModelConfig(n=n, width=16, layers=2, heads=4))


def test_q7_constraint_graph_and_published_certificate():
    cube = Cube.build(7)
    assert (len(cube.edges), len(cube.faces)) == (448, 672)
    assert all(len(face) == len(set(face)) == 4 for face in cube.faces)
    assert all(len(faces) == 6 for faces in cube.edge_faces)
    for e, faces in enumerate(cube.edge_faces):
        assert all(e in cube.faces[f] for f in faces)
    data = json.loads((ROOT / 'references/baselines/86-selected_edges_best.json').read_text())
    result = verify_edges(7, data['edges'])
    assert result['edges'] == 304 and result['square_histogram'] == {1: 36, 2: 120, 3: 516}
    encoded = cube.encode(data['edges'])
    transformed = cube.relabel(encoded, [6, 4, 2, 0, 5, 3, 1], 71)
    assert verify_edges(7, cube.decode(transformed))['degree_histogram'] == result['degree_histogram']


@pytest.mark.parametrize('edges', [
    [[0, 1], [0, 1]], [[0, 0]], [[0, 3]], [[0, 8]], [[False, 1]],
    [[0, 1], [1, 3], [3, 2], [2, 0]],
])
def test_independent_verifier_rejects_bad_objects(edges):
    with pytest.raises(ValueError):
        verify_edges(3, edges)


def test_no_future_value_leakage_into_local_or_global_branch():
    model = tiny_model().eval()
    count = model.coordinates.shape[0]
    ranks = torch.arange(count).repeat(2, 1)
    steps = torch.tensor([3, 8])
    targets = torch.randint(2, (2, count))
    changed = torch.where(ranks >= steps[:, None], 1 - targets, targets)
    prefix_a = prefix_states(targets, ranks, steps)
    prefix_b = prefix_states(changed, ranks, steps)
    assert torch.equal(prefix_a, prefix_b)
    with torch.no_grad():
        assert torch.equal(model(prefix_a, ranks, steps), model(prefix_b, ranks, steps))
    assert torch.all(prefix_a[ranks >= steps[:, None]] == 0)


def test_exact_mask_blocks_the_fourth_edge_but_allows_empty_faces():
    cube = Cube.build(2)
    model = tiny_model(n=2)
    state = torch.zeros(1, 4, dtype=torch.long)
    state[0, list(cube.faces[0][:3])] = 2
    assert not allowed_additions(state, model.faces, model.edge_faces)[0, cube.faces[0][3]]
    assert allowed_additions(torch.zeros_like(state), model.faces, model.edge_faces).all()
    with torch.no_grad():
        for parameter in model.parameters():
            parameter.zero_()
        model.output[-1].bias.fill_(-100)
    bits, _ = sample(model, 2, seed=11)
    assert all(sum(row) == 0 for row in bits)


def test_sampling_and_local_repair_pass_independent_verifier():
    cube = Cube.build(3)
    generated, info = sample(tiny_model(), 4, seed=19)
    assert info['forward_calls'] == 12
    for index, bits in enumerate(generated):
        verify_edges(3, cube.decode(bits))
        repaired = local_search(cube, bits, seed=index, kicks=3)
        assert sum(repaired) >= sum(bits)
        verify_edges(3, cube.decode(repaired))
    verify_edges(3, cube.decode(repair(cube, [1] * 12, random.Random(4))))


def test_checkpoint_resumes_exact_next_optimizer_step(tmp_path):
    torch.manual_seed(5)
    cube = Cube.build(3)
    graphs = [repair(cube, [0] * 12, random.Random(i)) for i in range(4)]
    trainer = Trainer(tiny_model(), seed=87)
    trainer.train_step(graphs, 4)
    trainer.save(tmp_path / 'state.pt', graphs)
    expected = trainer.train_step(graphs, 4)
    restored, population, _ = Trainer.load(tmp_path / 'state.pt')
    actual = restored.train_step(population, 4)
    assert expected == actual
    assert trainer.steps == restored.steps == 2
    for name, value in trainer.model.state_dict().items():
        assert torch.equal(value, restored.model.state_dict()[name])


def test_q7_full_pilot_architecture_backward_reaches_both_branches():
    config = load_config(ROOT / 'configs/graphgps/pilot.json')
    cube = Cube.build(7)
    data = json.loads((ROOT / 'references/baselines/86-selected_edges_best.json').read_text())
    model = Generator(ModelConfig(**config['model']))
    targets = torch.tensor([cube.encode(data['edges'])] * 2)
    ranks = torch.arange(448).repeat(2, 1)
    steps = torch.zeros(2, dtype=torch.long)  # An empty prefix cannot force zero.
    logits = model(prefix_states(targets, ranks, steps), ranks, steps)[:, 0]
    loss = torch.nn.functional.binary_cross_entropy_with_logits(logits, targets[:, 0].float())
    loss.backward()
    assert 0 < float(loss.detach()) < 10
    for part in ['factor_update', 'variable_update', 'qkv']:
        assert any(p.grad is not None and torch.any(p.grad != 0) for name, p in model.named_parameters() if part in name)


def test_gpu_budget_arithmetic_and_no_cpu_extrapolation():
    config = load_config(ROOT / 'configs/graphgps/pilot.json')
    result = estimate(config)
    assert result['training_steps'] == 11000
    assert result['generated_graphs'] == 12288
    assert result['sample_batches'] == 384
    assert result['full_graph_forward_calls'] == 172032
    with pytest.raises(ValueError, match='CPU calibration'):
        estimate(config, calibration={'device': 'cpu'})


def test_population_import_validates_and_only_claims_exact_dedup(tmp_path):
    path = tmp_path / 'population.jsonl'
    row = {'n': 3, 'edges': [[0, 1], [0, 2]]}
    path.write_text(json.dumps(row) + '\n' + json.dumps(row) + '\n')
    population, meta = read_population(path, Cube.build(3))
    assert len(population) == 1 and meta['rows'] == 2 and meta['orbit_dedup'] is False
    path.write_text(json.dumps({'n': 3, 'edges': [[0, 1], [1, 3], [3, 2], [2, 0]]}) + '\n')
    with pytest.raises(ValueError, match='C4'):
        read_population(path, Cube.build(3))


def test_expired_budget_checkpoints_without_training(tmp_path):
    config = load_config(ROOT / 'configs/graphgps/smoke.json')
    config.update(max_wall_seconds=1e-9, initial_population=1)
    report = run_loop(config, tmp_path / 'run', device='cpu')
    assert report['stopping_reason'] == 'wall_budget'
    assert report['training_steps_this_run'] == 0
    assert (tmp_path / 'run' / 'checkpoint.pt').is_file()


def test_audited_corpus_is_bound_to_exact_data_and_reaches_run(tmp_path):
    from hashlib import sha256
    source = ROOT / 'references/corpora/q7-304-orbits'
    path = tmp_path / 'representatives.jsonl'
    path.write_bytes((source / path.name).read_bytes())
    audit_path = tmp_path / 'audit.json'
    audit_path.write_bytes((source / audit_path.name).read_bytes())
    population, meta = read_population(path, Cube.build(7), audit_path=audit_path)
    assert len(population) == 180 and {sum(bits) for bits in population} == {304}
    assert meta['orbit_dedup'] is True and meta['held_out_evaluation'] is False
    # Even whitespace changes must fail the provenance binding.
    path.write_bytes(path.read_bytes() + b'\n')
    with pytest.raises(ValueError, match='audit mismatch'):
        read_population(path, Cube.build(7), audit_path=audit_path)
    path.write_bytes((source / path.name).read_bytes())
    audit = json.loads(audit_path.read_text())
    audit['canonical_minimality_verified'] = False
    audit_path.write_text(json.dumps(audit))
    with pytest.raises(ValueError, match='incomplete orbit'):
        read_population(path, Cube.build(7), audit_path=audit_path)
    audit_path.write_bytes((source / audit_path.name).read_bytes())
    config = load_config(ROOT / 'configs/graphgps/smoke.json')
    config.update(max_wall_seconds=1e-9)
    report = run_loop(config, tmp_path / 'run', device='cpu',
                      population_path=path, population_audit=audit_path)
    assert report['initial_population'] == 180 and report['initial_best'] == 304
    assert report['population_source']['sha256'] == sha256(path.read_bytes()).hexdigest()
    assert report['population_source']['orbit_dedup'] is True
    assert report['training_steps_this_run'] == 0
