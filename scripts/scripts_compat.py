from __future__ import annotations

from pathlib import Path

from aasvr.config import load_aasvr_config
from aasvr.pipeline import run_aasvr_on_frame
from aasvr.toydata import make_toy_hydroponic_data

ROOT = Path(__file__).resolve().parents[1]


def run_methods_toy() -> None:
    out = ROOT / "results/metrics/toy_aasvr_decisions.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    frame = make_toy_hydroponic_data()
    decisions = run_aasvr_on_frame(frame, ROOT / "configs/methods/aasvr.yaml")
    decisions.to_csv(out, index=False)
    load_aasvr_config(ROOT / "configs/methods/aasvr.yaml")

