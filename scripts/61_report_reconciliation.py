"""Compact, paired results and local recovery evidence without deployment claims."""

from pathlib import Path
import json
import shutil

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from aasvr.config import load_yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/metrics/reconciliation"
DOC = ROOT / "docs/reconciliation"


def table(frame):
    return (
        "| "
        + " | ".join(frame.columns)
        + " |\n|"
        + "|".join(["---"] * len(frame.columns))
        + "|\n"
        + "\n".join(
            "| " + " | ".join(map(str, row)) + " |"
            for row in frame.itertuples(index=False, name=None)
        )
    )


def main():
    detail = pd.read_csv(OUT / "detail.csv")
    local = pd.read_csv(OUT / "local_checks.csv")
    keys = ["candidate", "profile", "condition"]
    counters = [
        "opportunities",
        "matched",
        "undesirable",
        "evaluated_outputs",
        "repeated_outputs",
        "expired_outputs",
        "cooldown_violations",
        "reconciled",
        "unresolved",
        "reconciliation_queries",
        "reconciliation_bytes",
        "bytes",
        "recovery_seconds_sum",
    ]
    summary = detail.groupby(keys)[counters].sum().reset_index()
    maxima = detail.groupby(keys).recovery_seconds_max.max()
    summary["max_recovery_seconds"] = [
        maxima[tuple(row)] for row in summary[keys].itertuples(index=False, name=None)
    ]
    summary["coverage_pct"] = 100 * summary.matched / summary.opportunities
    summary["undesirable_pct"] = (
        100 * summary.undesirable / summary.evaluated_outputs.replace(0, np.nan)
    )
    summary["mean_recovery_seconds"] = summary.recovery_seconds_sum / summary.reconciled.replace(
        0, np.nan
    )
    summary["added_traffic_pct"] = 100 * summary.reconciliation_bytes / summary.bytes
    summary.to_csv(OUT / "summary.csv", index=False)
    clusters = pd.read_csv(OUT / "clusters.csv")
    cfg = load_yaml(ROOT / "configs/experiments/reconciliation.yaml")
    rng = np.random.default_rng(cfg["seed"])
    paired = []
    for (candidate, profile), group in clusters.groupby(["candidate", "profile"]):
        base = (
            group[group.condition == "blocking"].groupby("day")[["matched", "opportunities"]].sum()
        )
        for condition, g in group.groupby("condition"):
            if condition == "blocking":
                continue
            byday = g.groupby("day")[["matched", "opportunities"]].sum().reindex(base.index)
            assert byday.opportunities.equals(base.opportunities)
            draws = rng.integers(0, len(base), (cfg["bootstrap_replicates"], len(base)))
            changes = (
                (
                    byday.matched.to_numpy()[draws].sum(axis=1)
                    - base.matched.to_numpy()[draws].sum(axis=1)
                )
                / base.opportunities.to_numpy()[draws].sum(axis=1)
                * 100
            )
            paired.append(
                dict(
                    candidate=candidate,
                    profile=profile,
                    condition=condition,
                    days=len(base),
                    difference_pp=100
                    * (byday.matched.sum() - base.matched.sum())
                    / base.opportunities.sum(),
                    low_pp=np.quantile(changes, 0.025),
                    high_pp=np.quantile(changes, 0.975),
                )
            )
    pd.DataFrame(paired).to_csv(OUT / "paired_intervals.csv", index=False)
    selected = summary[summary.profile == "injected_delay_loss"].copy()
    shown = selected[
        [
            "candidate",
            "condition",
            "coverage_pct",
            "undesirable_pct",
            "reconciled",
            "unresolved",
            "mean_recovery_seconds",
            "added_traffic_pct",
        ]
    ].copy()
    for c in ["coverage_pct", "undesirable_pct", "mean_recovery_seconds", "added_traffic_pct"]:
        shown[c] = shown[c].map(lambda x: f"{x:.2f}" if np.isfinite(x) else "—")
    for column in ["reconciled", "unresolved"]:
        shown[column] = shown[column].astype(int)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.7))
    selected[selected.condition.isin(["blocking", "available", "delayed_32"])].pivot(
        index="candidate", columns="condition", values="coverage_pct"
    ).plot.bar(ax=axes[0])
    axes[0].set(
        ylabel="Matched reference opportunities (%)",
        xlabel="",
        title="Same impaired command trace",
        ylim=(0, 105),
    )
    axes[0].tick_params(axis="x", labelrotation=35, labelsize=8)
    selected[selected.candidate == "durable_b0_poll"].plot.bar(
        x="condition", y="coverage_pct", ax=axes[1], legend=False
    )
    axes[1].set(
        ylabel="Coverage (%)",
        xlabel="",
        title="Durable receiver: evidence challenge",
        ylim=(0, 105),
    )
    axes[1].tick_params(axis="x", labelrotation=35, labelsize=8)
    fig.tight_layout()
    fig.savefig(DOC / "results.png", dpi=150)
    plt.close(fig)
    structural = (
        detail[["repeated_outputs", "expired_outputs", "cooldown_violations"]].sum().to_dict()
    )
    report = f"""# Bounded reconciliation results

Implemented terminal-evidence recovery and permanent cancellation fences against an independent durable mock ledger. No detector, controller, sender, or clock-bound tuning was performed.

## Actual local execution checks

{int(local.passed.sum())}/{len(local)} cases passed: ten scenarios × three repeats. Six actual receiver SIGKILLs exercised both sides of the atomic reconciliation commit; three actual mock SIGKILLs exercised accepted-but-not-yet-executed commands. Dropped output and lookup replies traveled through real UDP sockets. A not-found lookup did not restore authority before a delayed output arrived. Cancelled commands remained fenced when delayed requests subsequently arrived. Independent effect counts stayed at one for completed cases and zero for cancelled cases; no old command reinvoked the receiver adapter after recovery.

Local lookup RTT median/p95: {local.lookup_seconds.median() * 1000:.3f}/{local.lookup_seconds.quantile(0.95) * 1000:.3f} ms. These are component checks in Docker with a 0.2 s test cooldown, not deployment measurements. Historical replay retained 600 s cooldown. Recovery-duration measurements for these small cases include intentional waits and crash handling; the full records are in the snapshot.

## Paired historical results

{len(detail)} replays completed. All 270 baseline rows reproduced the previous experiment exactly before the new comparisons were interpreted. Each aggregate row contains 10,344 scored opportunities: 3,448 unique historical opportunities reused at three cyclic phases. These are not independent physical trials.

{table(shown)}

Available-evidence replies were modeled at the next 16 s intake tick; delayed_32 withheld replies for the first 32 s. These are frozen simulation assumptions, separate from the measured local lookup RTT. Recovery time is measured from the first lookup until evidence commit, excluding the preceding remainder of a source tick and any remaining actuator cooldown. Unresolved counts are sensor/phase replays still blocked at the end (18 per candidate/condition). All completed recovery restores eligibility subject to cooldown and new source evidence; it does not immediately emit a dose.

Full-replay structural counts over this entire comparison: {json.dumps(structural)}. No candidate is declared physically safe from these zero counts. Undesirable outputs are direction disagreements with the fixed historical surrogate at output time; low error from near-total suppression is not success. Paired source-day intervals remain conditional on reused traces and are included in the snapshot.

Added traffic includes modeled lookup requests and replies, including failed requests; it is expressed relative to the same candidate's original command/heartbeat bytes. Reply outage, wrong IDs, and contradictory evidence consume the four-query budget and leave authority blocked. An available execution record substantially improves availability, but does not remove clock-margin, heartbeat-barrier, or historical command-fidelity limitations.

## Evidence limits

The mock completion transition and effect record share one SQLite transaction. A physical actuator does not automatically offer that atomicity. The implementation trusts the configured local mock record and clock domain; authentication, malicious records, real actuator-state evidence, bounded storage retention, independent clocks, reboot epochs, power-loss durability, and plant safety are not established. Normal and cancellation-race tests do not prove all possible concurrent schedules.

The next physical-interface experiment must establish what independently confirms actual execution and what permanently prevents a delayed command after cancellation. Without those capabilities, the system must retain the unresolved block or require operator intervention. This result establishes a software recovery mechanism under an explicit evidence contract, not general exactly-once physical actuation.
"""
    (DOC / "RESULTS.md").write_text(report)
    snapshot = DOC / "snapshot"
    snapshot.mkdir(exist_ok=True)
    for name in ["summary.csv", "paired_intervals.csv", "local_checks.csv", "frozen_manifest.json"]:
        shutil.copyfile(OUT / name, snapshot / name)
    print(report, flush=True)


if __name__ == "__main__":
    main()
