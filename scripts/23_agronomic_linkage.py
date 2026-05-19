from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from aasvr.agronomics import (
    AGRONOMIC_PROCESSED,
    compute_linkage_table,
    method_exposure_from_decisions,
    summarize_agronomic_harvest,
)

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--processed",
        default=str(ROOT / AGRONOMIC_PROCESSED),
        help="Processed per-plant agronomic harvest parquet.",
    )
    parser.add_argument("--experiment", type=int, default=1, help="Experiment to link with AASVR outputs.")
    args = parser.parse_args()
    processed = Path(args.processed)
    if not processed.exists():
        raise SystemExit(
            f"Missing processed agronomic data: {processed}. "
            "Run scripts/22_prepare_agronomic.py after adding the raw harvest sheet."
        )

    harvest = pd.read_parquet(processed)
    exposure = method_exposure_from_decisions(
        {
            "raw_threshold": ROOT / "results/metrics/hydro_exp1_raw_threshold_decisions.csv",
            "aasvr": ROOT / "results/metrics/hydro_exp1_aasvr_decisions.csv",
            "aasvr_r": ROOT / "results/metrics/hydro_exp1_aasvr_r_decisions.csv",
        }
    )
    if exposure.empty:
        raise SystemExit("Missing hydroponic decision outputs; run the hydro_exp1 method pipeline first.")

    out_dir = ROOT / "results/metrics"
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = summarize_agronomic_harvest(harvest)
    linkage = compute_linkage_table(harvest, exposure, experiment=args.experiment)
    exposure.to_csv(out_dir / "hydro_agronomic_exposure.csv", index=False)
    summary.to_csv(out_dir / "hydro_agronomic_summary.csv", index=False)
    linkage.to_csv(out_dir / "hydro_agronomic_linkage.csv", index=False)
    print(f"Wrote {out_dir / 'hydro_agronomic_exposure.csv'}")
    print(f"Wrote {out_dir / 'hydro_agronomic_summary.csv'}")
    print(f"Wrote {out_dir / 'hydro_agronomic_linkage.csv'}")


if __name__ == "__main__":
    main()
