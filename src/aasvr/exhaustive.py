from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from itertools import product
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from aasvr.config import load_yaml
from aasvr.core import AASVRConfig, SensorConfig


@dataclass(frozen=True)
class ExhaustiveProtocol:
    name: str
    sensors: tuple[str, ...]
    fault_types: tuple[str, ...]
    sigma_multipliers: tuple[float, ...]
    durations: tuple[int, ...]
    windows_per_cell: int
    pre_fault_samples: int
    post_fault_samples: int
    splits: tuple[str, ...]
    split_seed_offset: dict[str, int]
    max_trials_per_split: int | None = None


@dataclass(frozen=True)
class ExhaustiveSweep:
    scale_multiplier: tuple[float, ...]
    q_min: tuple[float, ...]
    transient_limit: tuple[int, ...]
    persistent_limit: tuple[int, ...]
    confirm_samples: tuple[int, ...]
    cooldown_samples: tuple[int, ...]
    rectification_mode: tuple[str, ...]
    cusum_drift_multiplier: tuple[float, ...]
    cusum_threshold_multiplier: tuple[float, ...]
    response_eta_decay: tuple[float, ...]
    eta_min_high: tuple[float, ...]
    eta_min_medium: tuple[float, ...]
    eta_min_low: tuple[float, ...]
    response_window: tuple[int, ...]


def load_exhaustive_protocol(path: str | Path, *, profile: str) -> tuple[ExhaustiveProtocol, ExhaustiveSweep]:
    data = load_yaml(path)
    profiles = data.get("profiles", {})
    if profile not in profiles:
        raise ValueError(f"Unknown exhaustive profile {profile!r}; available profiles: {sorted(profiles)}")
    defaults = data.get("defaults", {})
    selected = {**defaults, **profiles[profile]}
    protocol = ExhaustiveProtocol(
        name=f"{data.get('name', 'hydro_exp1')}_{profile}",
        sensors=tuple(selected["sensors"]),
        fault_types=tuple(selected["fault_types"]),
        sigma_multipliers=tuple(float(value) for value in selected["sigma_multipliers"]),
        durations=tuple(int(value) for value in selected["durations"]),
        windows_per_cell=int(selected["windows_per_cell"]),
        pre_fault_samples=int(selected.get("pre_fault_samples", 90)),
        post_fault_samples=int(selected.get("post_fault_samples", 120)),
        splits=tuple(selected.get("splits", ("tune", "validation", "test"))),
        split_seed_offset={key: int(value) for key, value in selected.get("split_seed_offset", {}).items()},
        max_trials_per_split=(
            int(selected["max_trials_per_split"])
            if selected.get("max_trials_per_split") is not None
            else None
        ),
    )
    sweep_data = selected.get("sweep", {})
    sweep = ExhaustiveSweep(
        scale_multiplier=tuple(float(v) for v in sweep_data.get("scale_multiplier", (6.0,))),
        q_min=tuple(float(v) for v in sweep_data.get("q_min", (0.70,))),
        transient_limit=tuple(int(v) for v in sweep_data.get("transient_limit", (2,))),
        persistent_limit=tuple(int(v) for v in sweep_data.get("persistent_limit", (5,))),
        confirm_samples=tuple(int(v) for v in sweep_data.get("confirm_samples", (3,))),
        cooldown_samples=tuple(int(v) for v in sweep_data.get("cooldown_samples", (4,))),
        rectification_mode=tuple(str(v) for v in sweep_data.get("rectification_mode", ("hold",))),
        cusum_drift_multiplier=tuple(float(v) for v in sweep_data.get("cusum_drift_multiplier", (0.10,))),
        cusum_threshold_multiplier=tuple(float(v) for v in sweep_data.get("cusum_threshold_multiplier", (0.60,))),
        response_eta_decay=tuple(float(v) for v in sweep_data.get("response_eta_decay", (0.50,))),
        eta_min_high=tuple(float(v) for v in sweep_data.get("eta_min_high", (0.75,))),
        eta_min_medium=tuple(float(v) for v in sweep_data.get("eta_min_medium", (0.65,))),
        eta_min_low=tuple(float(v) for v in sweep_data.get("eta_min_low", (0.50,))),
        response_window=tuple(int(v) for v in sweep_data.get("response_window", (6,))),
    )
    return protocol, sweep


def build_fault_grid(
    frame: pd.DataFrame,
    sensors: tuple[SensorConfig, ...],
    protocol: ExhaustiveProtocol,
    *,
    seed: int = 20260519,
) -> pd.DataFrame:
    lookup = {sensor.name: sensor for sensor in sensors}
    rows: list[dict[str, Any]] = []
    for split in protocol.splits:
        split_seed = seed + protocol.split_seed_offset.get(split, 0)
        rng = np.random.default_rng(split_seed)
        split_rows: list[dict[str, Any]] = []
        for sensor_name, fault_type, sigma_multiplier, duration in product(
            protocol.sensors,
            protocol.fault_types,
            protocol.sigma_multipliers,
            protocol.durations,
        ):
            if sensor_name not in lookup or sensor_name not in frame:
                continue
            sensor = lookup[sensor_name]
            values = pd.to_numeric(frame[sensor_name], errors="coerce").to_numpy(dtype=float)
            magnitude = _fault_magnitude(values, sensor, sigma_multiplier)
            starts = _candidate_starts(
                frame,
                duration=duration,
                pre=protocol.pre_fault_samples,
                post=protocol.post_fault_samples,
                windows=protocol.windows_per_cell,
                rng=rng,
            )
            for window_id, start in enumerate(starts):
                split_rows.append(
                    {
                        "dataset": "hydro_exp1",
                        "profile": protocol.name,
                        "split": split,
                        "trial_id": (
                            f"{split}_{sensor_name}_{fault_type}_"
                            f"{sigma_multiplier:g}x_{duration}_{window_id}"
                        ),
                        "fault_protocol_id": f"{sensor_name}_{fault_type}_{sigma_multiplier:g}x_{duration}",
                        "sensor": sensor_name,
                        "fault_type": fault_type,
                        "start": int(start),
                        "duration": int(duration),
                        "sigma_multiplier": float(sigma_multiplier),
                        "magnitude": float(magnitude),
                        "seed": int(split_seed + window_id),
                        "physical_min": sensor.physical_min,
                        "physical_max": sensor.physical_max,
                        "pre_fault_samples": protocol.pre_fault_samples,
                        "post_fault_samples": protocol.post_fault_samples,
                    }
                )
        if protocol.max_trials_per_split is not None and len(split_rows) > protocol.max_trials_per_split:
            indexes = rng.choice(len(split_rows), size=protocol.max_trials_per_split, replace=False)
            split_rows = [split_rows[int(idx)] for idx in sorted(indexes)]
        rows.extend(split_rows)
    return pd.DataFrame(rows)


def build_sweep_grid(sweep: ExhaustiveSweep, *, profile: str) -> pd.DataFrame:
    rows = []
    for values in product(
        sweep.scale_multiplier,
        sweep.q_min,
        sweep.transient_limit,
        sweep.persistent_limit,
        sweep.confirm_samples,
        sweep.cooldown_samples,
        sweep.rectification_mode,
        sweep.cusum_drift_multiplier,
        sweep.cusum_threshold_multiplier,
        sweep.response_eta_decay,
        sweep.eta_min_high,
        sweep.eta_min_medium,
        sweep.eta_min_low,
        sweep.response_window,
    ):
        row = {
            "profile": profile,
            "scale_multiplier": values[0],
            "q_min": values[1],
            "transient_limit": values[2],
            "persistent_limit": values[3],
            "confirm_samples": values[4],
            "cooldown_samples": values[5],
            "rectification_mode": values[6],
            "cusum_drift_multiplier": values[7],
            "cusum_threshold_multiplier": values[8],
            "eta_decay": values[9],
            "eta_min_high": values[10],
            "eta_min_medium": values[11],
            "eta_min_low": values[12],
            "response_window": values[13],
        }
        row["setting_id"] = "s" + str(abs(hash(tuple(row.values()))) % 10_000_000_000)
        rows.append(row)
    return pd.DataFrame(rows)


def config_from_sweep_row(base: AASVRConfig, row: pd.Series | dict[str, Any]) -> AASVRConfig:
    values = row.to_dict() if hasattr(row, "to_dict") else dict(row)
    sensors = tuple(
        replace(
            sensor,
            confirm_samples=int(values["confirm_samples"]),
            cooldown_samples=int(values["cooldown_samples"]),
            cusum_drift_multiplier=float(values["cusum_drift_multiplier"]),
            cusum_threshold_multiplier=float(values["cusum_threshold_multiplier"]),
            response_window=int(values["response_window"]),
        )
        for sensor in base.sensors
    )
    return replace(
        base,
        sensors=sensors,
        scale_multiplier=float(values["scale_multiplier"]),
        q_min=float(values["q_min"]),
        transient_limit=int(values["transient_limit"]),
        persistent_limit=int(values["persistent_limit"]),
        rectification_mode=str(values["rectification_mode"]),
        eta_decay=float(values["eta_decay"]),
        eta_min_high=float(values["eta_min_high"]),
        eta_min_medium=float(values["eta_min_medium"]),
        eta_min_low=float(values["eta_min_low"]),
    )


def protocol_summary(protocol: ExhaustiveProtocol) -> dict[str, Any]:
    cells = (
        len(protocol.sensors)
        * len(protocol.fault_types)
        * len(protocol.sigma_multipliers)
        * len(protocol.durations)
        * protocol.windows_per_cell
    )
    split_trials = min(cells, protocol.max_trials_per_split) if protocol.max_trials_per_split else cells
    data = asdict(protocol)
    data["full_factorial_cells_per_split"] = cells
    data["planned_trials_per_split"] = split_trials
    data["planned_total_trials"] = split_trials * len(protocol.splits)
    return data


def _candidate_starts(
    frame: pd.DataFrame,
    *,
    duration: int,
    pre: int,
    post: int,
    windows: int,
    rng: np.random.Generator,
) -> np.ndarray:
    low = max(pre, 0)
    high = max(len(frame) - duration - post - 1, low + 1)
    if windows <= 1:
        return np.asarray([int((low + high) // 2)])
    if high - low <= windows:
        return np.arange(low, min(high, low + windows), dtype=int)
    bins = np.linspace(low, high, num=windows + 1, dtype=int)
    starts = []
    for left, right in zip(bins[:-1], bins[1:], strict=False):
        starts.append(int(rng.integers(left, max(left + 1, right))))
    return np.asarray(starts, dtype=int)


def _fault_magnitude(values: np.ndarray, sensor: SensorConfig, multiplier: float) -> float:
    finite = values[np.isfinite(values)]
    if len(finite) < 3:
        scale = max(sensor.uncertainty, sensor.xi_min)
    else:
        diffs = np.diff(finite)
        mad = np.median(np.abs(diffs - np.median(diffs)))
        scale = max(1.4826 * mad, sensor.uncertainty, sensor.xi_min)
    return float(multiplier * scale)
