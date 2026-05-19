from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from aasvr.config import load_aasvr_config
from aasvr.core import AASVRConfig
from aasvr.fault_injection import FaultSpec, inject_fault
from aasvr.pipeline import run_aasvr_with_config
from aasvr.prepare import HYDRO_PRIMARY_SENSORS

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hydro-exp1", action="store_true")
    args = parser.parse_args()
    if not args.hydro_exp1:
        print("Use --hydro-exp1.")
        return
    run()


def run() -> None:
    frame = pd.read_parquet(ROOT / "data/processed/hydro_exp1_measurements.parquet")[
        ["timestamp", *HYDRO_PRIMARY_SENSORS]
    ].copy()
    grid = pd.read_csv(ROOT / "data/synthetic/hydro_exp1_fault_grid.csv")
    trial = _select_trial(grid)
    start = max(int(trial.start) - 40, 0)
    end = min(int(trial.start) + int(trial.duration) + 55, len(frame))
    local_start = int(trial.start) - start
    window = frame.iloc[start:end].reset_index(drop=True)
    spec = FaultSpec(
        sensor=trial.sensor,
        fault_type=trial.fault_type,
        start=local_start,
        duration=int(trial.duration),
        magnitude=float(trial.magnitude),
        seed=int(getattr(trial, "seed", 101)),
    )
    faulted, labels = inject_fault(window, spec)
    config = load_aasvr_config(ROOT / "configs/methods/aasvr.yaml")
    sensors = tuple(sensor for sensor in config.sensors if sensor.name in HYDRO_PRIMARY_SENSORS)
    decisions = run_aasvr_with_config(
        faulted,
        AASVRConfig(
            sensors=sensors,
            q_min=config.q_min,
            scale_multiplier=config.scale_multiplier,
            transient_limit=config.transient_limit,
            persistent_limit=config.persistent_limit,
            rectification_mode=config.rectification_mode,
        ),
    )
    audit = _audit_frame(decisions, labels, sensor=trial.sensor, local_start=local_start)
    out_dir = ROOT / "results/metrics"
    fig_dir = ROOT / "results/figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    audit.to_csv(out_dir / "hydro_exp1_aasvr_audit_trail.csv", index=False)
    _plot_audit(audit, trial.sensor, fig_dir / "hydro_exp1_aasvr_audit_trail.png")
    print(f"Wrote {out_dir / 'hydro_exp1_aasvr_audit_trail.csv'}")


def _select_trial(grid: pd.DataFrame):
    candidates = grid[
        grid["split"].eq("test")
        & grid["sensor"].eq("pH")
        & grid["fault_type"].isin(["spike", "step", "bias"])
        & grid["duration"].ge(5)
    ].copy()
    if candidates.empty:
        candidates = grid[grid["split"].eq("test")].copy()
    return candidates.sort_values(["fault_type", "duration", "magnitude"], ascending=[False, False, False]).iloc[0]


def _audit_frame(decisions: pd.DataFrame, labels: pd.DataFrame, *, sensor: str, local_start: int) -> pd.DataFrame:
    subset = decisions[decisions["sensor"].eq(sensor)].copy().reset_index(drop=True)
    keyed = labels[labels["sensor"].eq(sensor)].reset_index(drop=True)
    subset["sample"] = subset.index
    subset["relative_sample"] = subset["sample"] - local_start
    subset["fault"] = keyed["fault"].astype(bool).to_numpy()[: len(subset)]
    subset["reasons"] = subset["reason_codes"].astype(str)
    for gate, reason in {
        "G_P_physical": "physical_range",
        "G_R_rate": "rate_limit",
        "G_D_trusted_delta": "trusted_delta",
        "G_T_trend": "uncommanded_trend",
        "G_S_stuck": "stuck_at",
        "G_M_missing": "missing",
    }.items():
        subset[gate] = ~subset["reasons"].str.contains(reason, regex=False)
    keep = [
        "relative_sample",
        "timestamp",
        "fault",
        "raw_value",
        "trusted_value",
        "G_P_physical",
        "G_R_rate",
        "G_D_trusted_delta",
        "G_T_trend",
        "G_S_stuck",
        "G_M_missing",
        "trust_score",
        "state",
        "gate_result",
        "rectification_action",
        "actuation_authorized",
        "alert",
        "reason_codes",
        "trust_components",
    ]
    window = subset[subset["relative_sample"].between(-8, 18)].copy()
    return window[keep]


def _plot_audit(audit: pd.DataFrame, sensor: str, path: Path) -> None:
    sns.set_theme(style="whitegrid", context="paper", font_scale=1.0)
    fig, axes = plt.subplots(2, 1, figsize=(6.4, 4.2), sharex=True, height_ratios=[2.0, 1.0])
    x = audit["relative_sample"]
    axes[0].plot(x, audit["raw_value"], label="Raw", color="#666666", linewidth=1.0)
    axes[0].plot(x, audit["trusted_value"], label="Trusted", color="#0072B2", linewidth=1.3)
    rejected = audit[audit["gate_result"].eq("reject")]
    if not rejected.empty:
        axes[0].scatter(rejected["relative_sample"], rejected["raw_value"], color="#D55E00", s=18, label="Rejected")
    authorized = audit[audit["actuation_authorized"].astype(bool)]
    if not authorized.empty:
        axes[0].scatter(authorized["relative_sample"], authorized["trusted_value"], marker="^", color="#009E73", s=28, label="Authorized")
    fault = audit[audit["fault"].astype(bool)]
    if not fault.empty:
        axes[0].axvspan(fault["relative_sample"].min(), fault["relative_sample"].max(), color="#F0E442", alpha=0.25, label="Injected fault")
    axes[0].set_ylabel(sensor)
    axes[0].legend(frameon=False, ncols=2, fontsize=8)
    axes[1].plot(x, audit["trust_score"], color="#0072B2", linewidth=1.2)
    axes[1].scatter(x, audit["gate_result"].eq("reject").astype(int), color="#D55E00", s=12, label="Reject flag")
    axes[1].set_ylabel("Score / flag")
    axes[1].set_xlabel("Samples relative to fault start")
    axes[1].set_ylim(-0.05, 1.05)
    axes[1].legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=220)
    fig.savefig(path.with_suffix(".pdf"))
    plt.close(fig)


if __name__ == "__main__":
    main()
