from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

import pandas as pd

from aasvr.baselines import BaselineConfig
from aasvr.config import load_aasvr_config, load_yaml
from aasvr.evaluation import compute_metrics
from aasvr.fault_injection import FaultSpec, inject_fault
from aasvr.pipeline import run_aasvr_with_config, run_baseline_on_frame
from aasvr.prepare import HYDRO_PRIMARY_SENSORS

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--toy", action="store_true", help="Compute metrics for toy decisions.")
    parser.add_argument("--hydro-exp1", action="store_true", help="Compute metrics for hydroponic Experiment 1.")
    parser.add_argument(
        "--dataset",
        choices=[
            "hydro_exp1",
            "tep",
            "tep_csv",
            "wur",
            "hai",
            "skab",
            "metropt3",
            "batadal",
            "swat",
            "wadi",
            "damadics",
        ],
        help="Compute metrics for a prepared real/external dataset.",
    )
    args = parser.parse_args()
    if args.hydro_exp1 or args.dataset == "hydro_exp1":
        compute_hydro_exp1()
        return
    if args.dataset:
        compute_prepared_dataset(args.dataset)
        return
    if not args.toy:
        print("Use --toy, --hydro-exp1, or --dataset hydro_exp1.")
        return
    decisions_path = ROOT / "results/metrics/toy_aasvr_decisions.csv"
    if not decisions_path.exists():
        from scripts_compat import run_methods_toy

        run_methods_toy()
    decisions = pd.read_csv(decisions_path)
    labels_path = ROOT / "data/synthetic/toy_fault_labels.csv"
    labels = pd.read_csv(labels_path) if labels_path.exists() else None
    metrics = compute_metrics(decisions, labels)
    out = ROOT / "results/metrics/toy_summary.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([metrics.__dict__]).to_csv(out, index=False)
    print(f"Wrote {out}")


def compute_hydro_exp1() -> None:
    labels_path = ROOT / "data/processed/hydro_exp1_rule_labels.parquet"
    if not labels_path.exists():
        raise SystemExit("Missing hydro_exp1 labels; run scripts/02_prepare_datasets.py --hydro-exp1.")
    labels = pd.read_parquet(labels_path)
    out_dir = ROOT / "results/metrics"
    rows = []
    for path in sorted(out_dir.glob("hydro_exp1_*_decisions.csv")):
        method = path.name.removeprefix("hydro_exp1_").removesuffix("_decisions.csv")
        decisions = pd.read_csv(path)
        prediction_mode = "gate_reject" if method in {"aasvr", "aasvr_r", "aasvr_r2"} else "auto"
        metrics = compute_metrics(decisions, labels, prediction_mode=prediction_mode)
        row = {"dataset": "hydro_exp1", "method": method}
        row.update(metrics.__dict__)
        rows.append(row)
    if not rows:
        raise SystemExit("Missing hydro_exp1 decisions; run scripts/04_run_methods.py --hydro-exp1.")
    out = out_dir / "hydro_exp1_summary.csv"
    pd.DataFrame(rows).sort_values(["dataset", "method"]).to_csv(out, index=False)
    print(f"Wrote {out}")
    compute_hydro_exp1_synthetic()


def compute_hydro_exp1_synthetic() -> None:
    frame_path = ROOT / "data/processed/hydro_exp1_measurements.parquet"
    grid_path = ROOT / "data/synthetic/hydro_exp1_fault_grid.csv"
    if not frame_path.exists():
        raise SystemExit("Missing processed hydro_exp1 data; run scripts/02_prepare_datasets.py --hydro-exp1.")
    if not grid_path.exists():
        raise SystemExit("Missing hydro_exp1 fault grid; run scripts/05_inject_faults.py --hydro-exp1.")

    frame = pd.read_parquet(frame_path)[["timestamp", *HYDRO_PRIMARY_SENSORS]].copy()
    grid = pd.read_csv(grid_path)
    config = load_aasvr_config(ROOT / "configs/methods/aasvr.yaml")
    sensors = tuple(sensor for sensor in config.sensors if sensor.name in HYDRO_PRIMARY_SENSORS)
    from aasvr.core import AASVRConfig

    r2_sensors = _calibrated_sensors(frame, sensors)
    r2_config = AASVRConfig(
        sensors=r2_sensors,
        q_min=config.q_min,
        scale_multiplier=config.scale_multiplier,
        transient_limit=config.transient_limit,
        persistent_limit=config.persistent_limit,
        rectification_mode=config.rectification_mode,
        eta_decay=config.eta_decay,
        eta_min_low=config.eta_min_low,
        eta_min_medium=config.eta_min_medium,
        eta_min_high=config.eta_min_high,
        enable_response_residual=True,
        response_mode="sequential",
        reliability_mode="beta",
        beta_prior_success=config.beta_prior_success,
        beta_prior_failure=config.beta_prior_failure,
        beta_lcb_z=config.beta_lcb_z,
        compact_diagnostics=True,
    )
    response_config = AASVRConfig(
        sensors=sensors,
        q_min=config.q_min,
        scale_multiplier=config.scale_multiplier,
        transient_limit=config.transient_limit,
        persistent_limit=config.persistent_limit,
        rectification_mode=config.rectification_mode,
        eta_decay=config.eta_decay,
        eta_min_low=config.eta_min_low,
        eta_min_medium=config.eta_min_medium,
        eta_min_high=config.eta_min_high,
        enable_response_residual=config.enable_response_residual,
        response_mode=config.response_mode,
        reliability_mode=config.reliability_mode,
        beta_prior_success=config.beta_prior_success,
        beta_prior_failure=config.beta_prior_failure,
        beta_lcb_z=config.beta_lcb_z,
        compact_diagnostics=config.compact_diagnostics,
    )
    base_config = AASVRConfig(
        sensors=tuple(replace(sensor, response_window=0) for sensor in sensors),
        q_min=config.q_min,
        scale_multiplier=config.scale_multiplier,
        transient_limit=config.transient_limit,
        persistent_limit=config.persistent_limit,
        rectification_mode=config.rectification_mode,
        eta_decay=config.eta_decay,
        eta_min_low=0.0,
        eta_min_medium=0.0,
        eta_min_high=0.0,
        enable_response_residual=False,
    )
    baselines = load_yaml(ROOT / "configs/methods/baselines.yaml")["required"]
    baseline_configs = _load_tuned_baseline_configs()
    methods = ["aasvr_r2", "aasvr_r", "aasvr", *baselines]
    rows = []
    half_window_before = 90
    half_window_after = 120
    for trial in grid.itertuples(index=False):
        split = getattr(trial, "split", "test")
        if split != "test":
            continue
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
        for method in methods:
            if method == "aasvr_r2":
                decisions = run_aasvr_with_config(faulted, r2_config)
                prediction_mode = "gate_reject"
            elif method == "aasvr_r":
                decisions = run_aasvr_with_config(faulted, response_config)
                prediction_mode = "gate_reject"
            elif method == "aasvr":
                decisions = run_aasvr_with_config(faulted, base_config)
                prediction_mode = "gate_reject"
            else:
                decisions = run_baseline_on_frame(
                    faulted,
                    sensors,
                    method,
                    config=baseline_configs.get(method),
                )
                prediction_mode = "auto"
            metrics = compute_metrics(decisions, labels, prediction_mode=prediction_mode)
            row = {
                "dataset": "hydro_exp1",
                "trial_id": trial.trial_id,
                "split": split,
                "fault_protocol_id": getattr(trial, "fault_protocol_id", ""),
                "sensor": trial.sensor,
                "fault_type": trial.fault_type,
                "duration": int(trial.duration),
                "magnitude": float(trial.magnitude),
                "method": method,
            }
            row.update(metrics.__dict__)
            rows.append(row)
    detail = pd.DataFrame(rows)
    out_dir = ROOT / "results/metrics"
    detail_path = out_dir / "hydro_exp1_synthetic_detail.csv"
    summary_path = out_dir / "hydro_exp1_synthetic_summary.csv"
    fault_type_path = out_dir / "hydro_exp1_synthetic_by_fault_type.csv"
    detail.to_csv(detail_path, index=False)
    metric_cols = [
        "precision",
        "recall",
        "f1",
        "specificity",
        "balanced_accuracy",
        "false_positive_rate",
        "false_negative_rate",
        "event_recall",
        "mean_detection_delay_samples",
        "false_alarm_events",
        "false_actuations",
        "missed_actuations",
        "unsafe_samples",
        "decision_count",
        "unsafe_rate",
        "missed_authorization_rate",
        "alerts",
    ]
    summary = detail.groupby("method", as_index=False)[metric_cols].mean()
    counts = (
        detail.groupby("method", as_index=False)["trial_id"]
        .nunique()
        .rename(columns={"trial_id": "n_trials"})
    )
    false_actuation_sd = (
        detail.groupby("method", as_index=False)["false_actuations"]
        .std(ddof=1)
        .rename(columns={"false_actuations": "false_actuations_sd"})
    )
    (
        summary.merge(counts, on="method", how="left")
        .merge(false_actuation_sd, on="method", how="left")
        .sort_values("balanced_accuracy", ascending=False)
        .to_csv(summary_path, index=False)
    )
    by_fault = detail.groupby(["method", "fault_type"], as_index=False)[metric_cols].mean()
    fault_counts = (
        detail.groupby(["method", "fault_type"], as_index=False)["trial_id"]
        .nunique()
        .rename(columns={"trial_id": "n_trials"})
    )
    by_fault.merge(fault_counts, on=["method", "fault_type"], how="left").sort_values(
        ["fault_type", "balanced_accuracy"], ascending=[True, False]
    ).to_csv(fault_type_path, index=False)
    print(f"Wrote {detail_path}")
    print(f"Wrote {summary_path}")
    print(f"Wrote {fault_type_path}")


def _load_tuned_baseline_configs() -> dict[str, BaselineConfig]:
    path = ROOT / "results/metrics/hydro_exp1_baseline_tuning_best.csv"
    if not path.exists():
        return {}
    frame = pd.read_csv(path)
    configs = {}
    valid = BaselineConfig.__dataclass_fields__.keys()
    for row in frame.to_dict(orient="records"):
        kwargs = {
            key: value
            for key, value in row.items()
            if key in valid and pd.notna(value)
        }
        if "method" in kwargs:
            configs[str(kwargs["method"])] = BaselineConfig(**kwargs)
    return configs


def _calibrated_sensors(frame: pd.DataFrame, sensors: tuple) -> tuple:
    calibration = frame.iloc[: max(200, int(len(frame) * 0.20))]
    out = []
    for sensor in sensors:
        values = pd.to_numeric(calibration[sensor.name], errors="coerce")
        deltas = values.diff().abs().dropna()
        calibrated = None
        if not deltas.empty:
            calibrated = float(max(sensor.xi_min, sensor.uncertainty, deltas.quantile(0.995)))
        out.append(replace(sensor, calibrated_xi=calibrated))
    return tuple(out)


def compute_prepared_dataset(dataset: str) -> None:
    labels_path = ROOT / f"data/processed/{dataset}_labels.parquet"
    if not labels_path.exists():
        print(f"Skipping {dataset}; prepared labels are not available.")
        return
    labels = pd.read_parquet(labels_path)
    out_dir = ROOT / "results/metrics"
    rows = []
    for path in sorted(out_dir.glob(f"{dataset}_*_decisions.csv")):
        method = path.name.removeprefix(f"{dataset}_").removesuffix("_decisions.csv")
        decisions = pd.read_csv(path)
        prediction_mode = "gate_reject" if method in {"aasvr", "aasvr_r", "aasvr_r2"} else "auto"
        metrics = compute_metrics(decisions, labels, prediction_mode=prediction_mode)
        row = {"dataset": dataset, "method": method}
        row.update(metrics.__dict__)
        rows.append(row)
    if not rows:
        print(f"Skipping {dataset}; no method decisions are available.")
        return
    out = out_dir / f"{dataset}_summary.csv"
    pd.DataFrame(rows).sort_values(["dataset", "method"]).to_csv(out, index=False)
    print(f"Wrote {out}")
    if _has_timestamp_level_labels(labels):
        native_out = out_dir / f"{dataset}_native_event_summary.csv"
        _compute_timestamp_fraction_summary(dataset, labels, threshold=0.30).to_csv(native_out, index=False)
        print(f"Wrote {native_out}")


def _has_timestamp_level_labels(labels: pd.DataFrame) -> bool:
    return "sensor" in labels and labels["sensor"].fillna("").astype(str).str.len().eq(0).all()


def _compute_timestamp_fraction_summary(
    dataset: str,
    labels: pd.DataFrame,
    *,
    threshold: float,
) -> pd.DataFrame:
    actual = (
        labels.assign(timestamp=labels["timestamp"].astype(str))
        .groupby("timestamp")["fault"]
        .max()
        .astype(bool)
    )
    rows = []
    out_dir = ROOT / "results/metrics"
    for path in sorted(out_dir.glob(f"{dataset}_*_decisions.csv")):
        method = path.name.removeprefix(f"{dataset}_").removesuffix("_decisions.csv")
        decisions = pd.read_csv(path)
        if method in {"aasvr", "aasvr_r", "aasvr_r2"}:
            flag = decisions.get("gate_result", pd.Series("", index=decisions.index)).eq("reject")
        else:
            flag = decisions.get("alert", pd.Series(False, index=decisions.index)).astype(bool)
        scores = (
            decisions.assign(predicted=flag)
            .groupby(decisions["timestamp"].astype(str))["predicted"]
            .mean()
            .reindex(actual.index)
            .fillna(False)
        )
        predicted = scores >= threshold
        row = _classification_row(actual, predicted)
        row.update(
            {
                "dataset": dataset,
                "method": method,
                "evaluation_unit": "timestamp",
                "aggregation": "sensor_fraction",
                "threshold": threshold,
            }
        )
        rows.append(row)
    return pd.DataFrame(rows).sort_values("balanced_accuracy", ascending=False)


def _classification_row(actual: pd.Series, predicted: pd.Series) -> dict[str, float]:
    actual = actual.astype(bool)
    predicted = predicted.astype(bool)
    tp = int((predicted & actual).sum())
    fp = int((predicted & ~actual).sum())
    fn = int((~predicted & actual).sum())
    tn = int((~predicted & ~actual).sum())
    precision = _safe_div(tp, tp + fp)
    recall = _safe_div(tp, tp + fn)
    specificity = _safe_div(tn, tn + fp)
    return {
        "precision": precision,
        "recall": recall,
        "f1": _safe_div(2 * precision * recall, precision + recall),
        "specificity": specificity,
        "balanced_accuracy": (recall + specificity) / 2,
        "false_positive_rate": _safe_div(fp, fp + tn),
        "false_negative_rate": _safe_div(fn, fn + tp),
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "true_negative": tn,
    }


def _safe_div(num: float, den: float) -> float:
    return float(num / den) if den else 0.0


if __name__ == "__main__":
    main()
