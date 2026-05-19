from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from aasvr.deployment_evidence import (
    apply_water_level_calibration,
    fit_water_level_calibration,
    template_frame,
    WATER_LEVEL_CALIBRATION_COLUMNS,
)


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Fit optional water-level calibration.")
    parser.add_argument(
        "--calibration",
        default="data/raw/hydroponic/water_level_calibration.csv",
        help="CSV with raw water-level readings paired to physical reference levels.",
    )
    parser.add_argument("--write-template", action="store_true")
    args = parser.parse_args()
    template = ROOT / "configs/templates/water_level_calibration_template.csv"
    if args.write_template:
        template.parent.mkdir(parents=True, exist_ok=True)
        template_frame(WATER_LEVEL_CALIBRATION_COLUMNS).to_csv(template, index=False)
        print(f"Wrote {template.relative_to(ROOT)}")
        return

    path = ROOT / args.calibration
    out_dir = ROOT / "results/run_metadata"
    out_dir.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        pd.DataFrame(
            [
                {
                    "available": False,
                    "path": str(path),
                    "n": 0,
                    "slope": "",
                    "intercept": "",
                    "rmse_cm": "",
                    "r2": "",
                    "message": "Water-level calibration file is absent; Water_Level remains excluded.",
                }
            ]
        ).to_csv(out_dir / "hydro_water_level_calibration_status.csv", index=False)
        print(f"Missing {path}; wrote absence status.")
        return

    calibration_frame = pd.read_csv(path)
    calibration = fit_water_level_calibration(calibration_frame)
    pd.DataFrame(
        [
            {
                "available": True,
                "path": str(path),
                "n": calibration.n,
                "slope": calibration.slope,
                "intercept": calibration.intercept,
                "rmse_cm": calibration.rmse_cm,
                "r2": calibration.r2,
                "message": "Water-level calibration fitted; inspect RMSE/R2 before enabling Water_Level.",
            }
        ]
    ).to_csv(out_dir / "hydro_water_level_calibration_status.csv", index=False)

    raw_path = ROOT / "data/raw/hydroponic/Hydroponics Data First Trial.csv"
    if raw_path.exists():
        raw = pd.read_csv(raw_path)
        if "Water_Level" in raw:
            processed = pd.DataFrame(
                {
                    "timestamp": pd.to_datetime(raw.get("Timestamp"), errors="coerce", utc=True),
                    "water_level_raw": raw["Water_Level"],
                    "water_level_cm_calibrated": apply_water_level_calibration(raw["Water_Level"], calibration),
                }
            )
            processed.to_csv(ROOT / "data/interim/hydro_water_level_calibrated_preview.csv", index=False)
    print(f"Wrote {out_dir / 'hydro_water_level_calibration_status.csv'}")


if __name__ == "__main__":
    main()
