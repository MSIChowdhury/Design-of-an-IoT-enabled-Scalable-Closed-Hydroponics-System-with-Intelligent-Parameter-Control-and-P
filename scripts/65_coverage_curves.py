"""Coverage-matched operating curves for every validator in the reanalysis.

Reads validation operating points and locked evaluation results from the
extended reanalysis, writes per-method Pareto frontiers, a summary table, and
the coverage-versus-undesirable-authorization figure. Run in Docker.
"""
from __future__ import annotations

import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from aasvr.config import load_yaml

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / os.environ.get("AASVR_REANALYSIS_OUT", "results/metrics/reanalysis_extended")
CONFIG = ROOT / os.environ.get("AASVR_REANALYSIS_CONFIG", "configs/experiments/reanalysis_extended.yaml")
TABLE = ROOT / "results/tables/coverage_matched_summary.csv"
FRONTIER = ROOT / "results/metrics/coverage_frontiers.csv"
FIG = ROOT / "results/figures/coverage_frontiers"
LABELS = {"persistence_only": "Persistence only", "hampel": "Hampel", "cusum": "CUSUM", "lof": "LOF",
          "kalman": "Kalman", "ewma": "EWMA", "moving_median": "Moving median", "glr": "GLR",
          "aasvr_measurement": "AASVR-R supervisor", "aasvr_hold_only": "AASVR-R hold only",
          "aasvr_no_cusum": "AASVR-R without CUSUM"}
# Highlighted methods take fixed categorical slots; the rest stay gray context.
HIGHLIGHT = {"persistence_only": "#2a78d6", "aasvr_measurement": "#eb6834",
             "lof": "#1baf7a", "kalman": "#eda100"}
CONTEXT = "#b4b2a9"


def frontier(group):
    """Settings not dominated on (higher coverage, fewer undesirable authorizations)."""
    ordered = group.sort_values(["coverage", "undesirable_per_trial"], ascending=[False, True])
    keep, best = [], float("inf")
    for row in ordered.itertuples():
        if row.undesirable_per_trial < best:
            keep.append(row.Index)
            best = row.undesirable_per_trial
    return group.loc[keep].sort_values("coverage")


def main():
    cfg = load_yaml(CONFIG)
    deadline = cfg["selection_deadline_seconds"]
    points = pd.read_csv(RUN / "validation_operating_points.csv")
    points = points[(points.deadline == deadline) & (points.method != "always_deny")]
    fronts = pd.concat([frontier(g) for _, g in points.groupby("method")])
    FRONTIER.parent.mkdir(parents=True, exist_ok=True)
    fronts.to_csv(FRONTIER, index=False)
    evaluation = pd.read_csv(RUN / "evaluation_summary.csv")
    evaluation = evaluation[(evaluation.deadline == deadline) & (evaluation.status == "evaluated")]
    rows = []
    for method, group in points.groupby("method"):
        top = group.sort_values(["coverage", "undesirable_per_trial"], ascending=[False, True]).iloc[0]
        row = {"method": LABELS.get(method, method), "settings_searched": len(group),
               "max_validation_coverage": top.coverage,
               "undesirable_at_max_coverage": top.undesirable_per_trial}
        for target in cfg["minimum_coverages"]:
            hit = evaluation[(evaluation.method == method) & (evaluation.target == target)]
            row[f"eval_coverage_at_{target:g}"] = hit.coverage.iloc[0] if len(hit) else None
            row[f"eval_undesirable_at_{target:g}"] = hit.undesirable_per_trial.iloc[0] if len(hit) else None
        rows.append(row)
    table = pd.DataFrame(rows).sort_values("max_validation_coverage", ascending=False)
    table.to_csv(TABLE, index=False, float_format="%.4g")
    print(table.to_string(index=False))
    plot(points, fronts)


def plot(points, fronts):
    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    context = [m for m in fronts.method.unique() if m not in HIGHLIGHT]
    for method in context:
        f = fronts[fronts.method == method]
        ax.plot(f.coverage, f.undesirable_per_trial, color=CONTEXT, lw=1.2, marker="o", ms=3,
                label="Other baselines" if method == context[0] else None, zorder=1)
    for method, color in HIGHLIGHT.items():
        if method not in set(fronts.method):
            continue
        cloud = points[points.method == method]
        ax.scatter(cloud.coverage, cloud.undesirable_per_trial, s=10, color=color, alpha=.25, lw=0, zorder=2)
        f = fronts[fronts.method == method]
        ax.plot(f.coverage, f.undesirable_per_trial, color=color, lw=2, marker="o", ms=5,
                mec="white", mew=1, label=LABELS[method], zorder=3)
    ax.set(xlabel="Useful-authorization coverage (validation)",
           ylabel="Undesirable authorizations per trial", xlim=(0, 1.02))
    ax.grid(alpha=.25, lw=.6)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax.set_title("Operating frontiers: higher coverage at fewer undesirable authorizations is better",
                 fontsize=10, loc="left")
    fig.tight_layout()
    FIG.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG.with_suffix(".pdf"))
    fig.savefig(FIG.with_suffix(".png"), dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    main()
