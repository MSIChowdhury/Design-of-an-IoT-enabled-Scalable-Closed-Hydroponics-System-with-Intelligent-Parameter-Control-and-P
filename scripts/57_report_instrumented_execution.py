"""Report empirical local measurements separately from trace extrapolation."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from aasvr.config import load_yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/metrics/instrumented_execution"
DOC = ROOT / "docs/instrumented_execution"


def table(frame):
    # No optional tabulate dependency.
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
    cfg = load_yaml(ROOT / "configs/experiments/instrumented_execution.yaml")
    data = pd.read_csv(OUT / "transactions.csv")
    measured = data[data.measured]
    rows = []
    metrics = [
        "network_s",
        "acceptance_s",
        "journal_total_s",
        "reserve_s",
        "sender_lateness_s",
        "timer_lateness_s",
        "output_delay_s",
        "adapter_roundtrip_s",
    ]
    for profile, group in measured.groupby("profile"):
        for metric in metrics:
            values = group[metric].dropna().to_numpy() * 1000
            rows.append(
                dict(
                    profile=profile,
                    metric=metric,
                    n=len(values),
                    p50_ms=np.median(values),
                    p95_ms=np.quantile(values, 0.95),
                    p99_ms=np.quantile(values, 0.99),
                    max_ms=max(values),
                )
            )
    timing = pd.DataFrame(rows)
    timing.to_csv(OUT / "timing_summary.csv", index=False)
    restarts = pd.read_csv(OUT / "restart_checks.csv")
    uncertain = pd.read_csv(OUT / "uncertain_checks.csv")
    exchanges = pd.read_csv(OUT / "clock_exchanges.csv")
    detail = pd.read_csv(OUT / "replay_detail.csv")
    clusters = pd.read_csv(OUT / "replay_clusters.csv")
    totals = detail.groupby(["profile", "candidate"]).sum(numeric_only=True).reset_index()
    totals["coverage_pct"] = totals.matched / totals.opportunities * 100
    totals["undesirable_pct"] = np.where(
        totals.evaluated_outputs > 0, totals.undesirable / totals.evaluated_outputs * 100, np.nan
    )
    totals.to_csv(OUT / "replay_summary.csv", index=False)
    # Pair days across candidates; all sensors and phases remain together in each block.
    rng = np.random.default_rng(cfg["seed"])
    effects = []
    for profile, frame in clusters.groupby("profile"):
        baseline = (
            frame[frame.candidate == "current_b0_poll"]
            .groupby("day")[["matched", "opportunities"]]
            .sum()
        )
        for candidate, group in frame.groupby("candidate"):
            candidate_days = (
                group.groupby("day")[["matched", "opportunities"]].sum().reindex(baseline.index)
            )
            assert candidate_days.opportunities.equals(baseline.opportunities)
            draws = rng.integers(0, len(baseline), (cfg["bootstrap_replicates"], len(baseline)))
            delta = (
                (
                    candidate_days.matched.to_numpy()[draws].sum(axis=1)
                    - baseline.matched.to_numpy()[draws].sum(axis=1)
                )
                / baseline.opportunities.to_numpy()[draws].sum(axis=1)
                * 100
            )
            effects.append(
                dict(
                    profile=profile,
                    candidate=candidate,
                    days=len(baseline),
                    coverage_difference_pp=(candidate_days.matched.sum() - baseline.matched.sum())
                    / baseline.opportunities.sum()
                    * 100,
                    low_pp=np.quantile(delta, 0.025),
                    high_pp=np.quantile(delta, 0.975),
                )
            )
    pd.DataFrame(effects).to_csv(OUT / "paired_day_intervals.csv", index=False)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    labels = list(measured.profile.unique())
    for profile in labels:
        group = measured[measured.profile == profile]
        values = np.sort(group.output_delay_s.dropna().to_numpy() * 1000)
        axes[0].plot(values, np.arange(1, len(values) + 1) / len(values), label=profile)
    axes[0].set(
        xlabel="Authorization to mock ledger timestamp (ms)",
        ylabel="Empirical cumulative fraction",
        title="Measured local transactions",
    )
    axes[0].legend(fontsize=8)
    axes[0].grid(alpha=0.2)
    pivot = totals.pivot(index="candidate", columns="profile", values="coverage_pct")
    pivot.plot.bar(ax=axes[1])
    axes[1].set(
        ylabel="Matched reference opportunities (%)",
        xlabel="",
        title="Repeated-trace extrapolation",
        ylim=(0, 105),
    )
    axes[1].tick_params(axis="x", labelrotation=35, labelsize=8)
    axes[1].legend(fontsize=7)
    fig.tight_layout()
    DOC.mkdir(exist_ok=True, parents=True)
    fig.savefig(DOC / "results.png", dpi=160)
    plt.close(fig)
    shown = timing[
        timing.metric.isin(["timer_lateness_s", "output_delay_s", "journal_total_s"])
    ].copy()
    for c in ["p50_ms", "p95_ms", "p99_ms", "max_ms"]:
        shown[c] = shown[c].map(lambda x: f"{x:.3f}")
    comparison = totals[
        [
            "profile",
            "candidate",
            "coverage_pct",
            "undesirable_pct",
            "cooldown_violations",
            "expired_outputs",
            "missing_output_acks",
        ]
    ].copy()
    for c in ["coverage_pct", "undesirable_pct"]:
        comparison[c] = comparison[c].map(lambda x: f"{x:.2f}")
    timer_exceed = int(
        (measured.timer_lateness_s > cfg["requirements"]["timer_lateness_seconds"]).sum()
    )
    output_exceed = int((measured.output_delay_s > cfg["requirements"]["dispatch_seconds"]).sum())
    report = f"""# Local instrumented execution: measured results

Scope: three Docker containers on one host, UDP command transport, SQLite FULL journals, and an independent durable mock-output ledger. No physical actuator was connected. Unmodified prepared historical values selected controller inputs; their historical timestamps remain separate from new local execution timestamps.

## Actual measurements

- {len(measured)} measured transactions; {len(data) - len(measured)} warmup transactions excluded from timing summaries.
- {int(measured.injected_drop.sum())} deliberately dropped command packets; {int(measured.injected_ack_drop.sum())} deliberately suppressed output ACKs among scheduled measured transactions. These are injected conditions, not measured natural loss rates.
- {len(exchanges)} clock exchanges; verified same kernel boot and equal time-namespace offsets for all endpoints. Offset intervals containing zero: {int(((exchanges.offset_low_ns <= 0) & (exchanges.offset_high_ns >= 0)).sum())}/{len(exchanges)}.
- {int(restarts.passed.sum())}/{len(restarts)} actual SIGKILL/restart checks passed across five crash boundaries.
- {len(uncertain)}/{len(uncertain)} uncertain-output followups (including warmup) remained blocked, with no second mock output. Independent lookup is observer evidence and does not automatically restore authority.
- Receiver timer lateness above the prespecified 5 ms budget: {timer_exceed}/{int(measured.timer_lateness_s.notna().sum())}. Authorization-to-mock-record delay above 1 s: {output_exceed}/{int(measured.output_delay_s.notna().sum())}. Observed maxima do not establish hard bounds.

{table(shown)}

All timing values above are milliseconds. Output timing ends at the mock ledger insertion timestamp, before its commit; adapter RTT includes the durable commit and acknowledgment. Journal timing measures save transactions, while acceptance also includes construction/opening overhead. Each transaction uses a distinct stream/journal to isolate crash boundaries; this is not sustained controller-throughput evidence. CPU contention is one busy process pinned to the receiver CPU, not a worst-case load guarantee.

## Fixed-candidate trace extrapolation

{len(detail)} replays: five unchanged receiver/scheduling candidates × six sensors × three local profiles × three cyclic phases. Each profile repeats its 100 measured rows over the historical evaluation block. Phases are dependent sensitivity settings, not independent deployments. Reference opportunities and matching remain independent of receiver decisions.

{table(comparison)}

Packet intake retains the previous 16 s polling model. Even a positive submillisecond delay can defer intake one tick; this is a modeling assumption, not a measured edge-device intake period. Receiver timer lateness and output delay are carried together from the first command receipt's trace row. The volatile baseline excludes measured journal-write costs it does not perform. Sender timer jitter is reported but not applied to historical creation times; the measured network term starts at actual sending. Observer-confirmed mock effects are scored even when acknowledgment is missing. Durable candidates then block indefinitely because reconciliation is unimplemented. No loss is imputed as zero delay, no measured maximum is substituted for a contract bound, and clock bounds B=1/B=16 remain hypothetical.

Cooldown/expiry columns count modeled output-timestamp violations over the full replay, including warmup/tail; coverage and undesirable-output percentages exclude those edges. Undesirable means output direction disagrees with the fixed historical reference at output time. The reference is a surrogate, not physical ground truth. Byte counts in local CSV outputs are modeled protocol traffic, not instrumentation-wire measurements.

Paired source-day bootstrap intervals are saved in `results/metrics/instrumented_execution/paired_day_intervals.csv`; phases and sensors remain together within resampled days. These intervals describe historical block variation conditional on these repeated short traces; they do not quantify deployment/network uncertainty.

## Evidence boundary and next decision

The independent-device 1 ms clock budget and maximum 32 s interruption assumption remain **unverified**. Same-host clock exchanges and host NTP status cannot establish either. Process-kill tests do not establish power-loss durability, reboot clock continuity, physical actuation, or closed-loop plant safety.

These results support a reproducible software execution/recovery experiment. Missing output acknowledgments expose the availability cost of conservative unresolved-execution blocking. Any deployable recovery proposal needs explicit independent reconciliation evidence; silently retrying or resetting would change the contract. Before making an edge-deployment claim, repeat the frozen protocol on separately clocked devices and a timestamped physical/mock interface. No algorithm was retuned using these results.
"""
    (DOC / "RESULTS.md").write_text(report)
    print(report)


if __name__ == "__main__":
    main()
