from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from aasvr.schemas import CanonicalDataset, canonicalize_measurements, empty_labels


SENSOR_HINTS = {
    "swat": ("FIT", "LIT", "AIT", "PIT", "DPIT"),
    "wadi": ("1_", "2_", "3_", "FIT", "LIT", "AIT", "PIT"),
    "tep": ("XMEAS", "XMV"),
    "damadics": ("CV", "PV", "SP", "F"),
    "wur": ("air", "co2", "rh", "temp", "radiation", "heat", "vent"),
}


def load_csv_dataset(
    path: str | Path,
    *,
    dataset: str,
    split: str = "unknown",
    timestamp_column: str = "timestamp",
    label_column: str | None = None,
    actuator_columns: Iterable[str] = (),
) -> CanonicalDataset:
    frame = pd.read_csv(path)
    measurements = canonicalize_measurements(
        frame.drop(columns=[label_column], errors="ignore"),
        dataset=dataset,
        split=split,
        timestamp_column=timestamp_column,
    )
    labels = empty_labels(measurements, label_source="native" if label_column else "none")
    if label_column and label_column in frame:
        labels["fault"] = frame[label_column].astype(str).str.lower().isin(
            {"1", "true", "attack", "abnormal", "fault", "faulty"}
        )
        labels["fault_type"] = labels["fault"].map({True: "native_anomaly", False: ""})
        labels["confidence"] = labels["fault"].map({True: 1.0, False: 0.0})
    actuator_columns = tuple(actuator_columns)
    actuators = measurements[["timestamp", "dataset", *[c for c in actuator_columns if c in measurements]]]
    metadata = infer_metadata(measurements, dataset=dataset, actuator_columns=actuator_columns)
    return CanonicalDataset(
        measurements=measurements,
        labels=labels,
        actuators=actuators,
        metadata=metadata,
    )


def infer_metadata(
    measurements: pd.DataFrame,
    *,
    dataset: str,
    actuator_columns: Iterable[str] = (),
) -> pd.DataFrame:
    actuator_set = set(actuator_columns)
    rows = []
    for column in measurements.columns:
        if column in {"timestamp", "dataset", "split"}:
            continue
        series = pd.to_numeric(measurements[column], errors="coerce")
        if series.notna().sum() == 0:
            continue
        role = "actuator" if column in actuator_set else _infer_role(column, dataset)
        rows.append(
            {
                "dataset": dataset,
                "variable": column,
                "role": role,
                "unit": "",
                "physical_min": float(series.quantile(0.001)),
                "physical_max": float(series.quantile(0.999)),
                "control_low": "",
                "control_high": "",
                "rate_limit": float(series.diff().abs().quantile(0.999) or 0.0),
                "expected_direction": "unknown",
            }
        )
    return pd.DataFrame(rows)


def _infer_role(column: str, dataset: str) -> str:
    upper = column.upper()
    hints = SENSOR_HINTS.get(dataset.lower(), ())
    if any(upper.startswith(hint.upper()) or hint.upper() in upper for hint in hints):
        return "sensor"
    if upper.startswith(("P", "MV", "XMV")) or "ACT" in upper or "VALVE" in upper:
        return "actuator"
    return "sensor"

