from pathlib import Path

import pandas as pd
import pytest

from aasvr.deployment_evidence import (
    reconstruct_actuator_log,
    score_actuator_response_log,
    summarize_actuator_response,
)
from aasvr.prepare import HYDRO_PRIMARY_SENSORS, prepare_hydro_exp1


def test_prepare_hydro_exp1_excludes_water_level(tmp_path: Path) -> None:
    pytest.importorskip("pyarrow")
    raw = tmp_path / "Hydroponics Data First Trial.csv"
    pd.DataFrame(
        {
            "Timestamp": ["2024-02-27T20:01:07+00:00", "2024-02-27T20:01:23+00:00"],
            "entry_id": [1, 2],
            "EC": [1286, 1286],
            "pH": [6.31, 99.0],
            "Humidity": [99.9, 99.9],
            "Air_Temp": [27.3, 27.3],
            "Water_Temp": [23.62, 23.62],
            "Water_Level": [-1.30, -9.98],
            "CO2": [840, 1471],
        }
    ).to_csv(raw, index=False)
    prepared = prepare_hydro_exp1(
        raw,
        processed_dir=tmp_path / "processed",
        metadata_dir=tmp_path / "metadata",
    )
    measurements = pd.read_parquet(prepared.measurements_path)
    labels = pd.read_parquet(prepared.labels_path)
    metadata = pd.read_csv(prepared.metadata_path)
    assert "Water_Level" not in measurements.columns
    assert set(HYDRO_PRIMARY_SENSORS).issubset(measurements.columns)
    assert labels["fault"].sum() == 1
    excluded = metadata[metadata["variable"] == "Water_Level"].iloc[0]
    assert str(excluded["primary_analysis"]).lower() in {"false", "0"}


def test_prepare_hydro_exp1_merges_manual_events(tmp_path: Path) -> None:
    pytest.importorskip("pyarrow")
    raw = tmp_path / "Hydroponics Data First Trial.csv"
    pd.DataFrame(
        {
            "Timestamp": ["2024-02-27T20:01:07+00:00", "2024-02-27T20:01:23+00:00"],
            "entry_id": [1, 2],
            "EC": [1286, 1286],
            "pH": [6.31, 6.32],
            "Humidity": [70.0, 70.0],
            "Air_Temp": [24.0, 24.0],
            "Water_Temp": [21.0, 21.0],
            "Water_Level": [-1.30, -9.98],
            "CO2": [840, 850],
        }
    ).to_csv(raw, index=False)
    events = tmp_path / "experiment_1_events.csv"
    pd.DataFrame(
        {
            "event_id": ["manual_1"],
            "dataset": ["hydro_exp1"],
            "sensor": ["pH"],
            "start_time": ["2024-02-27T20:01:07+00:00"],
            "end_time": ["2024-02-27T20:01:23+00:00"],
            "event_type": ["probable_spike"],
            "confidence": [0.9],
            "evidence": ["manual review"],
            "severity": ["probable"],
            "manual_intervention": [""],
            "actuator_affected": [""],
            "notes": [""],
        }
    ).to_csv(events, index=False)
    prepared = prepare_hydro_exp1(
        raw,
        events_path=events,
        processed_dir=tmp_path / "processed",
        metadata_dir=tmp_path / "metadata",
    )
    labels = pd.read_parquet(prepared.labels_path)
    assert set(labels["label_source"]) == {"manual_event"}
    assert labels["fault"].sum() == 2


def test_reconstruct_actuator_log_requires_independent_measured_state() -> None:
    source = pd.DataFrame(
        {
            "time": ["2024-02-27T20:01:23+00:00"],
            "relay": ["acid_doser"],
            "command": [1],
            "sensor": ["pH"],
            "direction": ["decrease"],
        }
    )
    with pytest.raises(ValueError, match="measured_state"):
        reconstruct_actuator_log(source)


def test_reconstruct_actuator_log_normalizes_controller_export_and_scores_response() -> None:
    source = pd.DataFrame(
        {
            "time": ["2024-02-27T20:01:23+00:00"],
            "relay": ["acid_doser"],
            "type": ["doser"],
            "command": [1],
            "feedback_state": [1],
            "source": ["raspberry_pi"],
            "sensor": ["pH"],
            "direction": ["decrease"],
            "duration": [2.5],
            "lockout": [False],
            "manual": [False],
        }
    )
    actuator_log, reconstruction_summary = reconstruct_actuator_log(source, source_name="controller.csv")
    assert list(actuator_log["actuator_id"]) == ["acid_doser"]
    assert int(actuator_log.loc[0, "expected_direction"]) == -1
    assert float(reconstruction_summary.loc[0, "command_state_agreement"]) == 1.0

    measurements = pd.DataFrame(
        {
            "timestamp": [
                "2024-02-27T20:01:07+00:00",
                "2024-02-27T20:01:38+00:00",
                "2024-02-27T20:01:54+00:00",
            ],
            "pH": [6.7, 6.65, 6.60],
        }
    )
    response = score_actuator_response_log(measurements, actuator_log, response_window_samples=2, min_delta=0.05)
    summary = summarize_actuator_response(response)
    assert bool(response.loc[0, "response_confirmed"])
    assert summary.loc[0, "commands_scored"] == 1
    assert summary.loc[0, "response_confirmed_fraction"] == 1.0
