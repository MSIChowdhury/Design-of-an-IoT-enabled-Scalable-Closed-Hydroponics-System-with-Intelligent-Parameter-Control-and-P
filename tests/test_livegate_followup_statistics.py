import importlib

import numpy as np
import pandas as pd

followup = importlib.import_module("scripts.70_livegate_followup")


def test_cluster_draws_keep_pairing_and_pool_opportunity_counts():
    # Day A contributes two trials; B one. Their coverages are .5 and 1,
    # while the correct pooled result is 4/5, not the unweighted mean .75.
    frame = pd.DataFrame({"source_day": ["A", "A", "B"], "matched": [0, 1, 3],
                          "opportunities": [1, 1, 3], "unnecessary": [1, 0, 1],
                          "wrong_direction": [0, 0, 0], "fault_evidence": [1, 0, 0],
                          "held_fault_evidence": [0, 0, 0]})
    stats = followup.cluster_statistics(frame, ["A", "B"])
    assert followup.ratios(stats.sum(axis=0))[0] == .8
    draws = np.array([[2, 0], [0, 2], [1, 1]])
    rates = followup.ratios(draws @ stats)
    np.testing.assert_allclose(rates[:, 0], [.5, 1, .8])
    same_method = followup.cluster_statistics(frame.copy(), ["A", "B"])
    np.testing.assert_allclose(rates - followup.ratios(draws @ same_method), 0)


def test_no_opportunities_produces_undefined_coverage_not_zero():
    totals = np.array([2., 0., 0., 1., 0., 0.])
    values = followup.ratios(totals)
    assert np.isnan(values[0])
    np.testing.assert_allclose(values[1:], [.5, 0, 0])
