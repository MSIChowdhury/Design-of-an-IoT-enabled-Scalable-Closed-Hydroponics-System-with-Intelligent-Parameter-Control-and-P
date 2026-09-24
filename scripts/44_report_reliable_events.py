"""Report reliable-event outcomes, paired day intervals, and real UDP checks."""

from __future__ import annotations

import hashlib
import json
import multiprocessing as mp
import socket
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from aasvr.config import load_yaml
from aasvr.reliable_events import EventReceiver
from aasvr.telemetry import pack

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/metrics/reliable_events"
FIG = ROOT / "results/figures/reliable_events"


def udp_receiver(pipe):
    receiver = EventReceiver()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", 0))
    sock.settimeout(10)
    pipe.send(sock.getsockname()[1])
    while True:
        payload, address = sock.recvfrom(65535)
        if payload == b"STOP":
            break
        m = json.loads(payload)
        now = max(0.0, receiver.last_now, m.get("created", 0.0))
        ack = receiver.receive(payload, now)
        receiver.step(now)
        sock.sendto(ack, address)
    pipe.send(receiver.stats)
    sock.close()


def probe():
    parent, child = mp.Pipe()
    process = mp.Process(target=udp_receiver, args=(child,))
    process.start()
    if not parent.poll(10):
        process.terminate()
        process.join()
        raise RuntimeError("UDP receiver startup timed out")
    port = parent.recv()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)
    rtts = []
    total_bytes = 0
    try:
        for cycle in range(275):
            eid = 2 * cycle + 1
            created = float(cycle * 608)
            command = dict(
                kind="command", id=eid, rev=0, created=created, source=created, action=-1
            )
            cancelled = dict(
                kind="command",
                id=eid + 1,
                rev=0,
                created=created + 16,
                source=created + 16,
                action=-1,
            )
            messages = [command, command, dict(kind="cancel", id=eid + 1, rev=1), cancelled]
            for m in messages:
                payload = pack(m)
                begin = time.perf_counter_ns()
                sock.sendto(payload, ("127.0.0.1", port))
                ack, _ = sock.recvfrom(65535)
                elapsed = (time.perf_counter_ns() - begin) / 1e6
                response = json.loads(ack)
                assert (response["id"], response["rev"]) == (m["id"], m["rev"])
                if m is cancelled:
                    assert response["status"] == "cancelled"
                if cycle >= 25:
                    rtts.append(elapsed)
                    total_bytes += len(payload) + len(ack)
        sock.sendto(b"STOP", ("127.0.0.1", port))
        if not parent.poll(10):
            raise RuntimeError("UDP receiver shutdown timed out")
        stats = parent.recv()
        assert stats["executed"] == 275 and stats["cancelled"] == 275 and stats["duplicates"] == 550
    finally:
        sock.close()
        process.join(timeout=5)
        if process.is_alive():
            process.terminate()
            process.join()
    result = dict(
        measured_messages=len(rtts),
        warmup_messages=100,
        application_bytes_with_ack=total_bytes,
        median_rtt_ms=float(np.median(rtts)),
        p95_rtt_ms=float(np.percentile(rtts, 95)),
        p99_rtt_ms=float(np.percentile(rtts, 99)),
        receiver_stats=stats,
        scope="Real two-process UDP loopback, logical controller times; duplicates and cancellation-before-command exercised. No physical actuator.",
    )
    (OUT / "loopback.json").write_text(json.dumps(result, indent=2))
    return result


def md(frame):
    rows = [
        "| " + " | ".join(frame.columns) + " |",
        "| " + " | ".join("---" for _ in frame.columns) + " |",
    ]
    for row in frame.itertuples(index=False, name=None):
        rows.append(
            "| " + " | ".join(f"{v:.4f}" if isinstance(v, float) else str(v) for v in row) + " |"
        )
    return "\n".join(rows)


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    common = load_yaml(ROOT / "configs/experiments/telemetry.yaml")
    choices = pd.read_csv(OUT / "locked_selections.csv")
    operating = pd.read_csv(OUT / "evaluation_operating_points.csv")
    previous = pd.read_csv(ROOT / "results/metrics/telemetry/evaluation_operating_points.csv")
    rows = []
    for choice in choices.itertuples():
        g = operating[(operating.policy == choice.policy) & (operating.setting == choice.setting)]
        for r in g.itertuples():
            full = previous[
                (previous.policy == "full")
                & (previous.network == r.network)
                & (previous.deadline == r.deadline)
            ].iloc[0]
            rows.append(
                {
                    **r._asdict(),
                    "target": choice.target,
                    "status": choice.status,
                    "byte_savings": 1 - r.bytes / full.bytes,
                    "evaluation_target_met": r.coverage >= choice.target
                    and r.undesirable_fraction <= common["maximum_unnecessary_and_wrong_fraction"],
                }
            )
    report = pd.DataFrame(rows).drop(columns="Index", errors="ignore")
    report.to_csv(OUT / "evaluation_summary.csv", index=False)
    days = pd.read_csv(OUT / "evaluation_day_clusters.csv")
    old_days = pd.read_csv(ROOT / "results/metrics/telemetry/evaluation_day_clusters.csv")
    rng = np.random.default_rng(common["seed"])
    intervals = []
    for target in common["minimum_coverages"]:
        selected = choices[choices.target == target].set_index("policy")
        for network in operating.network.unique():
            a = days[
                (days.policy == "reliable_events")
                & (days.setting == selected.loc["reliable_events", "setting"])
                & (days.network == network)
            ]
            ta = a.groupby("day")[["matched", "opportunities", "undesirable"]].sum()
            for baseline in ("edge_events", "without_cancellation", "without_acknowledgments"):
                if baseline == "edge_events":
                    b = old_days[(old_days.policy == baseline) & (old_days.network == network)]
                else:
                    b = days[
                        (days.policy == baseline)
                        & (days.setting == selected.loc[baseline, "setting"])
                        & (days.network == network)
                    ]
                tb = (
                    b.groupby("day")[["matched", "opportunities", "undesirable"]]
                    .sum()
                    .loc[ta.index]
                )
                assert np.array_equal(ta.opportunities, tb.opportunities)
                indices = rng.integers(0, len(ta), size=(common["bootstrap_replicates"], len(ta)))
                xa = ta.to_numpy()[indices].sum(axis=1)
                xb = tb.to_numpy()[indices].sum(axis=1)
                for j, metric in ((0, "coverage"), (2, "undesirable_fraction")):
                    diff = xa[:, j] / xa[:, 1] - xb[:, j] / xb[:, 1]
                    intervals.append(
                        dict(
                            target=target,
                            network=network,
                            baseline=baseline,
                            metric=metric,
                            difference=ta.iloc[:, j].sum() / ta.opportunities.sum()
                            - tb.iloc[:, j].sum() / tb.opportunities.sum(),
                            low=np.quantile(diff, 0.025),
                            high=np.quantile(diff, 0.975),
                            source_days=len(ta),
                        )
                    )
    pd.DataFrame(intervals).to_csv(OUT / "paired_intervals.csv", index=False)
    draw(report, previous, common)
    measured = probe()
    summary = report[(report.target == 0.95) & (report.deadline == 64)]
    main_rows = summary[summary.policy == "reliable_events"]
    main_choice = choices[(choices.target == 0.95) & (choices.policy == "reliable_events")].iloc[0]
    passed = main_choice.status == "selected" and main_rows.evaluation_target_met.all()
    verdict = (
        "The reliable protocol passed the declared 95% coverage / 1% error requirements on all validation and evaluation profiles."
        if passed
        else "The reliable protocol did not pass the complete declared validation/evaluation requirement; retain infeasible settings as diagnostics."
    )
    fields = [
        "network",
        "policy",
        "setting",
        "status",
        "coverage",
        "undesirable_fraction",
        "byte_savings",
    ]
    ack_free = summary[summary.policy == "without_acknowledgments"].set_index("network")
    acknowledged = main_rows.set_index("network").loc[ack_free.index]
    same_outcomes = np.allclose(
        ack_free[["coverage", "undesirable_fraction"]],
        acknowledged[["coverage", "undesirable_fraction"]],
    )
    component_note = (
        "Removing ACKs produced identical measured coverage and undesirable-command rates on every profile. "
        if same_outcomes
        else "ACK removal changed measured outcomes; inspect the component rows above. "
    )
    component_note += (
        f"The ACK-free variant saved {100 * ack_free.byte_savings.min():.2f}%–"
        f"{100 * ack_free.byte_savings.max():.2f}% of modeled wire bytes. "
        "Receipt observability should therefore be distinguished from improvements in command fidelity."
    )
    stricter = choices[choices.target == 0.99]
    stricter_note = (
        "No tested policy met the 99% target across all validation profiles."
        if (stricter.status != "selected").all()
        else "Some settings passed the 99% validation target; see locked selections for their status."
    )
    text = f"""# Reliable command-event delivery results

**{verdict}** This is computational command fidelity, not physical plant safety, a prospective replication, or established research novelty.

## Evaluation results

The original source blocks, six sensors, controller timings, forward network profiles, seeds, 64-second matching deadline, and 95%/99% targets are preserved. The new reverse channel is impaired as well. Byte savings include forward commands, retries, cancellations, duplicate copies, and all ACK datagrams, each with the same modeled 28-byte IPv4/UDP header. Values below are fractions; negative byte savings would mean increased traffic.

{md(summary[fields])}

{component_note}

{stricter_note} The 95% result is a point-estimate feasibility criterion, not a confidence-bound guarantee.

Validation choices were saved before evaluation, but this is an **adaptive retrospective follow-up**: prior results on these evaluation periods motivated the protocol. The evaluation set is not newly untouched evidence. All three new policies use the same receiver and bounded-retry machinery; removing cancellation or ACKs provides component comparisons. Neither ablation is silently replaced by a weaker discard-on-cooldown receiver.

## Paired uncertainty

Reliable protocol minus baseline; two-sided percentile 95% intervals from 1,000 joint source-day resamples. All sensors and network seeds for a day stay together. Settings are selected independently per policy from the same validation grid; these are comparisons of tuned variants rather than every parameter held fixed.

{md(pd.DataFrame(intervals))}

## Executable protocol and real UDP check

Stable command IDs and revision-specific ACKs support retry without reexecution. A cancellation creates a higher-revision tombstone even when it arrives before the command. ACK of a lower revision cannot silence cancellation retries. Original creation and source times never change during retry. Receipt ACK does not certify execution; cancellation cannot undo an action already emitted. Output cooldown is authoritative, and only a still-valid command can execute after waiting for it.

A two-process UDP loopback exercise sent {measured["measured_messages"]} measured datagrams after {measured["warmup_messages"]} warm-up messages, including deliberate duplicates and cancellation-before-command. Receiver totals: {measured["receiver_stats"]["executed"]} distinct commands emitted, {measured["receiver_stats"]["cancelled"]} future commands cancelled, {measured["receiver_stats"]["duplicates"]} repeated/older-revision packets suppressed. Median RTT {measured["median_rtt_ms"]:.4f} ms; p95 {measured["p95_rtt_ms"]:.4f} ms; p99 {measured["p99_rtt_ms"]:.4f} ms. These are host loopback measurements with logical controller times, not radio or Raspberry Pi measurements.

## Limitations and artifacts

Unacknowledged cancellation can arrive too late to prevent an action; the study measures that remaining error rather than claiming zero unsafe commands. A 128-second outage exceeds the 64-second command lifetime, making some event loss unavoidable without changing requirements. Controller clocks are synchronized, event IDs are monotonic, and process restart persistence and malicious-packet handling are outside the tested scope. Receiver memory is bounded to the latest command ID/revision and one pending command; state is not persisted across restart. No capacity contention, encryption overhead, sensing-energy measurements, actual dosing, or crop outcomes are evaluated.

Generated outputs: `results/metrics/reliable_events/` and `results/figures/reliable_events/`. The previous telemetry outputs are preserved. Reproduce with `docker compose run --rm -T project-shell make reliable-events`. See [PROTOCOL.md](PROTOCOL.md).
"""
    (ROOT / "docs/reliable_events/RESULTS.md").write_text(text)
    files = [
        "src/aasvr/reliable_events.py",
        "src/aasvr/telemetry.py",
        "scripts/41_telemetry_feasibility.py",
        "scripts/43_reliable_event_benchmark.py",
        "scripts/44_report_reliable_events.py",
        "configs/experiments/telemetry.yaml",
        "configs/experiments/reliable_events.yaml",
        "configs/methods/aasvr.yaml",
    ]
    (OUT / "implementation_manifest.json").write_text(
        json.dumps(
            {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in files}, indent=2
        )
    )
    print(verdict, flush=True)
    print("Wrote reliable-event report, plots, intervals, and real UDP probe.", flush=True)


def draw(report, previous, common):
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8))
    networks = [n["name"] for n in common["networks"]]
    policies = ["edge_events", "reliable_events", "without_cancellation", "without_acknowledgments"]
    x = np.arange(len(networks))
    for j, policy in enumerate(policies):
        if policy == "edge_events":
            g = (
                previous[(previous.policy == policy) & (previous.deadline == 64)]
                .set_index("network")
                .loc[networks]
                .copy()
            )
            full = (
                previous[(previous.policy == "full") & (previous.deadline == 64)]
                .set_index("network")
                .loc[networks]
            )
            g["byte_savings"] = 1 - g.bytes / full.bytes
        else:
            g = (
                report[
                    (report.policy == policy) & (report.target == 0.95) & (report.deadline == 64)
                ]
                .set_index("network")
                .loc[networks]
            )
        for ax, metric in zip(axes, ("coverage", "undesirable_fraction", "byte_savings")):
            ax.plot(x, 100 * g[metric], marker="o", label=policy)
            ax.set_xticks(x, networks, rotation=25)
            ax.grid(alpha=0.2)
    axes[0].axhline(95, color="red", linestyle="--", alpha=0.6)
    axes[1].axhline(1, color="red", linestyle="--", alpha=0.6)
    axes[0].set_ylabel("Command-event coverage (%)")
    axes[1].set_ylabel("Undesirable commands / opportunities (%)")
    axes[2].set_ylabel("Modeled wire-byte savings (%)")
    axes[2].legend(fontsize=8)
    fig.suptitle(
        "Reliable event delivery: locked 95% target settings, ACK/retry/cancel traffic included"
    )
    fig.tight_layout()
    fig.savefig(FIG / "delivery_tradeoffs.png", dpi=180)
    fig.savefig(FIG / "delivery_tradeoffs.pdf")
    plt.close(fig)


if __name__ == "__main__":
    main()
