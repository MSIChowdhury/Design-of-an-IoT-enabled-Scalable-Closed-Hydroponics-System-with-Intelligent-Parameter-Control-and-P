# LiveGate locked comparison results

Protocol: [PROTOCOL.md](PROTOCOL.md), frozen at commit `468db4e` before the
measured-data run. Commands: `make livegate`, then `scripts/67_report_livegate.py`.
Retrospective data; see the protocol.

## Decision

**LiveGate does not meet the protocol's "best" criterion.** Rule 3 (overall best)
is false. Rule 1 fails at both feasible coverage targets; no method was feasible
at the 0.95 target.

| Target | LiveGate coverage | LiveGate undesirable/trial | Lowest undesirable | Runner-up − LiveGate (95% CI) |
|---|---|---|---|---|
| 0.5 | 0.505 | 0.135 | LOF 0.075 (coverage 0.357) | [−0.148, −0.004] |
| 0.8 | 0.790 | 0.135 | LiveGate liveness-only ablation 0.104 (coverage 0.663) | [−0.083, 0.002] |

At the 0.8 target, persistence-only had higher coverage (0.886) and fewer
undesirable authorizations (0.117) than full LiveGate.

## What worked: the liveness component

Per-scenario evaluation at the 0.8 target (authorizations made on fault evidence,
per trial):

| Scenario | Persistence only | Full LiveGate | Liveness only (no forecast) | Forecast only (no liveness) |
|---|---|---|---|---|
| Stuck | 0.725 | 0.500 | **0.225** | 0.725 |
| Saturation at full scale | 0.975 | 0.650 | **0.675** | 0.975 |

The liveness test cut stuck-fault-driven authorizations by 69% and
saturation-driven authorizations by 31% relative to persistence-only. Every other
comparator matched persistence-only on these two scenarios, except Kalman on
saturation (0.850). The
liveness-only arm also had the lowest undesirable rate at the 0.8 target, but its
coverage (0.663) was more than 0.02 below the best, so rule 1 does not credit it.

## What failed: the forecaster

The forecast-only ablation rejected 3.2% of clean readings at the 0.8 target
(persistence only: 0%) and had more undesirable authorizations (0.150 vs 0.117).

**Correction.** An earlier version of this file attributed the shortfall to the
near-zero fitted scales on the temperature channels (1.6×10⁻⁵ and 1.1×10⁻⁷ °C).
That diagnosis was wrong. The exploratory v2 below floors the scale at the
reading resolution and changes no decision, because the conformal threshold is
calibrated on scores divided by the same scale.

## Exploratory post-hoc variant (v2)

`livegate_v2` floors the residual scale at each sensor's reading resolution
(`resolution_floor=True`). It was rerun with every comparator
(`results/metrics/livegate_v2_exploratory/`). All 66 previously evaluated rows
reproduced exactly. LiveGate v2's selected settings and evaluation results are
identical to locked LiveGate at the 0.5 and 0.8 targets.

## Real-log audit

The evaluation period contained 180 certain-fault readings. Every method except
persistence-only (3 fault-driven authorizations) had 0 or 1. The long CO2
full-scale episodes fall outside the evaluation period, so the audit cannot
separate the methods.

## Outputs

`results/metrics/livegate/` (detail, selections, summaries, paired intervals,
audit) and `results/tables/livegate/` (decision rules, per-target, per-scenario,
audit totals).
