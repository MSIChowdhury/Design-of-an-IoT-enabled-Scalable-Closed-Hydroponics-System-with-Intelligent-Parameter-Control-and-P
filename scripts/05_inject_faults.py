from __future__ import annotations

import argparse
from pathlib import Path

from aasvr.fault_injection import FaultSpec, inject_fault
from aasvr.toydata import make_toy_hydroponic_data

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--toy", action="store_true", help="Create toy synthetic-fault data.")
    args = parser.parse_args()
    if not args.toy:
        print("Real synthetic injection requires prepared normal segments.")
        return
    frame = make_toy_hydroponic_data()
    faulted, labels = inject_fault(
        frame,
        FaultSpec(sensor="pH", fault_type="spike", start=30, duration=4, magnitude=3.0),
    )
    out_dir = ROOT / "data/synthetic"
    out_dir.mkdir(parents=True, exist_ok=True)
    faulted.to_csv(out_dir / "toy_faulted.csv", index=False)
    labels.to_csv(out_dir / "toy_fault_labels.csv", index=False)
    print(f"Wrote synthetic toy data to {out_dir}")


if __name__ == "__main__":
    main()
