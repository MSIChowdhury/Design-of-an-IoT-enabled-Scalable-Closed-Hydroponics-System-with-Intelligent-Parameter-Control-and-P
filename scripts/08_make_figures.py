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


if __name__ == "__main__":
    main()
