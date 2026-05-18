from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from aasvr.core import SensorConfig


@dataclass(frozen=True)
class DatasetFiles:
    name: str
    measurements: Path
    labels: Path
    metadata: Path


DATASETS = {
    "hydro_exp1": DatasetFiles(
        name="hydro_exp1",
        measurements=Path("data/processed/hydro_exp1_measurements.parquet"),
        labels=Path("data/processed/hydro_exp1_rule_labels.parquet"),
        metadata=Path("data/processed/hydro_exp1_metadata.csv"),
    ),
    "toy": DatasetFiles(
        name="toy",
        measurements=Path("data/processed/toy_hydroponic.parquet"),
        labels=Path("data/synthetic/toy_fault_labels.csv"),
        metadata=Path(""),
    ),
}


def available_real_datasets(root: str | Path = ".") -> list[str]:
    root = Path(root)
    available = []
    for name, files in DATASETS.items():
        if name == "toy":
            continue
        if (root / files.measurements).exists():
            available.append(name)
    return available


def sensors_from_metadata(metadata: pd.DataFrame) -> tuple[SensorConfig, ...]:
    sensors = []
    for row in metadata.itertuples(index=False):
        if getattr(row, "role", "sensor") != "sensor":
            continue
        physical_min = _float_or_default(getattr(row, "physical_min", 0.0), 0.0)
        physical_max = _float_or_default(getattr(row, "physical_max", 1.0), 1.0)
        if physical_max <= physical_min:
            physical_max = physical_min + 1.0
        control_low = _float_or_default(getattr(row, "control_low", ""), physical_min)
        control_high = _float_or_default(getattr(row, "control_high", ""), physical_max)
        rate_limit = max(_float_or_default(getattr(row, "rate_limit", 0.0), 0.0), 1e-6)
        sensors.append(
            SensorConfig(
                name=str(row.variable),
                physical_min=physical_min,
                physical_max=physical_max,
                control_low=control_low,
                control_high=control_high,
                rate_limit=rate_limit,
                uncertainty=0.0,
                xi_min=max((physical_max - physical_min) * 0.001, 1e-6),
                window=9,
                confirm_samples=3,
                cooldown_samples=0,
                expected_direction=str(getattr(row, "expected_direction", "unknown") or "unknown"),
            )
        )
    return tuple(sensors)


def _float_or_default(value: object, default: float) -> float:
    try:
        if pd.isna(value) or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default
