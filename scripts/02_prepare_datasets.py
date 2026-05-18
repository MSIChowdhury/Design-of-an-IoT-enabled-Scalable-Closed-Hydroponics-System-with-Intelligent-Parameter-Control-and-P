from __future__ import annotations

import argparse
from pathlib import Path

from aasvr.toydata import write_toy_dataset

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--toy", action="store_true", help="Generate and prepare toy data.")
    args = parser.parse_args()
    if not args.toy:
        print("Real dataset preparation requires local raw files under data/raw/.")
        return
    csv_path = write_toy_dataset(ROOT / "data/raw/hydroponic/toy_hydroponic.csv")
    out_path = ROOT / "data/processed/toy_hydroponic.parquet"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    import pandas as pd

    frame = pd.read_csv(csv_path, parse_dates=["timestamp"])
    frame.to_parquet(out_path, index=False)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
