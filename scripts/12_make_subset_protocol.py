from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--profile",
        choices=["minimal", "paper", "full"],
        default="paper",
        help="Profile to document in the subset protocol table.",
    )
    args = parser.parse_args()
    make_subset_protocol(args.profile)


def make_subset_protocol(profile: str = "paper") -> Path:
    rows = []
    for config_path in sorted((ROOT / "configs/datasets").glob("*.yaml")):
        config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        if config.get("name") in {"hydro_exp1", "hydro_exp2"}:
            continue
        subset = config.get("subset_protocol", {})
        profile_data = config.get("download_profiles", {}).get(profile, {})
        rows.append(
            {
                "dataset": config.get("name", config_path.stem),
                "domain": config.get("domain", ""),
                "profile": profile,
                "profile_action": profile_data.get("action", "notes_only"),
                "expected_size_mb": profile_data.get("expected_size_mb", ""),
                "subset_files": subset.get("subset_files", ""),
                "selected_faults": subset.get("selected_faults", ""),
                "max_runs": subset.get("max_runs", ""),
                "max_rows": subset.get("max_rows", ""),
                "selection_rationale": subset.get("selection_rationale", ""),
                "limitation": subset.get("limitation", ""),
                "source_url": config.get("source_url", config.get("source", "")),
            }
        )
    out = ROOT / "results/tables/benchmark_subset_protocol.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"Wrote {out}")
    return out


if __name__ == "__main__":
    main()
