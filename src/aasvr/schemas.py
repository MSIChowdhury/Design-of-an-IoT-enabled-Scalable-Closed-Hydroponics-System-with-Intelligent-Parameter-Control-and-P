from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


MEASUREMENT_COLUMNS = ("timestamp", "dataset", "split")
LABEL_COLUMNS = (
    "timestamp",
    "dataset",
    "event_id",
    "sensor",
    "fault",
    "fault_type",
    "severity",
    "label_source",
    "confidence",
)


@dataclass(frozen=True)
class CanonicalDataset:
    measurements: pd.DataFrame
    labels: pd.DataFrame
    actuators: pd.DataFrame
    metadata: pd.DataFrame


def canonicalize_measurements(
    frame: pd.DataFrame,
    *,
    dataset: str,
    split: str,
    timestamp_column: str = "timestamp",
) -> pd.DataFrame:
    out = frame.copy()
    if timestamp_column != "timestamp":
        out = out.rename(columns={timestamp_column: "timestamp"})
    if "timestamp" not in out:
        raise ValueError("Canonical measurements require a timestamp column.")
    out["timestamp"] = pd.to_datetime(out["timestamp"], errors="coerce")
    out["dataset"] = dataset
    out["split"] = split
    fixed = list(MEASUREMENT_COLUMNS)
    remainder = [col for col in out.columns if col not in fixed]
    return out[fixed + remainder].sort_values("timestamp").reset_index(drop=True)


def empty_labels(measurements: pd.DataFrame, *, label_source: str = "none") -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": measurements["timestamp"],
            "dataset": measurements["dataset"],
            "event_id": "",
            "sensor": "",
            "fault": False,
            "fault_type": "",
            "severity": "",
            "label_source": label_source,
            "confidence": 0.0,
        }
    )

