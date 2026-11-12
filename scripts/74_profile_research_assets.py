"""Profile accessible raw CSVs and expose notebook text for honest inspection.

No datasets are downloaded, notebooks executed, or pickle models deserialized.
Git LFS pointers are unavailable data, not three-row CSV datasets.
"""
from __future__ import annotations

import csv
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/research"
EXTRACTED = Path("/tmp/hydro-review-notebooks")


def csv_profile(path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", errors="replace") as stream:
        first = stream.readline()
    if first.startswith("version https://git-lfs.github.com/spec/v1"):
        return {"status": "Git LFS pointer only; data not locally accessible"}
    if not first:
        return {"status": "empty file"}
    delimiter = csv.Sniffer().sniff(first, delimiters=",;\t").delimiter
    frame = pd.read_csv(path, sep=delimiter)
    result = {"status": "fully profiled; individual values not manually adjudicated",
              "delimiter": delimiter, "rows": len(frame), "columns": list(frame),
              "dtypes": {column: str(dtype) for column, dtype in frame.dtypes.items()},
              "missing": frame.isna().sum().to_dict(), "duplicate_rows": int(frame.duplicated().sum())}
    timestamp = next((c for c in frame if c.lower() in {"timestamp", "datetime", "time"}), None)
    if timestamp:
        times = pd.to_datetime(frame[timestamp], utc=True, errors="coerce")
        result["timestamps"] = {"column": timestamp, "unparsable": int(times.isna().sum()),
                                "duplicate_nonmissing": int(times.dropna().duplicated().sum()),
                                "start": str(times.min()), "end": str(times.max()),
                                "monotonic_in_file": bool(times.is_monotonic_increasing)}
    return result


def main():
    datasets = []
    paths = sorted([*(ROOT / "data/raw").rglob("*.csv"), *(ROOT / "data/raw").rglob("*.csv.gz")])
    for path in paths:
        record = {"path": str(path.relative_to(ROOT)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        try:
            record.update(csv_profile(path))
        except (ValueError, pd.errors.ParserError, csv.Error, UnicodeError) as error:
            record.update(status="profile failed; not interpreted", error=f"{type(error).__name__}: {error}")
        datasets.append(record)
    notebooks = []
    EXTRACTED.mkdir(exist_ok=True)
    for i, path in enumerate(sorted(ROOT.rglob("*.ipynb"))):
        if ".ipynb_checkpoints" in path.parts:
            continue
        notebook = json.loads(path.read_text())
        cells = notebook.get("cells", [])
        text = "\n\n".join(f"CELL {j} ({cell.get('cell_type')})\n{''.join(cell.get('source', []))}"
                           for j, cell in enumerate(cells))
        extracted = EXTRACTED / f"{i:02d}-{path.stem}.txt"
        extracted.write_text(text)
        notebooks.append({"path": str(path.relative_to(ROOT)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                          "cells": len(cells), "code_cells": sum(c.get("cell_type") == "code" for c in cells),
                          "saved_output_types": sorted({output.get("output_type", "unknown") for c in cells for output in c.get("outputs", [])}),
                          "source_extracted_to": str(extracted), "source_characters": len(text),
                          "status": "source extracted; reading/execution not implied"})
    report = {"timestamp_utc": datetime.now(timezone.utc).isoformat(),
              "scope": "All local data/raw CSV and CSV.gz files; all non-checkpoint notebooks; no acquisition or execution",
              "datasets": datasets, "notebooks": notebooks}
    (OUT / "asset_profiles.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"raw_csv_files": len(datasets), "notebooks": len(notebooks),
                      "dataset_statuses": pd.Series([d["status"] for d in datasets]).value_counts().to_dict()}, indent=2))


if __name__ == "__main__":
    main()
