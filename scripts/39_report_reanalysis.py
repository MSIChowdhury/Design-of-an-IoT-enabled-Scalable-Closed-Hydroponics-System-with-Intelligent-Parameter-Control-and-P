"""Render compact reanalysis results without altering the historical manuscript."""
from pathlib import Path
import json
import hashlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from aasvr.reanalysis import Timing, reference_trace, summarize
from aasvr.config import load_aasvr_config, load_yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/metrics/reanalysis"
FIG = ROOT / "results/figures/reanalysis"


def markdown(frame):
    columns = list(frame.columns)
    rows = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in frame.itertuples(index=False, name=None):
        rows.append("| " + " | ".join(f"{v:.3f}" if isinstance(v, float) else str(v) for v in row) + " |")
    return "\n".join(rows)


def main():
    cfg = load_yaml(ROOT / "configs/experiments/reanalysis.yaml")
    report = pd.read_csv(OUT / "evaluation_summary.csv")
    validation = pd.read_csv(OUT / "validation_operating_points.csv")
    detail = pd.read_csv(OUT / "evaluation_detail.csv")
    selections = pd.read_csv(OUT / "locked_validation_selections.csv")
    audit = json.loads((OUT / "audit.json").read_text())
    rows = []
    for choice in selections[selections.status == "selected"].itertuples():
        selected = detail[(detail.method == choice.method) & (detail.setting == choice.setting)
                          & (detail.deadline == cfg["selection_deadline_seconds"])]
        for grouping in ("sensor", "scenario"):
            for name, group in selected.groupby(grouping):
                rows.append({"target": choice.target, "method": choice.method,
                             "grouping": grouping, "group": name, **summarize(group),
                             "estimate_mae": group.absolute_error_sum.sum()/group.estimate_samples.sum()
                                 if group.estimate_samples.sum() else np.nan,
                             "median_recovery_seconds": group.recovery_seconds.dropna().median()
                                 if group.recovery_seconds.notna().any() else np.nan})
    pd.DataFrame(rows).to_csv(OUT / "evaluation_subgroups.csv", index=False)
    display = report[(report.deadline == 180) | (report.status == "infeasible")].copy()
    fields = ["target", "method", "status", "coverage", "undesirable_per_trial",
              "fault_evidence_per_trial", "authorizations_per_trial", "opportunities"]
    maximum = validation[validation.deadline == 180].groupby("method", as_index=False).coverage.max()
    maximum = maximum.rename(columns={"coverage": "maximum_validation_coverage"})
    diagnostic = pd.read_csv(OUT / "diagnostic_evaluation_summary.csv")
    recovery = pd.read_csv(OUT / "legacy_recovery_summary.csv")
    runtime = pd.read_csv(OUT / "runtime.csv")
    runtime_metadata = json.loads((OUT / "runtime_metadata.json").read_text())
    intervals = pd.read_csv(OUT / "paired_cluster_intervals.csv")
    windows = pd.read_csv(OUT / "source_windows.csv")
    main_max = maximum.loc[maximum.method == "aasvr_measurement", "maximum_validation_coverage"].iloc[0]
    decision = ("**Decision: the measurement supervisor did not meet the lowest declared validation coverage target "
                "within this search. This run does not establish its advantage at comparable useful-action coverage.** "
                "Simplify or narrow the contribution before rebuilding the manuscript."
                if main_max < min(cfg["minimum_coverages"]) else
                "The supervisor met at least one validation target; inspect evaluation coverage and paired intervals "
                "before claiming an advantage. Passing validation alone does not establish superiority.")
    wrong = report.wrong_direction_per_trial.fillna(0).sum() + diagnostic.wrong_direction_per_trial.fillna(0).sum()
    direction_note = ("No wrong-direction authorizations occurred in the evaluated scenarios. This limits what the "
                      "experiment establishes about that endpoint; it does not demonstrate prevention of "
                      "wrong-direction commands." if wrong == 0 else
                      "Wrong-direction authorizations occurred; see their separate counts in the generated CSVs.")
    text = f'''# Retrospective replay reanalysis results

Run protocol: [PROTOCOL.md](PROTOCOL.md). Historical manuscript tables were not replaced.

{decision}

{direction_note} Injections use one fixed onset within each window, one magnitude per sensor, and do not specifically sample threshold-adjacent backgrounds. Those are explicit limitations of this compact stopping-point experiment.

## Scope and evidence

- Source: {audit['rows']:,} processed observations from {audit['first']} to {audit['last']}.
- Median interval: {audit['median_interval_seconds']:.0f} seconds; maximum gap: {audit['max_gap_seconds']:.0f} seconds; gaps above 120 seconds: {audit['gaps_above_120_seconds']}.
- Six primary sensors; 8 nonoverlapping source windows per block; 11 scenarios per sensor/window. There are 528 validation trials and 528 evaluation trials before method expansion.
- Evaluation uses {windows[windows.split == 'evaluation'].source_day.nunique()} distinct source days. Variants of a background are correlated, not independent physical experiments.
- Contiguous development/validation/evaluation blocks; windows crossing long gaps excluded. All inference is retrospective; prior development used this dataset.
- Surrogate-reference decisions are independent of tested estimates. Actuator activity is unknown. Main AASVR arms disable response-memory and uncommanded-trend gates.
- Source SHA-256: `{audit['source_sha256']}`.
- Config SHA-256: `{audit['config_sha256']}`.

## Locked operating points, 180-second matching deadline

Targets apply to validation coverage, not guaranteed evaluation coverage. Infeasible means no searched validation setting attained that target. Repeated settings across targets are not independent findings. Always-deny is shown separately at target zero.

{markdown(display[fields].fillna('—'))}

Maximum validation coverage within the declared search:

{markdown(maximum)}

An undesirable authorization is unnecessary or wrong-direction relative to the surrogate. Fault-evidence authorization is a separate endpoint. A low error count coupled to poor coverage is suppression, not demonstrated superiority. The last 600 seconds of each window provide matching follow-up. Opportunities recur after the ten-minute reference lockout.

## Diagnostics for supervisors that failed validation coverage

These settings maximize validation coverage and were locked before their separate evaluation. They did **not** meet even the 50% validation target and are not promoted into the matched-target comparison.

{markdown(diagnostic[diagnostic.deadline == 180][['method','coverage','undesirable_per_trial','fault_evidence_per_trial','authorizations_per_trial','sample_recall','clean_rejection_rate']])}

## Paired source-day bootstrap intervals

Differences are method minus persistence-only at the same validation target, using paired trial populations. Coverage is not forced equal on evaluation. Intervals are two-sided percentile 95% intervals from 1,000 day-cluster resamples. Eight source windows cannot establish deployment generalization.

{markdown(intervals)}

## Legacy AASVR-R recovery audit

{markdown(recovery)}

The constant out-of-band scenario demonstrates authorization lockout after a failed response. The legitimate-shift case tests an actual input change without a fault label; fault exit separately tests acceptance recovery. Missing measurements pause the legacy response countdown rather than immediately count as failed response. These are deterministic software scenarios, not measured actuator responses. No unverified automatic recovery/reset was added.

## Computation on the available host

CPU: {runtime_metadata['cpu_model']}. Scope: {runtime_metadata['scope']}. Platform: `{audit['hardware']}`. Logical CPU count reported by the container: {audit['cpu_count']}. Thread settings: `{audit['thread_settings']}`. Full software versions are in the local audit JSON.

{markdown(runtime)}

Latency is serial batch processing for the indicated software stream count; startup is measured separately. Allocation measurements cover Python allocations, not total process/device memory. These are neither Raspberry Pi measurements nor a physical-system scalability demonstration.

## Artifacts and interpretation limits

- `results/metrics/reanalysis/validation_operating_points.csv`: all searched validation settings.
- `results/metrics/reanalysis/locked_validation_selections.csv`: selections made before evaluation.
- `results/metrics/reanalysis/evaluation_detail.csv`: trial-level metrics and denominators.
- `results/metrics/reanalysis/evaluation_subgroups.csv`: sensor/scenario results, recovery, and per-sensor estimate error. Cross-sensor estimate-error magnitudes have incompatible units and should not be pooled.
- `results/metrics/reanalysis/source_windows.csv`: exact source intervals and cluster identifiers.
- `results/metrics/reanalysis/legacy_recovery_traces.csv`: response-memory audit traces.
- `results/figures/reanalysis/`: tradeoff, example traces, source timeline, and runtime plots.

Only one blocked split, eight source windows per validation/evaluation block, one fault magnitude per sensor, and a compact hyperparameter search were run. Reference errors, a single historical deployment, unknown actual commands, and the lack of causal response remain limitations. Legitimate-shift challenges modify the surrogate and input together and are not historical event annotations. The original method has not been silently fixed and credited with old results. A manuscript rebuild requires a defensible advantage at comparable coverage; differences in this table alone do not establish that advantage.
'''
    (ROOT / "docs/reanalysis/RESULTS.md").write_text(text)
    plot_examples(cfg)
    fig, ax = plt.subplots(figsize=(9,5))
    points = report[(report.status == "evaluated") & (report.deadline == 180)]
    for method, group in points.groupby("method"):
        ax.scatter(group.coverage,group.undesirable_per_trial,s=65,label=method)
    for row in diagnostic[diagnostic.deadline == 180].itertuples():
        ax.scatter(row.coverage,row.undesirable_per_trial,marker="x",s=90,
                   label=row.method+" (infeasible diagnostic)")
    ax.set(xlabel="Useful reference-opportunity coverage (evaluation)",
           ylabel="Unnecessary + wrong-direction authorizations / trial",
           title="Locked validation policies; 180-second matching deadline")
    ax.legend(fontsize=7,loc="lower right")
    ax.grid(alpha=.2)
    fig.tight_layout()
    fig.savefig(FIG / "authorization_tradeoff.png",dpi=180)
    fig.savefig(FIG / "authorization_tradeoff.pdf")
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(8,3.8))
    ax.plot(runtime.streams, runtime.batch_median_ms, 'o-', label='Median')
    ax.plot(runtime.streams, runtime.batch_p99_ms, 's-', label='99th percentile')
    ax.set(xlabel='Serial software streams', ylabel='Batch processing latency (ms)',
           title='Available-host software scaling; not physical deployment scaling')
    ax.legend()
    ax.grid(alpha=.2)
    fig.tight_layout()
    fig.savefig(FIG / 'runtime_scaling.png', dpi=180)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(9,2.8))
    for i, split in enumerate(('development','validation','evaluation')):
        group = windows[windows.split == split]
        for w in group.itertuples():
            a, b = pd.Timestamp(w.start_timestamp), pd.Timestamp(w.end_timestamp)
            ax.plot([a,b], [i,i], linewidth=7)
    ax.set_yticks([0,1,2], ['Development','Validation','Evaluation'])
    ax.set(title='Nonoverlapping source windows selected across chronological blocks')
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(FIG / 'source_timeline.png', dpi=180)
    plt.close(fig)
    paths = [ROOT / p for p in (
        "src/aasvr/reanalysis.py", "src/aasvr/core.py", "src/aasvr/baselines.py",
        "scripts/38_replay_reanalysis.py", "scripts/39_report_reanalysis.py",
        "scripts/40_reanalysis_diagnostics.py", "configs/experiments/reanalysis.yaml",
        "configs/methods/aasvr.yaml")]
    records = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    (OUT / "implementation_manifest.json").write_text(json.dumps(records, indent=2))
    print('Wrote docs/reanalysis/RESULTS.md and presentation figures')


def plot_examples(cfg):
    trace = pd.concat([pd.read_csv(OUT / 'example_traces.csv'),
                       pd.read_csv(OUT / 'diagnostic_example_traces.csv')],ignore_index=True)
    if trace.empty:
        return
    # Selection is fixed before outcome inspection: earliest evaluation window, pH,
    # first lexicographic evaluated setting, spike/bias/legitimate positive cases.
    method = 'aasvr_measurement'
    subset = trace[trace.method == method]
    if subset.empty:
        method = 'persistence_only'
        subset = trace[trace.method == method]
    if subset.empty:
        return
    setting = sorted(subset.setting.unique())[0]
    subset = subset[subset.setting == setting]
    sensor = next(s for s in load_aasvr_config(ROOT / 'configs/methods/aasvr.yaml').sensors if s.name == 'pH')
    fig, axes = plt.subplots(3, 3, figsize=(13,8), sharex='col', gridspec_kw={'height_ratios':[3,1,1]})
    for col, case in enumerate(('spike_positive','bias_positive','legitimate_positive')):
        g = subset[subset.scenario == case].sort_values('seconds')
        t = g.seconds.to_numpy()
        axes[0,col].plot(t/60,g.background,label='Surrogate',color='black',linewidth=1.3)
        axes[0,col].plot(t/60,g.corrupted,label='Input',alpha=.65)
        axes[0,col].plot(t/60,g.estimate,label='Held estimate',linestyle='--')
        axes[0,col].axhspan(sensor.control_low,sensor.control_high,color='green',alpha=.08)
        axes[0,col].set_title(case.replace('_',' '))
        axes[1,col].step(t/60,g.accepted.astype(int),where='post',label='Accepted')
        _,_,reference = reference_trace(t,g.background.to_numpy(),sensor.control_low,sensor.control_high,
            Timing(persistence=cfg['reference_persistence_seconds'],cooldown=cfg['cooldown_seconds']))
        ri = np.flatnonzero(reference)
        ai = np.flatnonzero(g.action.to_numpy())
        axes[2,col].scatter(t[ri]/60,reference[ri],marker='|',s=90,label='Reference')
        axes[2,col].scatter(t[ai]/60,g.action.to_numpy()[ai],marker='x',label='Policy')
        axes[2,col].set_xlabel('Elapsed minutes')
        for row in range(3):
            axes[row,col].grid(alpha=.15)
    axes[0,0].set_ylabel('pH')
    axes[1,0].set_ylabel('Gate pass')
    axes[2,0].set_ylabel('Direction')
    axes[0,0].legend(fontsize=8)
    axes[2,0].legend(fontsize=8)
    fig.suptitle(f'Diagnostic (coverage target not met): {method}, {setting}; first evaluation window')
    fig.tight_layout()
    fig.savefig(FIG / 'example_traces.png',dpi=180)
    fig.savefig(FIG / 'example_traces.pdf')
    plt.close(fig)


if __name__ == '__main__':
    main()
