from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from aasvr.prepare import prepare_hydro_exp1
from aasvr.toydata import write_toy_dataset

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--toy", action="store_true", help="Generate and prepare toy data.")
    parser.add_argument("--hydro-exp1", action="store_true", help="Prepare real hydroponic Experiment 1.")
    parser.add_argument(
        "--dataset",
        choices=["hydro_exp1", "tep", "wur", "hai", "swat", "wadi", "damadics"],
        help="Prepare a named real/external dataset.",
    )
    args = parser.parse_args()
    if args.hydro_exp1 or args.dataset == "hydro_exp1":
        prepared = prepare_hydro_exp1(ROOT / "data/raw/hydroponic/Hydroponics Data First Trial.csv")
        print(f"Wrote {prepared.measurements_path}")
        print(f"Wrote {prepared.labels_path}")
        print(f"Wrote {prepared.metadata_path}")
        print(f"Wrote {prepared.quality_path}")
        return
    if args.dataset:
        print(
            f"Skipping {args.dataset}; place raw files under data/raw/{args.dataset}/ "
            "and extend the dataset-specific loader when files are available."
        )
        return
    if args.toy:
        csv_path = write_toy_dataset(ROOT / "data/raw/hydroponic/toy_hydroponic.csv")
        out_path = ROOT / "data/processed/toy_hydroponic.parquet"
        out_path.parent.mkdir(parents=True, exist_ok=True)

        frame = pd.read_csv(csv_path, parse_dates=["timestamp"])
        frame.to_parquet(out_path, index=False)
        print(f"Wrote {out_path}")
        return
    print("Use --toy, --hydro-exp1, or --dataset hydro_exp1.")


if __name__ == "__main__":
    main()
