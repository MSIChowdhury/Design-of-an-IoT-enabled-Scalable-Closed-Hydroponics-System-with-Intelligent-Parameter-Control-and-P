"""Figures for the fault-to-actuation audit manuscript.

Reads the deployment audit, time-in-band table, locked LiveGate results, and
the measured log; writes PDF figures into Paper Files/figure/audit. Run in Docker.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from aasvr import livegate
from aasvr.config import load_aasvr_config, load_yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Paper Files/figure/audit"
BLUE, ORANGE, AQUA, GRAY, INK, MUTED = "#2a78d6", "#eb6834", "#1baf7a", "#b4b2a9", "#0b0b0b", "#52514e"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.titlesize": 10})


def clean_axes(ax, grid_axis="x"):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.grid(axis=grid_axis, alpha=.25, lw=.6)
    ax.set_axisbelow(True)


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(OUT / f"{name}.pdf")
    fig.savefig(OUT / f"{name}.png", dpi=200)
    plt.close(fig)


def audit_commands():
    table = pd.read_csv(ROOT / "results/tables/deployment_audit.csv")
    table["fault"] = table.flagged_commands
    arms = list(dict.fromkeys(table.arm))
    labels = ["Naive threshold", "Range check", "Range + persistence",
              "Reconstructed deployed", "+ liveness", "+ bound rejection"]
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 3.1), sharey=True)
    for ax, sensor in zip(axes, ("pH", "CO2")):
        part = table[table.sensor == sensor].set_index("arm").loc[arms]
        colors = [ORANGE if "liveness" in a else BLUE for a in arms]
        bars = ax.barh(range(len(arms)), part.fault, color=colors, height=.62)
        for bar, value, total in zip(bars, part.fault, part.commands):
            ax.text(bar.get_width() + max(part.fault) * .02, bar.get_y() + bar.get_height() / 2,
                    f"{value} / {total}", va="center", fontsize=9, color=MUTED)
        ax.set_title({"pH": "pH dosing (acid or base)", "CO2": "CO$_2$ injection"}[sensor], loc="left")
        ax.set_xlim(0, max(max(part.fault), 1) * 1.6)
        clean_axes(ax)
    axes[0].set_yticks(range(len(arms)), labels)
    axes[0].invert_yaxis()
    fig.supxlabel("Commands using flagged readings / all executable replay commands", fontsize=10)
    save(fig, "audit_fault_commands")


def time_in_band():
    band = pd.read_csv(ROOT / "results/tables/deployment_time_in_band.csv")
    names = {"pH": "pH", "EC": "EC", "CO2": "CO$_2$", "Water_Temp": "Water temp.", "Air_Temp": "Air temp."}
    band = band.set_index("sensor").loc[list(names)]
    fig, ax = plt.subplots(figsize=(6.8, 2.8))
    left = np.zeros(len(band))
    for column, color, label in (("fraction_below", AQUA, "Below band"), ("fraction_in_band", BLUE, "In band"),
                                 ("fraction_above", ORANGE, "Above band")):
        ax.barh(range(len(band)), band[column], left=left, color=color, height=.6, label=label,
                edgecolor="white", linewidth=1)
        left += band[column].to_numpy()
    for i, value in enumerate(band.fraction_in_band):
        ax.text(1.01, i, f"{value:.0%} in band", va="center", fontsize=9, color=MUTED)
    ax.set_yticks(range(len(band)), list(names.values()))
    ax.invert_yaxis()
    ax.set_xlim(0, 1)
    ax.set_xlabel("Fraction of valid readings over 30 days")
    ax.legend(frameon=False, ncol=3, fontsize=9, loc="lower left", bbox_to_anchor=(0, 1.0))
    clean_axes(ax)
    save(fig, "time_in_band")


def stuck_saturation():
    scenario = pd.read_csv(ROOT / "results/metrics/livegate/evaluation_by_scenario.csv")
    scenario = scenario[scenario.target == 0.8]
    labels = {"persistence_only": "Persistence only", "hampel": "Hampel", "cusum": "CUSUM",
              "kalman": "Kalman", "glr": "GLR", "livegate_no_liveness": "LiveGate, forecast only",
              "livegate": "LiveGate (full)", "livegate_no_forecast": "LiveGate, liveness only"}
    methods = [m for m in labels if m in set(scenario.method)]
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 3.4), sharey=True)
    for ax, kind, title in zip(axes, ("stuck", "saturation"), ("Stuck reading", "Pinned at full scale")):
        part = scenario[scenario.scenario == kind].set_index("method").loc[methods]
        colors = [ORANGE if m in ("livegate", "livegate_no_forecast") else BLUE for m in methods]
        bars = ax.barh(range(len(methods)), part.fault_evidence_per_trial, color=colors, height=.62)
        for bar, value in zip(bars, part.fault_evidence_per_trial):
            ax.text(bar.get_width() + .02, bar.get_y() + bar.get_height() / 2, f"{value:.2f}",
                    va="center", fontsize=9, color=MUTED)
        ax.set_title(title, loc="left")
        ax.set_xlim(0, 1.15)
        ax.set_xlabel("Commands during fault samples\nper trial", fontsize=9)
        clean_axes(ax)
    axes[0].set_yticks(range(len(methods)), [labels[m] for m in methods])
    axes[0].invert_yaxis()
    save(fig, "stuck_saturation")


def co2_trace():
    cfg = load_yaml(ROOT / "configs/experiments/livegate.yaml")
    base = load_aasvr_config(ROOT / "configs/methods/aasvr.yaml")
    frame = pd.read_parquet(ROOT / "data/processed/hydro_exp1_measurements.parquet").sort_values(
        "timestamp").reset_index(drop=True)
    times = frame.timestamp.astype("int64").to_numpy() / 1e9
    development = frame[times < times[0] + cfg["split_fractions"][0] * (times[-1] - times[0])]
    sensors = [s for s in base.sensors if s.name in cfg["sensors"]]
    model = livegate.fit(development, sensors, calibration_fraction=cfg["livegate"]["calibration_fraction"],
                         max_gap=cfg["max_gap_seconds"])["CO2"]
    x = frame.CO2.to_numpy(dtype=float)
    pinned = x == 5000
    starts = np.flatnonzero(pinned & ~np.r_[False, pinned[:-1]])
    lengths = [np.argmin(pinned[s:]) for s in starts]
    start = starts[int(np.argmax(lengths))]
    lo, hi = max(start - 450, 0), min(start + max(lengths) + 450, len(x))
    run = np.ones(hi - lo, dtype=int)
    for i in range(1, hi - lo):
        run[i] = run[i - 1] + 1 if x[lo + i] == x[lo + i - 1] else 1
    rejected = np.array([model.survival(r) < 0.05 for r in run])
    hours = (times[lo:hi] - times[lo]) / 3600
    fig, ax = plt.subplots(figsize=(6.8, 2.8))
    ax.fill_between(hours, 0, 5600, where=rejected, color=ORANGE, alpha=.18, lw=0,
                    label="Rejected by liveness test")
    ax.plot(hours, np.clip(x[lo:hi], 0, 5600), color=BLUE, lw=1, label="Logged CO$_2$")
    ax.axhspan(1900, 2100, color=GRAY, alpha=.35, lw=0, label="Setpoint band")
    ax.set(xlabel="Hours from window start", ylabel="CO$_2$ (ppm)", ylim=(0, 5600))
    ax.legend(frameon=False, fontsize=8.5, ncol=3, loc="lower left", bbox_to_anchor=(0, 1.0))
    clean_axes(ax, "y")
    save(fig, "co2_saturation_trace")


def operating_points():
    points = pd.read_csv(ROOT / "results/metrics/livegate/validation_operating_points.csv")
    points = points[(points.deadline == 180) & (points.method != "always_deny")]
    highlight = {"persistence_only": (BLUE, "Persistence only"), "lof": (AQUA, "LOF"),
                 "livegate": (ORANGE, "LiveGate (full)"),
                 "livegate_no_forecast": ("#6250d6", "LiveGate, liveness only")}
    fig, ax = plt.subplots(figsize=(6.8, 3.8))
    others = points[~points.method.isin(highlight)]
    ax.scatter(others.coverage, others.undesirable_per_trial, s=10, color=GRAY, lw=0, label="Other methods")
    for method, (color, label) in highlight.items():
        part = points[points.method == method]
        ax.scatter(part.coverage, part.undesirable_per_trial, s=26, color=color, lw=.6,
                   edgecolor="white", label=label, zorder=3)
    ax.set(xlabel="Useful-authorization coverage (validation)",
           ylabel="Undesirable authorizations / trial", xlim=(0, 1.02))
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    clean_axes(ax, "both")
    save(fig, "operating_points")


def main():
    audit_commands()
    time_in_band()
    stuck_saturation()
    co2_trace()
    operating_points()
    for source in ("real_fault_heatmap.pdf", "real_fault_heatmap.png"):
        (OUT / source).write_bytes((ROOT / "results/figures" / source).read_bytes())


if __name__ == "__main__":
    main()
