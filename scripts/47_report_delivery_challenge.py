"""Report absolute and paired crossed day/seed intervals and all challenge failures."""

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
OUT = ROOT / "results/metrics/delivery_challenge"
FIG = ROOT / "results/figures/delivery_challenge"


def md(frame):
    return (
        "| "
        + " | ".join(frame.columns)
        + " |\n| "
        + " | ".join(["---"] * len(frame.columns))
        + " |\n"
        + "\n".join(
            "| " + " | ".join(f"{x:.4f}" if isinstance(x, float) else str(x) for x in row) + " |"
            for row in frame.itertuples(index=False, name=None)
        )
    )


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    cfg = load_yaml(ROOT / "configs/experiments/delivery_challenge.yaml")
    detail = pd.read_csv(OUT / "detail.csv")
    clusters = pd.read_csv(OUT / "clusters.csv")
    rng = np.random.default_rng(cfg["seed"])
    summaries, paired = [], []
    for scenario, block in clusters.groupby("scenario", sort=True):
        days, seeds = sorted(block.day.unique()), sorted(block.seed.unique())
        shape = (len(days), len(seeds), 3)
        di = rng.integers(len(days), size=(cfg["bootstrap_replicates"], len(days)))
        si = rng.integers(len(seeds), size=(cfg["bootstrap_replicates"], len(seeds)))
        draws, points = {}, {}
        for policy, g in block.groupby("policy"):
            a = g.groupby(["day", "seed"])[["opportunities", "matched", "undesirable"]].sum()
            a = a.reindex(pd.MultiIndex.from_product([days, seeds])).to_numpy().reshape(shape)
            sample = a[di[:, :, None], si[:, None, :]].sum(axis=(1, 2))
            draws[policy] = sample[:, 1:] / sample[:, :1]
            point = a.sum(axis=(0, 1))
            points[policy] = point[1:] / point[0]
            raw = detail[(detail.scenario == scenario) & (detail.policy == policy)]
            ci = np.quantile(draws[policy], [0.025, 0.975], axis=0)
            summaries.append(
                dict(
                    scenario=scenario,
                    policy=policy,
                    coverage=points[policy][0],
                    error=points[policy][1],
                    coverage_low=ci[0, 0],
                    coverage_high=ci[1, 0],
                    error_low=ci[0, 1],
                    error_high=ci[1, 1],
                    opportunities=int(point[0]),
                    bytes=int(raw.bytes.sum()),
                    repeated_outputs=int(raw.repeated_outputs.sum()),
                    expired_outputs=int(raw.expired_outputs.sum()),
                    cooldown_violations=int(raw.cooldown_violations.sum()),
                    point_pass=points[policy][0] >= cfg["minimum_coverage"]
                    and points[policy][1] <= cfg["maximum_error"],
                    interval_pass=ci[0, 0] >= cfg["minimum_coverage"]
                    and ci[1, 1] <= cfg["maximum_error"],
                )
            )
        for baseline in ("plain_repetition", "acknowledged"):
            differences = draws["candidate"] - draws[baseline]
            ci = np.quantile(differences, [0.025, 0.975], axis=0)
            for j, metric in enumerate(("coverage", "error")):
                paired.append(
                    dict(
                        scenario=scenario,
                        baseline=baseline,
                        metric=metric,
                        difference=points["candidate"][j] - points[baseline][j],
                        low=ci[0, j],
                        high=ci[1, j],
                    )
                )
    summary, comparisons = pd.DataFrame(summaries), pd.DataFrame(paired)
    summary.to_csv(OUT / "summary.csv", index=False)
    comparisons.to_csv(OUT / "paired_intervals.csv", index=False)
    candidate = summary[summary.policy == "candidate"].set_index("scenario")
    plain = summary[summary.policy == "plain_repetition"].set_index("scenario").loc[candidate.index]
    candidate["extra_bytes_pct"] = 100 * (candidate.bytes / plain.bytes - 1)
    figures(summary)
    probes = (
        pd.read_csv(OUT / "network_probe.csv") if (OUT / "network_probe.csv").exists() else None
    )
    assumptions = json.loads((OUT / "assumption_checks.json").read_text())
    benefit = comparisons[
        (comparisons.baseline == "plain_repetition") & (comparisons.metric == "error")
    ]
    robust = benefit[benefit.high < 0]
    text = f"""# Frozen command-delivery challenge results

The candidate passed the 95% coverage / 1% undesirable-command **point criteria in {int(candidate.point_pass.sum())}/{len(candidate)} scenarios**. Its marginal 95% intervals lie entirely within both limits in {int(candidate.interval_pass.sum())}/{len(candidate)} scenarios. These are per-scenario intervals, not simultaneous guarantees over the suite.

No settings were tuned on these results. Candidate and simple repetition both use two transmissions 32 seconds apart, original 64-second expiry, the identical receiver, and a 600-second cooldown. The candidate additionally sends cancellation; the acknowledged comparator adds receipt ACKs. Clock-offset and restart scenarios deliberately violate the current implementation assumptions.

## Operating boundary (candidate)

Fractions below are coverage and undesirable commands per reference opportunity. Bytes include all offered command/cancellation/ACK payloads plus 28-byte IPv4/UDP headers, including lost traffic. Extra bytes compare with the same-receiver plain repetition baseline. Structural violation counts cover the entire replay, including warm-up/tail, and are separate from opportunity-based scoring.

{md(candidate.reset_index()[["scenario", "coverage", "coverage_low", "coverage_high", "error", "error_low", "error_high", "extra_bytes_pct", "repeated_outputs", "expired_outputs", "cooldown_violations", "point_pass"]])}

## Does cancellation add value?

Cancellation's paired error-difference interval excludes zero in the favorable direction in **{len(robust)}/{len(benefit)} scenarios**. This count is descriptive and unadjusted for multiple comparisons. Do not infer equivalence from intervals containing zero, or general superiority from selected favorable rows. Coverage and byte costs must also be considered.

{md(comparisons[comparisons.baseline == "plain_repetition"])}

## Assumption counterexamples

- Restart followed by the same command ID executes it again: **{assumptions["restart_reexecutes_same_id"]}**. Volatile duplicate protection and cooldown are lost.
- A -64-second receiver clock offset permits a command arriving at true time 96 seconds to execute at receiver time 32 seconds despite its 64-second lifetime: **{assumptions["negative_clock_offset_can_execute_truly_expired_command"]}**.

These deterministic counterexamples demonstrate failure modes, not their frequency in a deployment. No automatic recovery or persistence fix was added after seeing the challenge.

## Actual two-container UDP execution

{md(probes[["scenario", "policy", "opportunities", "coverage", "undesirable_fraction", "sent_udp_bytes", "ack_bytes", "processing_p99_us", "tick_lateness_p99_ms"]]) if probes is not None else "Not executed: do not claim actual network validation."}

The probe uses six historical windows selected before execution for maximum direction changes among fixed windows with a reference command. This is a purposive execution check, not a random or independent sample of the deployment. Sender and receiver run in separate Docker containers with actual UDP datagrams on a bridge network. A client-side application relay applies seeded delay and loss; this is not kernel netem or radio testing. Logical time runs 1000x faster; receiver ticks occur eight logical seconds after source ticks. Actual OS scheduling and datagram processing can therefore affect command outcomes. Forward sent UDP bytes exclude packets dropped before the socket; simulated offered bytes include them. Reverse packets traverse the socket before relay impairment. No energy or physical-actuator claims follow.

Receiver peak RSS range: {f"{probes.peak_rss_kib.min() / 1024:.1f}–{probes.peak_rss_kib.max() / 1024:.1f} MiB" if probes is not None else "unavailable"}. This includes Python/import overhead and is the process-lifetime high-water mark, not isolated protocol memory. Detailed timing, CPU, byte counters, environment, and action logs are saved with the CSV outputs.

## Evidence limits and reproduction

This is a frozen **new network challenge on previously reused historical sensor periods**. It is not independent physical replication or a newly untouched sensor dataset. Four new network seeds are paired across methods; all six sensors share exogenous network conditions. Crossed day/seed bootstrap resamples days and network seeds independently, retaining all sensors and paired policies together (1,000 replicates). Only four network seeds limit tail uncertainty; no distribution-free bound is claimed. Repeated seeds do not add physical deployments. All 25 scenarios and all comparator results remain in `summary.csv`; no failed scenario is discarded.

See [PROTOCOL.md](PROTOCOL.md) for the frozen design and reproduction command. Machine-readable outputs are under `results/metrics/delivery_challenge/`; plots are under `results/figures/delivery_challenge/`. The frozen manifest hashes source, configuration, and dataset before execution.
"""
    (ROOT / "docs/delivery_challenge/RESULTS.md").write_text(text)
    print(
        f"Candidate point pass: {candidate.point_pass.sum()}/{len(candidate)}; interval pass: {candidate.interval_pass.sum()}/{len(candidate)}",
        flush=True,
    )
    print(f"Favorable cancellation error intervals: {len(robust)}/{len(benefit)}", flush=True)


def figures(summary):
    names = sorted(summary.scenario.unique())
    fig, axes = plt.subplots(1, 2, figsize=(12, 10), sharey=True)
    y = np.arange(len(names))
    for j, policy in enumerate(("candidate", "plain_repetition", "acknowledged")):
        g = summary[summary.policy == policy].set_index("scenario").loc[names]
        for ax, metric in zip(axes, ("coverage", "error")):
            ax.errorbar(
                100 * g[metric],
                y + (j - 1) * 0.2,
                xerr=100
                * np.array([g[metric] - g[metric + "_low"], g[metric + "_high"] - g[metric]]),
                fmt="o",
                markersize=3,
                label=policy,
                alpha=0.8,
            )
    axes[0].axvline(95, color="red", linestyle="--")
    axes[1].axvline(1, color="red", linestyle="--")
    axes[0].set_yticks(y, names)
    axes[0].set_xlabel("Command-event coverage (%)")
    axes[1].set_xlabel("Undesirable commands / opportunities (%)")
    axes[1].legend()
    fig.suptitle("Frozen challenge: paired methods, crossed day/seed 95% intervals")
    fig.tight_layout()
    fig.savefig(FIG / "operating_boundary.png", dpi=180)
    fig.savefig(FIG / "operating_boundary.pdf")
    plt.close(fig)


if __name__ == "__main__":
    main()
