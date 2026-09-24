# Retrospective replay reanalysis results

Run protocol: [PROTOCOL.md](PROTOCOL.md). Historical manuscript tables were not replaced.

**Decision: the measurement supervisor did not meet the lowest declared validation coverage target within this search. This run does not establish its advantage at comparable useful-action coverage.** Simplify or narrow the contribution before rebuilding the manuscript.

No wrong-direction authorizations occurred in the evaluated scenarios. This limits what the experiment establishes about that endpoint; it does not demonstrate prevention of wrong-direction commands. Injections use one fixed onset within each window, one magnitude per sensor, and do not specifically sample threshold-adjacent backgrounds. Those are explicit limitations of this compact stopping-point experiment.

## Scope and evidence

- Source: 121,244 processed observations from 2024-02-27 20:01:07+00:00 to 2024-03-28 06:48:06+00:00.
- Median interval: 16 seconds; maximum gap: 32295 seconds; gaps above 120 seconds: 194.
- Six primary sensors; 8 nonoverlapping source windows per block; 11 scenarios per sensor/window. There are 528 validation trials and 528 evaluation trials before method expansion.
- Evaluation uses 7 distinct source days. Variants of a background are correlated, not independent physical experiments.
- Contiguous development/validation/evaluation blocks; windows crossing long gaps excluded. All inference is retrospective; prior development used this dataset.
- Surrogate-reference decisions are independent of tested estimates. Actuator activity is unknown. Main AASVR arms disable response-memory and uncommanded-trend gates.
- Source SHA-256: `6c034bed3948172e88d5ec9caf1885efe14795e4041c6a4b9cf2decc356e6a71`.
- Config SHA-256: `0daf4ce054ab9c21706abe40c2b86f8a951379cdbda820d8b1d87d40ed7c0414`.

## Locked operating points, 180-second matching deadline

Targets apply to validation coverage, not guaranteed evaluation coverage. Infeasible means no searched validation setting attained that target. Repeated settings across targets are not independent findings. Always-deny is shown separately at target zero.

| target | method | status | coverage | undesirable_per_trial | fault_evidence_per_trial | authorizations_per_trial | opportunities |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.500 | always_deny | infeasible | — | — | — | — | — |
| 0.500 | persistence_only | evaluated | 0.877 | 0.023 | 0.379 | 3.208 | 1755.000 |
| 0.500 | hampel | evaluated | 0.824 | 0.025 | 0.348 | 3.121 | 1755.000 |
| 0.500 | cusum | evaluated | 0.839 | 0.023 | 0.362 | 3.134 | 1755.000 |
| 0.500 | lof | evaluated | 0.379 | 0.017 | 0.176 | 1.693 | 1755.000 |
| 0.500 | aasvr_measurement | infeasible | — | — | — | — | — |
| 0.500 | aasvr_hold_only | evaluated | 0.591 | 0.019 | 0.282 | 2.540 | 1755.000 |
| 0.500 | aasvr_no_cusum | infeasible | — | — | — | — | — |
| 0.800 | always_deny | infeasible | — | — | — | — | — |
| 0.800 | persistence_only | evaluated | 0.877 | 0.023 | 0.379 | 3.208 | 1755.000 |
| 0.800 | hampel | evaluated | 0.813 | 0.025 | 0.347 | 3.191 | 1755.000 |
| 0.800 | cusum | evaluated | 0.815 | 0.021 | 0.347 | 3.193 | 1755.000 |
| 0.800 | lof | infeasible | — | — | — | — | — |
| 0.800 | aasvr_measurement | infeasible | — | — | — | — | — |
| 0.800 | aasvr_hold_only | infeasible | — | — | — | — | — |
| 0.800 | aasvr_no_cusum | infeasible | — | — | — | — | — |
| 0.950 | always_deny | infeasible | — | — | — | — | — |
| 0.950 | persistence_only | evaluated | 0.978 | 0.021 | 0.441 | 3.326 | 1755.000 |
| 0.950 | hampel | infeasible | — | — | — | — | — |
| 0.950 | cusum | infeasible | — | — | — | — | — |
| 0.950 | lof | infeasible | — | — | — | — | — |
| 0.950 | aasvr_measurement | infeasible | — | — | — | — | — |
| 0.950 | aasvr_hold_only | infeasible | — | — | — | — | — |
| 0.950 | aasvr_no_cusum | infeasible | — | — | — | — | — |
| 0.000 | always_deny | evaluated | 0.000 | 0.000 | 0.000 | 0.000 | 1755.000 |

Maximum validation coverage within the declared search:

| method | maximum_validation_coverage |
| --- | --- |
| aasvr_hold_only | 0.740 |
| aasvr_measurement | 0.397 |
| aasvr_no_cusum | 0.397 |
| always_deny | 0.000 |
| cusum | 0.930 |
| hampel | 0.929 |
| lof | 0.734 |
| persistence_only | 0.952 |

An undesirable authorization is unnecessary or wrong-direction relative to the surrogate. Fault-evidence authorization is a separate endpoint. A low error count coupled to poor coverage is suppression, not demonstrated superiority. The last 600 seconds of each window provide matching follow-up. Opportunities recur after the ten-minute reference lockout.

## Diagnostics for supervisors that failed validation coverage

These settings maximize validation coverage and were locked before their separate evaluation. They did **not** meet even the 50% validation target and are not promoted into the matched-target comparison.

| method | coverage | undesirable_per_trial | fault_evidence_per_trial | authorizations_per_trial | sample_recall | clean_rejection_rate |
| --- | --- | --- | --- | --- | --- | --- |
| aasvr_measurement | 0.483 | 0.021 | 0.229 | 2.318 | 0.466 | 0.297 |
| aasvr_no_cusum | 0.477 | 0.021 | 0.227 | 2.294 | 0.473 | 0.301 |

## Paired source-day bootstrap intervals

Differences are method minus persistence-only at the same validation target, using paired trial populations. Coverage is not forced equal on evaluation. Intervals are two-sided percentile 95% intervals from 1,000 day-cluster resamples. Eight source windows cannot establish deployment generalization.

| target | method | reference | metric | difference | ci_low | ci_high | source_days | bootstrap_unit | interval |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.500 | persistence_only | persistence_only | coverage | 0.000 | 0.000 | 0.000 | 7 | source_day | two-sided percentile 95% |
| 0.500 | persistence_only | persistence_only | undesirable_per_trial | 0.000 | 0.000 | 0.000 | 7 | source_day | two-sided percentile 95% |
| 0.500 | hampel | persistence_only | coverage | -0.054 | -0.057 | -0.049 | 7 | source_day | two-sided percentile 95% |
| 0.500 | hampel | persistence_only | undesirable_per_trial | 0.002 | 0.000 | 0.005 | 7 | source_day | two-sided percentile 95% |
| 0.500 | cusum | persistence_only | coverage | -0.038 | -0.059 | 0.002 | 7 | source_day | two-sided percentile 95% |
| 0.500 | cusum | persistence_only | undesirable_per_trial | 0.000 | 0.000 | 0.000 | 7 | source_day | two-sided percentile 95% |
| 0.500 | lof | persistence_only | coverage | -0.498 | -0.559 | -0.426 | 7 | source_day | two-sided percentile 95% |
| 0.500 | lof | persistence_only | undesirable_per_trial | -0.006 | -0.014 | 0.000 | 7 | source_day | two-sided percentile 95% |
| 0.500 | aasvr_hold_only | persistence_only | coverage | -0.286 | -0.339 | -0.187 | 7 | source_day | two-sided percentile 95% |
| 0.500 | aasvr_hold_only | persistence_only | undesirable_per_trial | -0.004 | -0.009 | 0.000 | 7 | source_day | two-sided percentile 95% |
| 0.800 | persistence_only | persistence_only | coverage | 0.000 | 0.000 | 0.000 | 7 | source_day | two-sided percentile 95% |
| 0.800 | persistence_only | persistence_only | undesirable_per_trial | 0.000 | 0.000 | 0.000 | 7 | source_day | two-sided percentile 95% |
| 0.800 | hampel | persistence_only | coverage | -0.065 | -0.104 | -0.032 | 7 | source_day | two-sided percentile 95% |
| 0.800 | hampel | persistence_only | undesirable_per_trial | 0.002 | -0.009 | 0.014 | 7 | source_day | two-sided percentile 95% |
| 0.800 | cusum | persistence_only | coverage | -0.063 | -0.099 | -0.028 | 7 | source_day | two-sided percentile 95% |
| 0.800 | cusum | persistence_only | undesirable_per_trial | -0.002 | -0.013 | 0.005 | 7 | source_day | two-sided percentile 95% |
| 0.950 | persistence_only | persistence_only | coverage | 0.000 | 0.000 | 0.000 | 7 | source_day | two-sided percentile 95% |
| 0.950 | persistence_only | persistence_only | undesirable_per_trial | 0.000 | 0.000 | 0.000 | 7 | source_day | two-sided percentile 95% |

## Legacy AASVR-R recovery audit

| scenario | authorizations | final_reliability | completed_responses | final_state | last_authorized_sample |
| --- | --- | --- | --- | --- | --- |
| one_failed_response | 1 | 0.500 | 1 | normal | 2 |
| no_pending_command | 0 | 1.000 | 0 | normal | -1 |
| missing_response_window | 2 | 0.500 | 1 | normal | 45 |
| legitimate_shift | 0 | 1.000 | 0 | fault_alert | -1 |
| fault_ends | 0 | 1.000 | 0 | normal | -1 |
| long_gap | 1 | 0.500 | 1 | normal | 2 |

The constant out-of-band scenario demonstrates authorization lockout after a failed response. The legitimate-shift case tests an actual input change without a fault label; fault exit separately tests acceptance recovery. Missing measurements pause the legacy response countdown rather than immediately count as failed response. These are deterministic software scenarios, not measured actuator responses. No unverified automatic recovery/reset was added.

## Computation on the available host

CPU: AMD Ryzen 7 9800X3D 8-Core Processor. Scope: AASVR measurement kernel only; excludes scoring, LOF fit, and pandas I/O. Platform: `Linux-7.0.0-31-generic-x86_64-with-glibc2.41`. Logical CPU count reported by the container: 16. Thread settings: `{'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1'}`. Full software versions are in the local audit JSON.

| streams | initialization_seconds_with_tracing | initialization_peak_python_allocated_bytes | batch_median_ms | batch_p95_ms | batch_p99_ms | sensor_updates_per_second | streaming_peak_python_allocated_bytes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.000 | 2536 | 0.046 | 0.050 | 0.061 | 21269.768 | 6068 |
| 8 | 0.000 | 16120 | 0.363 | 0.372 | 0.381 | 22307.302 | 5600 |
| 32 | 0.001 | 57088 | 1.425 | 1.446 | 1.463 | 22761.128 | 5600 |

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
