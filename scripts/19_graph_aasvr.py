from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

from aasvr.config import load_aasvr_config
from aasvr.core import AASVRConfig
from aasvr.evaluation import compute_metrics
from aasvr.fault_injection import FaultSpec, inject_fault
from aasvr.pipeline import run_aasvr_with_config, run_baseline_on_frame
from aasvr.prepare import HYDRO_PRIMARY_SENSORS

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class GraphModel:
    sensor: str
    neighbors: tuple[str, ...]
    model: object
    residual_sigma: float
    residual_floor: float


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hydro-exp1", action="store_true")
    args = parser.parse_args()
    if not args.hydro_exp1:
        print("Use --hydro-exp1.")
        return
    run()


def run() -> None:
    frame = pd.read_parquet(ROOT / "data/processed/hydro_exp1_measurements.parquet")[
        ["timestamp", *HYDRO_PRIMARY_SENSORS]
    ].copy()
    config = load_aasvr_config(ROOT / "configs/methods/aasvr.yaml")
    sensors = tuple(sensor for sensor in config.sensors if sensor.name in HYDRO_PRIMARY_SENSORS)
    aasvr_config = AASVRConfig(
        sensors=sensors,
        q_min=config.q_min,
        scale_multiplier=config.scale_multiplier,
        transient_limit=config.transient_limit,
        persistent_limit=config.persistent_limit,
        rectification_mode=config.rectification_mode,
    )
    sensor_floor = {sensor.name: max(sensor.uncertainty, sensor.xi_min) for sensor in sensors}
    graph_models = _fit_graph_models(frame, sensor_floor=sensor_floor)
    edges = [
        {"sensor": model.sensor, "neighbors": ";".join(model.neighbors), "residual_sigma": model.residual_sigma}
        for model in graph_models.values()
    ]

    grid = pd.read_csv(ROOT / "data/synthetic/hydro_exp1_fault_grid.csv")
    grid = grid[grid["split"].eq("test")].reset_index(drop=True)
    methods = ("aasvr", "graph_aasvr", "local_outlier_factor", "one_class_svm", "kalman", "hampel")
    rows = []
    half_window_before = 90
    half_window_after = 120
    for trial in grid.itertuples(index=False):
        global_start = int(trial.start)
        start = max(global_start - half_window_before, 0)
        end = min(global_start + int(trial.duration) + half_window_after, len(frame))
        local_start = global_start - start
        window = frame.iloc[start:end].reset_index(drop=True)
        spec = FaultSpec(
            sensor=trial.sensor,
            fault_type=trial.fault_type,
            start=local_start,
            duration=int(trial.duration),
            magnitude=float(trial.magnitude),
            seed=101,
        )
        faulted, labels = inject_fault(window, spec)
        aasvr_decisions = run_aasvr_with_config(faulted, aasvr_config)
        graph_decisions = _apply_graph_residuals(
            faulted,
            aasvr_decisions,
            graph_models,
            multiplier=4.0,
        )
        for method in methods:
            if method == "aasvr":
                decisions = aasvr_decisions
                prediction_mode = "gate_reject"
            elif method == "graph_aasvr":
                decisions = graph_decisions
                prediction_mode = "gate_reject"
            else:
                decisions = run_baseline_on_frame(faulted, sensors, method)
                prediction_mode = "auto"
            metrics = compute_metrics(decisions, labels, prediction_mode=prediction_mode)
            row = {
                "dataset": "hydro_exp1",
                "trial_id": trial.trial_id,
                "sensor": trial.sensor,
                "fault_type": trial.fault_type,
                "method": method,
            }
            row.update(metrics.__dict__)
            rows.append(row)
    detail = pd.DataFrame(rows)
    metric_cols = [
        "precision",
        "recall",
        "specificity",
        "balanced_accuracy",
        "false_positive_rate",
        "mean_detection_delay_samples",
        "false_alarm_events",
        "false_actuations",
        "alerts",
    ]
    summary = (
        detail.groupby("method", as_index=False)[metric_cols]
        .mean()
        .sort_values("balanced_accuracy", ascending=False)
    )
    by_fault = (
        detail.groupby(["method", "fault_type"], as_index=False)[metric_cols]
        .mean()
        .sort_values(["fault_type", "balanced_accuracy"], ascending=[True, False])
    )
    out_dir = ROOT / "results/metrics"
    out_dir.mkdir(parents=True, exist_ok=True)
    detail.to_csv(out_dir / "hydro_exp1_graph_aasvr_detail.csv", index=False)
    summary.to_csv(out_dir / "hydro_exp1_graph_aasvr_summary.csv", index=False)
    by_fault.to_csv(out_dir / "hydro_exp1_graph_aasvr_by_fault_type.csv", index=False)
    pd.DataFrame(edges).to_csv(out_dir / "hydro_exp1_graph_aasvr_edges.csv", index=False)
    print(f"Wrote {out_dir / 'hydro_exp1_graph_aasvr_summary.csv'}")


def _fit_graph_models(frame: pd.DataFrame, *, sensor_floor: dict[str, float]) -> dict[str, GraphModel]:
    calibration = frame.iloc[: max(200, int(len(frame) * 0.20))][list(HYDRO_PRIMARY_SENSORS)].copy()
    calibration = calibration.apply(pd.to_numeric, errors="coerce").dropna()
    corr = calibration.corr().abs()
    models: dict[str, GraphModel] = {}
    for sensor in HYDRO_PRIMARY_SENSORS:
        ranked = corr[sensor].drop(index=sensor).sort_values(ascending=False)
        neighbors = tuple(ranked[ranked >= 0.20].index[:3])
        if len(neighbors) < 2:
            neighbors = tuple(ranked.index[:2])
        train = calibration[[sensor, *neighbors]].dropna()
        if len(train) < 50:
            continue
        model = make_pipeline(StandardScaler(), Ridge(alpha=1.0))
        model.fit(train[list(neighbors)], train[sensor])
        predicted = model.predict(train[list(neighbors)])
        residuals = train[sensor].to_numpy(dtype=float) - predicted
        residual_sigma = _mad_sigma(residuals)
        models[sensor] = GraphModel(
            sensor=sensor,
            neighbors=neighbors,
            model=model,
            residual_sigma=residual_sigma,
            residual_floor=sensor_floor.get(sensor, 1e-6),
        )
    return models


def _apply_graph_residuals(
    frame: pd.DataFrame,
    decisions: pd.DataFrame,
    models: dict[str, GraphModel],
    *,
    multiplier: float,
) -> pd.DataFrame:
    out = decisions.copy()
    frame_values = frame.set_index("timestamp")
    last_trusted: dict[str, float] = {}
    for idx, row in out.iterrows():
        sensor = str(row["sensor"])
        model = models.get(sensor)
        if model is None:
            continue
        timestamp = row["timestamp"]
        if timestamp not in frame_values.index:
            continue
        sample = frame_values.loc[timestamp]
        if isinstance(sample, pd.DataFrame):
            sample = sample.iloc[0]
        values = pd.to_numeric(sample[list(model.neighbors)], errors="coerce")
        raw = pd.to_numeric(pd.Series([sample[sensor]]), errors="coerce").iloc[0]
        if not np.isfinite(raw) or values.isna().any():
            continue
        predicted = float(model.model.predict(pd.DataFrame([values.to_dict()]))[0])
        threshold = max(model.residual_floor, multiplier * model.residual_sigma)
        residual = abs(raw - predicted)
        if residual > threshold:
            out.at[idx, "gate_result"] = "reject"
            out.at[idx, "alert"] = True
            out.at[idx, "actuation_authorized"] = False
            out.at[idx, "trust_score"] = min(float(row.get("trust_score", 1.0)), 0.35)
            out.at[idx, "reason_codes"] = _append_reason(row.get("reason_codes", ()), "graph_residual")
            if sensor in last_trusted:
                out.at[idx, "trusted_value"] = last_trusted[sensor]
            out.at[idx, "rectification_action"] = "graph_hold"
        else:
            trusted = pd.to_numeric(pd.Series([out.at[idx, "trusted_value"]]), errors="coerce").iloc[0]
            if np.isfinite(trusted):
                last_trusted[sensor] = float(trusted)
    return out


def _append_reason(value: object, reason: str) -> tuple[str, ...]:
    if isinstance(value, tuple):
        items = list(value)
    elif isinstance(value, str):
        items = [item.strip(" '()") for item in value.split(",") if item.strip(" '()")]
    else:
        items = []
    if reason not in items:
        items.append(reason)
    return tuple(items)


def _mad_sigma(values: np.ndarray) -> float:
    finite = values[np.isfinite(values)]
    if len(finite) < 3:
        return 0.0
    median = float(np.median(finite))
    return float(1.4826 * np.median(np.abs(finite - median)))


if __name__ == "__main__":
    main()
