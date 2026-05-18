from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from aasvr.config import load_aasvr_config, load_yaml
from aasvr.pipeline import run_aasvr_on_frame, run_baseline_on_frame
from aasvr.toydata import make_toy_hydroponic_data

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--toy", action="store_true", help="Run methods on generated toy data.")
    args = parser.parse_args()
    if not args.toy:
        print("Real method runs require prepared local datasets.")
        return
    frame = make_toy_hydroponic_data()
    config_path = ROOT / "configs/methods/aasvr.yaml"
    aasvr_out = run_aasvr_on_frame(frame, config_path)
    out_dir = ROOT / "results/metrics"
    out_dir.mkdir(parents=True, exist_ok=True)
    aasvr_out.to_csv(out_dir / "toy_aasvr_decisions.csv", index=False)

    sensors = load_aasvr_config(config_path).sensors
    baselines = load_yaml(ROOT / "configs/methods/baselines.yaml")["required"]
    for method in baselines:
        baseline_out = run_baseline_on_frame(frame, sensors, method)
        baseline_out.to_csv(out_dir / f"toy_{method}_decisions.csv", index=False)
    print(f"Wrote decisions to {out_dir}")


if __name__ == "__main__":
    main()
