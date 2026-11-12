"""Isolated reproduction of the frozen controlled result and post-hoc follow-up."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import resource
import time

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/metrics/research_reproduction_controlled"
REPORT = ROOT / "docs/research/controlled_reproduction.json"


def fingerprints(paths):
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def main():
    started = time.monotonic()
    report = {"started_utc": datetime.now(timezone.utc).isoformat(), "checks": []}
    spec = importlib.util.spec_from_file_location("followup", ROOT / "scripts/70_livegate_followup.py")
    followup = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(followup)
    expected = followup.OUT
    frozen_paths = [p for p in expected.rglob("*") if p.is_file()]
    frozen_paths += [p for p in followup.ORIGINAL.rglob("*") if p.is_file()]
    frozen_paths += [followup.CONFIG, ROOT / "configs/experiments/livegate.yaml",
                     ROOT / "src/aasvr/livegate.py", ROOT / "src/aasvr/simple_gates.py",
                     ROOT / "scripts/66_livegate_benchmark.py", ROOT / "scripts/70_livegate_followup.py"]
    frozen = fingerprints(frozen_paths)
    followup.OUT = OUT
    followup.TABLE = ROOT / "results/metrics/research_reproduction_controlled/tables"
    followup.FIG = ROOT / "results/metrics/research_reproduction_controlled/figures"
    for path in (followup.OUT, followup.TABLE, followup.FIG):
        path.mkdir(parents=True, exist_ok=True)
    try:
        followup.runner().main()
        report["original_checks"] = followup.verify_reproduction()
        for path in sorted(expected.glob("*.csv")):
            pd.testing.assert_frame_equal(pd.read_csv(path), pd.read_csv(OUT / path.name),
                                          check_exact=False, rtol=1e-12, atol=1e-12)
            report["checks"].append(path.name)
        cfg = followup.load_yaml(followup.CONFIG)
        detail = pd.read_csv(OUT / "evaluation_detail.csv.gz")
        detail = detail[detail.deadline == cfg["selection_deadline_seconds"]]
        selections = pd.read_csv(OUT / "locked_validation_selections.csv")
        followup.confidence_and_sensor_tables(detail, selections, cfg)
        for path in sorted(followup.TABLE.glob("*.csv")):
            prior = ROOT / "results/tables/livegate_followup" / path.name
            pd.testing.assert_frame_equal(pd.read_csv(prior), pd.read_csv(path),
                                          check_exact=False, rtol=1e-12, atol=1e-12)
            report["checks"].append(f"tables/{path.name}")
        assert fingerprints(frozen_paths) == frozen, "Original artifacts changed"
        report["status"] = "passed"
    except Exception as error:
        report.update(status="failed", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        report.update(finished_utc=datetime.now(timezone.utc).isoformat(),
                      elapsed_seconds=time.monotonic() - started,
                      process_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                      original_artifacts_unchanged=fingerprints(frozen_paths) == frozen,
                      frozen_fingerprints=frozen,
                      output_hashes=fingerprints(sorted(p for p in OUT.rglob("*") if p.is_file())),
                      runner_hash=fingerprints([Path(__file__), ROOT / "docs/research/CYCLE_03_PROTOCOL.md"]))
        REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("status", "elapsed_seconds", "checks", "original_artifacts_unchanged")}, indent=2))


if __name__ == "__main__":
    main()
