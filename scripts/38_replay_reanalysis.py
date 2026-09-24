"""Blocked replay, independent opportunities, validation selection, and audit.

Outputs are separate from the historical manuscript pipeline. Run in Docker.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import time
import tracemalloc
from dataclasses import replace
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.neighbors import LocalOutlierFactor

from aasvr.baselines import BaselineConfig, StreamingBaseline
from aasvr.config import load_aasvr_config, load_yaml
from aasvr.core import AASVR
from aasvr.reanalysis import Timing, authorize, hold_estimate, score_actions, summarize

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/metrics/reanalysis"
FIG = ROOT / "results/figures/reanalysis"
METHODS = ("persistence_only", "hampel", "cusum", "lof", "aasvr_measurement", "aasvr_hold_only", "aasvr_no_cusum")


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def snapshot():
    directory = ROOT / "results/run_metadata/reanalysis_reference"
    directory.mkdir(parents=True, exist_ok=True)
    if (directory / "manifest.json").exists():
        return
    paths = [ROOT / "Paper Files/main_aasvr.tex", ROOT / "Paper Files/main_aasvr.pdf"]
    for pattern in ("src/aasvr/*.py", "configs/methods/*.yaml", "results/tables/*.csv",
                    "scripts/*.py"):
        paths.extend(ROOT.glob(pattern))
    records = []
    for path in paths:
        target = directory / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        records.append({"path": str(path.relative_to(ROOT)), "sha256": digest(path)})
    (directory / "manifest.json").write_text(json.dumps({
        "git_commit": subprocess.check_output(["git", "-c", f"safe.directory={ROOT}", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "files": records,
    }, indent=2))


def windows(frame, cfg):
    times = frame.timestamp.astype("int64").to_numpy() / 1e9
    bounds = [times[0], *[times[0] + f * (times[-1] - times[0])
                         for f in cfg["split_fractions"]], times[-1] + 1]
    rows = []
    for k, split in enumerate(("development", "validation", "evaluation")):
        indices = np.flatnonzero((times >= bounds[k]) & (times < bounds[k + 1]))
        candidates = []
        n = cfg["window_samples"]
        for start in range(int(indices[0]), int(indices[-1]) - n + 2, n):
            if np.max(np.diff(times[start:start+n])) <= cfg["max_gap_seconds"]:
                candidates.append(start)
        if len(candidates) < cfg["windows_per_split"]:
            raise ValueError(f"Not enough gap-free windows in {split}")
        selected = np.linspace(0, len(candidates)-1, cfg["windows_per_split"], dtype=int)
        for j in selected:
            start = candidates[j]
            rows.append({"split": split, "window_id": f"{split}_{start}", "start": start,
                         "end": start+n, "start_timestamp": str(frame.timestamp.iloc[start]),
                         "end_timestamp": str(frame.timestamp.iloc[start+n-1]),
                         "source_day": str(frame.timestamp.iloc[start].date())})
    result = pd.DataFrame(rows)
    ordered = result.sort_values("start")
    assert np.all(ordered.start.to_numpy()[1:] >= ordered.end.to_numpy()[:-1])
    return result, bounds


def scenario(values, kind, magnitude, start, duration):
    values = np.asarray(values, dtype=float)
    background = values.copy()
    corrupted = values.copy()
    sign = -1 if kind.endswith("negative") else 1
    end = start + duration
    if kind.startswith("legitimate"):
        background[start:] += sign * magnitude
        corrupted = background.copy()
    elif kind.startswith("spike"):
        corrupted[start] += sign * magnitude
    elif kind.startswith("bias"):
        corrupted[start:end] += sign * magnitude
    elif kind.startswith("drift"):
        corrupted[start:end] += sign * magnitude * np.linspace(0, 1, duration)
    elif kind == "stuck":
        corrupted[start:end] = values[start-1]
    elif kind == "dropout":
        corrupted[start:end] = np.nan
    labels = np.zeros(len(values), dtype=bool)
    if kind not in ("clean", "legitimate_positive", "legitimate_negative"):
        labels[start:start+1 if kind.startswith("spike") else end] = True
    return background, corrupted, labels


def detector(method, x, times, sensor, base, multiplier, lof):
    if method == "persistence_only":
        return np.isfinite(x), np.ones(len(x), dtype=bool)
    if method == "lof":
        finite = np.isfinite(x)
        accepted = finite.copy()
        # Fixed development-fitted model; multiplier sweeps its decision threshold.
        accepted[finite] = lof.score_samples(x[finite, None]) >= -1.5 * multiplier
        accepted &= (x >= sensor.physical_min) & (x <= sensor.physical_max)
        return accepted, accepted.copy()
    if method.startswith("aasvr"):
        s = replace(sensor, response_window=0, trend_window=0,
                    scale_multiplier=base.scale_multiplier * multiplier,
                    cusum_threshold_multiplier=sensor.cusum_threshold_multiplier * multiplier,
                    cusum_drift_multiplier=0 if method == "aasvr_no_cusum" else sensor.cusum_drift_multiplier)
        model = AASVR(replace(base, sensors=(s,), enable_response_residual=False,
                              eta_min_high=0, eta_min_medium=0, eta_min_low=0,
                              compact_diagnostics=True))
    else:
        model = StreamingBaseline((sensor,), BaselineConfig(
            method=method, window=9, threshold_multiplier=3 * multiplier,
            cusum_threshold=5 * multiplier))
    accepted, eligible = [], []
    for i, value in enumerate(x):
        model.dt_seconds = times[i] - times[i-1] if i else 16.0
        d = model.update({sensor.name: value, "timestamp": times[i]})[0]
        accepted.append(d.gate_result == "accept")
        eligible.append(d.gate_result == "accept")
    # Estimate holding and authorization are common downstream components.
    return np.asarray(accepted), np.asarray(eligible)


def recovery_audit(base):
    s = next(s for s in base.sensors if s.name == "pH")
    rows = []
    cases = {
        "one_failed_response": np.full(100, 6.7),
        "no_pending_command": np.full(100, 6.1),
        "missing_response_window": np.r_[np.full(3, 6.7), np.full(40, np.nan), np.full(57, 6.7)],
        "legitimate_shift": np.r_[np.full(20, 6.1), np.full(80, 6.7)],
        "fault_ends": np.r_[np.full(20, 6.1), np.full(20, 99.), np.full(60, 6.1)],
        "long_gap": np.full(100, 6.7),
    }
    traces = []
    for name, values in cases.items():
        model = AASVR(replace(base, sensors=(s,)))
        for i, y in enumerate(values):
            timestamp = i * 16 + (3600 if name == "long_gap" and i >= 4 else 0)
            d = model.update({"timestamp": timestamp, "pH": y})[0]
            r = model._sensors["pH"]
            traces.append({"scenario": name, "sample": i, "seconds": timestamp,
                           "measurement": y, "estimate": d.trusted_value,
                           "authorized": d.actuation_authorized, "state": d.state.value,
                           "reliability": d.response_reliability,
                           "pending_samples": r.response_countdown,
                           "completed_responses": r.response_observations})
        trace = pd.DataFrame(traces).query("scenario == @name")
        rows.append({"scenario": name, "authorizations": int(trace.authorized.sum()),
                     "final_reliability": r.response_reliability,
                     "completed_responses": r.response_observations,
                     "final_state": d.state.value,
                     "last_authorized_sample": int(trace.loc[trace.authorized, "sample"].max())
                         if trace.authorized.any() else -1})
    pd.DataFrame(traces).to_csv(OUT / "legacy_recovery_traces.csv", index=False)
    pd.DataFrame(rows).to_csv(OUT / "legacy_recovery_summary.csv", index=False)


def select(validation, cfg):
    rows = []
    for (method, setting, deadline), group in validation.groupby(["method", "setting", "deadline"]):
        rows.append({"method": method, "setting": setting, "deadline": deadline, **summarize(group)})
    operating = pd.DataFrame(rows)
    operating.to_csv(OUT / "validation_operating_points.csv", index=False)
    selections = []
    for target in cfg["minimum_coverages"]:
        for method in ["always_deny", *METHODS]:
            candidates = operating[(operating.method == method)
                                   & (operating.deadline == cfg["selection_deadline_seconds"])
                                   & (operating.coverage >= target)]
            if candidates.empty:
                selections.append({"target": target, "method": method, "status": "infeasible",
                                   "setting": ""})
            else:
                best = candidates.sort_values(["undesirable_per_trial", "fault_evidence_per_trial",
                                                "coverage", "setting"],
                                               ascending=[True, True, False, True]).iloc[0]
                selections.append({"target": target, "method": method, "status": "selected",
                                   "setting": best.setting})
    return pd.DataFrame(selections)


def confidence(detail, selections, cfg):
    rows = []
    rng = np.random.default_rng(cfg["seed"])
    detail = detail[detail.deadline == cfg["selection_deadline_seconds"]]
    for target in cfg["minimum_coverages"]:
        choices = selections[(selections.target == target) & (selections.status == "selected")]
        groups = {row.method: detail[(detail.method == row.method) & (detail.setting == row.setting)]
                  for row in choices.itertuples()}
        if "persistence_only" not in groups:
            continue
        reference = groups["persistence_only"].set_index("trial_id")
        for method, group in groups.items():
            aligned = group.set_index("trial_id").loc[reference.index]
            # Resample source days jointly across sensors/scenarios and both methods.
            days = sorted(reference.source_day.unique())
            samples = []
            for _ in range(cfg["bootstrap_replicates"]):
                chosen = rng.choice(days, size=len(days), replace=True)
                ids = np.concatenate([np.flatnonzero(reference.source_day.to_numpy() == day) for day in chosen])
                a, b = summarize(aligned.iloc[ids]), summarize(reference.iloc[ids])
                samples.append([a["coverage"] - b["coverage"],
                                a["undesirable_per_trial"] - b["undesirable_per_trial"]])
            values = np.asarray(samples)
            for j, metric in enumerate(("coverage", "undesirable_per_trial")):
                difference = summarize(aligned)[metric] - summarize(reference)[metric]
                low, high = np.nanquantile(values[:, j], [.025, .975])
                rows.append({"target": target, "method": method, "reference": "persistence_only",
                             "metric": metric, "difference": difference, "ci_low": low,
                             "ci_high": high, "source_days": len(days),
                             "bootstrap_unit": "source_day", "interval": "two-sided percentile 95%"})
    pd.DataFrame(rows).to_csv(OUT / "paired_cluster_intervals.csv", index=False)


def runtime_audit(base, sensor):
    records = []
    for streams in (1, 8, 32):
        tracemalloc.start()
        begin = time.perf_counter()
        models = [AASVR(replace(base, sensors=(replace(sensor, response_window=0, trend_window=0),),
                               enable_response_residual=False, compact_diagnostics=True))
                  for _ in range(streams)]
        initialization = time.perf_counter() - begin
        _, initialization_peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        durations = []
        for i in range(300):
            begin = time.perf_counter_ns()
            for m in models:
                m.update({sensor.name: (sensor.control_low+sensor.control_high)/2 + .001*np.sin(i),
                          "timestamp": i*16})
            durations.append((time.perf_counter_ns()-begin)/1e6)
        tracemalloc.start()
        for i in range(30):
            for m in models:
                m.update({sensor.name: sensor.control_low, "timestamp": (i+300)*16})
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        records.append({"streams": streams, "initialization_seconds_with_tracing": initialization,
                        "initialization_peak_python_allocated_bytes": initialization_peak,
                        "batch_median_ms": np.median(durations), "batch_p95_ms": np.percentile(durations,95),
                        "batch_p99_ms": np.percentile(durations,99),
                        "sensor_updates_per_second": streams*1000/np.mean(durations),
                        "streaming_peak_python_allocated_bytes": peak})
    pd.DataFrame(records).to_csv(OUT / "runtime.csv", index=False)
    cpu = next((line.split(":",1)[1].strip() for line in Path("/proc/cpuinfo").read_text().splitlines()
                if line.startswith("model name")), "unavailable")
    (OUT / "runtime_metadata.json").write_text(json.dumps({
        "cpu_model": cpu, "scope": "AASVR measurement kernel only; excludes scoring, LOF fit, and pandas I/O",
        "threads": {k: os.environ.get(k) for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")},
        "memory": "Python traced initialization peak and incremental streaming peak; not process RSS"
    }, indent=2))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    snapshot()
    cfg = load_yaml(ROOT / "configs/experiments/reanalysis.yaml")
    base = load_aasvr_config(ROOT / "configs/methods/aasvr.yaml")
    path = ROOT / "data/processed/hydro_exp1_measurements.parquet"
    frame = pd.read_parquet(path).sort_values("timestamp").reset_index(drop=True)
    if frame.timestamp.duplicated().any():
        raise ValueError("Duplicate timestamps need explicit resolution before replay")
    grid, boundaries = windows(frame, cfg)
    grid.to_csv(OUT / "source_windows.csv", index=False)
    deltas = frame.timestamp.diff().dt.total_seconds()
    audit = {"rows": len(frame), "first": str(frame.timestamp.min()), "last": str(frame.timestamp.max()),
             "duplicate_timestamps": int(frame.timestamp.duplicated().sum()),
             "median_interval_seconds": float(deltas.median()), "max_gap_seconds": float(deltas.max()),
             "gaps_above_120_seconds": int((deltas > 120).sum()),
             "missing_by_sensor": frame[cfg["sensors"]].isna().sum().to_dict(),
             "split_boundaries_unix_seconds": boundaries, "source_sha256": digest(path),
             "config_sha256": digest(ROOT / "configs/experiments/reanalysis.yaml"),
             "history": "Retrospective reanalysis; source periods were used in earlier development.",
             "preprocessing": "Injection after stored acquisition/preparation; historical firmware filtering unverified.",
             "actuator_evidence": "unknown; response and uncommanded-trend gates disabled in main comparison",
             "hardware": platform.platform(), "processor": platform.processor(),
             "cpu_count": os.cpu_count(), "thread_settings": {k: os.environ.get(k) for k in
                  ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")},
             "software": subprocess.check_output(["python", "-m", "pip", "freeze"], text=True).splitlines()}
    (OUT / "audit.json").write_text(json.dumps(audit, indent=2))
    recovery_audit(base)
    sensors = [s for s in base.sensors if s.name in cfg["sensors"]]
    development = frame[frame.timestamp.astype("int64")/1e9 < boundaries[1]]
    models = {}
    for sensor in sensors:
        values = development[sensor.name].dropna().to_numpy()
        # Deterministic bounded fit uses development only; no test-prefix fitting.
        values = values[np.linspace(0, len(values)-1, min(2000, len(values)), dtype=int)]
        models[sensor.name] = LocalOutlierFactor(n_neighbors=20, novelty=True, n_jobs=1).fit(values[:, None])
    timing = Timing(persistence=cfg["reference_persistence_seconds"], cooldown=cfg["cooldown_seconds"],
                    max_gap=cfg["max_gap_seconds"])
    selections = None
    for split in ("validation", "evaluation"):
        rows, examples = [], []
        for wi, window in enumerate(grid[grid.split == split].itertuples()):
            sub = frame.iloc[window.start:window.end]
            times = (sub.timestamp-sub.timestamp.iloc[0]).dt.total_seconds().to_numpy()
            score_start = times[cfg["warmup_samples"]]
            score_stop = times[-1] - max(cfg["deadlines_seconds"])
            for sensor in sensors:
                for kind in cfg["scenarios"]:
                    background, corrupted, labels = scenario(sub[sensor.name].to_numpy(), kind,
                        cfg["magnitudes"][sensor.name], cfg["warmup_samples"], cfg["fault_samples"])
                    trial_id = f"{window.window_id}_{sensor.name}_{kind}"
                    for method in ("always_deny", *METHODS):
                        multipliers = [1.] if method in ("always_deny", "persistence_only") else cfg["threshold_multipliers"]
                        for multiplier in multipliers:
                            accepted, gate = detector("persistence_only" if method == "always_deny" else method,
                                corrupted, times, sensor, base, multiplier, models[sensor.name])
                            estimate, age = hold_estimate(times, corrupted, accepted, max_gap=timing.max_gap)
                            settings = [(0,64)] if method == "always_deny" else [
                                (p,a) for p in cfg["persistence_seconds"] for a in cfg["max_age_seconds"]]
                            for persistence, max_age in settings:
                                setting = f"m{multiplier:g}_p{persistence}_a{max_age}"
                                if split == "evaluation" and method != "always_deny" and not ((selections.method == method)
                                        & (selections.setting == setting)).any():
                                    continue
                                policy = replace(timing, persistence=persistence, max_age=max_age)
                                # Held evidence may authorize within its age limit; current gate rejection
                                # blocks only AASVR's supervisor arm, making that distinction explicit.
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
                                        timing=replace(timing,max_age=max_age), deadline=deadline,
                                        start=score_start, stop=score_stop, fault_labels=labels,
                                        held=(estimate, age))
                                    rows.append({"trial_id": trial_id, "window_id": window.window_id,
                                        "source_day": window.source_day, "split": split, "sensor": sensor.name,
                                        "scenario": kind, "method": method, "setting": setting,
                                        "deadline": deadline, **metrics})
                                if split == "evaluation" and wi == 0 and sensor.name == "pH" and kind in (
                                        "spike_positive", "legitimate_positive", "bias_positive"):
                                    examples.extend({"trial_id": trial_id, "scenario": kind, "method": method,
                                        "setting": setting, "seconds": t, "background": b, "corrupted": c,
                                        "estimate": e, "accepted": a, "age_seconds": ag, "action": ac}
                                        for t,b,c,e,a,ag,ac in zip(times,background,corrupted,estimate,accepted,age,actions))
            print(f"{split}: window {wi+1}/{cfg['windows_per_split']} complete", flush=True)
        detail = pd.DataFrame(rows)
        detail.to_csv(OUT / f"{split}_detail.csv", index=False)
        if split == "validation":
            selections = select(detail, cfg)
            selections.to_csv(OUT / "locked_validation_selections.csv", index=False)
            print("Validation selections locked before evaluation scoring", flush=True)
        else:
            reports = []
            for choice in selections.itertuples():
                if choice.status != "selected":
                    reports.append({"target": choice.target, "method": choice.method, "status": "infeasible"})
                    continue
                subset = detail[(detail.method == choice.method) & (detail.setting == choice.setting)]
                for deadline, group in subset.groupby("deadline"):
                    reports.append({"target": choice.target, "method": choice.method, "status": "evaluated",
                                    "setting": choice.setting, "deadline": deadline, **summarize(group)})
            for deadline, group in detail[detail.method == "always_deny"].groupby("deadline"):
                reports.append({"target": 0., "method": "always_deny", "status": "evaluated",
                                "setting": "m1_p0_a64", "deadline": deadline, **summarize(group)})
            report = pd.DataFrame(reports)
            report.to_csv(OUT / "evaluation_summary.csv", index=False)
            pd.DataFrame(examples).to_csv(OUT / "example_traces.csv", index=False)
            confidence(detail, selections, cfg)
            plot_results(report, cfg)
    runtime_audit(base, next(s for s in sensors if s.name == "pH"))
    print(f"Results: {OUT}", flush=True)


def plot_results(report, cfg):
    fig, ax = plt.subplots(figsize=(8,5))
    selected = report[(report.status == "evaluated") & (report.deadline == cfg["selection_deadline_seconds"])]
    for method, group in selected.groupby("method"):
        ax.scatter(group.coverage, group.undesirable_per_trial, label=method, s=55)
    ax.set(xlabel="Useful reference-opportunity coverage (evaluation)",
           ylabel="Unnecessary + wrong-direction authorizations / trial",
           title="Validation-selected policies on retrospective temporal evaluation")
    ax.legend(fontsize=8)
    ax.grid(alpha=.2)
    fig.tight_layout()
    fig.savefig(FIG / "authorization_tradeoff.png", dpi=180)
    fig.savefig(FIG / "authorization_tradeoff.pdf")
    plt.close(fig)


if __name__ == "__main__":
    main()
