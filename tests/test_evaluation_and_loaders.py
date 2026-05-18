from pathlib import Path

import pandas as pd

from aasvr.evaluation import compute_metrics
from aasvr.loaders import load_csv_dataset
from aasvr.prepare import prepare_external_csv_dataset


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


def test_prepare_external_csv_dataset_skips_missing_raw(tmp_path: Path) -> None:
    config_dir = tmp_path / "configs/datasets"
    config_dir.mkdir(parents=True)
    (config_dir / "tep.yaml").write_text(
        "name: tep\npath: data/raw/tep/\nrole: test\n",
        encoding="utf-8",
    )
    assert prepare_external_csv_dataset("tep", root=tmp_path) is None


def test_prepare_external_csv_dataset_writes_canonical_outputs(tmp_path: Path) -> None:
    config_dir = tmp_path / "configs/datasets"
    raw_dir = tmp_path / "data/raw/tep"
    config_dir.mkdir(parents=True)
    raw_dir.mkdir(parents=True)
    (config_dir / "tep.yaml").write_text(
        "name: tep\npath: data/raw/tep/\nrole: test\ntimestamp_column: time\nlabel_column: label\n",
        encoding="utf-8",
    )
    pd.DataFrame(
        {
            "time": ["2026-01-01 00:00:00", "2026-01-01 00:01:00"],
            "XMEAS1": [1.0, 2.0],
            "label": [0, 1],
        }
    ).to_csv(raw_dir / "sample.csv", index=False)
    prepared = prepare_external_csv_dataset("tep", root=tmp_path)
    assert prepared is not None
    measurements = pd.read_parquet(prepared.measurements_path)
    labels = pd.read_parquet(prepared.labels_path)
    assert measurements["dataset"].eq("tep").all()
    assert labels["fault"].tolist() == [False, True]
