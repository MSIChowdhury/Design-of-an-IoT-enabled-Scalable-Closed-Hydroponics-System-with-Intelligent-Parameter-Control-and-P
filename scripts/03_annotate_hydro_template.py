from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    out = ROOT / "data/raw/hydroponic/annotation_template.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "event_id",
        "dataset",
        "sensor",
        "start_time",
        "end_time",
        "event_type",
        "confidence",
        "evidence",
        "severity",
        "manual_intervention",
        "actuator_affected",
        "notes",
    ]
    pd.DataFrame(columns=columns).to_csv(out, index=False)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()

