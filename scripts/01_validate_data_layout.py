from __future__ import annotations

from pathlib import Path

import yaml
from rich.console import Console
from rich.table import Table

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    console = Console()
    table = Table(title="Dataset layout")
    table.add_column("Dataset")
    table.add_column("Role")
    table.add_column("Path")
    table.add_column("Status")
    for config_path in sorted((ROOT / "configs/datasets").glob("*.yaml")):
        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        path = ROOT / data["path"]
        if path.is_dir():
            status = "present" if any(child.name != ".gitkeep" for child in path.iterdir()) else "missing"
        else:
            status = "present" if path.exists() else "missing"
        table.add_row(data["name"], data["role"], data["path"], status)
    console.print(table)


if __name__ == "__main__":
    main()
