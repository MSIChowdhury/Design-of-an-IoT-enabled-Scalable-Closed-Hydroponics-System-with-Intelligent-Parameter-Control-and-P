import importlib

import numpy as np

ident = importlib.import_module("scripts.76_ec_identification")


def synthetic(n=3000, a=4.0, bw=-6.0, c=-0.3, d=2, seed=0):
    rng = np.random.default_rng(seed)
    N = (rng.random(n) < 0.2) * rng.integers(1, 6, n)
    W = (rng.random(n) < 0.05).astype(float)
    x = np.empty(n)
    x[: d + 1] = 1100.0
    for k in range(d, n - 1):
        x[k + 1] = x[k] + a * N[k - d] + bw * W[k - d] + c + rng.normal(0, 0.5)
    clean = np.ones(n, dtype=bool)
    clean[500:520] = False
    return {"x": x, "N": N.astype(float), "W": W, "clean": clean}


def test_ols_recovers_known_dose_gain_and_respects_unclean_bins():
    b = synthetic()
    X, y = ident.pairs(b, 2)
    beta, se, n = ident.ols_hc1(X, y)
    np.testing.assert_allclose(beta, [4.0, -6.0, -0.3], atol=0.15)
    assert n < len(b["x"]) - 3          # gap bins excluded
    assert all(se > 0)


def test_simulation_beats_hold_when_model_is_right():
    b = synthetic(seed=1)
    ks = ident.starts(b, 2, 30)
    sim = ident.simulate_errors(b, 2, 30, 4.0, -6.0, -0.3, ks)
    hold = np.array([b["x"][k] - b["x"][k + 30] for k in ks])
    assert ident.rmse(sim) < 0.5 * ident.rmse(hold)
    assert not any(500 - 30 <= k <= 520 for k in ks)
