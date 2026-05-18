from __future__ import annotations

import argparse
import shutil
import subprocess
import urllib.request
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DATASETS = ("tep", "wur", "hai", "swat", "wadi", "damadics")
PUBLIC_DATASETS = ("tep", "wur", "hai")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--profile",
        choices=["minimal", "paper", "full"],
        default="paper",
        help="Acquisition profile. 'paper' avoids very large archive downloads by default.",
    )
    parser.add_argument("--download", action="store_true", help="Execute supported downloads.")
    parser.add_argument("--dry-run", action="store_true", help="Print acquisition plan only.")
    parser.add_argument("--all-public", action="store_true", help="Handle TEP, WUR, and HAI.")
    parser.add_argument("--all", action="store_true", help="Handle every configured external dataset.")
    for name in DATASETS:
        parser.add_argument(f"--{name}", action="store_true", help=f"Handle {name}.")
    args = parser.parse_args()

    selected = _selected_datasets(args)
    for name in selected:
        config = _load_dataset_config(name)
        text = render_note(name, config, profile=args.profile)
        target = ROOT / config["path"]
        if args.dry_run:
            print(text)
            continue
        target.mkdir(parents=True, exist_ok=True)
        out = target / "DOWNLOAD_NOTES.md"
        out.write_text(text, encoding="utf-8")
        print(f"Wrote {out}")
        if args.download:
            _execute_profile(name, config, args.profile, target)


def render_note(name: str, config: dict[str, Any], *, profile: str = "paper") -> str:
    profiles = config.get("download_profiles", {})
    profile_data = profiles.get(profile, {})
    subset = config.get("subset_protocol", {})
    lines = [
        f"# {name} Dataset Acquisition Notes",
        "",
        f"- Source: {config.get('source_url') or config.get('source')}",
        f"- Access: {config.get('access', '')}",
        f"- Selected profile: `{profile}`",
        f"- Profile action: `{profile_data.get('action', 'notes_only')}`",
        f"- Expected size (MB): {profile_data.get('expected_size_mb', 'unknown')}",
        f"- Intended use: {config.get('role', '')}",
        f"- Local target: `{config.get('path')}`",
        "",
        "## Subset protocol",
        "",
        f"- Default profile: {subset.get('default_profile', 'paper')}",
        f"- Subset files: {subset.get('subset_files', 'Use locally placed files only.')}",
        f"- Selected faults/events: {subset.get('selected_faults', 'Dataset-specific labels if present.')}",
        f"- Max runs: {subset.get('max_runs', '')}",
        f"- Max rows: {subset.get('max_rows', '')}",
        f"- Selection rationale: {subset.get('selection_rationale', '')}",
        f"- Limitation: {subset.get('limitation', '')}",
        "",
        "Raw files in this directory are intentionally ignored by git. Commit only loaders, "
        "configs, metadata summaries, and reproducible scripts.",
    ]
    if profile != "full" and profile_data.get("action") == "figshare_files":
        lines.append("")
        lines.append("Large archive downloads are disabled for this profile.")
    if profile == "full" and profile_data.get("files"):
        lines.extend(["", "## Full-profile files", ""])
        for file in profile_data["files"]:
            lines.append(f"- {file['name']}: {file.get('size_bytes', '')} bytes, {file['url']}")
    return "\n".join(lines) + "\n"


def _execute_profile(name: str, config: dict[str, Any], profile: str, target: Path) -> None:
    profile_data = config.get("download_profiles", {}).get(profile, {})
    action = profile_data.get("action", "notes_only")
    if profile != "full" and action in {"figshare_files", "git_lfs_full"}:
        print(f"Skipping {name}; profile {profile} does not allow full archive download.")
        return
    if action == "figshare_files":
        _ensure_space(profile_data, target)
        for file in profile_data.get("files", []):
            _download_file(file["url"], target / file["name"], int(file.get("size_bytes", 0)))
        return
    if action in {"git_metadata_or_shallow_clone", "git_lfs_subset", "git_lfs_full"} and name == "hai":
        _clone_hai(target, full_lfs=action == "git_lfs_full")
        return
    print(f"No automatic download for {name} profile {profile}; use the notes in {target / 'DOWNLOAD_NOTES.md'}.")


def _download_file(url: str, target: Path, expected_size: int) -> None:
    if target.exists() and expected_size and target.stat().st_size == expected_size:
        print(f"Skipping complete file {target}")
        return
    print(f"Downloading {url} -> {target}")
    urllib.request.urlretrieve(url, target)
    if expected_size and target.stat().st_size != expected_size:
        raise RuntimeError(f"Downloaded size mismatch for {target}: expected {expected_size}")


def _clone_hai(target: Path, *, full_lfs: bool) -> None:
    repo = target / "hai_repo"
    if not repo.exists():
        subprocess.run(["git", "clone", "--depth", "1", "https://github.com/icsdataset/hai.git", str(repo)], check=True)
    if full_lfs and shutil.which("git-lfs"):
        subprocess.run(["git", "-C", str(repo), "lfs", "pull"], check=True)
    elif full_lfs:
        print("git-lfs is not installed; cloned HAI metadata but did not fetch LFS payloads.")


def _ensure_space(profile_data: dict[str, Any], target: Path) -> None:
    required = sum(int(file.get("size_bytes", 0)) for file in profile_data.get("files", []))
    free = shutil.disk_usage(target).free
    if required and free < required:
        raise RuntimeError(
            f"Insufficient disk space for full download. Required {required / 1e9:.1f} GB, "
            f"available {free / 1e9:.1f} GB."
        )


def _selected_datasets(args: argparse.Namespace) -> list[str]:
    if args.all:
        return list(DATASETS)
    if args.all_public:
        return list(PUBLIC_DATASETS)
    selected = [name for name in DATASETS if getattr(args, name)]
    return selected or list(DATASETS)


def _load_dataset_config(name: str) -> dict[str, Any]:
    path = ROOT / "configs/datasets" / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(path)
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


if __name__ == "__main__":
    main()
