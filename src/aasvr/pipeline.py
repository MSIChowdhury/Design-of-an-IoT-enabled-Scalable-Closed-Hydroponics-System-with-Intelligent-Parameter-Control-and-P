from __future__ import annotations

from pathlib import Path

import pandas as pd

from aasvr.baselines import BaselineConfig, StreamingBaseline, decisions_to_frame
from aasvr.config import load_aasvr_config
from aasvr.core import AASVR, AASVRConfig, AASVRDecision, SensorConfig


def run_aasvr_on_frame(frame: pd.DataFrame, config_path: str | Path) -> pd.DataFrame:
    config = load_aasvr_config(config_path)
    return run_aasvr_with_config(frame, config)


def run_aasvr_with_config(frame: pd.DataFrame, config: AASVRConfig) -> pd.DataFrame:
    model = AASVR(config)
    decisions: list[AASVRDecision] = []
    for sample in frame.to_dict(orient="records"):
        decisions.extend(model.update(sample))
    return decisions_to_frame(decisions)


def run_baseline_on_frame(
    frame: pd.DataFrame,
    sensors: tuple[SensorConfig, ...],
    method: str,
) -> pd.DataFrame:
    model = StreamingBaseline(sensors, BaselineConfig(method=method))
    decisions: list[AASVRDecision] = []
    for sample in frame.to_dict(orient="records"):
        decisions.extend(model.update(sample))
    return decisions_to_frame(decisions)


def ensure_parent(path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
