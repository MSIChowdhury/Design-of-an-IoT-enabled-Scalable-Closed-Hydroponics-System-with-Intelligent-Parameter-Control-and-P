from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--toy", action="store_true", help="Create manuscript toy tables.")
    parser.add_argument("--hydro-exp1", action="store_true", help="Create hydroponic Experiment 1 tables.")
    parser.add_argument("--all-available", action="store_true", help="Create tables for all available processed datasets.")
    args = parser.parse_args()
    if args.hydro_exp1 or args.all_available:
        make_hydro_exp1_tables()
        if not args.toy:
            return
    if not args.toy:
        print("Real tables require completed benchmark metrics.")
        return
    metrics = ROOT / "results/metrics/toy_summary.csv"
    if not metrics.exists():
        raise SystemExit("Missing toy metrics; run scripts/06_compute_metrics.py --toy first.")
    frame = pd.read_csv(metrics)
    out = ROOT / "results/tables/toy_summary_table.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(out, index=False)
    print(f"Wrote {out}")


def make_hydro_exp1_tables() -> None:
    out_dir = ROOT / "results/tables"
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = ROOT / "results/metrics/hydro_exp1_summary.csv"
    if summary.exists():
        frame = pd.read_csv(summary)
        frame.to_csv(out_dir / "hydro_exp1_method_summary.csv", index=False)
        print(f"Wrote {out_dir / 'hydro_exp1_method_summary.csv'}")
    quality = ROOT / "results/run_metadata/hydro_exp1_data_quality.csv"
    if quality.exists():
        frame = pd.read_csv(quality)
        frame.to_csv(out_dir / "hydro_exp1_data_quality.csv", index=False)
        print(f"Wrote {out_dir / 'hydro_exp1_data_quality.csv'}")


if __name__ == "__main__":
    main()
