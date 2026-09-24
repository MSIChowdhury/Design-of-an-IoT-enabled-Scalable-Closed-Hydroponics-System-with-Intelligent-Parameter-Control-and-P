import numpy as np
import pytest

from aasvr.reanalysis import Timing, authorize, hold_estimate, score_actions


def test_reference_opportunities_do_not_depend_on_estimate():
    t = np.arange(0, 1000, 10.)
    background = np.full(len(t), 7.)
    kwargs = dict(timing=Timing(persistence=20, cooldown=100), deadline=50, start=0, stop=900)
    denied = score_actions(t, background, background, np.zeros(len(t), bool),
                           np.zeros(len(t), int), 5.8, 6.5, **kwargs)
    actions = authorize(t, background, np.ones(len(t), bool), 5.8, 6.5, kwargs['timing'])
    served = score_actions(t, background, background, np.ones(len(t), bool), actions,
                           5.8, 6.5, **kwargs)
    assert denied['opportunities'] == served['opportunities'] == 9
    assert denied['matched'] == 0
    assert served['matched'] == 9


def test_wrong_direction_and_faulty_evidence_are_distinct():
    t = np.arange(10.)
    background = np.full(10, 7.)
    corrupted = np.full(10, 7.1)
    actions = np.zeros(10, int)
    actions[2], actions[3] = -1, 1
    result = score_actions(t, background, corrupted, np.ones(10, bool), actions, 5.8, 6.5,
                           timing=Timing(persistence=0), deadline=1, stop=8)
    assert result['fault_evidence'] == 2
    assert result['wrong_direction'] == 1
    assert result['unnecessary'] == 0


def test_action_cannot_match_two_slots_or_cross_episode():
    t = np.arange(20.)
    x = np.full(20, 7.)
    actions = np.zeros(20, int)
    actions[6] = -1
    result = score_actions(t, x, x, np.ones(20, bool), actions, 5.8, 6.5,
                           timing=Timing(persistence=0, cooldown=5), deadline=8, stop=10)
    assert result['opportunities'] == 3
    assert result['matched'] == 1
    x[2:5] = 6.1
    actions[:] = 0
    actions[5] = -1
    result = score_actions(t, x, x, np.ones(20, bool), actions, 5.8, 6.5,
                           timing=Timing(persistence=0, cooldown=100), deadline=8, stop=10)
    assert result['matched'] == 0


def test_time_gap_resets_persistence_and_expires_estimate():
    t = np.array([0., 16., 1000., 1016., 1032.])
    x = np.full(5, 7.)
    timing = Timing(persistence=32, cooldown=600, max_gap=120)
    actions = authorize(t, x, np.ones(5, bool), 5.8, 6.5, timing)
    assert np.flatnonzero(actions).tolist() == [4]
    estimate, age = hold_estimate(t, x, [True, False, False, False, True])
    assert np.isnan(estimate[2]) and np.isinf(age[2])
    assert age[1] == 16 and age[4] == 0


def test_zero_opportunities_and_followup_are_explicit():
    t = np.arange(20.)
    x = np.full(20, 6.1)
    result = score_actions(t, x, x, np.ones(20, bool), np.zeros(20, int), 5.8, 6.5,
                           deadline=5, stop=14)
    assert result['zero_opportunity_trials'] == 1
    assert result['opportunities'] == 0
    with pytest.raises(ValueError, match='follow-up'):
        score_actions(t, x, x, np.ones(20, bool), np.zeros(20, int), 5.8, 6.5,
                      deadline=5, stop=19)


def test_stuck_labels_include_equal_values():
    t = np.arange(20.)
    x = np.full(20, 6.1)
    fault = np.zeros(20, bool)
    fault[2:6] = True
    result = score_actions(t, x, x, np.ones(20, bool), np.zeros(20, int), 5.8, 6.5,
                           deadline=5, stop=14, fault_labels=fault)
    assert result['fault_samples'] == 4


def test_blocked_windows_and_fault_metadata():
    import runpy
    import pandas as pd
    from pathlib import Path
    helpers = runpy.run_path(str(Path(__file__).parents[1] / 'scripts/38_replay_reanalysis.py'))
    frame = pd.DataFrame({'timestamp': pd.date_range('2024-01-01', periods=3000, freq='16s', tz='UTC')})
    cfg = dict(split_fractions=[.4, .7], window_samples=100, windows_per_split=3,
               max_gap_seconds=120)
    grid, boundaries = helpers['windows'](frame, cfg)
    for k, split in enumerate(('development', 'validation', 'evaluation')):
        for w in grid[grid.split == split].itertuples():
            assert frame.timestamp.iloc[w.start].timestamp() >= boundaries[k]
            assert frame.timestamp.iloc[w.end-1].timestamp() < boundaries[k+1]
    ordered = grid.sort_values('start')
    assert np.all(ordered.start.to_numpy()[1:] >= ordered.end.to_numpy()[:-1])
    x = np.full(100, 6.)
    background, corrupted, labels = helpers['scenario'](x, 'stuck', .5, 20, 10)
    assert labels.sum() == 10 and np.array_equal(background, corrupted)
    background, corrupted, labels = helpers['scenario'](x, 'legitimate_positive', .5, 20, 10)
    assert not labels.any() and np.array_equal(background, corrupted)
    assert background[-1] == 6.5


def test_legacy_reliability_failure_has_no_passive_recovery():
    from dataclasses import replace
    from pathlib import Path
    from aasvr.config import load_aasvr_config
    from aasvr.core import AASVR
    cfg = load_aasvr_config(Path(__file__).parents[1] / 'configs/methods/aasvr.yaml')
    sensor = next(s for s in cfg.sensors if s.name == 'pH')
    model = AASVR(replace(cfg, sensors=(sensor,)))
    decisions = [model.update({'timestamp': i*16, 'pH': 6.7})[0] for i in range(100)]
    assert sum(d.actuation_authorized for d in decisions) == 1
    assert decisions[-1].response_reliability == .5
    runtime = model._sensors['pH']
    assert runtime.response_observations == 1
