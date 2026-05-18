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
    seed: int = 17


def inject_fault(frame: pd.DataFrame, spec: FaultSpec) -> tuple[pd.DataFrame, pd.DataFrame]:
    out = frame.copy()
    labels = pd.DataFrame(
        {
            "timestamp": out["timestamp"],
            "sensor": spec.sensor,
            "fault": False,
            "fault_type": "",
        }
    )
    end = min(spec.start + spec.duration, len(out))
    idx = out.index[spec.start:end]
    out[spec.sensor] = pd.to_numeric(out[spec.sensor], errors="coerce").astype(float)
    original = out.loc[idx, spec.sensor].astype(float)
    if spec.fault_type == "spike":
        out.loc[idx, spec.sensor] = original + spec.magnitude
    elif spec.fault_type == "multi_spike":
        rng = np.random.default_rng(spec.seed)
        signs = rng.choice([-1.0, 1.0], size=len(idx))
        out.loc[idx, spec.sensor] = original + signs * spec.magnitude
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
        rng = np.random.default_rng(spec.seed)
        out.loc[idx, spec.sensor] = original + rng.normal(0, abs(spec.magnitude), len(idx))
    elif spec.fault_type == "step":
        out.loc[idx, spec.sensor] = original + spec.magnitude
    else:
        raise ValueError(f"Unknown fault type: {spec.fault_type}")
    labels.loc[idx, "fault"] = True
    labels.loc[idx, "fault_type"] = spec.fault_type
    return out, labels


def make_fault_grid(
    frame: pd.DataFrame,
    *,
    sensor: str,
    fault_types: tuple[str, ...] = (
        "spike",
        "multi_spike",
        "stuck_at",
        "dropout",
        "saturation",
        "drift",
        "bias",
        "noise_burst",
        "step",
    ),
    magnitudes: tuple[float, ...] = (2.0, 4.0, 8.0),
    durations: tuple[int, ...] = (1, 3, 5, 10, 30),
    repetitions: int = 3,
    seed: int = 17,
) -> list[tuple[FaultSpec, pd.DataFrame, pd.DataFrame]]:
    rng = np.random.default_rng(seed)
    trials: list[tuple[FaultSpec, pd.DataFrame, pd.DataFrame]] = []
    max_start = max(len(frame) - max(durations) - 1, 1)
    for fault_type in fault_types:
        for magnitude in magnitudes:
            for duration in durations:
                for rep in range(repetitions):
                    start = int(rng.integers(0, max_start))
                    spec = FaultSpec(
                        sensor=sensor,
                        fault_type=fault_type,
                        start=start,
                        duration=min(duration, len(frame) - start),
                        magnitude=magnitude,
                        seed=seed + rep,
                    )
                    faulted, labels = inject_fault(frame, spec)
                    trials.append((spec, faulted, labels))
    return trials
