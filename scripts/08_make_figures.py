from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--toy", action="store_true", help="Create toy diagnostic figures.")
    args = parser.parse_args()
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


if __name__ == "__main__":
    main()
