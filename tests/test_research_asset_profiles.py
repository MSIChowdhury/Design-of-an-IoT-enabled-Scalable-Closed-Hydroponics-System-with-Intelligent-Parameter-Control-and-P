import importlib
import gzip

study = importlib.import_module("scripts.74_profile_research_assets")


def test_profiles_distinguish_lfs_unavailability_from_real_missingness(tmp_path):
    pointer = tmp_path / "unavailable.csv"
    pointer.write_text("version https://git-lfs.github.com/spec/v1\noid sha256:123\nsize 123\n")
    assert "pointer only" in study.csv_profile(pointer)["status"]
    data = tmp_path / "real.csv"
    data.write_text("timestamp;value\n2024-01-01;1\n2024-01-01;1\n2024-01-02;\n")
    profile = study.csv_profile(data)
    assert profile["rows"] == 3 and profile["duplicate_rows"] == 1
    assert profile["missing"]["value"] == 1
    assert profile["timestamps"]["duplicate_nonmissing"] == 1
    compressed = tmp_path / "real.csv.gz"
    with gzip.open(compressed, "wt") as stream:
        stream.write(data.read_text())
    assert study.csv_profile(compressed) == profile
