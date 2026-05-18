from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--toy", action="store_true", help="Create manuscript toy tables.")
    args = parser.parse_args()
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


if __name__ == "__main__":
    main()
