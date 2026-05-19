from __future__ import annotations

from pathlib import Path

import pandas as pd

from aasvr.config import load_aasvr_config
from aasvr.exhaustive import (
    build_fault_grid,
    build_sweep_grid,
    config_from_sweep_row,
    load_exhaustive_protocol,
    protocol_summary,
)
from aasvr.fault_injection import FaultSpec, inject_fault
from aasvr.prepare import HYDRO_PRIMARY_SENSORS
from aasvr.toydata import make_toy_hydroponic_data


ROOT = Path(__file__).resolve().parents[1]


def test_extended_fault_types_are_injectable() -> None:
    frame = pd.DataFrame(
        {
            "timestamp": range(20),
            "pH": [6.0 + 0.01 * idx for idx in range(20)],
        }
    )
    for fault_type in [
        "stuck_plausible",
        "stuck_implausible",
        "saturation_high",
        "saturation_low",
        "nonlinear_drift",
        "gain_drift",
        "intermittent_burst",
    ]:
        faulted, labels = inject_fault(
            frame,
            FaultSpec(
                sensor="pH",
                fault_type=fault_type,
                start=5,
                duration=5,
                magnitude=1.0,
                physical_min=0.0,
                physical_max=14.0,
            ),
        )
        assert int(labels["fault"].sum()) == 5
        assert not faulted.loc[5:9, "pH"].equals(frame.loc[5:9, "pH"])


def test_mini_exhaustive_protocol_builds_expected_grid() -> None:
    frame = make_toy_hydroponic_data(240)
    base = load_aasvr_config(ROOT / "configs/methods/aasvr.yaml")
    sensors = tuple(sensor for sensor in base.sensors if sensor.name in HYDRO_PRIMARY_SENSORS)
    protocol, sweep = load_exhaustive_protocol(
        ROOT / "configs/experiments/exhaustive_hydro.yaml",
        profile="mini",
    )
    grid = build_fault_grid(frame, sensors, protocol)
    summary = protocol_summary(protocol)
    assert len(grid) == summary["planned_total_trials"]
    assert set(grid["split"]) == {"tune", "validation", "test"}
    assert {"physical_min", "physical_max", "pre_fault_samples", "post_fault_samples"}.issubset(
        grid.columns
    )
    sweep_grid = build_sweep_grid(sweep, profile="mini")
    assert len(sweep_grid) > 1
    config = config_from_sweep_row(base, sweep_grid.iloc[0])
    assert config.sensors[0].confirm_samples in {2, 3}
