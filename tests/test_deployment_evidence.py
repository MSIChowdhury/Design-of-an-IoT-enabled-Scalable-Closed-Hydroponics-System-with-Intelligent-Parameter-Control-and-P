from pathlib import Path

import pandas as pd
import pytest

from aasvr.deployment_evidence import (
    ACTUATOR_LOG_COLUMNS,
    REFERENCE_MEASUREMENT_COLUMNS,
    WATER_LEVEL_CALIBRATION_COLUMNS,
    apply_water_level_calibration,
    fit_water_level_calibration,
    load_optional_actuator_log,
    load_optional_reference_measurements,
    score_actuator_response_log,
    template_frame,
    write_templates,
)


def test_optional_evidence_loaders_absent_files_return_status(tmp_path: Path) -> None:
    actuator, actuator_status = load_optional_actuator_log(tmp_path / "missing_actuators.csv")
    references, reference_status = load_optional_reference_measurements(tmp_path / "missing_refs.csv")
    assert actuator.empty
    assert references.empty
    assert not actuator_status.available
    assert not reference_status.available
    assert list(actuator.columns) == list(ACTUATOR_LOG_COLUMNS)
    assert list(references.columns) == list(REFERENCE_MEASUREMENT_COLUMNS)


def test_write_templates_creates_expected_files(tmp_path: Path) -> None:
    paths = write_templates(tmp_path)
    assert {path.name for path in paths} == {
        "actuator_state_log_template.csv",
        "reference_measurements_template.csv",
        "water_level_calibration_template.csv",
    }
    assert list(pd.read_csv(tmp_path / "actuator_state_log_template.csv").columns) == list(ACTUATOR_LOG_COLUMNS)


def test_actuator_response_log_scores_expected_direction(tmp_path: Path) -> None:
    log = tmp_path / "actuator_state_log.csv"
    pd.DataFrame(
        [
            {
                "timestamp": "2026-01-01T00:00:15Z",
                "actuator_id": "acid_pump",
                "actuator_type": "pump",
                "commanded_state": 1,
                "measured_state": 1,
                "command_source": "controller",
                "target_sensor": "pH",
                "expected_direction": "decreasing",
                "dose_or_runtime": 2.0,
                "lockout_active": False,
                "manual_override": False,
            }
        ]
    ).to_csv(log, index=False)
    actuator_log, status = load_optional_actuator_log(log)
    measurements = pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-01-01", periods=5, freq="15s", tz="UTC"),
            "pH": [6.8, 6.8, 6.7, 6.6, 6.5],
        }
    )
    scored = score_actuator_response_log(measurements, actuator_log, min_delta=0.1)
    assert status.available
    assert bool(scored.loc[0, "response_confirmed"]) is True
    assert scored.loc[0, "directional_delta"] > 0


def test_reference_loader_validates_schema(tmp_path: Path) -> None:
    path = tmp_path / "reference_measurements.csv"
    template_frame(REFERENCE_MEASUREMENT_COLUMNS).to_csv(path, index=False)
    loaded, status = load_optional_reference_measurements(path)
    assert status.available
    assert loaded.empty
    bad = tmp_path / "bad.csv"
    pd.DataFrame({"timestamp": ["2026-01-01"]}).to_csv(bad, index=False)
    with pytest.raises(ValueError):
        load_optional_reference_measurements(bad)


def test_water_level_calibration_fit_and_apply() -> None:
    frame = pd.DataFrame(
        {
            "timestamp": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"],
            "raw_water_level": [0.0, 1.0, 2.0, 3.0],
            "reference_level_cm": [10.0, 12.0, 14.0, 16.0],
            "reference_method": ["ruler"] * 4,
            "operator": ["test"] * 4,
            "notes": [""] * 4,
        }
    )
    calibration = fit_water_level_calibration(frame)
    assert calibration.n == 4
    assert calibration.rmse_cm < 1e-9
    calibrated = apply_water_level_calibration(pd.Series([4.0]), calibration)
    assert calibrated.iloc[0] == pytest.approx(18.0)


def test_water_level_calibration_requires_three_pairs() -> None:
    frame = template_frame(WATER_LEVEL_CALIBRATION_COLUMNS)
    frame.loc[0] = ["2026-01-01", 1.0, 10.0, "ruler", "test", ""]
    with pytest.raises(ValueError):
        fit_water_level_calibration(frame)
