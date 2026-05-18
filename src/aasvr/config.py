from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from aasvr.core import AASVRConfig, SensorConfig


def load_yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_aasvr_config(path: str | Path) -> AASVRConfig:
    data = load_yaml(path)
    sensors = tuple(SensorConfig(**sensor) for sensor in data.get("sensors", []))
    options = {key: value for key, value in data.items() if key != "sensors"}
    return AASVRConfig(sensors=sensors, **options)

