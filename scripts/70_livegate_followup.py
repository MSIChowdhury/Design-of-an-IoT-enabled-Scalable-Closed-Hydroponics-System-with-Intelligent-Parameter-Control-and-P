"""Post-hoc direct-baseline comparison and paired liveness uncertainty.

Reuses the frozen runner without modifying it or its outputs. Run in Docker.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

from aasvr.config import load_yaml
from aasvr.reanalysis import summarize
from aasvr.simple_gates import fixed_run_length, physical_bound_rejection

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/metrics/livegate_followup"
TABLE = ROOT / "results/tables/livegate_followup"
FIG = ROOT / "results/figures/livegate_followup"
CONFIG = ROOT / "configs/experiments/livegate_followup.yaml"
ORIGINAL = ROOT / "results/metrics/livegate"
NEW_METHODS = ("fixed_run_length", "physical_bound")
FOCUS = ("persistence_only", "livegate", "livegate_no_forecast", *NEW_METHODS)
LABELS = {"persistence_only": "Persistence only", "livegate": "LiveGate",
          "livegate_no_forecast": "Learned liveness only", "fixed_run_length": "Fixed repeat cap",
          "physical_bound": "Physical-bound rejection"}


def fingerprints():
    paths = [ROOT / "scripts/66_livegate_benchmark.py", ROOT / "src/aasvr/livegate.py",
             ROOT / "configs/experiments/livegate.yaml", ROOT / "docs/livegate/PROTOCOL.md"]
    paths += sorted(p for p in ORIGINAL.rglob("*") if p.is_file())
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def runner():
    spec = importlib.util.spec_from_file_location("locked_livegate", ROOT / "scripts/66_livegate_benchmark.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.OUT, module.FIG, module.CONFIG = OUT, FIG, CONFIG
    module.METHODS = (*module.METHODS, *NEW_METHODS)
    original_detect, original_grid = module.detect, module.grid_values

    def detect(method, x, times, hours, context, sensor, base, value, lof, noise, models, cfg):
        if method == "fixed_run_length":
            accepted = fixed_run_length(x, times, sensor.physical_min, sensor.physical_max,
                                        max_run=value, max_gap=cfg["max_gap_seconds"])
        elif method == "physical_bound":
            accepted = physical_bound_rejection(x, sensor.physical_min, sensor.physical_max)
        else:
            return original_detect(method, x, times, hours, context, sensor, base,
                                   value, lof, noise, models, cfg)
        return accepted, accepted.copy()

    def grid(method, cfg):
        if method == "fixed_run_length":
            return cfg["fixed_run_caps"]
        return [1.0] if method == "physical_bound" else original_grid(method, cfg)

    module.detect, module.grid_values = detect, grid
    return module


def verify_reproduction():
    checks = []
    for name, keys in (("evaluation_summary.csv", ["target", "method", "deadline"]),
                       ("locked_validation_selections.csv", ["target", "method"]),
                       ("source_windows.csv", ["split", "window_id"])):
        expected, actual = pd.read_csv(ORIGINAL / name), pd.read_csv(OUT / name)
        if "method" in actual:
            actual = actual[~actual.method.isin(NEW_METHODS)]
        actual = actual[expected.columns].sort_values(keys).reset_index(drop=True)
        expected = expected.sort_values(keys).reset_index(drop=True)
        pd.testing.assert_frame_equal(expected, actual, check_exact=False, rtol=1e-12, atol=1e-12)
        checks.append({"artifact": name, "rows": len(expected), "reproduced": True})
    pd.DataFrame(checks).to_csv(TABLE / "reproduction_checks.csv", index=False)
    return checks


def selected_groups(detail, selections, target):
    selected = selections[(selections.target == target) & (selections.status == "selected")]
    return {r.method: detail[(detail.method == r.method) & (detail.setting == r.setting)]
            .set_index("trial_id").sort_index() for r in selected.itertuples()}


def cluster_statistics(group, days):
    data = group.copy()
    data["n"] = 1
    data["undesirable"] = data.unnecessary + data.wrong_direction
    columns = ["n", "matched", "opportunities", "undesirable", "fault_evidence", "held_fault_evidence"]
    return data.groupby("source_day")[columns].sum().reindex(days, fill_value=0).to_numpy(float)


def ratios(totals):
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.stack([totals[..., 1] / totals[..., 2], totals[..., 3] / totals[..., 0],
                         totals[..., 4] / totals[..., 0], totals[..., 5] / totals[..., 0]], axis=-1)


def confidence_and_sensor_tables(detail, selections, cfg):
    rows, sensors = [], []
    metric_names = ["coverage", "undesirable_per_trial", "fault_interval_per_trial", "held_fault_per_trial"]
    for target in cfg["minimum_coverages"]:
        groups = selected_groups(detail, selections, target)
        if "persistence_only" not in groups:
            continue
        ref = groups["persistence_only"]
        days = sorted(ref.source_day.unique())
        rng = np.random.default_rng(cfg["seed"])
        draws = rng.multinomial(len(days), np.ones(len(days)) / len(days),
                                size=cfg["bootstrap_replicates"])
        for method, group in groups.items():
            aligned = group.loc[ref.index]
            for sensor in ("ALL", *sorted(ref.sensor.unique())):
                for scenario in ("ALL", "stuck", "saturation"):
                    mask = np.ones(len(ref), bool)
                    if sensor != "ALL":
                        mask &= ref.sensor.to_numpy() == sensor
                    if scenario != "ALL":
                        mask &= ref.scenario.to_numpy() == scenario
                    a, b = aligned.iloc[np.flatnonzero(mask)], ref.iloc[np.flatnonzero(mask)]
                    stats_a, stats_b = cluster_statistics(a, days), cluster_statistics(b, days)
                    point_a, point_b = ratios(stats_a.sum(axis=0)), ratios(stats_b.sum(axis=0))
                    boot_a, boot_b = ratios(draws @ stats_a), ratios(draws @ stats_b)
                    sensors.append({"target": target, "method": method, "sensor": sensor,
                                    "scenario": scenario, "source_days": len(days), **summarize(a)})
                    for j, metric in enumerate(metric_names):
                        effects = [("difference", point_a[j] - point_b[j], boot_a[:, j] - boot_b[:, j])]
                        if metric in ("fault_interval_per_trial", "held_fault_per_trial"):
                            with np.errstate(divide="ignore", invalid="ignore"):
                                reduction = 1 - point_a[j] / point_b[j]
                                boot_reduction = 1 - boot_a[:, j] / boot_b[:, j]
                            effects.append(("relative_reduction", reduction, boot_reduction))
                        for effect, point, samples in effects:
                            finite = samples[np.isfinite(samples)]
                            lo, hi = np.quantile(finite, [.025, .975]) if len(finite) else (np.nan, np.nan)
                            rows.append({"target": target, "method": method, "reference": "persistence_only",
                                         "sensor": sensor, "scenario": scenario, "metric": metric,
                                         "effect": effect, "estimate": point, "ci_low": lo, "ci_high": hi,
                                         "source_days": len(days), "trials": len(a),
                                         "defined_replicates": len(finite), "bootstrap_replicates": len(draws)})
    intervals, by_sensor = pd.DataFrame(rows), pd.DataFrame(sensors)
    intervals.to_csv(TABLE / "paired_source_day_intervals.csv", index=False)
    by_sensor.to_csv(TABLE / "sensor_scenario_metrics.csv", index=False)
    return intervals, by_sensor


def cell_interval(row, percent=False):
    if not np.isfinite(row.estimate):
        return "undefined"
    scale, places = (100, 1) if percent else (1, 3)
    return (f"{row.estimate * scale:.{places}f} "
            f"[{row.ci_low * scale:.{places}f}, {row.ci_high * scale:.{places}f}]")


def md_table(frame, columns):
    header = "| " + " | ".join(columns) + " |\n"
    line = "| " + " | ".join("---" for _ in columns) + " |\n"
    return header + line + "\n".join("| " + " | ".join(str(row[c]) for c in columns) + " |"
                                     for _, row in frame.iterrows())


def plot_direct_comparison(table, by_sensor, target):
    import matplotlib.pyplot as plt

    methods = list(table.index)
    names = [LABELS[m] for m in methods]
    colors = ["#2a78d6", "#eb6834", "#eb6834", "#6250d6", "#1baf7a"][:len(methods)]
    fig, axes = plt.subplots(2, 2, figsize=(10.5, 6.2), sharey=True)
    values = [table.coverage.to_numpy(), table.undesirable_per_trial.to_numpy()]
    for scenario in ("stuck", "saturation"):
        part = by_sensor[(by_sensor.target == target) & (by_sensor.sensor == "ALL")
                         & (by_sensor.scenario == scenario)].set_index("method")
        values.append(part.loc[methods].held_fault_evidence_per_trial.to_numpy())
    titles = ["Useful-command coverage", "Undesirable commands / trial",
              "Stuck: commands using fault source / trial", "Saturation: commands using fault source / trial"]
    for ax, data, title in zip(axes.flat, values, titles):
        ax.barh(np.arange(len(methods)), data, color=colors, height=.62)
        limit = max(float(max(data)) * 1.2, .1)
        ax.set_xlim(0, max(limit, 1.04) if ax is axes.flat[0] else limit)
        ax.set_yticks(np.arange(len(methods)), names, fontsize=9)
        ax.set_title(title, fontsize=10, loc="left")
        for i, value in enumerate(data):
            ax.text(value + ax.get_xlim()[1] * .02, i, f"{value:.3f}", va="center", fontsize=9)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        ax.grid(axis="x", alpha=.2)
        ax.set_axisbelow(True)
    axes[0, 0].invert_yaxis()
    axes[0, 0].axvline(target, color="#666666", ls="--", lw=1)
    fig.suptitle("Post-hoc comparison: settings selected at 0.8 validation coverage", fontsize=12)
    fig.tight_layout()
    fig.savefig(FIG / "direct_comparison.pdf")
    fig.savefig(FIG / "direct_comparison.png", dpi=180)
    plt.close(fig)


def report(checks, intervals, by_sensor, cfg):
    summary = pd.read_csv(OUT / "evaluation_summary.csv")
    selected = pd.read_csv(OUT / "locked_validation_selections.csv")
    summary = summary[(summary.status == "evaluated") & (summary.deadline == cfg["selection_deadline_seconds"])]
    focus = summary[summary.method.isin(FOCUS)].copy()
    focus["evaluation_target_met"] = focus.coverage >= focus.target
    focus.to_csv(TABLE / "followup_operating_points.csv", index=False)
    selected[selected.method.isin(NEW_METHODS)].to_csv(TABLE / "new_baseline_selections.csv", index=False)
    target = .8
    table = focus[focus.target == target].set_index("method").reindex(FOCUS).dropna(subset=["coverage"])
    plot_direct_comparison(table, by_sensor, target)
    effects = intervals[(intervals.target == target) & (intervals.method == "livegate_no_forecast")
                        & (intervals.sensor == "ALL") & intervals.scenario.isin(["stuck", "saturation"])]
    compact = effects[["scenario", "metric", "effect", "estimate", "ci_low", "ci_high", "defined_replicates"]].copy()
    for column in ("estimate", "ci_low", "ci_high"):
        compact[column] = compact[column].round(4)
    view = table.reset_index()[["method", "setting", "coverage", "undesirable_per_trial", "evaluation_target_met"]]
    view[["coverage", "undesirable_per_trial"]] = view[["coverage", "undesirable_per_trial"]].round(4)
    all_view = focus[["target", "method", "setting", "coverage", "undesirable_per_trial", "evaluation_target_met"]].copy()
    all_view[["coverage", "undesirable_per_trial"]] = all_view[["coverage", "undesirable_per_trial"]].round(4)
    saturation = by_sensor[(by_sensor.target == target) & (by_sensor.sensor == "ALL")
                           & (by_sensor.scenario == "saturation")].set_index("method")
    bound_source = saturation.loc["physical_bound"].held_fault_evidence_per_trial
    bound_coverage = saturation.loc["physical_bound"].coverage
    interpretation = (
        f"Physical-bound rejection produced {bound_source:.3f} commands per saturation trial "
        "using an injected-fault source, while its useful-command coverage in those trials was "
        f"{bound_coverage:.3f}. Thus learned liveness was not unique in suppressing saturated "
        "source evidence. The fixed-cap gate and physical-bound gate improved both overall "
        "coverage and undesirable-command rate relative to full LiveGate at the selected 0.8 "
        "target. Physical-bound rejection also improved both relative to learned liveness-only, "
        "but its evaluation coverage (0.798) fell slightly below 0.8. Persistence-only had higher "
        "coverage than the fixed-cap gate at the same undesirable rate. These are point-estimate "
        "operating comparisons, not statistical superiority claims or evidence of field safety.")
    text = ("# Post-hoc direct-baseline follow-up results\n\n"
            "Protocol: [FOLLOWUP_PROTOCOL.md](FOLLOWUP_PROTOCOL.md). Run: "
            "`make livegate-followup` (or `python scripts/70_livegate_followup.py` in Docker).\n\n"
            "The original frozen artifacts were preserved byte-for-byte. All "
            f"{checks[0]['rows']} original evaluation-summary rows, original validation selections, "
            "and source windows reproduced to numerical tolerance 1e-12.\n\n"
            "Evaluation uses eight windows on seven source days, with five sensors and 12 scenarios "
            "(480 paired sensor/scenario trials per selected setting). These are not independent "
            "deployments. Added baselines are post-hoc and were selected only on validation.\n\n"
            "## Selected follow-up operating points\n\n" + md_table(all_view, list(all_view.columns)) +
            "\n\nThe cap in a fixed-repeat setting `mR_pP_aA` permits R identical readings; "
            "P and A are persistence and maximum held age in seconds. Target attainment in "
            "this table is evaluated after locking validation selections. The full selection table "
            "also reports infeasible targets; failure to reach a target is not hidden.\n\n"
            "## Interpretation\n\n" + interpretation + "\n\n"
            "## Learned liveness versus persistence: pooled paired intervals\n\n"
            "`fault_interval_per_trial` reproduces the original counter of commands at "
            "fault-labelled samples. `held_fault_per_trial` attributes commands to the last "
            "accepted source reading. Only the second establishes that the replay used injected "
            "fault evidence; neither measures physical execution. Differences are method minus "
            "persistence; reductions are 1 - method/reference.\n\n" + md_table(compact, list(compact.columns)) +
            "\n\nIntervals are paired source-day percentile 95% intervals from 1000 draws, "
            "conditional on the selected settings and without multiplicity adjustment. Few source "
            "days, post-hoc comparison, and limited backgrounds restrict generalization. Relative "
            "reductions with zero reference evidence are undefined; defined bootstrap counts are "
            "reported. Per-sensor outcomes, both evidence definitions, all overall coverage costs, "
            "and paired intervals are in `results/tables/livegate_followup/`.\n\n"
            "A learned survival threshold is mathematically a sensor-specific repeat cap at fixed "
            "epsilon. Beating a global fixed cap would not establish superiority to every "
            "per-sensor tuned cap. Physical-bound rejection is a direct saturation comparator. "
            "Claims should be limited to these settings and this retrospective benchmark.\n")
    (ROOT / "docs/livegate/FOLLOWUP_RESULTS.md").write_text(text)
    tex = [r"\subsection{Post-hoc direct-baseline comparison}",
           "A separately labelled follow-up reran the original methods and added two direct "
           "comparators: a fixed repeat cap and rejection at either physical bound. The repeat "
           "cap accepts the first $R$ identical in-range readings, rejects subsequent repeats, "
           "and resets after a change, invalid reading, or logging gap. "
           "$R\\in\\{2,4,8,16,32,64\\}$ is shared across channels; the six-value grid is larger "
           "than LiveGate's three-value grid. Both comparators use the original timing grid "
           "and validation-only selection. All original evaluation summary rows and selections "
           "reproduced, while the frozen artifacts remained unchanged. The follow-up is "
           "post-hoc because the data and original results had already been examined.",
           r"\begin{table}[!htbp]\centering\small\setlength{\tabcolsep}{4pt}",
           r"\caption{Post-hoc evaluation at the 0.8 validation coverage target. A dagger marks "
           r"evaluation coverage below 0.8. Fault-source counts attribute each command to its "
           r"last accepted reading, per trial. These are simulated authorizations.}",
           r"\label{tab:followup}",
           r"\begin{tabular}{p{0.35\linewidth}rrrr}\toprule",
           r"& Coverage & Undesirable & \multicolumn{2}{c}{Fault-source commands}\\",
           r"Method & & / trial & Stuck & Saturation\\\midrule"]
    for method, row in table.iterrows():
        kind = by_sensor[(by_sensor.target == target) & (by_sensor.method == method) & (by_sensor.sensor == "ALL")]
        stuck = kind[kind.scenario == "stuck"].iloc[0].held_fault_evidence_per_trial
        sat = kind[kind.scenario == "saturation"].iloc[0].held_fault_evidence_per_trial
        mark = r"$^{\dagger}$" if row.coverage < target else ""
        tex.append(f"{LABELS[method]} & {row.coverage:.3f}{mark} & {row.undesirable_per_trial:.3f} & {stuck:.3f} & {sat:.3f}" + r"\\")
    tex += [r"\bottomrule\end{tabular}\end{table}"]
    tex.append(interpretation)
    for method in NEW_METHODS:
        row = table.loc[method]
        value, persistence, age = [float(x[1:]) for x in row.setting.split("_")]
        cap = f"a repeat cap of {int(value)}, " if method == "fixed_run_length" else ""
        tex.append(f"At target 0.8, validation selected {cap}{persistence:g}~s persistence "
                   f"and {age:g}~s maximum age for {LABELS[method].lower()}.")
    for kind in ("stuck", "saturation"):
        a = effects[(effects.scenario == kind) & (effects.metric == "fault_interval_per_trial") &
                    (effects.effect == "relative_reduction")].iloc[0]
        b = effects[(effects.scenario == kind) & (effects.metric == "held_fault_per_trial") &
                    (effects.effect == "relative_reduction")].iloc[0]
        tex.append(f"For {kind}, the learned liveness-only arm's reduction relative to persistence "
                   f"was {cell_interval(a, True)}\\% for commands during injected-fault samples, "
                   f"and {cell_interval(b, True)}\\% for commands using injected-fault source readings "
                   "(paired source-day 95\\% intervals in brackets).")
        scenario_rows = by_sensor[(by_sensor.target == target) & (by_sensor.sensor == "ALL")
                                  & (by_sensor.scenario == kind)].set_index("method")
        learned_coverage = scenario_rows.loc["livegate_no_forecast"].coverage
        reference_coverage = scenario_rows.loc["persistence_only"].coverage
        tex.append(f"Useful-command coverage in the same {kind} trials fell from "
                   f"{reference_coverage:.3f} with persistence to {learned_coverage:.3f} "
                   "with learned liveness. These reductions therefore do not establish "
                   "better fault handling at matched useful-command coverage.")
    tex.append("These two counters answer different questions: a command during a fault interval "
               "can still use a held clean reading. Neither measures physical execution or damage. "
               "The estimates use eight evaluation windows on seven source-day clusters; settings "
               "remain fixed during resampling, and the secondary intervals have no multiplicity "
               "adjustment. The limited number of days makes generalization uncertain.")
    tex += [r"\begin{table}[!htbp]\centering\small\setlength{\tabcolsep}{4pt}",
            r"\caption{Sensor-specific learned-liveness effects relative to persistence at target 0.8. "
            r"Differences are method minus persistence. Fault-source differences are commands per "
            r"trial; brackets give paired source-day 95\% intervals. Coverage differences pool all scenarios.}",
            r"\label{tab:liveness-sensors}",
            r"\begin{tabular}{lrrr}\toprule",
            r"Sensor & \shortstack{Coverage\\difference} & \shortstack{Stuck\\difference [95\% CI]} & \shortstack{Saturation\\difference [95\% CI]}\\\midrule"]
    labels = {"Air_Temp": "Air temp.", "Water_Temp": "Water temp.", "CO2": r"CO$_2$"}
    for sensor in cfg["sensors"]:
        mask = (intervals.target == target) & (intervals.method == "livegate_no_forecast") & (intervals.sensor == sensor) & (intervals.effect == "difference")
        part = intervals[mask]
        cov = part[(part.metric == "coverage") & (part.scenario == "ALL")].iloc[0]
        stuck = part[(part.metric == "held_fault_per_trial") & (part.scenario == "stuck")].iloc[0]
        sat = part[(part.metric == "held_fault_per_trial") & (part.scenario == "saturation")].iloc[0]
        tex.append(f"{labels.get(sensor, sensor)} & {cov.estimate:.3f} & {cell_interval(stuck)} & {cell_interval(sat)}" + r"\\")
    tex += [r"\bottomrule\end{tabular}\end{table}",
            "The learned rule is itself a sensor-specific repeat threshold at fixed $\\varepsilon$. "
            "Comparison with a global fixed cap does not establish superiority over all "
            "per-sensor thresholds. Benefits must be weighed against the useful-authorizations "
            "lost by rejecting legitimate repeated readings."]
    (ROOT / "Paper Files/livegate_followup_results.tex").write_text("\n\n".join(tex) + "\n")
    print(view.to_string(index=False), flush=True)
    print(compact.to_string(index=False), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-only", action="store_true", help="rebuild reports from existing follow-up outputs")
    args = parser.parse_args()
    for path in (OUT, FIG, TABLE):
        path.mkdir(parents=True, exist_ok=True)
    frozen = fingerprints()
    if not args.report_only:
        runner().main()
    if fingerprints() != frozen:
        raise AssertionError("Frozen artifacts changed during the follow-up")
    checks = verify_reproduction()
    cfg = load_yaml(CONFIG)
    detail = pd.read_csv(OUT / "evaluation_detail.csv.gz")
    detail = detail[detail.deadline == cfg["selection_deadline_seconds"]]
    selections = pd.read_csv(OUT / "locked_validation_selections.csv")
    intervals, by_sensor = confidence_and_sensor_tables(detail, selections, cfg)
    report(checks, intervals, by_sensor, cfg)
    inputs = [CONFIG, ROOT / "scripts/70_livegate_followup.py", ROOT / "src/aasvr/simple_gates.py",
              ROOT / "data/processed/hydro_exp1_measurements.parquet"]
    manifest = {"status": "post-hoc retrospective follow-up", "original_artifacts_preserved": True,
                "frozen_fingerprints": frozen, "reproduction_checks": checks,
                "followup_inputs": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}}
    (OUT / "provenance.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
