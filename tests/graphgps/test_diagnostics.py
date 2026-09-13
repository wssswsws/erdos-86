import json
from pathlib import Path
import random

import pytest
import torch

from erdos86_gps.cli import read_population
from erdos86_gps.cube import Cube
from erdos86_gps.diagnostics import sampling_weights, split_corpus, update_exploration
from erdos86_gps.engine import Trainer
from erdos86_gps.evaluation import evaluate_prefixes, fixed_prefixes
from erdos86_gps.model import Generator, ModelConfig
from erdos86_gps.search import local_search, repair
from erdos86_gps.verify import verify_edges

ROOT = Path(__file__).resolve().parents[2]


def tiny():
    return Generator(ModelConfig(n=3, width=16, layers=2, heads=4))


def test_reference_weight_is_preserved_as_archive_grows():
    for count in [1, 10, 368]:
        weights = sampling_weights(144, count, 'reference80', .8)
        assert sum(weights) == pytest.approx(1)
        assert sum(weights[:144]) == pytest.approx(.8)
    weights = sampling_weights(144, 368, 'legacy_topk', .8)
    assert sum(weights[:144]) == pytest.approx(144 / 512)
    assert sum(sampling_weights(144, 0, 'reference80', .8)) == pytest.approx(1)


def test_weighted_batch_reaches_expected_distribution_and_resumes(tmp_path):
    trainer = Trainer(tiny(), seed=42)
    # batch does no constraint checking: constant targets make sampled group observable.
    *_, labels = trainer.batch([[0] * 12, [1] * 12], 4096, sample_weights=[.8, .2])
    assert .18 < float(labels.mean()) < .22
    with pytest.raises(ValueError, match='weights'):
        trainer.batch([[0] * 12], 1, sample_weights=[0])
    cube = Cube.build(3)
    population = [repair(cube, [0] * 12, random.Random(i)) for i in range(3)]
    weights = [.8, .1, .1]
    trainer.train_step(population, 4, sample_weights=weights)
    trainer.save(tmp_path / 'weights.pt', population)
    expected = trainer.train_step(population, 4, sample_weights=weights)
    restored, rows, _ = Trainer.load(tmp_path / 'weights.pt')
    assert restored.train_step(rows, 4, sample_weights=weights) == expected


def test_fixed_evaluation_does_not_change_training_rng_or_weights():
    cube = Cube.build(3)
    population = [repair(cube, [0] * 12, random.Random(i)) for i in range(3)]
    trainer = Trainer(tiny(), seed=11)
    rng_before = trainer.rng.get_state().clone()
    augment_before = trainer.augment_rng.getstate()
    global_before = torch.random.get_rng_state().clone()
    weights_before = {k: v.clone() for k, v in trainer.model.state_dict().items()}
    data, meta = fixed_prefixes(cube, population, 32, 86)
    again, meta_again = fixed_prefixes(cube, population, 32, 86)
    assert meta == meta_again
    assert all(torch.equal(data[k], again[k]) for k in data)
    result = evaluate_prefixes(trainer.model, data, 8)
    assert result == evaluate_prefixes(trainer.model, again, 8)
    assert result['examples'] == 32 and result['conditional_bce_nonforced'] > 0
    assert torch.equal(rng_before, trainer.rng.get_state())
    assert augment_before == trainer.augment_rng.getstate()
    assert torch.equal(global_before, torch.random.get_rng_state())
    assert trainer.model.training and trainer.steps == 0
    assert all(torch.equal(v, trainer.model.state_dict()[k]) for k, v in weights_before.items())


def test_holdout_is_split_before_augmentation_and_cannot_reenter_archive():
    cube = Cube.build(7)
    folder = ROOT / 'references/corpora/q7-304-orbits'
    population, _ = read_population(folder / 'representatives.jsonl', cube, audit_path=folder / 'audit.json')
    train, heldout, split = split_corpus(population, 36, 860086)
    assert len(train) == 144 and len(heldout) == 36
    assert set(split['training_indices']).isdisjoint(split['heldout_indices'])
    assert split == split_corpus(population, 36, 860086)[2]
    transformed = cube.relabel(heldout[0], list(reversed(range(7))), 51)
    lower = transformed.copy()
    lower[lower.index(1)] = 0
    assert update_exploration([], [transformed, train[0], lower], 368) == [lower]


def test_downhill_search_preserves_best_valid_certificate():
    cube = Cube.build(7)
    data = json.loads((ROOT / 'references/baselines/86-selected_edges_best.json').read_text())
    stats = {}
    result = local_search(cube, cube.encode(data['edges']), seed=91, kicks=32,
                          kick_min=8, kick_max=24, kick_mode='mixed',
                          temperature_start=100, temperature_end=100, stats=stats)
    assert stats['accepted_downhill'] > 0
    assert sum(result) >= 304
    verify_edges(7, cube.decode(result))
