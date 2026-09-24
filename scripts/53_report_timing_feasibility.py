"""Per-command attribution, component costs, and empirical timing frontiers."""

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
OUT = ROOT / "results/metrics/timing_feasibility"
FIG = ROOT / "results/figures/timing_feasibility"


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
    cfg = load_yaml(ROOT / "configs/experiments/timing_feasibility.yaml")
    detail = pd.read_csv(OUT / "detail.csv")
    clusters = pd.read_csv(OUT / "clusters.csv")
    assert (detail.groupby(["scenario", "sensor", "seed"]).opportunities.nunique() == 1).all()
    rng = np.random.default_rng(cfg["seed"])
    summaries = []
    paired = []
    for scenario, block in clusters.groupby("scenario"):
        days, seeds = sorted(block.day.unique()), sorted(block.seed.unique())
        di = rng.integers(len(days), size=(cfg["bootstrap_replicates"], len(days)))
        si = rng.integers(len(seeds), size=(cfg["bootstrap_replicates"], len(seeds)))
        draws, points = {}, {}
        for variant, g in block.groupby("variant"):
            a = g.groupby(["day", "seed"])[["opportunities", "matched", "undesirable"]].sum()
            a = (
                a.reindex(pd.MultiIndex.from_product([days, seeds]))
                .to_numpy()
                .reshape(len(days), len(seeds), 3)
            )
            sample = a[di[:, :, None], si[:, None, :]].sum(axis=(1, 2))
            draws[variant] = sample[:, 1:] / sample[:, :1]
            t = a.sum(axis=(0, 1))
            points[variant] = t[1:] / t[0]
            ci = np.quantile(draws[variant], [0.025, 0.975], axis=0)
            raw = detail[(detail.scenario == scenario) & (detail.variant == variant)]
            summaries.append(
                dict(
                    scenario=scenario,
                    variant=variant,
                    stage=raw.stage.iloc[0],
                    bound=int(raw.bound.iloc[0]),
                    scheduler=raw.scheduler.iloc[0],
                    coverage=points[variant][0],
                    error=points[variant][1],
                    coverage_low=ci[0, 0],
                    coverage_high=ci[1, 0],
                    error_low=ci[0, 1],
                    error_high=ci[1, 1],
                    opportunities=int(t[0]),
                    matched=int(t[1]),
                    bytes=int(raw.bytes.sum()),
                    heartbeat_bytes=int(raw.heartbeat_bytes.sum()),
                    repeated_outputs=int(raw.repeated_outputs.sum()),
                    expired_outputs=int(raw.expired_outputs.sum()),
                    cooldown_violations=int(raw.cooldown_violations.sum()),
                )
            )
        for variant in points:
            for baseline in {"current_b0_poll", variant.replace("_deadline", "_poll")}:
                if baseline == variant:
                    continue
                ci = np.quantile(draws[variant] - draws[baseline], [0.025, 0.975], axis=0)
                for j, metric in enumerate(("coverage", "error")):
                    paired.append(
                        dict(
                            scenario=scenario,
                            variant=variant,
                            baseline=baseline,
                            metric=metric,
                            difference=points[variant][j] - points[baseline][j],
                            low=ci[0, j],
                            high=ci[1, j],
                        )
                    )
    summary = pd.DataFrame(summaries)
    comparisons = pd.DataFrame(paired)
    summary.to_csv(OUT / "summary.csv", index=False)
    comparisons.to_csv(OUT / "paired_intervals.csv", index=False)
    # Every scored reference opportunity appears in a compressed ledger.
    reasons = []
    interval_counts = []
    total_ledger = 0
    for path in sorted((OUT / "ledgers").glob("*.csv.gz")):
        frame = pd.read_csv(path)
        total_ledger += len(frame)
        reasons.append(
            frame.groupby(["variant", "scenario", "reason"]).size().rename("commands").reset_index()
        )
        misses = frame[~frame.matched]
        for (variant, scenario), g in misses.groupby(["variant", "scenario"]):
            arrived = g[np.isfinite(g.first_arrival)]
            interval_counts.append(
                dict(
                    variant=variant,
                    scenario=scenario,
                    missed=len(g),
                    never_arrived=len(g) - len(arrived),
                    timing_feasible=int(arrived.timing_feasible.sum()),
                    timing_empty=int((~arrived.timing_feasible).sum()),
                    feasible_without_poll_tick=int(
                        (arrived.timing_feasible & ~arrived.poll_tick_exists).sum()
                    ),
                )
            )
    reasons = (
        pd.concat(reasons).groupby(["variant", "scenario", "reason"], as_index=False).commands.sum()
    )
    reasons.to_csv(OUT / "reason_counts.csv", index=False)
    intervals = pd.DataFrame(interval_counts).groupby(["variant", "scenario"], as_index=False).sum()
    intervals.to_csv(OUT / "interval_counts.csv", index=False)
    assert total_ledger == detail.opportunities.sum()
    assert not reasons.reason.str.startswith("other_terminal_").any(), (
        "Unexplained terminal state in ledger"
    )
    routine = summary[summary.scenario != "uncertain_output"]
    frontier = routine.groupby(["variant", "stage", "bound", "scheduler"], as_index=False).agg(
        worst_coverage=("coverage", "min"),
        worst_error=("error", "max"),
        bytes=("bytes", "sum"),
        repeated_outputs=("repeated_outputs", "sum"),
        expired_outputs=("expired_outputs", "sum"),
        cooldown_violations=("cooldown_violations", "sum"),
    )
    frontier["structural_violations"] = frontier[
        ["repeated_outputs", "expired_outputs", "cooldown_violations"]
    ].sum(axis=1)
    # Observed Pareto screen only, within stage and assumed B: no cross-guarantee equivalence.
    frontier["dominated_within_contract"] = False
    for (stage, bound), g in frontier.groupby(["stage", "bound"]):
        for i, a in g.iterrows():
            for j, b in g.iterrows():
                if i == j:
                    continue
                if (
                    b.worst_coverage >= a.worst_coverage
                    and b.worst_error <= a.worst_error
                    and b.bytes <= a.bytes
                    and b.structural_violations <= a.structural_violations
                    and (
                        b.worst_coverage > a.worst_coverage
                        or b.worst_error < a.worst_error
                        or b.bytes < a.bytes
                        or b.structural_violations < a.structural_violations
                    )
                ):
                    frontier.loc[i, "dominated_within_contract"] = True
    frontier.to_csv(OUT / "frontier.csv", index=False)
    examples = draw(summary)
    anchor = [
        "current_b0_poll",
        "durable_b0_poll",
        "clock_b0_poll",
        "clock_b16_poll",
        "recovery_b16_poll",
        "recovery_b16_deadline",
    ]
    ablation = summary[(summary.scenario == "ideal") & summary.variant.isin(anchor)].copy()
    old = ablation.loc[ablation.variant == "current_b0_poll", "bytes"].iloc[0]
    ablation["traffic_multiple"] = ablation.bytes / old
    core_reasons = (
        reasons[
            (reasons.variant == "recovery_b16_poll")
            & (reasons.scenario != "uncertain_output")
            & (reasons.reason != "matched")
        ]
        .groupby("reason", as_index=False)
        .commands.sum()
    )
    sensitivities = (
        summary[summary.stage == "recovery"]
        .pivot(index=["bound", "scheduler"], columns="scenario", values="coverage")
        .reset_index()
    )
    core_intervals = intervals[(intervals.variant == "recovery_b16_poll")]
    unknown = summary[(summary.scenario == "uncertain_output") & summary.variant.isin(anchor)]
    text = f"""# Timing feasibility and component costs

Completed **{len(detail)} replays** with **{total_ledger:,} independently scored reference opportunities** recorded in compressed per-command ledgers. Repetition across methods/seeds does not create new physical evidence. The clock bounds are sensitivity assumptions; synchronization was not measured. No setting was selected for deployment.

## Ideal-link component isolation

`durable` adds reservations/persisted identity and cooldown, but no clock margin or heartbeat recovery. `clock_b0` additionally reserves the one-second dispatch margin; larger clock variants add the stated clock uncertainty. `recovery` adds fresh-evidence heartbeats and recovery barriers. A durable receiver still blocks unresolved execution even when recovery gates are disabled. Each stage is a weaker/different contract, not an interchangeable competitor.

{md(ablation[["variant", "coverage", "coverage_low", "coverage_high", "error", "traffic_multiple"]])}

## Every missed command: recorded terminal explanation

The table aggregates routine scenarios for recovery B=16 with polling. Primary explanations use documented precedence, not a causal decomposition. All ledgers retain overlapping flags and interval endpoints, so a cancellation cannot be interpreted as proving the timing would otherwise have succeeded. The unresolved-output scenario is reported separately below, not dropped from outputs.

{md(core_reasons)}

{md(core_intervals)}

`timing_feasible` means a nonempty interval at first receipt, conditional on that method's already-realized output history. Subsequent cancellation, disconnection, restart, or uncertainty may invalidate it. It is not a global scheduling optimum. `feasible_without_poll_tick` identifies timing windows containing no point of the 16-second output grid. Never-arrived commands have no arrival-conditioned interval and are counted separately.

## Clock-bound and scheduling sensitivity

Coverage fractions for the full recovery stage:

{md(sensitivities)}

For packet intake at time `a`, prior reserved cooldown endpoint `q`, command creation `c`, source timestamp `s`, assumed clock bound `B`, and dispatch margin `D`, the admissible receiver-clock interval is:

`[max(a, c+B, q+B), min(c+64, s+120)-B-D]`.

If its lower endpoint exceeds its upper endpoint, changing the output polling schedule cannot rescue that command under the current history. If nonempty, the deadline scheduler wakes at its earliest admissible time. At source-tick ties, newly received cancellations are processed first. Both schedulers retain the same 16-second packet-intake and source schedule: this isolates output timing, rather than silently changing network delivery or source sampling. The scheduler uses no future measurements or arrivals.

A useful directed example has `c=s=a=640`, `q=665`, `B=16`, `D=1`. The valid interval is **[681,687] seconds**; ticks 672 and 688 miss it, while an output timer can execute at 681. That earlier output changes later cooldown history, so individual rescue does not imply every later reference event becomes feasible. This result is a software scheduling study, not a hard real-time measurement of timer precision.

## Empirical correctness–coverage–traffic frontier

Worst coverage/error across the four routine scenarios; uncertainty after output is separate because safe unresolved execution intentionally blocks. Dominance is assessed only within the same component stage and clock-bound assumption, using observed point values. It is not a statistical or global optimality claim. Full per-scenario intervals and paired scheduler differences are in the CSV outputs.

{md(frontier[["variant", "worst_coverage", "worst_error", "bytes", "structural_violations", "dominated_within_contract"]])}

## Unresolved execution availability

The first output at or after logical time 20,000 is followed by a simulated crash before completion recording. It is triggered at each method's own first eligible output after that fixed threshold; exact failure instants therefore differ. Durable stages retain an uncertain reservation and stop further outputs, while the volatile current receiver loses memory. This is a diagnostic intervention, not an identical-wall-time causal treatment or another real SIGKILL experiment.

{md(unknown[["variant", "coverage", "error", "repeated_outputs", "expired_outputs", "cooldown_violations"]])}

## Examples, assumptions, and reproducibility

{len(examples)} representative timelines were selected by fixed criteria: earliest scored command for specified method/scenario/reason combinations, with deterministic sensor/seed tie breaks. The plotting script also saves their complete source traces and interval metadata. These include feasible windows missed by polling, empty cooldown windows, recovery rejection, and unresolved execution when present.

Run `docker compose run --rm -T project-shell make timing-feasibility`. See [PROTOCOL.md](PROTOCOL.md). CSVs, compressed command ledgers, source fingerprints, and selected examples are under `results/metrics/timing_feasibility/`. Figures are under `results/figures/timing_feasibility/`.

All main replays have zero actual clock offset and vary assumed B in {{0,1,4,8,16}} seconds. This investigates cost as a function of a hypothetical verified bound; neither the sensor cadence nor these results establish that bound in a deployment. Prior clock-offset/crash findings remain applicable. The same SQLite reservation implementation runs in memory during replay; previous disk/SIGKILL evidence is not relabeled as a new physical or network experiment. All historical sensor periods have been reused. Three paired new network seeds and crossed day/seed bootstrap intervals (1,000 draws) are limited retrospective uncertainty estimates, not simultaneous guarantees.
"""
    (ROOT / "docs/timing_feasibility/RESULTS.md").write_text(text)
    print(ablation[["variant", "coverage", "traffic_multiple"]].to_string(index=False), flush=True)
    print(
        f"All {total_ledger} command records reconciled; no unexplained terminal reasons.",
        flush=True,
    )


def draw(summary):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for scenario in ("ideal", "iid_10", "delay_tail", "restart_correlated"):
        for scheduler, style in [("poll", "--"), ("deadline", "-")]:
            g = summary[
                (summary.scenario == scenario)
                & (summary.stage == "recovery")
                & (summary.scheduler == scheduler)
            ].sort_values("bound")
            axes[0].plot(
                g.bound, 100 * g.coverage, style, marker="o", label=f"{scenario}: {scheduler}"
            )
    axes[0].axhline(95, color="red", alpha=0.5)
    axes[0].set(xlabel="Assumed relative clock bound B (s)", ylabel="Coverage (%)")
    axes[0].legend(fontsize=7)
    ideal = summary[
        (summary.scenario == "ideal")
        & summary.variant.isin(
            [
                "current_b0_poll",
                "durable_b0_poll",
                "clock_b0_poll",
                "clock_b16_poll",
                "recovery_b16_poll",
                "recovery_b16_deadline",
            ]
        )
    ]
    axes[1].barh(ideal.variant, 100 * ideal.coverage)
    axes[1].set_xlabel("Ideal-link coverage (%)")
    fig.suptitle("Timing feasibility: explicit clock assumptions, unchanged source/intake schedule")
    fig.tight_layout()
    fig.savefig(FIG / "frontier.png", dpi=180)
    fig.savefig(FIG / "frontier.pdf")
    plt.close(fig)
    criteria = [
        ("clock_b16_poll", "ideal", "polling_missed_feasible_interval"),
        ("clock_b16_deadline", "ideal", "cooldown_no_interval"),
        ("recovery_b16_poll", "restart_correlated", "recovery_barrier"),
        ("durable_b0_poll", "uncertain_output", "unresolved_execution"),
    ]
    selected = []
    for variant, scenario, reason in criteria:
        candidates = []
        for path in sorted((OUT / "examples").glob(f"{variant}_*.json")):
            candidates += [
                r
                for r in json.loads(path.read_text())
                if r["scenario"] == scenario and r["reason"] == reason
            ]
        if candidates:
            selected.append(
                min(candidates, key=lambda r: (r["command"]["created"], r["sensor"], r["seed"]))
            )
    (OUT / "selected_examples.json").write_text(json.dumps(selected, indent=2))
    if selected:
        fig, axes = plt.subplots(len(selected), 1, figsize=(11, 2.6 * len(selected)), squeeze=False)
        for ax, example in zip(axes[:, 0], selected):
            r = example["command"]
            origin = r["created"]
            ax.step(
                np.array(example["times"]) - origin,
                example["directions"],
                where="post",
                label="reference direction",
            )
            ax.axvline(0, color="black", label="reference command")
            if np.isfinite(r["first_arrival"]):
                ax.axvline(r["first_arrival"] - origin, color="orange", label="first receipt")
            if r["timing_feasible"]:
                ax.axvspan(
                    r["earliest"] - origin,
                    r["latest"] - origin,
                    color="green",
                    alpha=0.2,
                    label="timing interval",
                )
            for o in example["outputs"]:
                ax.plot(o["time"] - origin, o["action"], "rx")
            ax.set(
                xlim=(-64, 96),
                ylim=(-1.3, 1.3),
                yticks=[-1, 0, 1],
                title=f"{example['sensor']} / {example['scenario']}: {example['reason']}",
            )
        axes[0, 0].legend(fontsize=8, loc="lower left")
        axes[-1, 0].set_xlabel("Seconds relative to reference command")
        fig.tight_layout()
        fig.savefig(FIG / "missed_command_timelines.png", dpi=180)
        plt.close(fig)
    return selected


if __name__ == "__main__":
    main()
