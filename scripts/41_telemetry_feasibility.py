"""Full-block telemetry feasibility study; no manuscript result replacement."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

from aasvr.config import load_aasvr_config, load_yaml
from aasvr.telemetry import Link, replay, score

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/metrics/telemetry"
POLICIES = ("full", "periodic", "delta", "threshold", "edge_events", "stateful")


def settings(cfg):
    result = []
    for policy in POLICIES:
        beats = [16] if policy in ("full", "edge_events") else cfg["heartbeats_seconds"]
        multipliers = cfg["delta_multipliers"] if policy == "delta" else [1]
        for beat in beats:
            for multiplier in multipliers:
                result.append((policy, f"h{beat}_d{multiplier}", beat, multiplier))
    return result


def load_block(split, cfg):
    frame = pd.read_parquet(ROOT / "data/processed/hydro_exp1_measurements.parquet").sort_values(
        "timestamp"
    )
    timestamps = frame.timestamp.astype("int64").to_numpy() / 1e9
    bounds = [
        timestamps[0],
        *[timestamps[0] + f * (timestamps[-1] - timestamps[0]) for f in cfg["split_fractions"]],
        timestamps[-1],
    ]
    k = 1 if split == "validation" else 2
    part = frame[(timestamps >= bounds[k]) & (timestamps < bounds[k + 1])]
    raw_time = part.timestamp.astype("int64").to_numpy() / 1e9
    ticks = np.arange(raw_time[0], raw_time[-1], cfg["controller_tick_seconds"])
    indices = np.searchsorted(raw_time, ticks, side="right") - 1
    values = {s: part[s].to_numpy(dtype=float)[indices] for s in cfg["sensors"]}
    return ticks - ticks[0], raw_time[indices] - ticks[0], values, ticks, bounds


def job(split, sensor_name, policy, setting, heartbeat, multiplier):
    cfg = load_yaml(ROOT / "configs/experiments/telemetry.yaml")
    base = load_aasvr_config(ROOT / "configs/methods/aasvr.yaml")
    sensor = next(s for s in base.sensors if s.name == sensor_name)
    times, source, values, absolute, _ = load_block(split, cfg)
    days = pd.to_datetime(absolute, unit="s", utc=True).strftime("%Y-%m-%d").to_numpy()
    rows, clusters = [], []
    # One prespecified realization per network during selection; three unseen seeds at evaluation.
    seeds = [0] if split == "validation" else [101 + i for i in cfg["network_seeds"]]
    for network in cfg["networks"]:
        link = Link(**network)
        for seed in [seeds[0]] if link.name == "ideal" else seeds:
            begin = time.perf_counter()
            result = replay(
                times,
                source,
                values[sensor_name],
                sensor.control_low,
                sensor.control_high,
                policy,
                heartbeat,
                link,
                seed=cfg["seed"] + seed,
                delta=cfg["delta"][sensor_name] * multiplier,
                freshness=cfg["source_freshness_seconds"],
                event_ttl=cfg["command_expiry_seconds"],
            )
            elapsed = time.perf_counter() - begin
            meta = dict(
                split=split,
                sensor=sensor_name,
                policy=policy,
                setting=setting,
                network=link.name,
                seed=seed,
            )
            for deadline in cfg["deadlines_seconds"]:
                scored = score(
                    times,
                    result["reference"],
                    result["actions"],
                    result["directions"],
                    deadline=deadline,
                    warmup=cfg["warmup_seconds"],
                    tail=cfg["tail_seconds"],
                )
                scalar = {k: v for k, v in scored.items() if np.isscalar(v)}
                rows.append(
                    {
                        **meta,
                        "deadline": deadline,
                        **scalar,
                        "messages": result["sent"],
                        "bytes": result["wire_bytes"],
                        "delivered": result["delivered"],
                        "lost": result["lost"],
                        "runtime_seconds": elapsed,
                        "total_ticks": len(times),
                        **result["contracts"],
                    }
                )
                if split == "evaluation" and deadline == cfg["selection_deadline_seconds"]:
                    for day in np.unique(days):
                        mask = days == day
                        clusters.append(
                            {
                                **meta,
                                "day": day,
                                "opportunities": int(scored["reference_mask"][mask].sum()),
                                "matched": int(scored["matched_mask"][mask].sum()),
                                "undesirable": int(
                                    (
                                        scored["wrong_mask"][mask]
                                        | scored["unnecessary_mask"][mask]
                                    ).sum()
                                ),
                            }
                        )
    return rows, clusters


def aggregate(group):
    opportunities = group.opportunities.sum()
    return dict(
        coverage=group.matched.sum() / opportunities if opportunities else np.nan,
        undesirable_fraction=(group.wrong_direction.sum() + group.unnecessary.sum()) / opportunities
        if opportunities
        else np.nan,
        opportunities=int(opportunities),
        matched=int(group.matched.sum()),
        wrong_direction=int(group.wrong_direction.sum()),
        unnecessary=int(group.unnecessary.sum()),
        messages=float(group.messages.sum()),
        bytes=float(group.bytes.sum()),
        delay_seconds=group.delay_sum.sum() / group.matched.sum()
        if group.matched.sum()
        else np.nan,
        exact_disagreement_fraction=group.exact_disagreement.sum() / group.ticks.sum(),
        stale_fraction=group.stale_ticks.sum() / group.total_ticks.sum(),
        duplicate_or_reordered=int(group.duplicate_or_reordered.sum()),
        expired=int(group.expired.sum()),
        lockout_veto=int(group.lockout_veto.sum()),
    )


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = load_yaml(ROOT / "configs/experiments/telemetry.yaml")
    _, _, _, _, bounds = load_block("validation", cfg)
    manifest = dict(
        config=cfg,
        boundaries_unix=bounds,
        platform=platform.platform(),
        hardware_cpu=next(
            (
                x.split(":", 1)[1].strip()
                for x in Path("/proc/cpuinfo").read_text().splitlines()
                if x.startswith("model name")
            ),
            "unknown",
        ),
        source_sha256=hashlib.sha256(
            (ROOT / "data/processed/hydro_exp1_measurements.parquet").read_bytes()
        ).hexdigest(),
        interpretation="Computational fidelity to a specified full-stream controller; no physical control outcomes.",
        source_history="Previously used dataset; retrospective temporal validation/evaluation.",
        threading={
            k: os.environ.get(k)
            for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")
        },
    )
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2))
    choices = None
    for split in ("validation", "evaluation"):
        tasks = []
        for policy, setting, heartbeat, multiplier in settings(cfg):
            if (
                split == "evaluation"
                and policy != "full"
                and not ((choices.policy == policy) & (choices.setting == setting)).any()
            ):
                continue
            tasks.extend((split, s, policy, setting, heartbeat, multiplier) for s in cfg["sensors"])
        rows, clusters = [], []
        with ProcessPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(job, *task) for task in tasks]
            for i, f in enumerate(as_completed(futures)):
                a, b = f.result()
                rows.extend(a)
                clusters.extend(b)
                if (i + 1) % 12 == 0 or i + 1 == len(tasks):
                    print(f"{split}: {i + 1}/{len(tasks)} sensor-policy jobs", flush=True)
        detail = pd.DataFrame(rows).sort_values(
            ["sensor", "policy", "setting", "network", "seed", "deadline"]
        )
        detail.to_csv(OUT / f"{split}_detail.csv", index=False)
        summary = []
        for keys, g in detail.groupby(["policy", "setting", "network", "deadline"]):
            summary.append(
                dict(zip(["policy", "setting", "network", "deadline"], keys), **aggregate(g))
            )
        summary = pd.DataFrame(summary)
        summary.to_csv(OUT / f"{split}_operating_points.csv", index=False)
        if split == "validation":
            # One common setting per policy, meeting the target on EVERY network profile.
            choices = []
            scores = summary[summary.deadline == cfg["selection_deadline_seconds"]]
            for target in cfg["minimum_coverages"]:
                for policy, g in scores.groupby("policy"):
                    candidates = (
                        g.groupby("setting")
                        .agg(
                            min_coverage=("coverage", "min"),
                            max_error=("undesirable_fraction", "max"),
                            bytes=("bytes", "sum"),
                        )
                        .reset_index()
                    )
                    feasible = candidates[
                        (candidates.min_coverage >= target)
                        & (candidates.max_error <= cfg["maximum_unnecessary_and_wrong_fraction"])
                    ]
                    if len(feasible):
                        best = feasible.sort_values(["bytes", "setting"]).iloc[0]
                        status = "selected"
                    else:
                        best = candidates.sort_values(
                            ["min_coverage", "max_error", "bytes", "setting"],
                            ascending=[False, True, True, True],
                        ).iloc[0]
                        status = "infeasible_diagnostic"
                    choices.append(
                        dict(
                            target=target,
                            policy=policy,
                            setting=best.setting,
                            status=status,
                            validation_min_coverage=best.min_coverage,
                            validation_max_error=best.max_error,
                        )
                    )
            choices = pd.DataFrame(choices)
            choices.to_csv(OUT / "locked_selections.csv", index=False)
            print(
                "Settings locked before evaluation; infeasible policies retained as diagnostics.",
                flush=True,
            )
        else:
            pd.DataFrame(clusters).to_csv(OUT / "evaluation_day_clusters.csv", index=False)
    print(f"Completed telemetry replay: {OUT}", flush=True)


if __name__ == "__main__":
    main()
