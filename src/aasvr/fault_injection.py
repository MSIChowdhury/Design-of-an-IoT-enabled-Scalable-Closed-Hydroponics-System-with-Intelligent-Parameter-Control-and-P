from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class FaultSpec:
    sensor: str
    fault_type: str
    start: int
    duration: int
    magnitude: float


def inject_fault(frame: pd.DataFrame, spec: FaultSpec) -> tuple[pd.DataFrame, pd.DataFrame]:
    out = frame.copy()
    labels = pd.DataFrame({"timestamp": out["timestamp"], "fault": False, "fault_type": ""})
    end = min(spec.start + spec.duration, len(out))
    idx = out.index[spec.start:end]
    original = out.loc[idx, spec.sensor].astype(float)
    if spec.fault_type == "spike":
        out.loc[idx, spec.sensor] = original + spec.magnitude
    elif spec.fault_type == "stuck_at":
        out.loc[idx, spec.sensor] = float(original.iloc[0])
    elif spec.fault_type == "dropout":
        out.loc[idx, spec.sensor] = np.nan
    elif spec.fault_type == "saturation":
        out.loc[idx, spec.sensor] = spec.magnitude
    elif spec.fault_type == "drift":
        out.loc[idx, spec.sensor] = original + np.linspace(0, spec.magnitude, len(idx))
    elif spec.fault_type == "bias":
        out.loc[idx, spec.sensor] = original + spec.magnitude
    elif spec.fault_type == "noise_burst":
        rng = np.random.default_rng(17)
        out.loc[idx, spec.sensor] = original + rng.normal(0, abs(spec.magnitude), len(idx))
    elif spec.fault_type == "step":
        out.loc[idx, spec.sensor] = original + spec.magnitude
    else:
        raise ValueError(f"Unknown fault type: {spec.fault_type}")
    labels.loc[idx, "fault"] = True
    labels.loc[idx, "fault_type"] = spec.fault_type
    return out, labels

