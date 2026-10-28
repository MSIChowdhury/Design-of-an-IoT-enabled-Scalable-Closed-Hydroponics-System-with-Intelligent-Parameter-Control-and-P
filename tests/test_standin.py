import json

import numpy as np
import pandas as pd

from aasvr.standin import fit_profile, generate, summary

RANGES = {"pH": (0.0, 14.0), "EC": (0.0, 5000.0)}


def source(n=3000, seed=1):
    rng = np.random.default_rng(seed)
    t = pd.Timestamp("2024-02-27T20:00:00Z") + pd.to_timedelta(np.arange(n) * 16.0, unit="s")
    ph = 6.2 + 0.05 * np.sin(np.arange(n) / 500) + rng.normal(0, .01, n)
    ph[::700] = 67101.0
    return pd.DataFrame({"timestamp": t, "pH": np.round(ph, 2),
                         "EC": np.round(1330 + rng.normal(0, 5, n))})


def test_profile_holds_aggregates_only():
    profile = fit_profile(source(), RANGES)
    channel = profile["channels"]["pH"]
    assert len(channel["hourly_median"]) == 24
    assert channel["out_of_range_rate"] > 0
    # No per-sample series is stored anywhere in the profile.
    assert len(json.dumps(profile)) < 5000


def test_generation_is_deterministic_and_matches_shape():
    frame = source()
    profile = fit_profile(frame, RANGES)
    a, b = generate(profile, seed=3), generate(profile, seed=3)
    pd.testing.assert_frame_equal(a, b)
    assert len(a) == len(frame)
    real, fake = summary(frame, RANGES).set_index("sensor"), summary(a, RANGES).set_index("sensor")
    assert abs(real.loc["pH", "median"] - fake.loc["pH", "median"]) < .05
    assert abs(real.loc["EC", "median"] - fake.loc["EC", "median"]) < 10
