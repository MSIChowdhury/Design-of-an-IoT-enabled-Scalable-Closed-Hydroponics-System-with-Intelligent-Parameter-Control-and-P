from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from aasvr.evaluation import compute_metrics

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--toy", action="store_true", help="Compute metrics for toy decisions.")
    parser.add_argument("--hydro-exp1", action="store_true", help="Compute metrics for hydroponic Experiment 1.")
    parser.add_argument(
        "--dataset",
        choices=["hydro_exp1", "tep", "wur", "hai", "swat", "wadi", "damadics"],
        help="Compute metrics for a prepared real/external dataset.",
    )
    args = parser.parse_args()
    if args.hydro_exp1 or args.dataset == "hydro_exp1":
        compute_hydro_exp1()
        return
    if args.dataset:
        print(f"Skipping {args.dataset}; no method outputs are available yet.")
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
        metrics = compute_metrics(decisions, labels)
        row = {"dataset": "hydro_exp1", "method": method}
        row.update(metrics.__dict__)
        rows.append(row)
    if not rows:
        raise SystemExit("Missing hydro_exp1 decisions; run scripts/04_run_methods.py --hydro-exp1.")
    out = out_dir / "hydro_exp1_summary.csv"
    pd.DataFrame(rows).sort_values(["dataset", "method"]).to_csv(out, index=False)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
