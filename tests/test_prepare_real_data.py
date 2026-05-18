from pathlib import Path

import pandas as pd
import pytest

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
