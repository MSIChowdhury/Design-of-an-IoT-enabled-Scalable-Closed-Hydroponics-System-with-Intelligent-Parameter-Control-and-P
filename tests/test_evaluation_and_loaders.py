from pathlib import Path

import pandas as pd

from aasvr.evaluation import compute_metrics
from aasvr.loaders import load_csv_dataset


def test_event_metrics_count_detection_delay_and_false_alarm() -> None:
    decisions = pd.DataFrame(
        {
            "alert": [False, False, True, False, False, True, True, False],
            "actuation_authorized": [False] * 8,
            "unsafe_band": [False] * 8,
        }
    )
    labels = pd.DataFrame({"fault": [False, False, False, False, False, True, True, False]})
    metrics = compute_metrics(decisions, labels)
    assert metrics.event_recall == 1.0
    assert metrics.mean_detection_delay_samples == 0.0
    assert metrics.false_alarm_events == 1


def test_aasvr_gate_reject_prediction_mode_scores_suspect_rejections() -> None:
    decisions = pd.DataFrame(
        {
            "alert": [False, False, False],
            "gate_result": ["accept", "reject", "accept"],
            "actuation_authorized": [False, False, False],
            "unsafe_band": [False, False, False],
        }
    )
    labels = pd.DataFrame({"fault": [False, True, False]})
    alert_metrics = compute_metrics(decisions, labels, prediction_mode="alert")
    gate_metrics = compute_metrics(decisions, labels, prediction_mode="gate_reject")
    assert alert_metrics.recall == 0.0
    assert gate_metrics.recall == 1.0


def test_csv_loader_returns_canonical_frames(tmp_path: Path) -> None:
    path = tmp_path / "sample.csv"
    pd.DataFrame(
        {
            "time": ["2026-01-01 00:00:00", "2026-01-01 00:00:15"],
            "FIT101": [1.0, 1.1],
            "P101": [0, 1],
            "Normal/Attack": ["Normal", "Attack"],
        }
    ).to_csv(path, index=False)
    loaded = load_csv_dataset(
        path,
        dataset="swat",
        split="test",
        timestamp_column="time",
        label_column="Normal/Attack",
        actuator_columns=("P101",),
    )
    assert list(loaded.measurements.columns[:3]) == ["timestamp", "dataset", "split"]
    assert loaded.labels["fault"].tolist() == [False, True]
    assert "P101" in loaded.actuators
    assert set(loaded.metadata["role"]) >= {"sensor", "actuator"}
