from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest, rankdata, wilcoxon

ROOT = Path(__file__).resolve().parents[1]
METRICS = [
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
    "alerts",
]
REFERENCE_METHOD = "aasvr_r"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hydro-exp1", action="store_true", help="Analyze hydro Exp. 1 synthetic results.")
    parser.add_argument("--bootstrap", type=int, default=1000, help="Bootstrap resamples.")
    args = parser.parse_args()
    if not args.hydro_exp1:
        print("Use --hydro-exp1.")
        return
    analyze_hydro_exp1(bootstrap=args.bootstrap)


def analyze_hydro_exp1(*, bootstrap: int) -> None:
    detail_path = ROOT / "results/metrics/hydro_exp1_synthetic_detail.csv"
    if not detail_path.exists():
        raise SystemExit("Missing synthetic detail; run scripts/06_compute_metrics.py --hydro-exp1.")
    detail = pd.read_csv(detail_path)
    out_dir = ROOT / "results/metrics"
    out_dir.mkdir(parents=True, exist_ok=True)

    _bootstrap_ci(detail, bootstrap=bootstrap).to_csv(
        out_dir / "hydro_exp1_bootstrap_ci.csv", index=False
    )
    _method_ranks(detail).to_csv(out_dir / "hydro_exp1_method_ranks.csv", index=False)
    _paired_tests(detail).to_csv(out_dir / "hydro_exp1_paired_tests.csv", index=False)
    _paired_effects(detail, bootstrap=bootstrap).to_csv(
        out_dir / "hydro_exp1_paired_effects.csv", index=False
    )
    _fault_grid_tests(detail).to_csv(out_dir / "hydro_exp1_fault_grid_tests.csv", index=False)
    _group_summary(detail, ["method", "sensor"]).to_csv(
        out_dir / "hydro_exp1_synthetic_by_sensor.csv", index=False
    )
    _group_summary(detail, ["method", "sensor", "fault_type"]).to_csv(
        out_dir / "hydro_exp1_synthetic_by_sensor_fault_type.csv", index=False
    )
    _aasvr_group_ci(detail, ["sensor"], bootstrap=bootstrap).to_csv(
        out_dir / "hydro_exp1_aasvr_by_sensor_ci.csv", index=False
    )
    _aasvr_group_ci(detail, ["fault_type"], bootstrap=bootstrap).to_csv(
        out_dir / "hydro_exp1_aasvr_by_fault_type_ci.csv", index=False
    )
    print(f"Wrote {out_dir / 'hydro_exp1_bootstrap_ci.csv'}")
    print(f"Wrote {out_dir / 'hydro_exp1_method_ranks.csv'}")
    print(f"Wrote {out_dir / 'hydro_exp1_paired_tests.csv'}")
    print(f"Wrote {out_dir / 'hydro_exp1_paired_effects.csv'}")
    print(f"Wrote {out_dir / 'hydro_exp1_fault_grid_tests.csv'}")
    print(f"Wrote {out_dir / 'hydro_exp1_synthetic_by_sensor.csv'}")
    print(f"Wrote {out_dir / 'hydro_exp1_synthetic_by_sensor_fault_type.csv'}")
    print(f"Wrote {out_dir / 'hydro_exp1_aasvr_by_sensor_ci.csv'}")
    print(f"Wrote {out_dir / 'hydro_exp1_aasvr_by_fault_type_ci.csv'}")


def _bootstrap_ci(detail: pd.DataFrame, *, bootstrap: int) -> pd.DataFrame:
    rng = np.random.default_rng(20260518)
    trial_ids = detail["trial_id"].drop_duplicates().to_numpy()
    rows = []
    for method, method_frame in detail.groupby("method"):
        trial_lookup = {trial_id: group for trial_id, group in method_frame.groupby("trial_id")}
        estimates = {metric: [] for metric in METRICS if metric in method_frame.columns}
        for _ in range(bootstrap):
            sample_ids = rng.choice(trial_ids, size=len(trial_ids), replace=True)
            sample = pd.concat([trial_lookup[trial_id] for trial_id in sample_ids], ignore_index=True)
            for metric in estimates:
                estimates[metric].append(float(sample[metric].mean()))
        for metric, values in estimates.items():
            arr = np.asarray(values, dtype=float)
            rows.append(
                {
                    "method": method,
                    "metric": metric,
                    "mean": float(method_frame[metric].mean()),
                    "ci_low": float(np.quantile(arr, 0.025)),
                    "ci_high": float(np.quantile(arr, 0.975)),
                    "bootstrap_samples": bootstrap,
                }
            )
    return pd.DataFrame(rows).sort_values(["metric", "mean"], ascending=[True, False])


def _method_ranks(detail: pd.DataFrame) -> pd.DataFrame:
    rank_specs = {
        "balanced_accuracy": False,
        "recall": False,
        "specificity": False,
        "false_actuations": True,
        "false_alarm_events": True,
        "alerts": True,
    }
    rows = []
    for trial_id, trial_frame in detail.groupby("trial_id"):
        for metric, ascending in rank_specs.items():
            ranked = trial_frame[["method", metric]].copy()
            ranked["rank"] = ranked[metric].rank(method="average", ascending=ascending)
            ranked["trial_id"] = trial_id
            ranked["metric"] = metric
            rows.append(ranked[["trial_id", "method", "metric", "rank"]])
    ranks = pd.concat(rows, ignore_index=True)
    summary = (
        ranks.groupby(["method", "metric"], as_index=False)["rank"]
        .mean()
        .rename(columns={"rank": "mean_rank"})
    )
    return summary.sort_values(["metric", "mean_rank"])


def _group_summary(detail: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    available = [metric for metric in METRICS if metric in detail.columns]
    summary = (
        detail.groupby(group_cols, as_index=False)[available]
        .mean()
        .sort_values([*group_cols[:-1], "balanced_accuracy"], ascending=[*[True] * (len(group_cols) - 1), False])
    )
    counts = (
        detail.groupby(group_cols, as_index=False)["trial_id"]
        .nunique()
        .rename(columns={"trial_id": "n_trials"})
    )
    return summary.merge(counts, on=group_cols, how="left")


def _aasvr_group_ci(detail: pd.DataFrame, group_cols: list[str], *, bootstrap: int) -> pd.DataFrame:
    aasvr = detail[detail["method"].eq(REFERENCE_METHOD)].copy()
    rows = []
    for keys, group in aasvr.groupby(group_cols):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(group_cols, keys, strict=False))
        for metric in ("balanced_accuracy", "recall", "specificity", "false_actuations"):
            low, high = _bootstrap_mean_ci(group[metric].to_numpy(dtype=float), bootstrap=bootstrap)
            row[metric] = float(group[metric].mean())
            row[f"{metric}_ci_low"] = low
            row[f"{metric}_ci_high"] = high
            row[f"{metric}_n_trials"] = int(len(group))
        rows.append(row)
    return pd.DataFrame(rows).sort_values(group_cols)


def _paired_tests(detail: pd.DataFrame) -> pd.DataFrame:
    metrics = {
        "balanced_accuracy": "greater",
        "false_actuations": "less",
    }
    rows = []
    for metric, alternative in metrics.items():
        pivot = detail.pivot_table(index="trial_id", columns="method", values=metric, aggfunc="mean")
        if REFERENCE_METHOD not in pivot:
            continue
        for method in pivot.columns:
            if method == REFERENCE_METHOD:
                continue
            paired = pivot[[REFERENCE_METHOD, method]].dropna()
            if len(paired) < 3:
                continue
            stat, p_value = _safe_wilcoxon(
                paired[REFERENCE_METHOD].to_numpy(),
                paired[method].to_numpy(),
                alternative=alternative,
            )
            rows.append(
                {
                    "metric": metric,
                    "comparison": f"{REFERENCE_METHOD}_vs_{method}",
                    "alternative": alternative,
                    "n_pairs": len(paired),
                    "statistic": stat,
                    "p_value": p_value,
                }
            )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["p_holm"] = _holm(out["p_value"].to_numpy())
    family_sizes = out.groupby("metric")["comparison"].transform("count")
    out["holm_family_size"] = family_sizes
    return out.sort_values(["metric", "p_holm"])


def _paired_effects(detail: pd.DataFrame, *, bootstrap: int) -> pd.DataFrame:
    tests = _paired_tests(detail)
    if tests.empty:
        return tests
    ba_tests = _test_lookup(tests, "balanced_accuracy")
    fa_tests = _test_lookup(tests, "false_actuations")
    pivot_ba = detail.pivot_table(index="trial_id", columns="method", values="balanced_accuracy", aggfunc="mean")
    pivot_fa = detail.pivot_table(index="trial_id", columns="method", values="false_actuations", aggfunc="mean")
    rows = []
    for method in sorted(set(pivot_ba.columns).intersection(pivot_fa.columns) - {REFERENCE_METHOD}):
        paired_ba = pivot_ba[[REFERENCE_METHOD, method]].dropna()
        paired_fa = pivot_fa[[REFERENCE_METHOD, method]].dropna()
        if paired_ba.empty or paired_fa.empty:
            continue
        delta_ba = paired_ba[REFERENCE_METHOD] - paired_ba[method]
        delta_fa = paired_fa[method] - paired_fa[REFERENCE_METHOD]
        ci_low, ci_high = _bootstrap_mean_ci(delta_fa.to_numpy(), bootstrap=bootstrap)
        median_low, median_high = _bootstrap_median_ci(delta_fa.to_numpy(), bootstrap=bootstrap)
        nonzero_fa = delta_fa[~np.isclose(delta_fa, 0.0)]
        positive_fa = int((nonzero_fa > 0).sum())
        sign_p = (
            float(binomtest(positive_fa, len(nonzero_fa), 0.5, alternative="greater").pvalue)
            if len(nonzero_fa)
            else 1.0
        )
        rows.append(
            {
                "method": method,
                "n_pairs": int(min(len(paired_ba), len(paired_fa))),
                "delta_balanced_accuracy_aasvr_minus_method": float(delta_ba.mean()),
                "median_delta_balanced_accuracy": float(delta_ba.median()),
                "sd_delta_balanced_accuracy": float(delta_ba.std(ddof=1)),
                "rank_biserial_balanced_accuracy": _rank_biserial(delta_ba.to_numpy()),
                "cohen_dz_balanced_accuracy": _cohen_dz(delta_ba.to_numpy()),
                "p_holm_balanced_accuracy": ba_tests.get(method, float("nan")),
                "delta_false_actuations_method_minus_aasvr": float(delta_fa.mean()),
                "median_delta_false_actuations": float(delta_fa.median()),
                "delta_false_actuations_ci_low": ci_low,
                "delta_false_actuations_ci_high": ci_high,
                "median_delta_false_actuations_ci_low": median_low,
                "median_delta_false_actuations_ci_high": median_high,
                "rank_biserial_false_actuations": _rank_biserial(delta_fa.to_numpy()),
                "cohen_dz_false_actuations": _cohen_dz(delta_fa.to_numpy()),
                "sign_test_p_false_actuations": sign_p,
                "p_holm_false_actuations": fa_tests.get(method, float("nan")),
            }
        )
    out = pd.DataFrame(rows).sort_values(
        "delta_false_actuations_method_minus_aasvr", ascending=False
    )
    if not out.empty:
        out["sign_test_p_holm_false_actuations"] = _holm(
            out["sign_test_p_false_actuations"].to_numpy(dtype=float)
        )
    return out


def _test_lookup(tests: pd.DataFrame, metric: str) -> dict[str, float]:
    subset = tests[tests["metric"].eq(metric)]
    out = {}
    prefix = f"{REFERENCE_METHOD}_vs_"
    for row in subset.to_dict(orient="records"):
        comparison = str(row["comparison"])
        if comparison.startswith(prefix):
            out[comparison.removeprefix(prefix)] = float(row["p_holm"])
    return out


def _bootstrap_mean_ci(values: np.ndarray, *, bootstrap: int) -> tuple[float, float]:
    finite = values[np.isfinite(values)]
    if len(finite) == 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(20260518)
    estimates = []
    for _ in range(bootstrap):
        sample = rng.choice(finite, size=len(finite), replace=True)
        estimates.append(float(np.mean(sample)))
    arr = np.asarray(estimates, dtype=float)
    return float(np.quantile(arr, 0.025)), float(np.quantile(arr, 0.975))


def _bootstrap_median_ci(values: np.ndarray, *, bootstrap: int) -> tuple[float, float]:
    finite = values[np.isfinite(values)]
    if len(finite) == 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(20260519)
    estimates = []
    for _ in range(bootstrap):
        sample = rng.choice(finite, size=len(finite), replace=True)
        estimates.append(float(np.median(sample)))
    arr = np.asarray(estimates, dtype=float)
    return float(np.quantile(arr, 0.025)), float(np.quantile(arr, 0.975))


def _rank_biserial(values: np.ndarray) -> float:
    finite = values[np.isfinite(values)]
    finite = finite[~np.isclose(finite, 0.0)]
    if len(finite) == 0:
        return 0.0
    ranks = rankdata(np.abs(finite))
    total = float(ranks.sum())
    positive = float(ranks[finite > 0].sum())
    negative = float(ranks[finite < 0].sum())
    return (positive - negative) / total if total else 0.0


def _cohen_dz(values: np.ndarray) -> float:
    finite = values[np.isfinite(values)]
    if len(finite) < 2:
        return float("nan")
    std = float(np.std(finite, ddof=1))
    if std <= 0:
        return 0.0
    return float(np.mean(finite) / std)


def _fault_grid_tests(detail: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (sensor, fault_type), group in detail.groupby(["sensor", "fault_type"]):
        pivot = group.pivot_table(index="trial_id", columns="method", values="balanced_accuracy", aggfunc="mean")
        if REFERENCE_METHOD not in pivot:
            continue
        for method in pivot.columns:
            if method == REFERENCE_METHOD:
                continue
            paired = pivot[[REFERENCE_METHOD, method]].dropna()
            if len(paired) < 3:
                continue
            stat, p_value = _safe_wilcoxon(
                paired[REFERENCE_METHOD].to_numpy(),
                paired[method].to_numpy(),
                alternative="greater",
            )
            rows.append(
                {
                    "sensor": sensor,
                    "fault_type": fault_type,
                    "comparison": f"{REFERENCE_METHOD}_vs_{method}",
                    "n_pairs": len(paired),
                    "statistic": stat,
                    "p_value": p_value,
                }
            )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["p_bh"] = _benjamini_hochberg(out["p_value"].to_numpy())
    return out.sort_values(["sensor", "fault_type", "p_bh"])


def _safe_wilcoxon(x: np.ndarray, y: np.ndarray, *, alternative: str) -> tuple[float, float]:
    diff = x - y
    if np.allclose(diff, 0):
        return 0.0, 1.0
    result = wilcoxon(x, y, alternative=alternative, zero_method="wilcox")
    return float(result.statistic), float(result.pvalue)


def _holm(p_values: np.ndarray) -> np.ndarray:
    order = np.argsort(p_values)
    adjusted = np.empty_like(p_values, dtype=float)
    running = 0.0
    m = len(p_values)
    for rank, idx in enumerate(order):
        value = min(1.0, (m - rank) * p_values[idx])
        running = max(running, value)
        adjusted[idx] = running
    return adjusted


def _benjamini_hochberg(p_values: np.ndarray) -> np.ndarray:
    order = np.argsort(p_values)[::-1]
    adjusted = np.empty_like(p_values, dtype=float)
    running = 1.0
    m = len(p_values)
    for rank, idx in enumerate(order, start=1):
        value = min(running, p_values[idx] * m / (m - rank + 1))
        running = value
        adjusted[idx] = value
    return adjusted


if __name__ == "__main__":
    main()
