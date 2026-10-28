# Post-hoc direct-baseline follow-up results

Protocol: [FOLLOWUP_PROTOCOL.md](FOLLOWUP_PROTOCOL.md). Run: `make livegate-followup` (or `python scripts/70_livegate_followup.py` in Docker).

The original frozen artifacts were preserved byte-for-byte. All 89 original evaluation-summary rows, original validation selections, and source windows reproduced to numerical tolerance 1e-12.

Evaluation uses eight windows on seven source days, with five sensors and 12 scenarios (480 paired sensor/scenario trials per selected setting). These are not independent deployments. Added baselines are post-hoc and were selected only on validation.

## Selected follow-up operating points

| target | method | setting | coverage | undesirable_per_trial | evaluation_target_met |
| --- | --- | --- | --- | --- | --- |
| 0.5 | persistence_only | m1_p96_a64 | 0.7947 | 0.1104 | True |
| 0.5 | livegate | m0.05_p96_a64 | 0.5048 | 0.1354 | True |
| 0.5 | livegate_no_forecast | m0.05_p96_a64 | 0.56 | 0.0812 | True |
| 0.5 | fixed_run_length | m4_p96_a320 | 0.5556 | 0.1083 | True |
| 0.5 | physical_bound | m1_p96_a64 | 0.727 | 0.0667 | True |
| 0.8 | persistence_only | m1_p32_a64 | 0.8859 | 0.1167 | True |
| 0.8 | livegate | m0.002_p32_a64 | 0.7903 | 0.1354 | False |
| 0.8 | livegate_no_forecast | m0.05_p32_a64 | 0.663 | 0.1042 | False |
| 0.8 | fixed_run_length | m64_p32_a64 | 0.8492 | 0.1167 | True |
| 0.8 | physical_bound | m1_p32_a64 | 0.7976 | 0.0833 | False |

The cap in a fixed-repeat setting `mR_pP_aA` permits R identical readings; P and A are persistence and maximum held age in seconds. Target attainment in this table is evaluated after locking validation selections. The full selection table also reports infeasible targets; failure to reach a target is not hidden.

## Interpretation

Physical-bound rejection produced 0.000 commands per saturation trial using an injected-fault source, while its useful-command coverage in those trials was 0.073. Thus learned liveness was not unique in suppressing saturated source evidence. The fixed-cap gate and physical-bound gate improved both overall coverage and undesirable-command rate relative to full LiveGate at the selected 0.8 target. Physical-bound rejection also improved both relative to learned liveness-only, but its evaluation coverage (0.798) fell slightly below 0.8. Persistence-only had higher coverage than the fixed-cap gate at the same undesirable rate. These are point-estimate operating comparisons, not statistical superiority claims or evidence of field safety.

## Learned liveness versus persistence: pooled paired intervals

`fault_interval_per_trial` reproduces the original counter of commands at fault-labelled samples. `held_fault_per_trial` attributes commands to the last accepted source reading. Only the second establishes that the replay used injected fault evidence; neither measures physical execution. Differences are method minus persistence; reductions are 1 - method/reference.

| scenario | metric | effect | estimate | ci_low | ci_high | defined_replicates |
| --- | --- | --- | --- | --- | --- | --- |
| stuck | coverage | difference | -0.7091 | -0.7963 | -0.6132 | 1000 |
| stuck | undesirable_per_trial | difference | -0.025 | -0.06 | 0.0 | 1000 |
| stuck | fault_interval_per_trial | difference | -0.5 | -0.6753 | -0.36 | 1000 |
| stuck | fault_interval_per_trial | relative_reduction | 0.6897 | 0.5427 | 0.8573 | 1000 |
| stuck | held_fault_per_trial | difference | -0.575 | -0.7143 | -0.46 | 1000 |
| stuck | held_fault_per_trial | relative_reduction | 0.7931 | 0.7097 | 0.8889 | 1000 |
| saturation | coverage | difference | -0.5091 | -0.6293 | -0.3964 | 1000 |
| saturation | undesirable_per_trial | difference | -0.125 | -0.2286 | -0.044 | 1000 |
| saturation | fault_interval_per_trial | difference | -0.3 | -0.4502 | -0.1799 | 1000 |
| saturation | fault_interval_per_trial | relative_reduction | 0.3077 | 0.18 | 0.4617 | 1000 |
| saturation | held_fault_per_trial | difference | -0.3 | -0.4502 | -0.1799 | 1000 |
| saturation | held_fault_per_trial | relative_reduction | 0.3077 | 0.18 | 0.4617 | 1000 |

Intervals are paired source-day percentile 95% intervals from 1000 draws, conditional on the selected settings and without multiplicity adjustment. Few source days, post-hoc comparison, and limited backgrounds restrict generalization. Relative reductions with zero reference evidence are undefined; defined bootstrap counts are reported. Per-sensor outcomes, both evidence definitions, all overall coverage costs, and paired intervals are in `results/tables/livegate_followup/`.

A learned survival threshold is mathematically a sensor-specific repeat cap at fixed epsilon. Beating a global fixed cap would not establish superiority to every per-sensor tuned cap. Physical-bound rejection is a direct saturation comparator. Claims should be limited to these settings and this retrospective benchmark.
