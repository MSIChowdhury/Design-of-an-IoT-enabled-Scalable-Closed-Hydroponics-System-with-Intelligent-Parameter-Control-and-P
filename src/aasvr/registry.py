from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


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

