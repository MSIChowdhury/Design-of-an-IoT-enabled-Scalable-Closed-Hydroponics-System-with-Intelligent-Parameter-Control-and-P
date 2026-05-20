from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from aasvr.deployment_evidence import reconstruct_actuator_log


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Normalize an independent controller/dashboard actuator-command export "
            "to data/raw/hydroponic/actuator_state_log.csv."
        )
    )
    parser.add_argument("--source", required=True, help="CSV export containing real command/state records.")
    parser.add_argument(
        "--out",
        default="data/raw/hydroponic/actuator_state_log.csv",
        help="Canonical actuator-state log output path.",
    )
    parser.add_argument(
        "--summary-out",
        default="results/run_metadata/hydro_exp1_reconstructed_actuator_log_summary.csv",
        help="Non-sensitive reconstruction summary output path.",
    )
    parser.add_argument(
        "--allow-commanded-as-measured",
        action="store_true",
        help=(
            "Use commanded_state as measured_state only when the source column is a relay/device "
            "state observation rather than an inferred controller request."
        ),
    )
    args = parser.parse_args()

    source = Path(args.source)
    frame = pd.read_csv(source)
    actuator_log, summary = reconstruct_actuator_log(
        frame,
        source_name=str(source),
        allow_commanded_as_measured=args.allow_commanded_as_measured,
    )
    out = ROOT / args.out
    summary_out = ROOT / args.summary_out
    out.parent.mkdir(parents=True, exist_ok=True)
    summary_out.parent.mkdir(parents=True, exist_ok=True)
    actuator_log.to_csv(out, index=False)
    summary.to_csv(summary_out, index=False)
    print(f"Wrote {out.relative_to(ROOT)}")
    print(f"Wrote {summary_out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
