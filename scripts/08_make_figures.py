from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parents[1]

METHOD_LABELS = {
    "aasvr": "AASVR",
    "raw_threshold": "Raw threshold",
    "original": "Original",
    "moving_average": "Moving average",
    "moving_median": "Moving median",
    "hampel": "Hampel",
    "kalman": "Kalman",
    "ewma": "EWMA",
    "cusum": "CUSUM",
    "pca": "PCA",
    "isolation_forest": "Isolation Forest",
    "one_class_svm": "One-Class SVM",
    "local_outlier_factor": "LOF",
}

PALETTE = {
    "AASVR": "#0072B2",
    "Kalman": "#009E73",
    "PCA": "#E69F00",
    "Hampel": "#CC79A7",
    "CUSUM": "#D55E00",
    "EWMA": "#56B4E9",
    "Moving average": "#999999",
    "Moving median": "#666666",
    "Original": "#8B8B8B",
    "Raw threshold": "#B0B0B0",
    "Isolation Forest": "#7B3294",
    "One-Class SVM": "#008837",
    "LOF": "#A6611A",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--toy", action="store_true", help="Create toy diagnostic figures.")
    parser.add_argument("--hydro-exp1", action="store_true", help="Create hydroponic Experiment 1 figures.")
    parser.add_argument("--all-available", action="store_true", help="Create figures for available processed datasets.")
    args = parser.parse_args()
    if args.hydro_exp1 or args.all_available:
        _set_style()
        make_hydro_exp1_figures()
        if args.all_available:
            make_all_available_figures()
        if not args.toy:
            return
    if not args.toy:
        print("Real figures require completed benchmark outputs.")
        return
    _set_style()
    decisions = pd.read_csv(ROOT / "results/metrics/toy_aasvr_decisions.csv")
    ph = decisions[decisions["sensor"] == "pH"].copy()
    out = ROOT / "results/figures/toy_ph_event.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(8, 3))
    plt.plot(pd.to_datetime(ph["timestamp"]), ph["raw_value"], label="raw")
    plt.plot(pd.to_datetime(ph["timestamp"]), ph["trusted_value"], label="AASVR trusted")
    plt.legend()
    plt.tight_layout()
    _save_current(out)
    plt.close()
    print(f"Wrote {out}")


def make_hydro_exp1_figures() -> None:
    decisions_path = ROOT / "results/metrics/hydro_exp1_aasvr_decisions.csv"
    if not decisions_path.exists():
        raise SystemExit("Missing hydro_exp1 decisions; run scripts/04_run_methods.py --hydro-exp1.")
    decisions = pd.read_csv(decisions_path)
    out_dir = ROOT / "results/figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    for sensor in ("pH", "CO2"):
        subset = decisions[decisions["sensor"] == sensor].copy().head(2500)
        if subset.empty:
            continue
        out = out_dir / f"hydro_exp1_{sensor.lower()}_trace.png"
        plt.figure(figsize=(6.6, 2.8))
        plt.plot(
            pd.to_datetime(subset["timestamp"]),
            subset["raw_value"],
            label="Raw",
            linewidth=0.9,
            color="#666666",
        )
        plt.plot(
            pd.to_datetime(subset["timestamp"]),
            subset["trusted_value"],
            label="AASVR trusted",
            linewidth=1.3,
            color=PALETTE["AASVR"],
        )
        alerts = subset[subset["alert"].astype(bool)]
        if not alerts.empty:
            plt.scatter(
                pd.to_datetime(alerts["timestamp"]),
                alerts["raw_value"],
                s=9,
                label="Alert",
                color="#D55E00",
            )
        plt.ylabel(sensor)
        plt.xlabel("Time")
        plt.legend(frameon=False, ncols=3, loc="upper right")
        plt.tight_layout()
        _save_current(out)
        plt.close()
        print(f"Wrote {out}")
    summary_path = ROOT / "results/metrics/hydro_exp1_synthetic_summary.csv"
    if summary_path.exists():
        summary = _with_labels(pd.read_csv(summary_path)).sort_values("balanced_accuracy", ascending=True)
        out = out_dir / "hydro_exp1_synthetic_balanced_accuracy.png"
        plt.figure(figsize=(6.3, 3.8))
        colors = [PALETTE.get(method, "#777777") for method in summary["method_label"]]
        plt.barh(summary["method_label"], summary["balanced_accuracy"], color=colors)
        plt.xlabel("Balanced accuracy")
        plt.xlim(0, 1)
        plt.tight_layout()
        _save_current(out)
        plt.close()
        print(f"Wrote {out}")
    ablation_path = ROOT / "results/metrics/hydro_exp1_ablation_summary.csv"
    if ablation_path.exists():
        ablation = pd.read_csv(ablation_path).sort_values("balanced_accuracy", ascending=True)
        out = out_dir / "hydro_exp1_ablation_balanced_accuracy.png"
        plt.figure(figsize=(6.4, 3.6))
        plt.barh(ablation["variant"], ablation["balanced_accuracy"])
        plt.xlabel("Balanced accuracy")
        plt.xlim(0, 1)
        plt.tight_layout()
        _save_current(out)
        plt.close()
        print(f"Wrote {out}")
    ci_path = ROOT / "results/metrics/hydro_exp1_bootstrap_ci.csv"
    if ci_path.exists():
        ci = pd.read_csv(ci_path)
        metric = _with_labels(ci[ci["metric"] == "balanced_accuracy"]).sort_values("mean", ascending=True)
        if not metric.empty:
            out = out_dir / "hydro_exp1_balanced_accuracy_ci.png"
            lower = metric["mean"] - metric["ci_low"]
            upper = metric["ci_high"] - metric["mean"]
            plt.figure(figsize=(6.3, 3.8))
            colors = [PALETTE.get(method, "#777777") for method in metric["method_label"]]
            plt.barh(
                metric["method_label"],
                metric["mean"],
                xerr=[lower, upper],
                capsize=3,
                color=colors,
            )
            plt.xlabel("Balanced accuracy with bootstrap 95% CI")
            plt.xlim(0, 1)
            plt.tight_layout()
            _save_current(out)
            plt.close()
            print(f"Wrote {out}")
    fault_path = ROOT / "results/metrics/hydro_exp1_synthetic_by_fault_type.csv"
    if fault_path.exists():
        fault = pd.read_csv(fault_path)
        fault = _with_labels(fault)
        pivot = fault.pivot(index="fault_type", columns="method_label", values="balanced_accuracy")
        if not pivot.empty:
            ordered_columns = [label for label in METHOD_LABELS.values() if label in pivot.columns]
            pivot = pivot[ordered_columns]
            out = out_dir / "hydro_exp1_fault_type_heatmap.png"
            plt.figure(figsize=(7.2, 3.8))
            sns.heatmap(
                pivot,
                vmin=0,
                vmax=1,
                cmap="YlGnBu",
                annot=True,
                fmt=".2f",
                linewidths=0.35,
                linecolor="white",
                cbar_kws={"label": "Balanced accuracy"},
            )
            plt.xlabel("")
            plt.ylabel("")
            plt.xticks(rotation=35, ha="right")
            plt.tight_layout()
            _save_current(out)
            plt.close()
            print(f"Wrote {out}")


def make_all_available_figures() -> None:
    summary_path = ROOT / "results/tables/main_benchmark_table.csv"
    if not summary_path.exists():
        return
    summary = pd.read_csv(summary_path)
    if summary.empty or "balanced_accuracy" not in summary:
        return
    out_dir = ROOT / "results/figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    rank_rows = []
    for dataset, frame in summary.groupby("dataset"):
        ranked = frame[["method", "balanced_accuracy"]].copy()
        ranked["rank"] = ranked["balanced_accuracy"].rank(method="average", ascending=False)
        ranked["dataset"] = dataset
        rank_rows.append(ranked)
    ranks = pd.concat(rank_rows, ignore_index=True)
    plot = (
        _with_labels(ranks)
        .groupby("method_label", as_index=False)["rank"]
        .mean()
        .sort_values("rank", ascending=True)
    )
    out = out_dir / "cross_dataset_rank_plot.png"
    plt.figure(figsize=(6.2, 3.7))
    colors = [PALETTE.get(method, "#777777") for method in plot["method_label"]]
    plt.barh(plot["method_label"], plot["rank"], color=colors)
    plt.gca().invert_yaxis()
    plt.xlabel("Mean rank by balanced accuracy")
    plt.tight_layout()
    _save_current(out)
    plt.close()
    print(f"Wrote {out}")
    threshold_path = ROOT / "results/metrics/external_native_threshold_sensitivity.csv"
    if threshold_path.exists():
        threshold = pd.read_csv(threshold_path)
        aasvr = threshold[threshold["method"].eq("aasvr")].copy()
        if not aasvr.empty:
            out = out_dir / "external_aasvr_threshold_sensitivity.png"
            plt.figure(figsize=(5.8, 3.2))
            for dataset, frame in aasvr.groupby("dataset"):
                frame = frame.sort_values("threshold")
                plt.plot(frame["threshold"], frame["balanced_accuracy"], marker="o", label=dataset)
            plt.xlabel("Sensor-fraction aggregation threshold")
            plt.ylabel("Balanced accuracy")
            plt.ylim(0, 1)
            plt.legend(frameon=False)
            plt.tight_layout()
            _save_current(out)
            plt.close()
            print(f"Wrote {out}")


def _set_style() -> None:
    sns.set_theme(style="whitegrid", context="paper", font_scale=1.05)
    plt.rcParams.update(
        {
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.dpi": 160,
            "savefig.bbox": "tight",
        }
    )


def _with_labels(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    frame["method_label"] = frame["method"].map(METHOD_LABELS).fillna(frame["method"])
    return frame


def _save_current(path: Path) -> None:
    plt.savefig(path, dpi=220)
    plt.savefig(path.with_suffix(".pdf"))


if __name__ == "__main__":
    main()
