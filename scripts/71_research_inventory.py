"""Inventory local research assets without equating hashing with scientific review.

Run in Docker. Credentials and dependency/cache trees are listed as exclusions,
never opened. The separate human coverage ledger records what was actually read.
"""
from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/research"
CACHES = {".git", ".idea", ".pytest_cache", ".ruff_cache", "__pycache__",
          ".ipynb_checkpoints", ".venv", "venv", "node_modules"}


def exclusion(path: Path) -> str:
    if any(part in CACHES for part in path.parts):
        return "dependency/cache/version-control metadata"
    if (path.name.startswith(".env") or path.suffix in {".pem", ".key"}
            or path.name in {"id_rsa", "id_ed25519"}
            or "credential" in path.name.lower()
            or (path.parent == Path("Code Files/Web Interface") and path.suffix == ".json")):
        return "potential credential; content excluded"
    if path.as_posix() in {"docs/research/inventory.csv", "docs/research/inventory_summary.json"}:
        return "inventory output; avoids self-reference"
    return ""


def inventory(root: Path) -> list[dict]:
    rows = []
    for directory, dirs, files in os.walk(root, followlinks=False):
        for name in sorted(dirs + files):
            path = Path(directory) / name
            relative = path.relative_to(root)
            reason = exclusion(relative)
            is_dir = name in dirs
            if is_dir and not reason and not path.is_symlink():
                continue
            if is_dir:
                dirs.remove(name)
            row = {"path": relative.as_posix(), "kind": "directory" if is_dir else "file",
                   "bytes": "", "sha256": "", "status": reason or "inventoried; content review pending"}
            if path.is_symlink():
                row["status"] = "symlink; target not followed"
            elif not is_dir:
                try:
                    row["bytes"] = path.stat().st_size
                    if not reason:
                        with path.open("rb") as stream:
                            row["sha256"] = hashlib.file_digest(stream, "sha256").hexdigest()
                except OSError as error:
                    row["status"] = f"unreadable: {type(error).__name__}"
            rows.append(row)
    return sorted(rows, key=lambda row: row["path"])


def main():
    rows = inventory(ROOT)
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "inventory.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = {"timestamp_utc": datetime.now(timezone.utc).isoformat(),
               "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
               "entries": len(rows), "hashed_files": sum(bool(row["sha256"]) for row in rows),
               "hashed_bytes": sum(row["bytes"] for row in rows if row["sha256"]),
               "meaning": "Hashes establish identity, not semantic reading or validation. See coverage.csv and reviewer_coverage.csv.",
               "exclusions": [row for row in rows if row["status"] != "inventoried; content review pending"]}
    (OUT / "inventory_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({key: value for key, value in summary.items() if key != "exclusions"}, indent=2))


if __name__ == "__main__":
    main()
