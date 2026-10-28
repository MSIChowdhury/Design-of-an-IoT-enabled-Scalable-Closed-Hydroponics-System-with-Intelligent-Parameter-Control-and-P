"""Locked LiveGate comparison on the reanalysis protocol plus a real-log audit.

Reuses the windowing, fault injection, detectors, authorization, scoring, and
validation selection of scripts/38_replay_reanalysis.py. Changes, all fixed in
configs/experiments/livegate.yaml before evaluation: deployed setpoints, the
five controlled channels, a full-scale saturation scenario, and the LiveGate
arms. Validation selects every method's setting before evaluation is scored.
Run in Docker.
"""
from __future__ import annotations

import importlib.util
import os
from dataclasses import replace
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.neighbors import LocalOutlierFactor

from aasvr import livegate
from aasvr.config import load_aasvr_config, load_yaml
from aasvr.reanalysis import Timing, authorize, hold_estimate, score_actions, summarize

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("replay", ROOT / "scripts/38_replay_reanalysis.py")
replay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replay)

OUT = ROOT / os.environ.get("LIVEGATE_OUT", "results/metrics/livegate")
FIG = ROOT / os.environ.get("LIVEGATE_FIG", "results/figures/livegate")
SOURCE = ROOT / os.environ.get("LIVEGATE_SOURCE", "data/processed/hydro_exp1_measurements.parquet")
CONFIG = ROOT / os.environ.get("LIVEGATE_CONFIG", "configs/experiments/livegate.yaml")
GATES = ("livegate", "livegate_no_liveness", "livegate_no_forecast")
METHODS = ("persistence_only", "hampel", "cusum", "lof", "kalman", "ewma", "moving_median", "glr",
           "aasvr_measurement", "aasvr_hold_only", "aasvr_no_cusum", *GATES)


def scenario(values, kind, magnitude, start, duration, sensor):
    if kind != "saturation":
        return replay.scenario(values, kind, magnitude, start, duration)
    background = np.asarray(values, dtype=float).copy()
    corrupted = background.copy()
    corrupted[start:start + duration] = sensor.physical_max
    labels = np.zeros(len(background), dtype=bool)
    labels[start:start + duration] = True
    return background, corrupted, labels


def detect(method, x, times, hours, context, sensor, base, setting_value, lof, noise, models, cfg):
    if method not in GATES:
        return replay.detector(method, x, times, sensor, base, setting_value, lof, noise)
    accepted = livegate.gate(models[sensor.name], x, times, hours, context, epsilon=setting_value,
                             use_liveness=method != "livegate_no_liveness",
                             use_forecast=method != "livegate_no_forecast",
                             max_confirm=cfg["livegate"]["max_confirm"], max_gap=cfg["max_gap_seconds"])
    return accepted, accepted.copy()


def grid_values(method, cfg):
    if method in ("always_deny", "persistence_only"):
        return [1.0]
    return cfg["livegate"]["epsilons"] if method in GATES else cfg["threshold_multipliers"]


def load(path):
    frame = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)
    frame["timestamp"] = pd.to_datetime(frame.timestamp, format="ISO8601", utc=True)
    return frame.sort_values("timestamp").reset_index(drop=True)


def paired_intervals(detail, selections, cfg, reference="livegate"):
    """Method minus LiveGate at each target, resampling source days jointly."""
    rng = np.random.default_rng(cfg["seed"])
    detail = detail[detail.deadline == cfg["selection_deadline_seconds"]]
    rows = []
    for target in cfg["minimum_coverages"]:
        chosen = selections[(selections.target == target) & (selections.status == "selected")]
        groups = {r.method: detail[(detail.method == r.method) & (detail.setting == r.setting)]
                  .set_index("trial_id") for r in chosen.itertuples()}
        if reference not in groups:
            continue
        ref = groups[reference]
        days = sorted(ref.source_day.unique())
        index = {day: np.flatnonzero(ref.source_day.to_numpy() == day) for day in days}
        draws = [np.concatenate([index[d] for d in rng.choice(days, len(days))])
                 for _ in range(cfg["bootstrap_replicates"])]
        for method, group in groups.items():
            aligned = group.loc[ref.index]
            for metric in ("coverage", "undesirable_per_trial"):
                values = [summarize(aligned.iloc[ids])[metric] - summarize(ref.iloc[ids])[metric]
                          for ids in draws]
                low, high = np.nanquantile(values, [.025, .975])
                rows.append({"target": target, "method": method, "reference": reference,
                             "metric": metric,
                             "difference": summarize(aligned)[metric] - summarize(ref)[metric],
                             "ci_low": low, "ci_high": high, "source_days": len(days)})
    return pd.DataFrame(rows)


def audit_setting(selections, operating, method, cfg):
    targets = sorted([t for t in cfg["minimum_coverages"] if t <= cfg["audit_target"]], reverse=True)
    for target in targets:
        hit = selections[(selections.method == method) & (selections.target == target)
                         & (selections.status == "selected")]
        if len(hit):
            return hit.setting.iloc[0], f"locked@{target:g}"
    pool = operating[(operating.method == method) & (operating.deadline == cfg["selection_deadline_seconds"])]
    best = pool.sort_values(["coverage", "undesirable_per_trial"], ascending=[False, True]).iloc[0]
    return best.setting, "max_validation_coverage"


def real_audit(frame, boundaries, sensors, base, models, lofs, noise, selections, operating, cfg):
    """Replay every method on the unmodified evaluation-period log.

    A certain fault is a reading outside the physical range or exactly at a
    declared physical bound (full-scale saturation). Counts authorizations whose
    held estimate is a certain fault; no other labels are inferred.
    """
    sub = frame[frame.timestamp.astype("int64") / 1e9 >= boundaries[2]]
    times = sub.timestamp.astype("int64").to_numpy() / 1e9
    hours = (sub.timestamp.dt.hour + sub.timestamp.dt.minute / 60).to_numpy()
    timing = Timing(cooldown=cfg["cooldown_seconds"], max_gap=cfg["max_gap_seconds"])
    rows = []
    for method in ("always_deny", *METHODS):
        if method == "always_deny":
            continue
        setting, basis = audit_setting(selections, operating, method, cfg)
        value, persistence, max_age = (float(part[1:]) for part in setting.split("_"))
        for sensor in sensors:
            x = sub[sensor.name].to_numpy(dtype=float)
            context = sub[list(models[sensor.name].others)].to_numpy(dtype=float)
            accepted, gate = detect(method, x, times, hours, context, sensor, base, value,
                                    lofs[sensor.name], noise[sensor.name], models, cfg)
            estimate, age = hold_estimate(times, x, accepted, max_gap=timing.max_gap)
            eligible = age <= max_age
            if method in ("aasvr_measurement", "aasvr_no_cusum"):
                eligible &= gate
            actions = authorize(times, estimate, eligible, sensor.control_low, sensor.control_high,
                                replace(timing, persistence=persistence, max_age=max_age))
            certain = ((estimate < sensor.physical_min) | (estimate > sensor.physical_max)
                       | (estimate == sensor.physical_min) | (estimate == sensor.physical_max))
            raw_fault = (x < sensor.physical_min) | (x > sensor.physical_max) | (x == sensor.physical_max)
            rows.append({"method": method, "setting": setting, "setting_basis": basis,
                         "sensor": sensor.name, "authorizations": int((actions != 0).sum()),
                         "fault_driven_authorizations": int(((actions != 0) & certain).sum()),
                         "certain_fault_readings": int(raw_fault.sum()),
                         "rejected_certain_fault_readings": int((raw_fault & ~accepted).sum()),
                         "readings": len(x)})
    return pd.DataFrame(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    cfg = load_yaml(CONFIG)
    replay.OUT, replay.METHODS = OUT, METHODS
    base = load_aasvr_config(ROOT / "configs/methods/aasvr.yaml")
    frame = load(SOURCE)
    grid, boundaries = replay.windows(frame, cfg)
    grid.to_csv(OUT / "source_windows.csv", index=False)
    sensors = [replace(s, control_low=cfg["setpoints"][s.name][0], control_high=cfg["setpoints"][s.name][1])
               for s in base.sensors if s.name in cfg["sensors"]]
    development = frame[frame.timestamp.astype("int64") / 1e9 < boundaries[1]]
    models = livegate.fit(development, sensors, calibration_fraction=cfg["livegate"]["calibration_fraction"],
                          max_gap=cfg["max_gap_seconds"])
    pd.DataFrame([{"sensor": m.name, "scale": m.scale, "calibration_scores": len(m.calibration_scores),
                   "live_runs": len(m.run_lengths), "max_live_run": int(m.run_lengths.max()),
                   **{f"q_eps_{e:g}": m.threshold(e) for e in cfg["livegate"]["epsilons"]}}
                  for m in models.values()]).to_csv(OUT / "livegate_models.csv", index=False)
    lofs, noise = {}, {}
    for sensor in sensors:
        values = development[sensor.name].dropna().to_numpy()
        steps = np.diff(values[(values >= sensor.physical_min) & (values <= sensor.physical_max)])
        noise[sensor.name] = max(np.sqrt(np.pi) / 2 * np.mean(np.abs(steps)), 1e-6)
        values = values[np.linspace(0, len(values) - 1, min(2000, len(values)), dtype=int)]
        lofs[sensor.name] = LocalOutlierFactor(n_neighbors=20, novelty=True, n_jobs=1).fit(values[:, None])
    timing = Timing(persistence=cfg["reference_persistence_seconds"], cooldown=cfg["cooldown_seconds"],
                    max_gap=cfg["max_gap_seconds"])
    selections = operating = None
    for split in ("validation", "evaluation"):
        rows = []
        for wi, window in enumerate(grid[grid.split == split].itertuples()):
            sub = frame.iloc[window.start:window.end]
            times = (sub.timestamp - sub.timestamp.iloc[0]).dt.total_seconds().to_numpy()
            hours = (sub.timestamp.dt.hour + sub.timestamp.dt.minute / 60).to_numpy()
            score_start = times[cfg["warmup_samples"]]
            score_stop = times[-1] - max(cfg["deadlines_seconds"])
            for sensor in sensors:
                context = sub[list(models[sensor.name].others)].to_numpy(dtype=float)
                for kind in cfg["scenarios"]:
                    background, corrupted, labels = scenario(sub[sensor.name].to_numpy(), kind,
                        cfg["magnitudes"][sensor.name], cfg["warmup_samples"], cfg["fault_samples"], sensor)
                    trial_id = f"{window.window_id}_{sensor.name}_{kind}"
                    for method in ("always_deny", *METHODS):
                        for value in grid_values(method, cfg):
                            accepted, gate = detect("persistence_only" if method == "always_deny" else method,
                                corrupted, times, hours, context, sensor, base, value,
                                lofs[sensor.name], noise[sensor.name], models, cfg)
                            estimate, age = hold_estimate(times, corrupted, accepted, max_gap=timing.max_gap)
                            settings = [(0, 64)] if method == "always_deny" else [
                                (p, a) for p in cfg["persistence_seconds"] for a in cfg["max_age_seconds"]]
                            for persistence, max_age in settings:
                                setting = f"m{value:g}_p{persistence}_a{max_age}"
                                if split == "evaluation" and method != "always_deny" and not (
                                        (selections.method == method) & (selections.setting == setting)).any():
                                    continue
                                policy = replace(timing, persistence=persistence, max_age=max_age)
                                eligible = age <= max_age
                                if method in ("aasvr_measurement", "aasvr_no_cusum"):
                                    eligible &= gate
                                actions = authorize(times, estimate, eligible, sensor.control_low,
                                                    sensor.control_high, policy)
                                if method == "always_deny":
                                    actions[:] = 0
                                for deadline in cfg["deadlines_seconds"]:
                                    metrics = score_actions(times, background, corrupted, accepted, actions,
                                        sensor.control_low, sensor.control_high,
                                        timing=replace(timing, max_age=max_age), deadline=deadline,
                                        start=score_start, stop=score_stop, fault_labels=labels,
                                        held=(estimate, age))
                                    rows.append({"trial_id": trial_id, "window_id": window.window_id,
                                        "source_day": window.source_day, "split": split,
                                        "sensor": sensor.name, "scenario": kind, "method": method,
                                        "setting": setting, "deadline": deadline, **metrics})
            print(f"{split}: window {wi + 1}/{cfg['windows_per_split']} complete", flush=True)
        detail = pd.DataFrame(rows)
        detail.to_csv(OUT / f"{split}_detail.csv.gz", index=False)
        if split == "validation":
            selections = replay.select(detail, cfg)  # also writes validation_operating_points.csv
            selections.to_csv(OUT / "locked_validation_selections.csv", index=False)
            operating = pd.read_csv(OUT / "validation_operating_points.csv")
            print("Validation selections locked before evaluation scoring", flush=True)
            continue
        reports = []
        for choice in selections.itertuples():
            if choice.status != "selected":
                reports.append({"target": choice.target, "method": choice.method, "status": "infeasible"})
                continue
            subset = detail[(detail.method == choice.method) & (detail.setting == choice.setting)]
            for deadline, group in subset.groupby("deadline"):
                reports.append({"target": choice.target, "method": choice.method, "status": "evaluated",
                                "setting": choice.setting, "deadline": deadline, **summarize(group)})
        report = pd.DataFrame(reports)
        report.to_csv(OUT / "evaluation_summary.csv", index=False)
        by_scenario = []
        for choice in selections[selections.status == "selected"].itertuples():
            subset = detail[(detail.method == choice.method) & (detail.setting == choice.setting)
                            & (detail.deadline == cfg["selection_deadline_seconds"])]
            for kind, group in subset.groupby("scenario"):
                by_scenario.append({"target": choice.target, "method": choice.method, "scenario": kind,
                                    **summarize(group)})
        pd.DataFrame(by_scenario).to_csv(OUT / "evaluation_by_scenario.csv", index=False)
        paired_intervals(detail, selections, cfg).to_csv(OUT / "paired_intervals_vs_livegate.csv", index=False)
    audit = real_audit(frame, boundaries, sensors, base, models, lofs, noise, selections, operating, cfg)
    audit.to_csv(OUT / "real_log_audit.csv", index=False)
    plot(operating, cfg)
    print(f"Results: {OUT}", flush=True)


def plot(operating, cfg):
    points = operating[(operating.deadline == cfg["selection_deadline_seconds"])
                       & (operating.method != "always_deny")]
    colors = {"livegate": "#eb6834", "persistence_only": "#2a78d6", "lof": "#1baf7a",
              "aasvr_measurement": "#6250d6"}
    labels = {"livegate": "LiveGate", "persistence_only": "Persistence only", "lof": "LOF",
              "aasvr_measurement": "AASVR-R supervisor"}
    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    for method, group in points.groupby("method"):
        color = colors.get(method, "#b4b2a9")
        ax.scatter(group.coverage, group.undesirable_per_trial, s=28 if method in colors else 10,
                   color=color, alpha=.9 if method in colors else .5, lw=0,
                   label=labels.get(method), zorder=3 if method in colors else 1)
    ax.scatter([], [], s=10, color="#b4b2a9", label="Other baselines")
    ax.set(xlabel="Useful-authorization coverage (validation)",
           ylabel="Undesirable authorizations per trial", xlim=(0, 1.02))
    ax.grid(alpha=.25, lw=.6)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax.set_title("Validation operating points (lower right is better)", fontsize=10, loc="left")
    fig.tight_layout()
    fig.savefig(FIG / "operating_points.pdf")
    fig.savefig(FIG / "operating_points.png", dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    main()
