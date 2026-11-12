"""Reproduce the current audit without overwriting its data or frozen outputs.

See docs/research/CYCLE_01_PROTOCOL.md. Assertions are the deterministic
reproduction endpoints, not independent validation of the original experiment.
"""
from __future__ import annotations

from contextlib import redirect_stdout
from datetime import datetime, timezone
import hashlib
import importlib.util
from importlib.metadata import version
import json
import os
from pathlib import Path
import resource
import subprocess
import tempfile
import time

import pandas as pd

from aasvr.prepare import prepare_hydro_exp1

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/research/reproduction"
SOURCE = ROOT / "data/raw/hydroponic/Hydroponics Data First Trial.csv"
ALIASES = {"Air_temp": "Air_Temp", "Water_temp": "Water_Temp",
           "Water_level": "Water_Level", "CO2_conc": "CO2"}


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def profile(path):
    frame = pd.read_csv(path).rename(columns=ALIASES)
    frame["Timestamp"] = pd.to_datetime(frame.Timestamp, utc=True, errors="raise")
    gaps = frame.Timestamp.sort_values().diff().dt.total_seconds()
    return frame, {"path": str(path.relative_to(ROOT)), "sha256": digest(path),
                   "rows": len(frame), "columns": list(frame),
                   "missing": frame.isna().sum().to_dict(),
                   "duplicate_rows": int(frame.duplicated().sum()),
                   "duplicate_timestamps": int(frame.Timestamp.duplicated().sum()),
                   "duplicate_entry_ids": int(frame.entry_id.duplicated().sum()),
                   "start_utc": frame.Timestamp.min().isoformat(),
                   "end_utc": frame.Timestamp.max().isoformat(),
                   "median_interval_seconds": float(gaps.median()),
                   "gaps_over_120_seconds": int((gaps > 120).sum()),
                   "fraction_elapsed_in_gaps_over_120_seconds": float(gaps[gaps > 120].sum() / gaps.sum())}


def main():
    started = time.monotonic()
    OUT.mkdir(parents=True, exist_ok=True)
    report = {"started_utc": datetime.now(timezone.utc).isoformat(),
              "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "image_id": os.environ.get("AASVR_AUDIT_IMAGE_ID", "unrecorded"),
              "packages": {name: version(name) for name in ("numpy", "pandas", "scipy", "scikit-learn", "pyarrow", "pytest", "ruff")},
              "command": "python scripts/72_reproduce_audit.py", "checks": {}}
    paths = [SOURCE, ROOT / "scripts/68_deployment_audit.py", ROOT / "scripts/72_reproduce_audit.py"]
    paths += sorted((ROOT / "src/aasvr").glob("*.py"))
    paths += sorted((ROOT / "configs").rglob("*.yaml"))
    report["input_hashes"] = {str(path.relative_to(ROOT)): digest(path) for path in paths}
    original, report["public_data_profile"] = profile(SOURCE)
    extra = ROOT / "data/Actual/feeds.csv"
    if extra.exists():
        candidate, candidate_profile = profile(extra)
        equivalent = set(original) == set(candidate) and original.equals(candidate.reindex(columns=original.columns))
        report["additional_feed"] = {"path": "data/Actual/feeds.csv", "sha256": candidate_profile["sha256"],
                                     "equivalent_after_header_and_UTC_normalization": equivalent,
                                     "independent_evidence": False if equivalent else "unresolved provenance"}
    spec = importlib.util.spec_from_file_location("deployment_audit", ROOT / "scripts/68_deployment_audit.py")
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    originals = {path: digest(path) for path in (audit.TABLE, audit.BAND, audit.SOURCE)}
    try:
        with tempfile.TemporaryDirectory(prefix="audit-reproduction-") as temporary:
            temporary = Path(temporary)
            prepared = prepare_hydro_exp1(SOURCE, events_path=ROOT / "data/raw/hydroponic/experiment_1_events.csv",
                                         processed_dir=temporary / "processed", metadata_dir=temporary / "metadata")
            pd.testing.assert_frame_equal(pd.read_parquet(prepared.measurements_path), pd.read_parquet(audit.SOURCE))
            report["checks"]["all_processed_rows_exactly_equal"] = True
            audit.SOURCE = prepared.measurements_path
            expected = {"TABLE": audit.TABLE, "BAND": audit.BAND}
            audit.TABLE, audit.BAND = OUT / "deployment_audit.csv", OUT / "deployment_time_in_band.csv"
            with (OUT / "baseline.log").open("w") as log, redirect_stdout(log):
                audit.main()
            for name, frozen in expected.items():
                reproduced = getattr(audit, name)
                assert reproduced.read_bytes() == frozen.read_bytes(), f"Reproduction mismatch: {frozen}"
                report["checks"][f"{frozen.name}_byte_equal"] = True
            assert all(digest(path) == before for path, before in originals.items()), "Original artifact changed"
            report["checks"]["original_artifacts_unchanged"] = True
        report["status"] = "passed"
    except Exception as error:
        report["status"] = "failed"
        report["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        report["finished_utc"] = datetime.now(timezone.utc).isoformat()
        report["elapsed_seconds"] = time.monotonic() - started
        report["process_peak_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        report["output_hashes"] = {path.name: digest(path) for path in OUT.iterdir() if path.suffix == ".csv"}
        (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "checks": report["checks"],
                      "elapsed_seconds": report["elapsed_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
