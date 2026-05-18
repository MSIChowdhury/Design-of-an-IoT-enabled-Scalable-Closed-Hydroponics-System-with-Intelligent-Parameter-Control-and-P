from pathlib import Path

import pandas as pd

from aasvr.config import load_aasvr_config
from aasvr.pipeline import run_aasvr_on_frame
from aasvr.toydata import make_toy_hydroponic_data


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
