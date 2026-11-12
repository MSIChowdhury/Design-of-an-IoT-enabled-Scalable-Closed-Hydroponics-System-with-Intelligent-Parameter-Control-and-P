import importlib
from pathlib import Path

audit = importlib.import_module("scripts.71_research_inventory")


def test_inventory_hashes_scientific_data_but_never_credentials_or_symlinks(tmp_path):
    (tmp_path / "data").mkdir()
    (tmp_path / "data/feed.csv").write_text("value\n1\n")
    (tmp_path / ".env").write_text("must not read")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git/config").write_text("must not read")
    (tmp_path / "linked").symlink_to(tmp_path / ".env")
    rows = {row["path"]: row for row in audit.inventory(tmp_path)}
    assert len(rows["data/feed.csv"]["sha256"]) == 64
    assert rows[".env"]["sha256"] == rows["linked"]["sha256"] == ""
    assert ".git/config" not in rows
    assert audit.exclusion(Path("Code Files/Web Interface/channel.json"))
    assert not audit.exclusion(Path("configs/datasets/hai.yaml"))
