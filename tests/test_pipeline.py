from pathlib import Path

import pandas as pd

from aasvr.config import load_aasvr_config
from aasvr.pipeline import run_aasvr_on_frame
from aasvr.registry import sensors_from_metadata
from aasvr.toydata import make_toy_hydroponic_data
from scripts.download_datasets import render_note
from scripts.run_all import _has_raw_csv


def test_toy_pipeline_runs(tmp_path: Path) -> None:
    config_path = tmp_path / "aasvr.yaml"
    config_path.write_text(
        """
q_min: 0.7
scale_multiplier: 3.0
sensors:
  - name: pH
    physical_min: 0
    physical_max: 14
    control_low: 5.8
    control_high: 6.5
    rate_limit: 0.03
    uncertainty: 0.01
    xi_min: 0.05
    window: 9
    confirm_samples: 3
    cooldown_samples: 3
""",
        encoding="utf-8",
    )
    frame = make_toy_hydroponic_data(20)[["timestamp", "pH"]]
    decisions = run_aasvr_on_frame(frame, config_path)
    assert isinstance(decisions, pd.DataFrame)
    assert len(decisions) == len(frame)
    assert load_aasvr_config(config_path).sensors[0].name == "pH"


def test_download_note_documents_raw_data_policy() -> None:
    note = render_note(
        "tep",
        {
            "source": "https://example.test",
            "access": "manual",
            "role": "benchmark",
            "path": "data/raw/tep",
            "download_profiles": {
                "paper": {
                    "action": "local_subset_required",
                    "expected_size_mb": 50,
                }
            },
            "subset_protocol": {
                "subset_files": "fixed subset",
                "selection_rationale": "predefined diversity",
            },
        },
        profile="paper",
    )
    assert "Raw files" in note
    assert "data/raw/tep" in note
    assert "fixed subset" in note
    assert "local_subset_required" in note


def test_download_note_full_profile_lists_large_files() -> None:
    note = render_note(
        "tep",
        {
            "source": "https://example.test",
            "access": "manual",
            "role": "benchmark",
            "path": "data/raw/tep",
            "download_profiles": {
                "full": {
                    "action": "figshare_files",
                    "expected_size_mb": 1000,
                    "files": [{"name": "large.h5", "size_bytes": 1000, "url": "https://example.test/large.h5"}],
                }
            },
            "subset_protocol": {},
        },
        profile="full",
    )
    assert "large.h5" in note
    assert "Full-profile files" in note


def test_sensors_from_metadata_uses_physical_bounds_for_generic_datasets() -> None:
    sensors = sensors_from_metadata(
        pd.DataFrame(
            {
                "variable": ["XMEAS1", "XMV1"],
                "role": ["sensor", "actuator"],
                "physical_min": [0.0, 0.0],
                "physical_max": [10.0, 1.0],
                "control_low": ["", ""],
                "control_high": ["", ""],
                "rate_limit": [0.5, 1.0],
                "expected_direction": ["unknown", "unknown"],
            }
        )
    )
    assert len(sensors) == 1
    assert sensors[0].name == "XMEAS1"
    assert sensors[0].control_low == 0.0
    assert sensors[0].control_high == 10.0


def test_external_raw_csv_detection(tmp_path: Path, monkeypatch) -> None:
    import scripts.run_all as run_all

    monkeypatch.setattr(run_all, "ROOT", tmp_path)
    raw_dir = tmp_path / "data/raw/tep"
    raw_dir.mkdir(parents=True)
    assert not _has_raw_csv("tep")
    (raw_dir / "sample.csv").write_text("timestamp,x\n2026-01-01,1\n", encoding="utf-8")
    assert _has_raw_csv("tep")
