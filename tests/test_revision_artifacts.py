from __future__ import annotations

import importlib

import pandas as pd


revision = importlib.import_module("scripts.35_revision_artifacts")


def test_operating_settings_include_manuscript_setting() -> None:
    settings = revision._operating_settings()
    assert len(settings) == 5 * 5 * 7 * 3
    assert any(
        row["q_min"] == 0.70
        and row["confirm_samples"] == 3
        and row["cooldown_samples"] == 4
        and row["risk_profile"] == "manuscript"
        for row in settings
    )


def test_pareto_mask_keeps_only_non_dominated_rows() -> None:
    frame = pd.DataFrame(
        [
            {
                "balanced_accuracy": 0.80,
                "replay_false_authorized_actuations": 0.10,
                "missed_authorization_rate": 0.50,
                "alerts": 10,
            },
            {
                "balanced_accuracy": 0.82,
                "replay_false_authorized_actuations": 0.09,
                "missed_authorization_rate": 0.49,
                "alerts": 9,
            },
            {
                "balanced_accuracy": 0.84,
                "replay_false_authorized_actuations": 0.30,
                "missed_authorization_rate": 0.30,
                "alerts": 20,
            },
        ]
    )
    assert revision._pareto_mask(frame) == [False, True, True]
