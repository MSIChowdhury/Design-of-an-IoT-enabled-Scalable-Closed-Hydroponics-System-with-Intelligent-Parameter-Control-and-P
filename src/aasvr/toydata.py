from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def make_toy_hydroponic_data(rows: int = 240, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    t = pd.date_range("2026-01-01", periods=rows, freq="15s")
    frame = pd.DataFrame(
        {
            "timestamp": t,
            "pH": 6.1 + 0.04 * rng.normal(size=rows),
            "EC": 1100 + 12 * rng.normal(size=rows),
            "Air_Temp": 24 + 0.2 * rng.normal(size=rows),
            "Water_Temp": 21 + 0.1 * rng.normal(size=rows),
            "Water_Level": 12 + 0.05 * rng.normal(size=rows),
            "CO2": 800 + 20 * rng.normal(size=rows),
        }
    )
    if rows > 40:
        frame.loc[40, "pH"] = 9.5
    if rows > 85:
        frame.loc[85 : min(90, rows - 1), "EC"] = 3500
    if rows > 130:
        frame.loc[130 : min(150, rows - 1), "Water_Level"] = np.nan
    if rows > 180:
        start, end = 180, min(220, rows - 1)
        frame.loc[start:end, "CO2"] += np.linspace(0, 450, end - start + 1)
    return frame


def write_toy_dataset(path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    make_toy_hydroponic_data().to_csv(path, index=False)
    return path
