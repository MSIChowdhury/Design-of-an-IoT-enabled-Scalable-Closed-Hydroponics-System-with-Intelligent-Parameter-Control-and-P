"""Apply the frozen LiveGate decision rules and write tables.

Rules are those in docs/livegate/PROTOCOL.md; this script only evaluates them.
Run in Docker after scripts/66_livegate_benchmark.py.
"""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

from aasvr.config import load_yaml

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / os.environ.get("LIVEGATE_OUT", "results/metrics/livegate")
CONFIG = ROOT / os.environ.get("LIVEGATE_CONFIG", "configs/experiments/livegate.yaml")
TABLES = ROOT / "results/tables/livegate"
COVERAGE_SLACK = 0.02
TRIVIAL = ("always_deny",)


def main():
    cfg = load_yaml(CONFIG)
    deadline = cfg["selection_deadline_seconds"]
    TABLES.mkdir(parents=True, exist_ok=True)
    summary = pd.read_csv(RUN / "evaluation_summary.csv")
    paired = pd.read_csv(RUN / "paired_intervals_vs_livegate.csv")
    evaluated = summary[(summary.status == "evaluated") & (summary.deadline == deadline)
                        & ~summary.method.isin(TRIVIAL)]
    verdicts = []
    for target in cfg["minimum_coverages"]:
        pool = evaluated[evaluated.target == target]
        row = {"target": target, "feasible_methods": len(pool),
               "livegate_feasible": "livegate" in set(pool.method)}
        if pool.empty:
            verdicts.append({**row, "rule1_best": None, "rule2_clearly_best": None})
            continue
        ranked = pool.sort_values(["undesirable_per_trial", "coverage"], ascending=[True, False])
        row["lowest_undesirable_method"] = ranked.method.iloc[0]
        row["best_coverage"] = pool.coverage.max()
        if row["livegate_feasible"]:
            lg = pool[pool.method == "livegate"].iloc[0]
            others = pool[pool.method != "livegate"]
            runner = others.sort_values(["undesirable_per_trial", "coverage"], ascending=[True, False]).iloc[0]
            rule1 = (lg.undesirable_per_trial <= others.undesirable_per_trial.min()
                     and lg.coverage >= pool.coverage.max() - COVERAGE_SLACK)
            interval = paired[(paired.target == target) & (paired.method == runner.method)
                              & (paired.metric == "undesirable_per_trial")]
            rule2 = bool(rule1 and len(interval) and interval.ci_low.iloc[0] > 0)
            row.update({"livegate_coverage": lg.coverage, "livegate_undesirable": lg.undesirable_per_trial,
                        "runner_up": runner.method, "runner_up_coverage": runner.coverage,
                        "runner_up_undesirable": runner.undesirable_per_trial,
                        "runner_minus_livegate_ci": f"[{interval.ci_low.iloc[0]:.4f}, {interval.ci_high.iloc[0]:.4f}]"
                            if len(interval) else "",
                        "rule1_best": bool(rule1), "rule2_clearly_best": rule2})
        verdicts.append(row)
    verdicts = pd.DataFrame(verdicts)
    feasible_somewhere = verdicts[verdicts.feasible_methods > 0]
    overall = bool(feasible_somewhere.livegate_feasible.all()
                   and feasible_somewhere.loc[feasible_somewhere.livegate_feasible, "rule1_best"].all())
    verdicts.to_csv(TABLES / "decision_rules.csv", index=False)
    evaluated.sort_values(["target", "undesirable_per_trial"]).to_csv(TABLES / "evaluation_by_target.csv", index=False)
    scenario = pd.read_csv(RUN / "evaluation_by_scenario.csv")
    focus = scenario[scenario.scenario.isin(["stuck", "saturation", "spike_positive", "bias_positive",
                                              "legitimate_positive", "clean"])]
    focus.to_csv(TABLES / "evaluation_selected_scenarios.csv", index=False)
    audit = pd.read_csv(RUN / "real_log_audit.csv")
    audit_total = audit.groupby(["method", "setting", "setting_basis"], as_index=False)[
        ["authorizations", "fault_driven_authorizations", "certain_fault_readings",
         "rejected_certain_fault_readings"]].sum().sort_values("fault_driven_authorizations")
    audit_total.to_csv(TABLES / "real_log_audit_totals.csv", index=False)
    pd.set_option("display.width", 200)
    print(verdicts.to_string(index=False))
    print(f"\nOverall 'best' claim (rule 3): {overall}\n")
    print(audit_total.to_string(index=False))


if __name__ == "__main__":
    main()
