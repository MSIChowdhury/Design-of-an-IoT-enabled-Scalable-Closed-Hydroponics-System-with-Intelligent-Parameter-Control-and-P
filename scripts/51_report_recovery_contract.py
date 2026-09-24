"""Report recovery-contract correctness separately from availability and traffic."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from aasvr.config import load_yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/metrics/recovery_contract"
FIG = ROOT / "results/figures/recovery_contract"
VIOLATIONS = [
    "repeated_outputs",
    "expired_outputs",
    "cooldown_violations",
    "stale_recovery_outputs",
]


def md(frame):
    return (
        "| "
        + " | ".join(frame.columns)
        + " |\n| "
        + " | ".join(["---"] * len(frame.columns))
        + " |\n"
        + "\n".join(
            "| " + " | ".join(f"{v:.4f}" if isinstance(v, float) else str(v) for v in row) + " |"
            for row in frame.itertuples(index=False, name=None)
        )
    )


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    cfg = load_yaml(ROOT / "configs/experiments/recovery_contract.yaml")
    detail = pd.read_csv(OUT / "detail.csv")
    clusters = pd.read_csv(OUT / "clusters.csv")
    assert (detail.groupby(["scenario", "seed", "sensor"]).opportunities.nunique() == 1).all()
    rng = np.random.default_rng(cfg["seed"])
    summaries, paired = [], []
    for scenario, block in clusters.groupby("scenario"):
        days, seeds = sorted(block.day.unique()), sorted(block.seed.unique())
        di = rng.integers(len(days), size=(cfg["bootstrap_replicates"], len(days)))
        si = rng.integers(len(seeds), size=(cfg["bootstrap_replicates"], len(seeds)))
        samples, points = {}, {}
        for policy, g in block.groupby("policy"):
            a = g.groupby(["day", "seed"])[["opportunities", "matched", "undesirable"]].sum()
            a = (
                a.reindex(pd.MultiIndex.from_product([days, seeds]))
                .to_numpy()
                .reshape(len(days), len(seeds), 3)
            )
            draw = a[di[:, :, None], si[:, None, :]].sum(axis=(1, 2))
            samples[policy] = draw[:, 1:] / draw[:, :1]
            total = a.sum(axis=(0, 1))
            points[policy] = total[1:] / total[0]
            ci = np.quantile(samples[policy], [0.025, 0.975], axis=0)
            raw = detail[(detail.scenario == scenario) & (detail.policy == policy)]
            summaries.append(
                dict(
                    scenario=scenario,
                    policy=policy,
                    in_contract=bool(raw.in_contract.iloc[0]),
                    coverage=points[policy][0],
                    error=points[policy][1],
                    coverage_low=ci[0, 0],
                    coverage_high=ci[1, 0],
                    error_low=ci[0, 1],
                    error_high=ci[1, 1],
                    opportunities=int(total[0]),
                    matched=int(total[1]),
                    undesirable=int(total[2]),
                    bytes=int(raw.bytes.sum()),
                    heartbeat_bytes=int(raw.heartbeat_bytes.sum()),
                    **{k: int(raw[k].sum()) for k in VIOLATIONS},
                    point_pass=bool(points[policy][0] >= 0.95 and points[policy][1] <= 0.01),
                )
            )
        for baseline in ("current", "plain_repetition"):
            ci = np.quantile(samples["recovery_v2"] - samples[baseline], [0.025, 0.975], axis=0)
            for i, metric in enumerate(("coverage", "error")):
                paired.append(
                    dict(
                        scenario=scenario,
                        baseline=baseline,
                        metric=metric,
                        difference=points["recovery_v2"][i] - points[baseline][i],
                        low=ci[0, i],
                        high=ci[1, i],
                    )
                )
    summary, comparisons = pd.DataFrame(summaries), pd.DataFrame(paired)
    summary.to_csv(OUT / "summary.csv", index=False)
    comparisons.to_csv(OUT / "paired_intervals.csv", index=False)
    crash = pd.read_csv(OUT / "crash_probe.csv")
    latency = json.loads((OUT / "journal_latency.json").read_text())
    inside = summary[summary.in_contract]
    structural = inside.groupby("policy")[VIOLATIONS].sum().reset_index()
    candidate = summary[summary.policy == "recovery_v2"].set_index("scenario")
    current = summary[summary.policy == "current"].set_index("scenario").loc[candidate.index]
    candidate["traffic_multiple"] = candidate.bytes / current.bytes
    candidate["current_coverage"] = current.coverage
    candidate["structural_violations"] = candidate[VIOLATIONS].sum(axis=1)
    valid = candidate[candidate.in_contract]
    success = valid.structural_violations.sum() == 0 and crash.passed.all()
    plot(summary)
    text = f"""# Recovery-contract results

**Conditional structural criterion: {"passed in the tested in-contract cases" if success else "failed"}.** This reports finite software tests under the declared assumptions, not a physical exactly-once or plant-safety guarantee. The recovery version met the original 95% coverage / 1% undesirable-command point criteria in **{int(valid.point_pass.sum())}/{len(valid)} in-contract scenarios**. No parameters were retuned.

## Structural failures, kept separate from availability

An initial complete run exposed a review gap in the recovery contract: first returning contact now advances the freshness barrier, requiring subsequently generated evidence. The receiver and a directed test were corrected, and this report comes from rerunning the full unchanged grid and crash probe. No parameters were retuned. Initial outputs/source are archived under `initial_barrier_audit/`; the final run is correctness reanalysis, not an untouched validation claim.

Counts aggregate all six streams and four seeds across the twelve in-contract scenarios, including warm-up/tail. They are replay counts rather than independent physical incidents. The observer detects violations but never vetoes an output. Baselines do not implement a recovery barrier, so their stale-recovery column is not applicable and is recorded as zero rather than evidence of recovery correctness.

{md(structural)}

## Coverage, error, and cost

All rows, including the explicitly unsupported -48-second clock-offset case, are retained. Coverage and error are fractions; error is unnecessary/wrong-direction outputs per reference opportunity. Traffic is offered serialized payload plus 28-byte IPv4/UDP overhead, including lost packets. V2 adds 32-second fresh-evidence heartbeats, which are counted; current/plain repetition do not use them. Coverage matching uses the unchanged independent reference controller and 64-second deadline.

{md(candidate.reset_index()[["scenario", "in_contract", "coverage", "coverage_low", "coverage_high", "current_coverage", "error", "traffic_multiple", "structural_violations", "point_pass"]])}

## Real process crashes and disk durability

{md(crash.groupby("stage", sort=False).agg(trials=("passed", "size"), passed=("passed", "sum"), old_outputs=("old_outputs", "sum"), new_outputs=("new_outputs", "sum"), uncertain=("uncertain", "sum")).reset_index())}

Each test sends SIGKILL to a separate child process, reopens its SQLite journal, retries the original command, then offers a later new command. The mock output is an independently fsynced append-only file. The five boundaries are before receipt, after accepted-state commit, after reservation commit, after output but before completion commit, and after completion commit. Crashes around reservation/output remain uncertain and block even the later command. This intentionally sacrifices availability instead of guessing what happened. An independent reconciliation path is not implemented; elapsed time alone cannot clear uncertainty.

Disk-backed reservation → fsynced mock output → completion commit took median **{latency["median_ms"]:.3f} ms**, p95 **{latency["p95_ms"]:.3f} ms**, p99 **{latency["p99_ms"]:.3f} ms**, maximum **{latency["max_ms"]:.3f} ms** over {latency["samples"]} measured operations after {latency["warmup"]} warm-ups. Host storage measurements do not establish a hard real-time bound or real actuator execution. The historical benchmark uses the same SQLite transactions in memory, retaining the connection across receiver reconstruction; disk/process durability is tested separately.

## Contract and argument

Assume one active receiver, durable untampered journal storage, monotonic sender IDs/timestamps, receiver time `r` with true sender-relative time in `[r-B,r+B]`, and an output adapter that emits within `D` seconds or definitively cannot emit later. Here `B=16 s`, `D=1 s`. The adapter bound is an external integration obligation, not established by average timing tests.

Before output, require `r-B >= command_created`, `r+B+D <= min(command_created+64, source_time+120)`, and `r-B >= persisted_next_allowed`. Reserve identity and `persisted_next_allowed=r+B+D+600` durably before output. These inequalities prevent early/expired output and shortened cooldown within the bounds. A crash leaves either a committed reservation (uncertain and blocked) or a completed identity (never replayed). Accepted but unreserved commands are abandoned at restart. This protects software output issuance; physical exactly-once execution still requires actuator-side support or feedback.

Restart or a 96-second heartbeat timeout sets a durable recovery barrier at the receiver's current upper time bound. First returning contact after silence advances that barrier again, so the returning packet cannot itself restore readiness. Resumption requires a fresh source timestamp and a newly eligible command strictly after the barrier. Old IDs, original timestamps, and expiration are never renewed. Recovery readiness is volatile and must be reestablished after each restart. Clock-invalid indications or backward receiver time latch a block; an undetected violation of the assumed clock bound is not made safe by configuration alone.

## Paired availability/error uncertainty

Crossed source-day and seed resampling (1,000 draws) retains all sensors and paired methods together. Intervals are marginal, not simultaneous guarantees; four network seeds limit tail inference. Structural zero counts are not assigned a zero-risk claim. Current versus recovery changes persistence, uncertainty handling, and heartbeat recovery together; this is a complete contract comparison, not an isolated cancellation ablation.

{md(comparisons[comparisons.baseline == "current"])}

## Reproduce and interpret

Run `docker compose run --rm -T project-shell make recovery-contract`. The source periods are retrospectively reused; new seeds and fault schedules do not create independent physical deployments. This version is stored separately and prior results are preserved. No actual dosing, power-loss/storage-corruption test, networked-actuator execution guarantee, or journal-loss/split-brain protection is claimed. No new two-container UDP benchmark was run for V2; the new execution evidence is the disk-backed SIGKILL probe.

See [PROTOCOL.md](PROTOCOL.md). Generated CSVs, the frozen configuration/source manifest, and machine details are under `results/metrics/recovery_contract/`; the comparison plot is under `results/figures/recovery_contract/`.
"""
    (ROOT / "docs/recovery_contract/RESULTS.md").write_text(text)
    print(
        f"Structural criterion passed: {success}; availability point pass: {valid.point_pass.sum()}/{len(valid)}",
        flush=True,
    )
    print(structural.to_string(index=False), flush=True)


def plot(summary):
    names = sorted(summary.scenario.unique())
    fig, axes = plt.subplots(1, 2, figsize=(12, 7), sharey=True)
    y = np.arange(len(names))
    for j, policy in enumerate(("recovery_v2", "current", "plain_repetition")):
        g = summary[summary.policy == policy].set_index("scenario").loc[names]
        for ax, metric in zip(axes, ("coverage", "error")):
            errors = np.maximum(
                0, 100 * np.array([g[metric] - g[metric + "_low"], g[metric + "_high"] - g[metric]])
            )
            ax.errorbar(
                100 * g[metric], y + (j - 1) * 0.2, xerr=errors, fmt="o", markersize=4, label=policy
            )
    axes[0].set_yticks(y, names)
    axes[0].set_xlabel("Matched reference commands (%)")
    axes[1].set_xlabel("Undesirable commands / opportunities (%)")
    axes[0].axvline(95, color="red", linestyle="--")
    axes[1].axvline(1, color="red", linestyle="--")
    axes[1].legend()
    fig.suptitle("Recovery contract: availability cost with paired 95% intervals")
    fig.tight_layout()
    fig.savefig(FIG / "availability_cost.png", dpi=180)
    fig.savefig(FIG / "availability_cost.pdf")
    plt.close(fig)


if __name__ == "__main__":
    main()
