"""Summarize locked telemetry results, cluster uncertainty, and loopback timings."""

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
from aasvr.telemetry import Receiver, pack

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/metrics/telemetry"
FIG = ROOT / "results/figures/telemetry"


def udp_receiver(pipe):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", 0))
    sock.settimeout(10)
    pipe.send(sock.getsockname()[1])
    receiver = Receiver(5.8, 6.5)
    while True:
        payload, address = sock.recvfrom(65535)
        if payload == b"STOP":
            break
        msg = json.loads(payload)
        now = max(receiver.last_now, msg["time"])
        action = receiver.receive(payload, now)
        action = action or receiver.step(now)
        sock.sendto(pack(dict(seq=msg["seq"], action=action)), address)
    pipe.send(receiver.stats)
    sock.close()


def protocol_probe():
    parent, child = mp.Pipe()
    process = mp.Process(target=udp_receiver, args=(child,))
    process.start()
    port = parent.recv()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)
    rtts = []
    byte_count = 0
    try:
        for i in range(1100):
            payload = pack(dict(kind="sample", seq=i, time=float(i * 16), value=6.1))
            begin = time.perf_counter_ns()
            sock.sendto(payload, ("127.0.0.1", port))
            answer, _ = sock.recvfrom(65535)
            elapsed = (time.perf_counter_ns() - begin) / 1e6
            assert json.loads(answer)["seq"] == i
            if i >= 100:
                rtts.append(elapsed)
                byte_count += len(payload) + len(answer)
        sock.sendto(b"STOP", ("127.0.0.1", port))
        contracts = parent.recv()
    finally:
        sock.close()
        process.join(timeout=5)
        if process.is_alive():
            process.terminate()
            process.join()
    result = dict(
        messages_measured=len(rtts),
        warmup_messages=100,
        udp_rtt_median_ms=float(np.median(rtts)),
        udp_rtt_p95_ms=float(np.percentile(rtts, 95)),
        udp_rtt_p99_ms=float(np.percentile(rtts, 99)),
        application_bytes_including_ack=byte_count,
        receiver_contracts=contracts,
        scope="Two processes on local UDP loopback; sequential acknowledged sample messages. Not radio or Raspberry Pi performance.",
    )
    (OUT / "loopback_measurement.json").write_text(json.dumps(result, indent=2))
    return result


def md(frame):
    text = [
        "| " + " | ".join(frame.columns) + " |",
        "| " + " | ".join("---" for _ in frame.columns) + " |",
    ]
    for row in frame.itertuples(index=False, name=None):
        text.append(
            "| " + " | ".join(f"{v:.4f}" if isinstance(v, float) else str(v) for v in row) + " |"
        )
    return "\n".join(text)


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    cfg = load_yaml(ROOT / "configs/experiments/telemetry.yaml")
    choices = pd.read_csv(OUT / "locked_selections.csv")
    operating = pd.read_csv(OUT / "evaluation_operating_points.csv")
    days = pd.read_csv(OUT / "evaluation_day_clusters.csv")
    manifest = json.loads((OUT / "manifest.json").read_text())
    rows = []
    for choice in choices.itertuples():
        group = operating[
            (operating.policy == choice.policy) & (operating.setting == choice.setting)
        ]
        for row in group.itertuples():
            full = operating[
                (operating.policy == "full")
                & (operating.network == row.network)
                & (operating.deadline == row.deadline)
            ].iloc[0]
            rows.append(
                {
                    **row._asdict(),
                    "target": choice.target,
                    "selection_status": choice.status,
                    "byte_savings": 1 - row.bytes / full.bytes,
                    "message_savings": 1 - row.messages / full.messages,
                    "evaluation_target_met": row.coverage >= choice.target
                    and row.undesirable_fraction <= cfg["maximum_unnecessary_and_wrong_fraction"],
                }
            )
    report = pd.DataFrame(rows).drop(columns="Index", errors="ignore")
    report.to_csv(OUT / "evaluation_summary.csv", index=False)
    ci = []
    rng = np.random.default_rng(cfg["seed"])
    for (policy, setting, network), g in days.groupby(["policy", "setting", "network"]):
        # Joint day clustering retains all sensors and network seeds in each resample.
        totals = g.groupby("day")[["matched", "opportunities", "undesirable"]].sum()
        a = totals.to_numpy()
        selections = rng.integers(0, len(a), size=(cfg["bootstrap_replicates"], len(a)))
        samples = a[selections].sum(axis=1)
        rates = samples[:, 0] / samples[:, 1]
        errors = samples[:, 2] / samples[:, 1]
        ci.append(
            dict(
                policy=policy,
                setting=setting,
                network=network,
                source_days=len(a),
                coverage_low=np.quantile(rates, 0.025),
                coverage_high=np.quantile(rates, 0.975),
                error_low=np.quantile(errors, 0.025),
                error_high=np.quantile(errors, 0.975),
            )
        )
    pd.DataFrame(ci).to_csv(OUT / "cluster_intervals.csv", index=False)
    # Paired comparisons with the strongest simple policy and event-only baseline.
    comparisons = []
    for target in cfg["minimum_coverages"]:
        selected = choices[choices.target == target].set_index("policy")
        for network in operating.network.unique():
            for baseline in ("threshold", "edge_events"):
                ga = days[
                    (days.policy == "stateful")
                    & (days.setting == selected.loc["stateful", "setting"])
                    & (days.network == network)
                ]
                gb = days[
                    (days.policy == baseline)
                    & (days.setting == selected.loc[baseline, "setting"])
                    & (days.network == network)
                ]
                ta = ga.groupby("day")[["matched", "opportunities", "undesirable"]].sum()
                tb = (
                    gb.groupby("day")[["matched", "opportunities", "undesirable"]]
                    .sum()
                    .loc[ta.index]
                )
                assert np.array_equal(ta.opportunities, tb.opportunities)
                indices = rng.integers(0, len(ta), size=(cfg["bootstrap_replicates"], len(ta)))
                sa = ta.to_numpy()[indices].sum(axis=1)
                sb = tb.to_numpy()[indices].sum(axis=1)
                difference = sa[:, 0] / sa[:, 1] - sb[:, 0] / sb[:, 1]
                comparisons.append(
                    dict(
                        target=target,
                        network=network,
                        baseline=baseline,
                        coverage_difference=ta.matched.sum() / ta.opportunities.sum()
                        - tb.matched.sum() / tb.opportunities.sum(),
                        ci_low=np.quantile(difference, 0.025),
                        ci_high=np.quantile(difference, 0.975),
                    )
                )
    pd.DataFrame(comparisons).to_csv(OUT / "paired_coverage_intervals.csv", index=False)
    draw(report, cfg)
    probe = protocol_probe()
    shown = report[
        (report.target == cfg["minimum_coverages"][0])
        & (report.deadline == cfg["selection_deadline_seconds"])
    ]
    fields = [
        "network",
        "policy",
        "setting",
        "selection_status",
        "coverage",
        "undesirable_fraction",
        "byte_savings",
    ]
    feasible_count = int((choices.status == "selected").sum())
    verdict = (
        "**No policy met the joint validation requirements on every network profile.** "
        "All reported operating points are explicitly diagnostic; the study is not yet a positive "
        "submission result."
        if feasible_count == 0
        else f"{feasible_count} policy/target combinations met validation requirements; inspect "
        "their evaluation transfer before claiming a successful design."
    )
    edge = shown[shown.policy == "edge_events"]
    snapshot = shown[shown.policy == "stateful"]
    impaired_edge = edge[edge.network != "ideal"]
    impaired_snapshot = snapshot[snapshot.network != "ideal"]
    conclusion = (
        f"The simple edge-event policy reduced modeled bytes by "
        f"{100 * edge.byte_savings.mean():.1f}% and retained "
        f"{100 * impaired_edge.coverage.min():.1f}–{100 * impaired_edge.coverage.max():.1f}% "
        f"coverage on impaired links. State snapshots retained "
        f"{100 * impaired_snapshot.coverage.min():.1f}–{100 * impaired_snapshot.coverage.max():.1f}% "
        f"coverage, with mean modeled byte savings of {100 * snapshot.byte_savings.mean():.1f}% "
        f"(negative means increased traffic) and a worst-profile undesirable-command rate of "
        f"{100 * impaired_snapshot.undesirable_fraction.max():.2f}% per reference opportunity. "
        "These results favor investigating reliable event delivery before adding snapshot complexity. "
        "They do not establish novel superiority, physical safety, or energy savings. "
        "Payload encoding and untested retransmission/cancellation protocols could change the tradeoff."
    )
    text = f"""# Telemetry feasibility results

This is a new computational fidelity study. No measured crop, dosing, energy, or closed-loop safety improvement is inferred.

{verdict}

{conclusion}

Input SHA-256: `{manifest["source_sha256"]}`. CPU: {manifest["hardware_cpu"]}. Controller tick: 16 seconds. The complete chronological validation/evaluation blocks are used; source gaps are retained and evidence expires after 120 seconds. Previously used data: this remains retrospective evaluation.

## Selection and evaluation

Settings were locked using validation only. A policy must attain the requested coverage and at most 1% unnecessary/wrong-direction authorizations per reference opportunity on **every** validation network profile. No setting is chosen anew for each evaluation network. Infeasible policies are shown at their validation-maximum-minimum-coverage setting, explicitly as diagnostics.

The table shows the 95% validation target and 64-second event-matching deadline. Byte savings are relative to full reporting on the same network. Values are fractions. Validation has one network realization; evaluation has three different realizations per impaired profile and one deterministic ideal profile. Inference resamples source days jointly across sensors and seeds, not packets as independent experiments.

{md(shown[fields])}

The other target (99%), 16/180-second deadlines, explicit opportunity counts, unwanted-action counts, receiver contract counters, latency, and all settings are in the local CSV outputs. A coverage deficit is not repaired by post-hoc threshold adjustment.

## Paired controller-state comparison

Stateful minus each baseline, with two-sided 95% source-day bootstrap intervals. These compare validation-selected operating points, not identical achieved coverage or bandwidth. They do not establish equivalence or superiority on their own.

{md(pd.DataFrame(comparisons))}

## Measured protocol implementation

Two actual processes exchanged 1,000 acknowledged UDP sample messages on local loopback after 100 warm-up messages. Median RTT: {probe["udp_rtt_median_ms"]:.4f} ms; p95: {probe["udp_rtt_p95_ms"]:.4f} ms; p99: {probe["udp_rtt_p99_ms"]:.4f} ms. Application payload plus acknowledgment bytes: {probe["application_bytes_including_ack"]}. Network impairments in the trace benchmark are **simulated**, not measured radio behavior. The loopback probe is a separate implementation measurement; its ACK traffic is not silently included in the one-way replay protocol.

## Interpretation boundaries

The full-stream reference is a specified software controller, not historical actuator ground truth. The source trajectory is unchanged by replayed commands. All senders observe all locally available measurements: savings concern communication, not sensing energy. Policy payloads use compact JSON; wire-byte accounting adds a modeled 28-byte IPv4/UDP header and counts duplicate copies, but excludes link-layer overhead, encryption, retransmissions, and connection management. Alternative encodings may alter the tradeoff.

All primary traces and large outputs remain local. The protocol is documented in [PROTOCOL.md](PROTOCOL.md). Reproduce with `docker compose run --rm -T project-shell make telemetry-feasibility`.
"""
    (ROOT / "docs/telemetry/RESULTS.md").write_text(text)
    files = [
        "src/aasvr/telemetry.py",
        "scripts/41_telemetry_feasibility.py",
        "scripts/42_report_telemetry.py",
        "configs/experiments/telemetry.yaml",
        "configs/methods/aasvr.yaml",
    ]
    (OUT / "implementation_manifest.json").write_text(
        json.dumps(
            {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in files}, indent=2
        )
    )
    print(
        "Wrote telemetry report, uncertainty tables, plots and loopback measurements.", flush=True
    )


def draw(report, cfg):
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True, sharey=True)
    markers = {
        "full": "o",
        "periodic": "s",
        "delta": "^",
        "threshold": "D",
        "edge_events": "P",
        "stateful": "X",
    }
    for ax, network in zip(axes.flat, [n["name"] for n in cfg["networks"]]):
        g = report[
            (report.target == cfg["minimum_coverages"][0])
            & (report.deadline == cfg["selection_deadline_seconds"])
            & (report.network == network)
        ]
        for row in g.itertuples():
            ax.scatter(
                row.byte_savings * 100,
                row.coverage * 100,
                s=90,
                marker=markers[row.policy],
                label=row.policy,
            )
        ax.axhline(95, linestyle="--", color="gray", alpha=0.5)
        ax.set_title(network.replace("_", " "))
        ax.grid(alpha=0.2)
    axes[0, 0].legend(fontsize=8)
    fig.supxlabel("Modeled wire-byte savings relative to full reporting (%)")
    fig.supylabel("Reference command-event coverage within 64 seconds (%)")
    fig.suptitle("Locked validation settings; infeasible policies retained as diagnostics")
    fig.tight_layout()
    fig.savefig(FIG / "communication_fidelity.png", dpi=180)
    fig.savefig(FIG / "communication_fidelity.pdf")
    plt.close(fig)
    fig, axes = plt.subplots(2, 2, figsize=(12, 7), sharey=True)
    for ax, network in zip(axes.flat, [n["name"] for n in cfg["networks"]]):
        g = report[
            (report.target == cfg["minimum_coverages"][0])
            & (report.deadline == cfg["selection_deadline_seconds"])
            & (report.network == network)
        ]
        ax.bar(g.policy, 100 * g.undesirable_fraction)
        ax.axhline(100 * cfg["maximum_unnecessary_and_wrong_fraction"], color="red", linestyle="--")
        ax.tick_params(axis="x", rotation=35)
        ax.set_title(network.replace("_", " "))
        ax.grid(axis="y", alpha=0.2)
    fig.supylabel("Unnecessary + wrong-direction commands / reference opportunities (%)")
    fig.suptitle("Undesirable-command constraint; dashed line is the declared 1% ceiling")
    fig.tight_layout()
    fig.savefig(FIG / "undesirable_commands.png", dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    main()
