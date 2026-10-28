"""Generate the public synthetic stand-in for the request-only sensor log.

Writes the stand-in CSV, its fitted aggregate profile, and a real-versus-stand-in
summary comparison. Only aggregates of the real log are written. Run in Docker.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from aasvr.config import load_aasvr_config
from aasvr.standin import fit_profile, generate, summary

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/processed/hydro_exp1_measurements.parquet"
OUT = ROOT / "data/standin"
SENSORS = ("EC", "pH", "Humidity", "Air_Temp", "Water_Temp", "CO2")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=20261028)
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    base = load_aasvr_config(ROOT / "configs/methods/aasvr.yaml")
    ranges = {s.name: (s.physical_min, s.physical_max) for s in base.sensors if s.name in SENSORS}
    real = pd.read_parquet(SOURCE)
    profile = fit_profile(real, ranges)
    (OUT / "standin_profile.json").write_text(json.dumps(profile, indent=2))
    standin = generate(profile, seed=args.seed)
    standin.to_csv(OUT / "hydro_standin.csv.gz", index=False, float_format="%.4f")
    comparison = pd.concat([summary(real, ranges).assign(source="deployment"),
                            summary(standin, ranges).assign(source="synthetic_standin")])
    comparison.to_csv(OUT / "standin_vs_deployment_summary.csv", index=False, float_format="%.5g")
    print(comparison.to_string(index=False))


if __name__ == "__main__":
    main()
