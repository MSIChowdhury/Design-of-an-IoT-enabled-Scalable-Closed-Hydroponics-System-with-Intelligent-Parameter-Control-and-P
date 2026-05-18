from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Metrics:
    precision: float
    recall: float
    f1: float
    false_positive_rate: float
    false_negative_rate: float
    false_actuations: int
    alerts: int


def compute_metrics(decisions: pd.DataFrame, labels: pd.DataFrame | None = None) -> Metrics:
    predicted = decisions["alert"].astype(bool).to_numpy()
    if labels is None:
        actual = np.zeros_like(predicted, dtype=bool)
    else:
        actual = labels["fault"].astype(bool).to_numpy()[: len(predicted)]
        predicted = predicted[: len(actual)]
    tp = int(np.sum(predicted & actual))
    fp = int(np.sum(predicted & ~actual))
    fn = int(np.sum(~predicted & actual))
    tn = int(np.sum(~predicted & ~actual))
    precision = _safe_div(tp, tp + fp)
    recall = _safe_div(tp, tp + fn)
    return Metrics(
        precision=precision,
        recall=recall,
        f1=_safe_div(2 * precision * recall, precision + recall),
        false_positive_rate=_safe_div(fp, fp + tn),
        false_negative_rate=_safe_div(fn, fn + tp),
        false_actuations=int(decisions["actuation_authorized"].sum()),
        alerts=int(decisions["alert"].sum()),
    )


def _safe_div(num: float, den: float) -> float:
    return float(num / den) if den else 0.0

