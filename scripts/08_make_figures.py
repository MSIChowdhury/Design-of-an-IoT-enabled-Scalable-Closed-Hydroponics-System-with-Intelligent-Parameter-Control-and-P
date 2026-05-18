from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--toy", action="store_true", help="Create toy diagnostic figures.")
    parser.add_argument("--hydro-exp1", action="store_true", help="Create hydroponic Experiment 1 figures.")
    parser.add_argument("--all-available", action="store_true", help="Create figures for available processed datasets.")
    args = parser.parse_args()
    if args.hydro_exp1 or args.all_available:
        make_hydro_exp1_figures()
        if args.all_available:
            make_all_available_figures()
        if not args.toy:
            return
    if not args.toy:
        print("Real figures require completed benchmark outputs.")
        return
    decisions = pd.read_csv(ROOT / "results/metrics/toy_aasvr_decisions.csv")
    ph = decisions[decisions["sensor"] == "pH"].copy()
    out = ROOT / "results/figures/toy_ph_event.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(8, 3))
    plt.plot(pd.to_datetime(ph["timestamp"]), ph["raw_value"], label="raw")
    plt.plot(pd.to_datetime(ph["timestamp"]), ph["trusted_value"], label="AASVR trusted")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out, dpi=160)
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
        plt.figure(figsize=(9, 3))
        plt.plot(pd.to_datetime(subset["timestamp"]), subset["raw_value"], label="raw", linewidth=0.8)
        plt.plot(pd.to_datetime(subset["timestamp"]), subset["trusted_value"], label="AASVR trusted", linewidth=0.8)
        alerts = subset[subset["alert"].astype(bool)]
        if not alerts.empty:
            plt.scatter(pd.to_datetime(alerts["timestamp"]), alerts["raw_value"], s=8, label="alert")
        plt.title(f"hydro_exp1 {sensor} AASVR replay")
        plt.legend()
        plt.tight_layout()
        plt.savefig(out, dpi=160)
        plt.close()
        print(f"Wrote {out}")
    summary_path = ROOT / "results/metrics/hydro_exp1_synthetic_summary.csv"
    if summary_path.exists():
        summary = pd.read_csv(summary_path).sort_values("balanced_accuracy", ascending=True)
        out = out_dir / "hydro_exp1_synthetic_balanced_accuracy.png"
        plt.figure(figsize=(8, 4))
        plt.barh(summary["method"], summary["balanced_accuracy"])
        plt.xlabel("Mean balanced accuracy")
        plt.title("Hydroponic synthetic-fault benchmark")
        plt.tight_layout()
        plt.savefig(out, dpi=160)
        plt.close()
        print(f"Wrote {out}")
    ablation_path = ROOT / "results/metrics/hydro_exp1_ablation_summary.csv"
    if ablation_path.exists():
        ablation = pd.read_csv(ablation_path).sort_values("balanced_accuracy", ascending=True)
        out = out_dir / "hydro_exp1_ablation_balanced_accuracy.png"
        plt.figure(figsize=(8, 4))
        plt.barh(ablation["variant"], ablation["balanced_accuracy"])
        plt.xlabel("Mean balanced accuracy")
        plt.title("AASVR ablation benchmark")
        plt.tight_layout()
        plt.savefig(out, dpi=160)
        plt.close()
        print(f"Wrote {out}")
    ci_path = ROOT / "results/metrics/hydro_exp1_bootstrap_ci.csv"
    if ci_path.exists():
        ci = pd.read_csv(ci_path)
        metric = ci[ci["metric"] == "balanced_accuracy"].sort_values("mean", ascending=True)
        if not metric.empty:
            out = out_dir / "hydro_exp1_balanced_accuracy_ci.png"
            lower = metric["mean"] - metric["ci_low"]
            upper = metric["ci_high"] - metric["mean"]
            plt.figure(figsize=(8, 4))
            plt.barh(metric["method"], metric["mean"], xerr=[lower, upper], capsize=3)
            plt.xlabel("Balanced accuracy with bootstrap 95% CI")
            plt.title("Hydroponic synthetic-fault uncertainty")
            plt.tight_layout()
            plt.savefig(out, dpi=160)
            plt.close()
            print(f"Wrote {out}")
    fault_path = ROOT / "results/metrics/hydro_exp1_synthetic_by_fault_type.csv"
    if fault_path.exists():
        fault = pd.read_csv(fault_path)
        pivot = fault.pivot(index="fault_type", columns="method", values="balanced_accuracy")
        if not pivot.empty:
            out = out_dir / "hydro_exp1_fault_type_heatmap.png"
            plt.figure(figsize=(9, 4))
            plt.imshow(pivot, aspect="auto", vmin=0, vmax=1, cmap="viridis")
            plt.xticks(range(len(pivot.columns)), pivot.columns, rotation=45, ha="right")
            plt.yticks(range(len(pivot.index)), pivot.index)
            plt.colorbar(label="Balanced accuracy")
            plt.title("Fault-type robustness")
            plt.tight_layout()
            plt.savefig(out, dpi=160)
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
    plot = ranks.groupby("method", as_index=False)["rank"].mean().sort_values("rank", ascending=True)
    out = out_dir / "cross_dataset_rank_plot.png"
    plt.figure(figsize=(8, 4))
    plt.barh(plot["method"], plot["rank"])
    plt.gca().invert_yaxis()
    plt.xlabel("Mean rank by balanced accuracy")
    plt.title("Available-dataset method ranking")
    plt.tight_layout()
    plt.savefig(out, dpi=160)
    plt.close()
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
