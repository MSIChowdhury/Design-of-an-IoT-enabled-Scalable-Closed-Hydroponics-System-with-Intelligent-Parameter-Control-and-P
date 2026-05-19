from pathlib import Path

import pandas as pd
import pytest

from aasvr.agronomics import (
    canonicalize_agronomic_frame,
    compute_linkage_table,
    method_exposure_from_decisions,
    prepare_agronomic_harvest,
    summarize_agronomic_harvest,
    write_agronomic_template,
)


def _harvest_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "experiment": [1, 1, 1, 1],
            "treatment": ["P1", "P1", "P2", "P3"],
            "plant_id": ["p1a", "p1b", "p2a", "p3a"],
            "FMAP_g": [250.0, 260.0, 140.0, 100.0],
            "DMAP_g": [35.0, 34.0, 16.0, 12.0],
            "TPL_cm": [80.0, 82.0, 57.0, 21.0],
            "RL_cm": [35.0, 36.0, 27.0, 6.0],
            "SL_cm": [45.0, 46.0, 30.0, 15.0],
            "TNL_count": [20, 21, 14, 12],
            "NL10_count": [10, 11, 9, 7],
        }
    )


def test_agronomic_template_contains_required_units(tmp_path: Path) -> None:
    path = write_agronomic_template(tmp_path / "template.csv")
    frame = pd.read_csv(path)
    assert {"FMAP_g", "TNL_count", "NL10_count"}.issubset(frame.columns)
    assert frame["treatment"].tolist() == ["P1", "P2", "P3", "P1", "P2", "P3"]


def test_canonicalize_agronomic_frame_treats_leaf_fields_as_counts() -> None:
    harvest = canonicalize_agronomic_frame(_harvest_frame())
    assert pd.api.types.is_integer_dtype(harvest["TNL_count"])
    assert pd.api.types.is_integer_dtype(harvest["NL10_count"])
    assert harvest["NL10_count"].le(harvest["TNL_count"]).all()


def test_canonicalize_agronomic_frame_rejects_bad_leaf_counts() -> None:
    frame = _harvest_frame()
    frame.loc[0, "NL10_count"] = 25
    with pytest.raises(ValueError, match="NL10_count cannot exceed TNL_count"):
        canonicalize_agronomic_frame(frame)


def test_prepare_agronomic_harvest_writes_outputs(tmp_path: Path) -> None:
    raw = tmp_path / "agronomic_harvest.csv"
    _harvest_frame().to_csv(raw, index=False)
    outputs = prepare_agronomic_harvest(
        raw,
        processed_path=tmp_path / "processed.parquet",
        quality_path=tmp_path / "quality.csv",
    )
    assert outputs.processed_path.exists()
    assert outputs.quality_path.exists()
    assert pd.read_parquet(outputs.processed_path).shape[0] == 4


def test_agronomic_summary_and_linkage_are_mechanistic_only(tmp_path: Path) -> None:
    harvest = canonicalize_agronomic_frame(_harvest_frame())
    decisions = tmp_path / "aasvr.csv"
    pd.DataFrame(
        {
            "raw_value": [1.0, 4.0, 2.0],
            "trusted_value": [1.0, 2.0, 2.0],
            "gate_result": ["accept", "reject", "accept"],
            "state": ["normal", "fault", "normal"],
            "unsafe_band": [False, True, False],
            "alert": [False, True, False],
            "actuation_authorized": [False, False, True],
            "reason_codes": ["()", "('actuator_response_residual',)", "()"],
        }
    ).to_csv(decisions, index=False)
    exposure = method_exposure_from_decisions({"aasvr_r": decisions})
    summary = summarize_agronomic_harvest(harvest, bootstrap_resamples=10)
    linkage = compute_linkage_table(harvest, exposure)
    assert not summary.empty
    assert set(linkage["treatment"]) == {"P1"}
    assert linkage["causal_interpretation"].eq("mechanistic_link_only").all()
    assert linkage["untrusted_rate"].iloc[0] > 0
