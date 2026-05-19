from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import OneClassSVM

from aasvr.baselines import BaselineConfig, StreamingBaseline, decisions_to_frame
from aasvr.config import load_aasvr_config
from aasvr.core import AASVR, AASVRConfig, AASVRDecision, SensorConfig
from aasvr.states import SensorState


ML_BASELINES = {"isolation_forest", "one_class_svm", "local_outlier_factor"}


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
    config: BaselineConfig | None = None,
) -> pd.DataFrame:
    config = config or BaselineConfig(method=method)
    if method in ML_BASELINES:
        return _run_one_class_baseline_on_frame(
            frame,
            sensors,
            method,
            calibration_fraction=getattr(config, "ml_calibration_fraction", 0.2),
            contamination=getattr(config, "ml_contamination", 0.05),
            neighbors=getattr(config, "ml_neighbors", 20),
        )
    model = StreamingBaseline(sensors, config)
    decisions: list[AASVRDecision] = []
    for sample in frame.to_dict(orient="records"):
        decisions.extend(model.update(sample))
    return decisions_to_frame(decisions)


def ensure_parent(path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _run_one_class_baseline_on_frame(
    frame: pd.DataFrame,
    sensors: tuple[SensorConfig, ...],
    method: str,
    *,
    calibration_fraction: float = 0.2,
    contamination: float = 0.05,
    neighbors: int = 20,
    max_calibration_samples: int = 1000,
) -> pd.DataFrame:
    """Run lightweight one-class ML baselines with a fixed calibration segment.

    These baselines are intentionally batch-calibrated rather than refit at every
    sample. That matches the paper protocol: use a normal/calibration prefix, then
    replay the remaining stream through the same controller-facing decision schema.
    """

    timestamps = frame["timestamp"] if "timestamp" in frame else pd.Series(range(len(frame)))
    decisions: list[AASVRDecision] = []
    calibrate_n = max(10, int(len(frame) * calibration_fraction))
    for sensor in sensors:
        values = pd.to_numeric(frame[sensor.name], errors="coerce").to_numpy(dtype=float)
        finite = np.isfinite(values)
        physical = (sensor.physical_min <= values) & (values <= sensor.physical_max)
        calibration_values = values[:calibrate_n][finite[:calibrate_n] & physical[:calibrate_n]]
        if len(calibration_values) < 10:
            calibration_values = values[finite & physical]
        if len(calibration_values) > max_calibration_samples:
            idx = np.linspace(0, len(calibration_values) - 1, max_calibration_samples).astype(int)
            calibration_values = calibration_values[idx]
        center = float(np.nanmedian(calibration_values)) if len(calibration_values) else float("nan")
        model = _fit_one_class_model(method, calibration_values, contamination, neighbors=neighbors)
        anomalies = _predict_one_class_anomalies(model, values, sensor)
        violations = 0
        for timestamp, y, anomaly in zip(timestamps, values, anomalies, strict=False):
            trusted = center if anomaly and np.isfinite(center) else y
            authorized, violations = _authorize_from_trusted(sensor, trusted, violations)
            decisions.append(
                AASVRDecision(
                    timestamp=timestamp,
                    sensor=sensor.name,
                    raw_value=float(y) if np.isfinite(y) else float("nan"),
                    trusted_value=float(trusted) if np.isfinite(trusted) else float("nan"),
                    state=SensorState.FAULT_ALERT if anomaly else SensorState.NORMAL,
                    trust_score=0.0 if anomaly else 1.0,
                    gate_result="reject" if anomaly else "accept",
                    rectification_action=method,
                    actuation_authorized=authorized,
                    alert=anomaly,
                    reason_codes=("one_class_anomaly",) if anomaly else (),
                )
            )
    return decisions_to_frame(decisions)


def _fit_one_class_model(method: str, values: np.ndarray, contamination: float, *, neighbors: int):
    if len(values) < 10:
        return None
    x = values.reshape(-1, 1)
    if method == "isolation_forest":
        return make_pipeline(
            StandardScaler(),
            IsolationForest(contamination=contamination, random_state=29, n_estimators=100),
        ).fit(x)
    if method == "one_class_svm":
        return make_pipeline(StandardScaler(), OneClassSVM(nu=contamination, gamma="scale")).fit(x)
    if method == "local_outlier_factor":
        neighbors = min(neighbors, max(2, len(values) - 1))
        return make_pipeline(
            StandardScaler(),
            LocalOutlierFactor(
                n_neighbors=neighbors,
                novelty=True,
                contamination=contamination,
            ),
        ).fit(x)
    raise ValueError(f"Unknown one-class baseline method: {method}")


def _predict_one_class_anomalies(model, values: np.ndarray, sensor: SensorConfig) -> np.ndarray:
    finite = np.isfinite(values)
    physical = (sensor.physical_min <= values) & (values <= sensor.physical_max)
    anomalies = ~(finite & physical)
    if model is None:
        return anomalies
    valid = finite & physical
    if np.any(valid):
        predictions = model.predict(values[valid].reshape(-1, 1))
        anomalies[valid] = predictions == -1
    return anomalies


def _authorize_from_trusted(
    sensor: SensorConfig,
    trusted: float,
    violations: int,
) -> tuple[bool, int]:
    if not np.isfinite(trusted):
        return False, 0
    violation = trusted < sensor.control_low or trusted > sensor.control_high
    violations = violations + 1 if violation else 0
    if violations >= sensor.confirm_samples:
        return True, 0
    return False, violations
