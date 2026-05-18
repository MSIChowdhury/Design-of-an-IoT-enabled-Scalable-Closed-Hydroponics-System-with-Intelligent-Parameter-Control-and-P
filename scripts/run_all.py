from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--toy", action="store_true", help="Run the toy reproducibility pipeline.")
    parser.add_argument("--available-real", action="store_true", help="Run every locally available real dataset pipeline.")
    args = parser.parse_args()
    if args.available_real:
        run_available_real()
        return
    if not args.toy:
        print("Use --toy or --available-real.")
        return
    commands = [
        ["scripts/02_prepare_datasets.py", "--toy"],
        ["scripts/04_run_methods.py", "--toy"],
        ["scripts/05_inject_faults.py", "--toy"],
        ["scripts/06_compute_metrics.py", "--toy"],
        ["scripts/07_make_tables.py", "--toy"],
        ["scripts/08_make_figures.py", "--toy"],
    ]
    for command in commands:
        subprocess.run([sys.executable, *command], check=True)
    print("Toy pipeline completed.")


def run_available_real() -> None:
    raw_hydro = ROOT / "data/raw/hydroponic/Hydroponics Data First Trial.csv"
    if not raw_hydro.exists():
        print(f"Skipping hydro_exp1; missing {raw_hydro}")
        return
    commands = [
        ["scripts/02_prepare_datasets.py", "--hydro-exp1"],
        ["scripts/04_run_methods.py", "--hydro-exp1"],
        ["scripts/05_inject_faults.py", "--hydro-exp1"],
        ["scripts/06_compute_metrics.py", "--hydro-exp1"],
        ["scripts/09_tune_aasvr.py", "--hydro-exp1"],
        ["scripts/07_make_tables.py", "--hydro-exp1"],
        ["scripts/08_make_figures.py", "--hydro-exp1"],
    ]
    for command in commands:
        subprocess.run([sys.executable, *command], check=True)
    print("Available real-data pipeline completed.")


if __name__ == "__main__":
    main()
