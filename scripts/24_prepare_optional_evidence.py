from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from aasvr.deployment_evidence import (
    load_optional_actuator_log,
    load_optional_reference_measurements,
    score_actuator_response_log,
    summarize_actuator_response,
    write_templates,
)


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare optional deployment evidence files.")
    parser.add_argument("--write-templates", action="store_true")
    parser.add_argument("--hydro-exp1", action="store_true")
    args = parser.parse_args()
    if args.write_templates:
        for path in write_templates(ROOT / "configs/templates"):
            print(f"Wrote {path.relative_to(ROOT)}")
    if args.hydro_exp1:
        run_hydro_exp1()
    if not args.write_templates and not args.hydro_exp1:
        parser.print_help()


def run_hydro_exp1() -> None:
    out_dir = ROOT / "results/run_metadata"
    out_dir.mkdir(parents=True, exist_ok=True)
    actuator_log, actuator_status = load_optional_actuator_log(
        ROOT / "data/raw/hydroponic/actuator_state_log.csv"
    )
    references, reference_status = load_optional_reference_measurements(
        ROOT / "data/raw/hydroponic/reference_measurements.csv"
    )
    statuses = pd.DataFrame([actuator_status.__dict__, reference_status.__dict__])
    statuses["path"] = statuses["path"].astype(str)
    statuses.to_csv(out_dir / "hydro_exp1_optional_evidence_status.csv", index=False)

    measurements_path = ROOT / "data/processed/hydro_exp1_measurements.parquet"
    if measurements_path.exists() and not actuator_log.empty:
        measurements = pd.read_parquet(measurements_path)
        response = score_actuator_response_log(
            measurements,
            actuator_log,
            response_window_samples=4,
        )
    else:
        response = score_actuator_response_log(pd.DataFrame(), pd.DataFrame())
    response.to_csv(ROOT / "results/metrics/hydro_exp1_real_actuator_response.csv", index=False)
    response_summary = summarize_actuator_response(response)
    response_summary.to_csv(
        ROOT / "results/metrics/hydro_exp1_real_actuator_response_summary.csv",
        index=False,
    )

    if not references.empty:
        reference_summary = (
            references.assign(error=references["raw_value"] - references["reference_value"])
            .groupby("sensor", as_index=False)
            .agg(
                n=("error", "size"),
                mean_error=("error", "mean"),
                mae=("error", lambda s: float(s.abs().mean())),
                max_abs_error=("error", lambda s: float(s.abs().max())),
            )
        )
    else:
        reference_summary = pd.DataFrame(columns=["sensor", "n", "mean_error", "mae", "max_abs_error"])
    reference_summary.to_csv(ROOT / "results/metrics/hydro_exp1_reference_error_summary.csv", index=False)
    print(f"Wrote {out_dir / 'hydro_exp1_optional_evidence_status.csv'}")


if __name__ == "__main__":
    main()
