import numpy as np
import pandas as pd

from aasvr.core import SensorConfig
from aasvr.livegate import fit, gate

SENSORS = [SensorConfig("pH", 0.0, 14.0, 5.8, 6.5, 1.0),
           SensorConfig("EC", 0.0, 5000.0, 1000.0, 1500.0, 100.0)]


def frame(n=6000, seed=0):
    rng = np.random.default_rng(seed)
    t = pd.Timestamp("2024-03-01T00:00:00Z") + pd.to_timedelta(np.arange(n) * 16.0, unit="s")
    walk = np.cumsum(rng.normal(0, .003, n))
    return pd.DataFrame({"timestamp": t, "pH": np.round(6.2 + walk + rng.normal(0, .02, n), 2),
                         "EC": np.round(1300 + 20 * walk + rng.normal(0, 4, n))})


def run(models, x, data, epsilon=.01):
    times = np.arange(len(x)) * 16.0
    hours = (times / 3600) % 24
    context = data[list(models["pH"].others)].to_numpy(dtype=float)[:len(x)]
    return gate(models["pH"], x, times, hours, context, epsilon=epsilon)


def test_conformal_rejection_rate_is_near_epsilon_on_clean_data():
    data = frame()
    models = fit(data, SENSORS)
    fresh = frame(seed=1)
    accepted = run(models, fresh.pH.to_numpy(float), fresh, epsilon=.05)
    assert 1 - accepted.mean() < .12


def test_spike_rejected_and_real_step_reanchored():
    data = frame()
    models = fit(data, SENSORS)
    x = data.pH.to_numpy(float)[:300].copy()
    x[100] = 9.0
    x[200:] += .6
    accepted = run(models, x, data)
    assert not accepted[100]
    assert accepted[200 + 8:].mean() > .8


def test_stuck_reading_is_rejected_once_run_exceeds_live_behavior():
    data = frame()
    models = fit(data, SENSORS)
    x = data.pH.to_numpy(float)[:400].copy()
    x[100:400] = x[99]
    accepted = run(models, x, data)
    assert accepted[:100].mean() > .8
    assert not accepted[200:400].any()
