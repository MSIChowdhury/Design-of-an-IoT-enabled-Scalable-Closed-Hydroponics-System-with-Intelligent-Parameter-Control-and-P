from __future__ import annotations

import argparse
import subprocess
import sys


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--toy", action="store_true", help="Run the toy reproducibility pipeline.")
    args = parser.parse_args()
    if not args.toy:
        print("Use --toy until real datasets are present under data/raw/.")
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


if __name__ == "__main__":
    main()
