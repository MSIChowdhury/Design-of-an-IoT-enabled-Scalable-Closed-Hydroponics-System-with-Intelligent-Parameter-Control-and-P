from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXTERNAL_DATASETS = (
    "tep",
    "tep_csv",
    "wur",
    "hai",
    "skab",
    "metropt3",
    "batadal",
    "swat",
    "wadi",
    "damadics",
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--toy", action="store_true", help="Run the toy reproducibility pipeline.")
    parser.add_argument("--available-real", action="store_true", help="Run every locally available real dataset pipeline.")
    parser.add_argument(
        "--dataset-profile",
        choices=["minimal", "paper", "full"],
        default="paper",
        help="External benchmark acquisition/subset profile to document.",
    )
    args = parser.parse_args()
    if args.available_real:
        run_available_real(dataset_profile=args.dataset_profile)
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


def run_available_real(*, dataset_profile: str = "paper") -> None:
    raw_hydro = ROOT / "data/raw/hydroponic/Hydroponics Data First Trial.csv"
    if not raw_hydro.exists():
        print(f"Skipping hydro_exp1; missing {raw_hydro}")
        return
    commands = [
        ["scripts/02_prepare_datasets.py", "--hydro-exp1"],
        ["scripts/04_run_methods.py", "--hydro-exp1"],
        ["scripts/05_inject_faults.py", "--hydro-exp1"],
        ["scripts/09_tune_aasvr.py", "--hydro-exp1"],
        ["scripts/14_tune_baselines.py", "--hydro-exp1"],
        ["scripts/06_compute_metrics.py", "--hydro-exp1"],
        ["scripts/10_run_ablation.py", "--hydro-exp1"],
        ["scripts/11_statistical_analysis.py", "--hydro-exp1"],
        ["scripts/07_make_tables.py", "--hydro-exp1"],
        ["scripts/08_make_figures.py", "--hydro-exp1"],
    ]
    for command in commands:
        subprocess.run([sys.executable, *command], check=True)
    subprocess.run(
        [sys.executable, "scripts/download_datasets.py", "--all", "--profile", dataset_profile],
        check=True,
    )
    subprocess.run(
        [sys.executable, "scripts/12_make_subset_protocol.py", "--profile", dataset_profile],
        check=True,
    )
    for dataset in EXTERNAL_DATASETS:
        if not _has_raw_csv(dataset):
            print(f"Skipping {dataset}; no CSV raw files found under data/raw/{dataset}/.")
            continue
        subprocess.run([sys.executable, "scripts/02_prepare_datasets.py", "--dataset", dataset], check=True)
        if not (ROOT / f"data/processed/{dataset}_measurements.parquet").exists():
            continue
        subprocess.run([sys.executable, "scripts/04_run_methods.py", "--dataset", dataset], check=True)
        subprocess.run([sys.executable, "scripts/06_compute_metrics.py", "--dataset", dataset], check=True)
    subprocess.run([sys.executable, "scripts/07_make_tables.py", "--all-available"], check=True)
    subprocess.run([sys.executable, "scripts/15_tune_external_aasvr.py"], check=True)
    subprocess.run([sys.executable, "scripts/07_make_tables.py", "--all-available"], check=True)
    print("Available real-data pipeline completed.")


def _has_raw_csv(dataset: str) -> bool:
    raw_dir = ROOT / "data/raw" / dataset
    return raw_dir.exists() and any(
        path.is_file() and (path.name.endswith(".csv") or path.name.endswith(".csv.gz"))
        for path in raw_dir.rglob("*")
    )


if __name__ == "__main__":
    main()
