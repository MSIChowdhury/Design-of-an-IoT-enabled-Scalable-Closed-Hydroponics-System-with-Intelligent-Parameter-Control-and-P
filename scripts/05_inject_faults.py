from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from aasvr.fault_injection import FaultSpec, inject_fault
from aasvr.prepare import HYDRO_PRIMARY_SENSORS
from aasvr.toydata import make_toy_hydroponic_data

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--toy", action="store_true", help="Create toy synthetic-fault data.")
    parser.add_argument("--hydro-exp1", action="store_true", help="Create hydroponic Experiment 1 synthetic-fault descriptors.")
    parser.add_argument(
        "--dataset",
        choices=["hydro_exp1", "tep", "wur", "hai", "swat", "wadi", "damadics"],
        help="Inject faults for a prepared real/external dataset.",
    )
    args = parser.parse_args()
    if args.hydro_exp1 or args.dataset == "hydro_exp1":
        inject_hydro_exp1()
        return
    if args.dataset:
        print(f"Skipping {args.dataset}; no prepared measurements are available yet.")
        return
    if not args.toy:
        print("Use --toy, --hydro-exp1, or --dataset hydro_exp1.")
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


def inject_hydro_exp1() -> None:
    path = ROOT / "data/processed/hydro_exp1_measurements.parquet"
    if not path.exists():
        raise SystemExit("Missing processed hydro_exp1 data; run scripts/02_prepare_datasets.py --hydro-exp1.")
    frame = pd.read_parquet(path)
    frame = frame[["timestamp", *HYDRO_PRIMARY_SENSORS]].copy()
    out_dir = ROOT / "data/synthetic"
    out_dir.mkdir(parents=True, exist_ok=True)
    summaries = []
    rng = np.random.default_rng(29)
    max_start = max(len(frame) - 31, 1)
    for sensor in ("pH", "CO2", "EC"):
        trial_id = 0
        for fault_type in ("spike", "multi_spike", "dropout", "drift", "bias", "noise_burst", "step"):
            for magnitude in (2.0, 4.0):
                for duration in (1, 5, 30):
                    for rep in range(2):
                        trial_id += 1
                        spec = FaultSpec(
                            sensor=sensor,
                            fault_type=fault_type,
                            start=int(rng.integers(0, max_start)),
                            duration=duration,
                            magnitude=magnitude,
                            seed=29 + rep,
                        )
                        _faulted, labels = inject_fault(frame, spec)
                        summaries.append(
                            {
                                "dataset": "hydro_exp1",
                                "trial_id": f"{sensor}_{trial_id}",
                                "sensor": spec.sensor,
                                "fault_type": spec.fault_type,
                                "start": spec.start,
                                "duration": spec.duration,
                                "magnitude": spec.magnitude,
                                "fault_samples": int(labels["fault"].sum()),
                            }
                        )
    out = out_dir / "hydro_exp1_fault_grid.csv"
    pd.DataFrame(summaries).to_csv(out, index=False)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
