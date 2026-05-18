from __future__ import annotations

from pathlib import Path

import pandas as pd

from aasvr.labels import EVENT_COLUMNS, event_template_from_decisions

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    out = ROOT / "data/raw/hydroponic/annotation_template.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    decisions_path = ROOT / "results/metrics/hydro_exp1_aasvr_decisions.csv"
    if decisions_path.exists():
        decisions = pd.read_csv(decisions_path)
        template = event_template_from_decisions(decisions)
    else:
        template = pd.DataFrame(columns=EVENT_COLUMNS)
    template.to_csv(out, index=False)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
