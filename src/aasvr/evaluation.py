from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Metrics:
    precision: float
    recall: float
    f1: float
    specificity: float
    balanced_accuracy: float
    false_positive_rate: float
    false_negative_rate: float
    false_actuations: int
    missed_actuations: int
    unsafe_samples: int
    event_recall: float
    mean_detection_delay_samples: float
    false_alarm_events: int
    alerts: int


def compute_metrics(
    decisions: pd.DataFrame,
    labels: pd.DataFrame | None = None,
    *,
    prediction_mode: str = "auto",
) -> Metrics:
    predicted = _prediction_series(decisions, prediction_mode=prediction_mode).to_numpy(dtype=bool)
    if labels is None:
        actual = np.zeros_like(predicted, dtype=bool)
    else:
        actual = _align_labels(decisions, labels)
        predicted = predicted[: len(actual)]
    tp = int(np.sum(predicted & actual))
    fp = int(np.sum(predicted & ~actual))
    fn = int(np.sum(~predicted & actual))
    tn = int(np.sum(~predicted & ~actual))
    precision = _safe_div(tp, tp + fp)
    recall = _safe_div(tp, tp + fn)
    specificity = _safe_div(tn, tn + fp)
    event_recall, mean_delay, false_alarm_events = _event_metrics(predicted, actual)
    false_actuations = _false_actuations(decisions, actual)
    missed_actuations = _missed_actuations(decisions, actual)
    return Metrics(
        precision=precision,
        recall=recall,
        f1=_safe_div(2 * precision * recall, precision + recall),
        specificity=specificity,
        balanced_accuracy=(recall + specificity) / 2,
        false_positive_rate=_safe_div(fp, fp + tn),
        false_negative_rate=_safe_div(fn, fn + tp),
        false_actuations=false_actuations,
        missed_actuations=missed_actuations,
        unsafe_samples=int(decisions.get("unsafe_band", pd.Series(False, index=decisions.index)).sum()),
        event_recall=event_recall,
        mean_detection_delay_samples=mean_delay,
        false_alarm_events=false_alarm_events,
        alerts=int(decisions["alert"].sum()),
    )


def _safe_div(num: float, den: float) -> float:
    return float(num / den) if den else 0.0


def _prediction_series(decisions: pd.DataFrame, *, prediction_mode: str = "auto") -> pd.Series:
    if prediction_mode == "alert":
        return decisions.get("alert", pd.Series(False, index=decisions.index)).astype(bool)
    if prediction_mode == "gate_reject":
        return decisions.get("gate_result", pd.Series("", index=decisions.index)).eq("reject")
    if "alert" in decisions:
        return decisions["alert"].astype(bool)
    if "gate_result" in decisions:
        return decisions["gate_result"].eq("reject")
    return pd.Series(False, index=decisions.index)


def _align_labels(decisions: pd.DataFrame, labels: pd.DataFrame) -> np.ndarray:
    if {"timestamp", "sensor"}.issubset(decisions.columns) and {"timestamp", "sensor"}.issubset(
        labels.columns
    ):
        keyed = labels.copy()
        keyed["timestamp"] = keyed["timestamp"].astype(str)
        keyed["sensor"] = keyed["sensor"].astype(str)
        fault_map = {
            (row.timestamp, row.sensor): bool(row.fault)
            for row in keyed[["timestamp", "sensor", "fault"]].itertuples(index=False)
        }
        return np.asarray(
            [
                fault_map.get((str(row.timestamp), str(row.sensor)), False)
                for row in decisions[["timestamp", "sensor"]].itertuples(index=False)
            ],
            dtype=bool,
        )
    if "timestamp" in decisions.columns and "timestamp" in labels.columns:
        keyed = labels.copy()
        keyed["timestamp"] = keyed["timestamp"].astype(str)
        by_time = keyed.groupby("timestamp")["fault"].max().to_dict()
        return decisions["timestamp"].astype(str).map(by_time).fillna(False).to_numpy(dtype=bool)
    actual = labels["fault"].astype(bool).to_numpy()
    if len(actual) < len(decisions):
        actual = np.pad(actual, (0, len(decisions) - len(actual)), constant_values=False)
    return actual[: len(decisions)]


def _event_metrics(predicted: np.ndarray, actual: np.ndarray) -> tuple[float, float, int]:
    actual_events = _runs(actual)
    predicted_events = _runs(predicted)
    detected = 0
    delays: list[int] = []
    matched_predictions: set[int] = set()
    for start, end in actual_events:
        hits = np.flatnonzero(predicted[start : end + 1])
        if len(hits):
            detected += 1
            delays.append(int(hits[0]))
            for idx, (pred_start, pred_end) in enumerate(predicted_events):
                if pred_start <= start + hits[0] <= pred_end:
                    matched_predictions.add(idx)
                    break
    false_alarm_events = len(predicted_events) - len(matched_predictions)
    return (
        _safe_div(detected, len(actual_events)),
        float(np.mean(delays)) if delays else 0.0,
        false_alarm_events,
    )


def _runs(mask: np.ndarray) -> list[tuple[int, int]]:
    runs: list[tuple[int, int]] = []
    start: int | None = None
    for idx, value in enumerate(mask):
        if value and start is None:
            start = idx
        elif not value and start is not None:
            runs.append((start, idx - 1))
            start = None
    if start is not None:
        runs.append((start, len(mask) - 1))
    return runs


def _false_actuations(decisions: pd.DataFrame, actual: np.ndarray) -> int:
    if "actuation_authorized" not in decisions:
        return 0
    auth = decisions["actuation_authorized"].astype(bool).to_numpy()[: len(actual)]
    return int(np.sum(auth & actual))


def _missed_actuations(decisions: pd.DataFrame, actual: np.ndarray) -> int:
    if "unsafe_band" not in decisions or "actuation_authorized" not in decisions:
        return 0
    unsafe = decisions["unsafe_band"].astype(bool).to_numpy()[: len(actual)]
    auth = decisions["actuation_authorized"].astype(bool).to_numpy()[: len(actual)]
    return int(np.sum(unsafe & ~actual & ~auth))
