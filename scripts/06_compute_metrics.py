from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from aasvr.evaluation import compute_metrics

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--toy", action="store_true", help="Compute metrics for toy decisions.")
    args = parser.parse_args()
    if not args.toy:
        print("Real metric computation requires method outputs and labels.")
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


if __name__ == "__main__":
    main()
