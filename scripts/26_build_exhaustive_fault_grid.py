from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from aasvr.config import load_aasvr_config
from aasvr.exhaustive import build_fault_grid, load_exhaustive_protocol, protocol_summary
from aasvr.prepare import HYDRO_PRIMARY_SENSORS

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=["mini", "paper", "exhaustive"], default="mini")
    parser.add_argument(
        "--config",
        default="configs/experiments/exhaustive_hydro.yaml",
        help="Exhaustive protocol YAML.",
    )
    args = parser.parse_args()
    frame_path = ROOT / "data/processed/hydro_exp1_measurements.parquet"
    if not frame_path.exists():
        raise SystemExit("Missing processed hydro_exp1 data; run scripts/02_prepare_datasets.py --hydro-exp1.")
    frame = pd.read_parquet(frame_path)[["timestamp", *HYDRO_PRIMARY_SENSORS]].copy()
    base = load_aasvr_config(ROOT / "configs/methods/aasvr.yaml")
    sensors = tuple(sensor for sensor in base.sensors if sensor.name in HYDRO_PRIMARY_SENSORS)
    protocol, _sweep = load_exhaustive_protocol(ROOT / args.config, profile=args.profile)
    grid = build_fault_grid(frame, sensors, protocol)
    out_dir = ROOT / "data/synthetic"
    meta_dir = ROOT / "results/run_metadata"
    out_dir.mkdir(parents=True, exist_ok=True)
    meta_dir.mkdir(parents=True, exist_ok=True)
    grid_path = out_dir / f"hydro_exp1_fault_grid_{args.profile}.csv"
    summary_path = meta_dir / f"hydro_exp1_exhaustive_protocol_{args.profile}.csv"
    grid.to_csv(grid_path, index=False)
    pd.DataFrame([protocol_summary(protocol)]).to_csv(summary_path, index=False)
    print(f"Wrote {grid_path} ({len(grid)} trials)")
    print(f"Wrote {summary_path}")


if __name__ == "__main__":
    main()
