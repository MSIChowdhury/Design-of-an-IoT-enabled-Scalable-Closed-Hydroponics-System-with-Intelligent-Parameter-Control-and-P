from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml
import pandas as pd

from aasvr.labels import labels_from_events, load_manual_events, merge_label_sources
from aasvr.loaders import load_csv_dataset


HYDRO_EXP1_RAW = Path("data/raw/hydroponic/Hydroponics Data First Trial.csv")
HYDRO_EXP1_EVENTS = Path("data/raw/hydroponic/experiment_1_events.csv")
HYDRO_PRIMARY_SENSORS = ("EC", "pH", "Humidity", "Air_Temp", "Water_Temp", "CO2")
HYDRO_EXCLUDED_SENSORS = ("Water_Level",)

PHYSICAL_RANGES = {
    "EC": (0.0, 5000.0),
    "pH": (0.0, 14.0),
    "Humidity": (0.0, 100.0),
    "Air_Temp": (-10.0, 60.0),
    "Water_Temp": (0.0, 50.0),
    "CO2": (250.0, 5000.0),
}


@dataclass(frozen=True)
class PreparedDataset:
    measurements_path: Path
    labels_path: Path
    metadata_path: Path
    quality_path: Path


def prepare_hydro_exp1(
    raw_path: str | Path = HYDRO_EXP1_RAW,
    *,
    events_path: str | Path = HYDRO_EXP1_EVENTS,
    processed_dir: str | Path = "data/processed",
    metadata_dir: str | Path = "results/run_metadata",
) -> PreparedDataset:
    raw_path = Path(raw_path)
    if not raw_path.exists():
        raise FileNotFoundError(f"Missing hydroponic Experiment 1 raw file: {raw_path}")
    frame = pd.read_csv(raw_path)
    required = {"Timestamp", "entry_id", *HYDRO_PRIMARY_SENSORS}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Hydroponic Experiment 1 is missing columns: {missing}")

    measurements = frame[["Timestamp", "entry_id", *HYDRO_PRIMARY_SENSORS]].copy()
    measurements = measurements.rename(columns={"Timestamp": "timestamp"})
    measurements["timestamp"] = pd.to_datetime(measurements["timestamp"], errors="coerce", utc=True)
    if measurements["timestamp"].isna().any():
        bad = int(measurements["timestamp"].isna().sum())
        raise ValueError(f"Hydroponic Experiment 1 has {bad} unparsable timestamps.")
    measurements = measurements.sort_values("timestamp").reset_index(drop=True)
    measurements.insert(1, "dataset", "hydro_exp1")
    measurements.insert(2, "split", "development_tuning")

    rule_labels = make_rule_labels(measurements)
    manual_events = load_manual_events(events_path)
    manual_labels = labels_from_events(manual_events, measurements)
    labels = merge_label_sources(rule_labels, manual_labels)
    metadata = make_hydro_metadata()
    quality = make_data_quality_report(frame, measurements)

    processed_dir = Path(processed_dir)
    metadata_dir = Path(metadata_dir)
    processed_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)
    measurements_path = processed_dir / "hydro_exp1_measurements.parquet"
    labels_path = processed_dir / "hydro_exp1_rule_labels.parquet"
    metadata_path = processed_dir / "hydro_exp1_metadata.csv"
    quality_path = metadata_dir / "hydro_exp1_data_quality.csv"
    measurements.to_parquet(measurements_path, index=False)
    labels.to_parquet(labels_path, index=False)
    metadata.to_csv(metadata_path, index=False)
    quality.to_csv(quality_path, index=False)
    return PreparedDataset(
        measurements_path=measurements_path,
        labels_path=labels_path,
        metadata_path=metadata_path,
        quality_path=quality_path,
    )


def prepare_external_csv_dataset(
    dataset: str,
    *,
    root: str | Path = ".",
    processed_dir: str | Path = "data/processed",
    metadata_dir: str | Path = "results/run_metadata",
) -> PreparedDataset | None:
    root = Path(root)
    config_path = root / "configs/datasets" / f"{dataset}.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Missing dataset config: {config_path}")
    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    raw_path = root / str(config["path"])
    raw_file = _first_csv(raw_path)
    if raw_file is None:
        return None

    frame = pd.read_csv(raw_file)
    timestamp_column = _timestamp_column(frame, config.get("timestamp_column"))
    if timestamp_column is None:
        timestamp_column = "timestamp"
        frame.insert(0, timestamp_column, pd.date_range("2000-01-01", periods=len(frame), freq="min"))
        staging = root / "data/interim" / f"{dataset}_with_synthetic_timestamp.csv"
        staging.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(staging, index=False)
        raw_file = staging
    label_column = _label_column(frame, config.get("label_column"))
    actuator_columns = tuple(config.get("actuator_columns", ()))

    loaded = load_csv_dataset(
        raw_file,
        dataset=dataset,
        split="external",
        timestamp_column=timestamp_column,
        label_column=label_column,
        actuator_columns=actuator_columns,
    )
    processed_dir = Path(processed_dir)
    metadata_dir = Path(metadata_dir)
    processed_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)
    measurements_path = processed_dir / f"{dataset}_measurements.parquet"
    labels_path = processed_dir / f"{dataset}_labels.parquet"
    metadata_path = processed_dir / f"{dataset}_metadata.csv"
    quality_path = metadata_dir / f"{dataset}_data_quality.csv"
    loaded.measurements.to_parquet(measurements_path, index=False)
    loaded.labels.to_parquet(labels_path, index=False)
    loaded.metadata.to_csv(metadata_path, index=False)
    make_generic_quality_report(dataset, loaded.measurements, loaded.metadata).to_csv(quality_path, index=False)
    return PreparedDataset(
        measurements_path=measurements_path,
        labels_path=labels_path,
        metadata_path=metadata_path,
        quality_path=quality_path,
    )


def make_rule_labels(measurements: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for sensor, (lo, hi) in PHYSICAL_RANGES.items():
        values = pd.to_numeric(measurements[sensor], errors="coerce")
        fault = values.isna() | (values < lo) | (values > hi)
        flagged = measurements.loc[fault, ["timestamp", "dataset"]].copy()
        for row in flagged.itertuples(index=False):
            rows.append(
                {
                    "timestamp": row.timestamp,
                    "dataset": row.dataset,
                    "event_id": f"rule_{sensor}_{len(rows) + 1}",
                    "sensor": sensor,
                    "fault": True,
                    "fault_type": "physical_range",
                    "severity": "candidate",
                    "label_source": "rule_candidate",
                    "confidence": 0.75,
                }
            )
    return pd.DataFrame(
        rows,
        columns=[
            "timestamp",
            "dataset",
            "event_id",
            "sensor",
            "fault",
            "fault_type",
            "severity",
            "label_source",
            "confidence",
        ],
    )


def make_hydro_metadata() -> pd.DataFrame:
    rows = []
    for sensor in HYDRO_PRIMARY_SENSORS:
        lo, hi = PHYSICAL_RANGES[sensor]
        rows.append(
            {
                "dataset": "hydro_exp1",
                "variable": sensor,
                "role": "sensor",
                "primary_analysis": True,
                "physical_min": lo,
                "physical_max": hi,
                "exclusion_reason": "",
            }
        )
    for sensor in HYDRO_EXCLUDED_SENSORS:
        rows.append(
            {
                "dataset": "hydro_exp1",
                "variable": sensor,
                "role": "sensor",
                "primary_analysis": False,
                "physical_min": "",
                "physical_max": "",
                "exclusion_reason": "Excluded because raw values are uncalibrated and mostly negative.",
            }
        )
    return pd.DataFrame(rows)


def make_data_quality_report(raw: pd.DataFrame, measurements: pd.DataFrame) -> pd.DataFrame:
    rows = []
    timestamp = measurements["timestamp"]
    deltas = timestamp.sort_values().diff().dropna()
    rows.append(
        {
            "dataset": "hydro_exp1",
            "variable": "timestamp",
            "rows": len(measurements),
            "missing": int(timestamp.isna().sum()),
            "min": timestamp.min(),
            "median": "",
            "max": timestamp.max(),
            "physical_violations": 0,
            "notes": f"median cadence {deltas.median() if len(deltas) else 'NA'}",
        }
    )
    for sensor in HYDRO_PRIMARY_SENSORS:
        values = pd.to_numeric(measurements[sensor], errors="coerce")
        lo, hi = PHYSICAL_RANGES[sensor]
        violations = values.isna() | (values < lo) | (values > hi)
        rows.append(
            {
                "dataset": "hydro_exp1",
                "variable": sensor,
                "rows": len(values),
                "missing": int(values.isna().sum()),
                "min": float(values.min()),
                "median": float(values.median()),
                "max": float(values.max()),
                "physical_violations": int(violations.sum()),
                "notes": "primary analysis sensor",
            }
        )
    for sensor in HYDRO_EXCLUDED_SENSORS:
        if sensor in raw:
            values = pd.to_numeric(raw[sensor], errors="coerce")
            rows.append(
                {
                    "dataset": "hydro_exp1",
                    "variable": sensor,
                    "rows": len(values),
                    "missing": int(values.isna().sum()),
                    "min": float(values.min()),
                    "median": float(values.median()),
                    "max": float(values.max()),
                    "physical_violations": "",
                    "notes": "excluded from primary analysis; calibration not established",
                }
            )
    return pd.DataFrame(rows)


def make_generic_quality_report(
    dataset: str,
    measurements: pd.DataFrame,
    metadata: pd.DataFrame,
) -> pd.DataFrame:
    rows = []
    timestamps = pd.to_datetime(measurements["timestamp"], errors="coerce")
    rows.append(
        {
            "dataset": dataset,
            "variable": "timestamp",
            "rows": len(measurements),
            "missing": int(timestamps.isna().sum()),
            "min": timestamps.min(),
            "median": "",
            "max": timestamps.max(),
            "physical_violations": 0,
            "notes": "generic external dataset timestamp",
        }
    )
    for row in metadata.itertuples(index=False):
        variable = row.variable
        values = pd.to_numeric(measurements[variable], errors="coerce")
        lo = float(row.physical_min)
        hi = float(row.physical_max)
        violations = values.isna() | (values < lo) | (values > hi)
        rows.append(
            {
                "dataset": dataset,
                "variable": variable,
                "rows": len(values),
                "missing": int(values.isna().sum()),
                "min": float(values.min()) if values.notna().any() else "",
                "median": float(values.median()) if values.notna().any() else "",
                "max": float(values.max()) if values.notna().any() else "",
                "physical_violations": int(violations.sum()),
                "notes": f"generic external dataset {row.role}",
            }
        )
    return pd.DataFrame(rows)


def _first_csv(path: Path) -> Path | None:
    if path.is_file() and path.suffix.lower() == ".csv":
        return path
    if not path.exists() or not path.is_dir():
        return None
    candidates = sorted(candidate for candidate in path.rglob("*.csv") if candidate.is_file())
    return candidates[0] if candidates else None


def _timestamp_column(frame: pd.DataFrame, configured: str | None) -> str | None:
    if configured and configured in frame:
        return configured
    for candidate in ("timestamp", "Timestamp", "time", "Time", "datetime", "Datetime", "date", "Date"):
        if candidate in frame:
            return candidate
    return None


def _label_column(frame: pd.DataFrame, configured: str | None) -> str | None:
    if configured and configured in frame:
        return configured
    for candidate in ("label", "Label", "fault", "Fault", "Normal/Attack", "Attack", "class", "Class"):
        if candidate in frame:
            return candidate
    return None
