"""Validate reliable command-event settings, lock them, then evaluate."""

from __future__ import annotations

import hashlib
import json
import runpy
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

from aasvr.config import load_aasvr_config, load_yaml
from aasvr.reliable_events import Delivery, replay_reliable
from aasvr.telemetry import Link, score

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/metrics/reliable_events"


def settings(cfg):
    return [
        (p, f"r{r}_n{n}", r, n)
        for p in cfg["policies"]
        for r in cfg["retry_seconds"]
        for n in cfg["max_attempts"]
    ]


def job(split, sensor_name, policy, setting, retry, attempts):
    common = load_yaml(ROOT / "configs/experiments/telemetry.yaml")
    helper = runpy.run_path(str(ROOT / "scripts/41_telemetry_feasibility.py"))
    times, source, values, absolute, _ = helper["load_block"](split, common)
    days = pd.to_datetime(absolute, unit="s", utc=True).strftime("%Y-%m-%d").to_numpy()
    sensor = next(
        s
        for s in load_aasvr_config(ROOT / "configs/methods/aasvr.yaml").sensors
        if s.name == sensor_name
    )
    delivery = Delivery(
        retry_seconds=retry,
        max_attempts=attempts,
        cancellation=policy != "without_cancellation",
        acknowledgments=policy != "without_acknowledgments",
        expiry_seconds=common["command_expiry_seconds"],
        freshness_seconds=common["source_freshness_seconds"],
    )
    rows, clusters = [], []
    seeds = [0] if split == "validation" else [101 + i for i in common["network_seeds"]]
    for network in common["networks"]:
        link = Link(**network)
        for seed in [seeds[0]] if link.name == "ideal" else seeds:
            result = replay_reliable(
                times,
                source,
                values[sensor_name],
                sensor.control_low,
                sensor.control_high,
                link,
                delivery,
                seed=common["seed"] + seed,
            )
            meta = dict(
                split=split,
                sensor=sensor_name,
                policy=policy,
                setting=setting,
                network=link.name,
                seed=seed,
            )
            counters = {k: v for k, v in result.items() if np.isscalar(v)}
            for deadline in common["deadlines_seconds"]:
                scored = score(
                    times,
                    result["reference"],
                    result["actions"],
                    result["directions"],
                    deadline,
                    common["warmup_seconds"],
                    common["tail_seconds"],
                )
                scalar = {k: v for k, v in scored.items() if np.isscalar(v)}
                rows.append(
                    {
                        **meta,
                        **counters,
                        **scalar,
                        "deadline": deadline,
                        "bytes": result["forward_bytes"] + result["ack_bytes"],
                        "messages": result["forward_messages"] + result["ack_messages"],
                    }
                )
                if split == "evaluation" and deadline == common["selection_deadline_seconds"]:
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


def aggregate(g):
    n = g.opportunities.sum()
    return dict(
        coverage=g.matched.sum() / n,
        undesirable_fraction=(g.wrong_direction.sum() + g.unnecessary.sum()) / n,
        opportunities=int(n),
        matched=int(g.matched.sum()),
        unnecessary=int(g.unnecessary.sum()),
        wrong_direction=int(g.wrong_direction.sum()),
        authorizations=int(g.authorizations.sum()),
        bytes=int(g.bytes.sum()),
        forward_bytes=int(g.forward_bytes.sum()),
        ack_bytes=int(g.ack_bytes.sum()),
        messages=int(g.messages.sum()),
        retries=int(g.sender_retries.sum()),
        cancellations=int(g.sender_cancellations.sum()),
        late_cancellations=int(g.receiver_late_cancellations.sum()),
        duplicates=int(g.receiver_duplicates.sum()),
        expired=int(g.receiver_expired.sum()),
        delay_seconds=g.delay_sum.sum() / g.matched.sum() if g.matched.sum() else np.nan,
    )


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    common = load_yaml(ROOT / "configs/experiments/telemetry.yaml")
    cfg = load_yaml(ROOT / "configs/experiments/reliable_events.yaml")
    old = json.loads((ROOT / "results/metrics/telemetry/manifest.json").read_text())
    digest = hashlib.sha256(
        (ROOT / "data/processed/hydro_exp1_measurements.parquet").read_bytes()
    ).hexdigest()
    if old["config"] != common or old["source_sha256"] != digest:
        raise ValueError(
            "Existing baseline population/config changed; rerun make telemetry-feasibility first"
        )
    baseline_code = json.loads(
        (ROOT / "results/metrics/telemetry/implementation_manifest.json").read_text()
    )
    for name in (
        "src/aasvr/telemetry.py",
        "scripts/41_telemetry_feasibility.py",
        "configs/methods/aasvr.yaml",
    ):
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != baseline_code[name]:
            raise ValueError(
                f"Baseline implementation changed: {name}; rerun telemetry-feasibility"
            )
    (OUT / "manifest.json").write_text(
        json.dumps(
            dict(
                common=common,
                delivery=cfg,
                source_sha256=digest,
                baseline_manifest_sha256=hashlib.sha256(
                    (ROOT / "results/metrics/telemetry/manifest.json").read_bytes()
                ).hexdigest(),
                source_history="Retrospective follow-up; evaluation periods have been inspected in earlier studies.",
                comparison="Same source blocks/controller/forward network draws/seeds as previous telemetry study; ACK traffic is impaired and charged.",
            ),
            indent=2,
        )
    )
    choices = None
    for split in ("validation", "evaluation"):
        tasks = []
        for policy, setting, retry, attempts in settings(cfg):
            if (
                split == "evaluation"
                and not ((choices.policy == policy) & (choices.setting == setting)).any()
            ):
                continue
            tasks.extend((split, s, policy, setting, retry, attempts) for s in common["sensors"])
        rows, clusters = [], []
        with ProcessPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(job, *task) for task in tasks]
            for i, future in enumerate(as_completed(futures)):
                a, b = future.result()
                rows.extend(a)
                clusters.extend(b)
                if (i + 1) % 12 == 0 or i + 1 == len(tasks):
                    print(f"{split}: {i + 1}/{len(tasks)} jobs complete", flush=True)
        detail = pd.DataFrame(rows).sort_values(
            ["sensor", "policy", "setting", "network", "seed", "deadline"]
        )
        detail.to_csv(OUT / f"{split}_detail.csv", index=False)
        summary = []
        for key, g in detail.groupby(["policy", "setting", "network", "deadline"]):
            summary.append(
                dict(zip(["policy", "setting", "network", "deadline"], key), **aggregate(g))
            )
        summary = pd.DataFrame(summary)
        summary.to_csv(OUT / f"{split}_operating_points.csv", index=False)
        # Check old and new event denominators before comparing outcomes.
        previous = pd.read_csv(ROOT / f"results/metrics/telemetry/{split}_detail.csv")
        previous = previous[previous.policy == "edge_events"]
        p = (
            previous.groupby(["sensor", "network", "seed", "deadline"])
            .opportunities.first()
            .sort_index()
        )
        q = (
            detail.groupby(["sensor", "network", "seed", "deadline"])
            .opportunities.first()
            .sort_index()
        )
        assert p.equals(q), "Reference opportunity population diverged"
        if split == "validation":
            choices = []
            main = summary[summary.deadline == common["selection_deadline_seconds"]]
            for target in common["minimum_coverages"]:
                for policy, g in main.groupby("policy"):
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
                        & (candidates.max_error <= common["maximum_unnecessary_and_wrong_fraction"])
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
            print("Validation selections locked before evaluation.", flush=True)
        else:
            pd.DataFrame(clusters).to_csv(OUT / "evaluation_day_clusters.csv", index=False)
    print(f"Completed: {OUT}", flush=True)


if __name__ == "__main__":
    main()
