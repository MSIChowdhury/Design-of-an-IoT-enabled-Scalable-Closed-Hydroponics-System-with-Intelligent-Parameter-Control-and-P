# Timing feasibility and component costs

Completed **2160 replays** with **1,241,280 independently scored reference opportunities** recorded in compressed per-command ledgers. Repetition across methods/seeds does not create new physical evidence. The clock bounds are sensitivity assumptions; synchronization was not measured. No setting was selected for deployment.

## Ideal-link component isolation

`durable` adds reservations/persisted identity and cooldown, but no clock margin or heartbeat recovery. `clock_b0` additionally reserves the one-second dispatch margin; larger clock variants add the stated clock uncertainty. `recovery` adds fresh-evidence heartbeats and recovery barriers. A durable receiver still blocks unresolved execution even when recovery gates are disabled. Each stage is a weaker/different contract, not an interchangeable competitor.

| variant | coverage | coverage_low | coverage_high | error | traffic_multiple |
| --- | --- | --- | --- | --- | --- |
| clock_b0_poll | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| clock_b16_poll | 0.5142 | 0.5064 | 0.5262 | 0.0000 | 1.0000 |
| current_b0_poll | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| durable_b0_poll | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| recovery_b16_deadline | 0.6673 | 0.6615 | 0.6741 | 0.0000 | 9.8913 |
| recovery_b16_poll | 0.4994 | 0.4951 | 0.5047 | 0.0000 | 9.8913 |

## Every missed command: recorded terminal explanation

The table aggregates routine scenarios for recovery B=16 with polling. Primary explanations use documented precedence, not a causal decomposition. All ledgers retain overlapping flags and interval endpoints, so a cancellation cannot be interpreted as proving the timing would otherwise have succeeded. The unresolved-output scenario is reported separately below, not dropped from outputs.

| reason | commands |
| --- | --- |
| abandoned_on_disconnect | 14 |
| abandoned_on_restart | 35 |
| cancelled | 493 |
| clock_or_dispatch_margin_on_arrival | 5807 |
| cooldown_no_interval | 5550 |
| expired_before_arrival | 1950 |
| missing_fresh_heartbeat | 185 |
| no_delivery | 879 |
| output_after_episode_or_deadline | 114 |
| polling_missed_feasible_interval | 7417 |
| recovery_barrier | 2068 |
| restart_abandoned | 1 |

| variant | scenario | missed | never_arrived | timing_feasible | timing_empty | feasible_without_poll_tick |
| --- | --- | --- | --- | --- | --- | --- |
| recovery_b16_poll | delay_tail | 8144 | 0 | 358 | 7786 | 177 |
| recovery_b16_poll | ideal | 5178 | 0 | 5121 | 57 | 4809 |
| recovery_b16_poll | iid_10 | 5581 | 156 | 1730 | 3695 | 1239 |
| recovery_b16_poll | restart_correlated | 5610 | 723 | 1881 | 3006 | 1355 |
| recovery_b16_poll | uncertain_output | 10134 | 0 | 9921 | 213 | 58 |

`timing_feasible` means a nonempty interval at first receipt, conditional on that method's already-realized output history. Subsequent cancellation, disconnection, restart, or uncertainty may invalidate it. It is not a global scheduling optimum. `feasible_without_poll_tick` identifies timing windows containing no point of the 16-second output grid. Never-arrived commands have no arrival-conditioned interval and are counted separately.

## Clock-bound and scheduling sensitivity

Coverage fractions for the full recovery stage:

| bound | scheduler | delay_tail | ideal | iid_10 | restart_correlated | uncertain_output |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | deadline | 0.5142 | 0.9745 | 0.8676 | 0.8397 | 0.0389 |
| 0 | poll | 0.5139 | 0.9745 | 0.8664 | 0.8387 | 0.0389 |
| 1 | deadline | 0.5142 | 0.9736 | 0.8669 | 0.8394 | 0.0389 |
| 1 | poll | 0.5135 | 0.9669 | 0.8657 | 0.8385 | 0.0389 |
| 4 | deadline | 0.5122 | 0.9678 | 0.8587 | 0.8361 | 0.0377 |
| 4 | poll | 0.4044 | 0.7445 | 0.6386 | 0.6395 | 0.0284 |
| 8 | deadline | 0.4099 | 0.8521 | 0.7092 | 0.7025 | 0.0307 |
| 8 | poll | 0.4040 | 0.7445 | 0.6371 | 0.6353 | 0.0284 |
| 16 | deadline | 0.2272 | 0.6673 | 0.5210 | 0.5208 | 0.0230 |
| 16 | poll | 0.2127 | 0.4994 | 0.4605 | 0.4577 | 0.0203 |

For packet intake at time `a`, prior reserved cooldown endpoint `q`, command creation `c`, source timestamp `s`, assumed clock bound `B`, and dispatch margin `D`, the admissible receiver-clock interval is:

`[max(a, c+B, q+B), min(c+64, s+120)-B-D]`.

If its lower endpoint exceeds its upper endpoint, changing the output polling schedule cannot rescue that command under the current history. If nonempty, the deadline scheduler wakes at its earliest admissible time. At source-tick ties, newly received cancellations are processed first. Both schedulers retain the same 16-second packet-intake and source schedule: this isolates output timing, rather than silently changing network delivery or source sampling. The scheduler uses no future measurements or arrivals.

A useful directed example has `c=s=a=640`, `q=665`, `B=16`, `D=1`. The valid interval is **[681,687] seconds**; ticks 672 and 688 miss it, while an output timer can execute at 681. That earlier output changes later cooldown history, so individual rescue does not imply every later reference event becomes feasible. This result is a software scheduling study, not a hard real-time measurement of timer precision.

## Empirical correctness–coverage–traffic frontier

Worst coverage/error across the four routine scenarios; uncertainty after output is separate because safe unresolved execution intentionally blocks. Dominance is assessed only within the same component stage and clock-bound assumption, using observed point values. It is not a statistical or global optimality claim. Full per-scenario intervals and paired scheduler differences are in the CSV outputs.

| variant | worst_coverage | worst_error | bytes | structural_violations | dominated_within_contract |
| --- | --- | --- | --- | --- | --- |
| clock_b0_deadline | 0.5393 | 0.0058 | 9422928 | 0 | False |
| clock_b0_poll | 0.5391 | 0.0060 | 9422928 | 0 | True |
| clock_b16_deadline | 0.2418 | 0.0046 | 9422928 | 0 | False |
| clock_b16_poll | 0.2265 | 0.0043 | 9422928 | 0 | False |
| clock_b1_deadline | 0.5393 | 0.0058 | 9422928 | 0 | False |
| clock_b1_poll | 0.5387 | 0.0060 | 9422928 | 0 | True |
| clock_b4_deadline | 0.5382 | 0.0060 | 9422928 | 0 | False |
| clock_b4_poll | 0.4228 | 0.0047 | 9422928 | 0 | False |
| clock_b8_deadline | 0.4295 | 0.0055 | 9422928 | 0 | False |
| clock_b8_poll | 0.4224 | 0.0047 | 9422928 | 0 | False |
| current_b0_deadline | 0.7782 | 0.0061 | 9422928 | 742 | False |
| current_b0_poll | 0.7766 | 0.0064 | 9422928 | 920 | True |
| durable_b0_deadline | 0.7782 | 0.0061 | 9422928 | 0 | False |
| durable_b0_poll | 0.7766 | 0.0064 | 9422928 | 0 | True |
| recovery_b0_deadline | 0.5142 | 0.0057 | 93205152 | 0 | False |
| recovery_b0_poll | 0.5139 | 0.0060 | 93205152 | 0 | True |
| recovery_b16_deadline | 0.2272 | 0.0044 | 93205152 | 0 | False |
| recovery_b16_poll | 0.2127 | 0.0042 | 93205152 | 0 | False |
| recovery_b1_deadline | 0.5142 | 0.0057 | 93205152 | 0 | False |
| recovery_b1_poll | 0.5135 | 0.0060 | 93205152 | 0 | True |
| recovery_b4_deadline | 0.5122 | 0.0060 | 93205152 | 0 | False |
| recovery_b4_poll | 0.4044 | 0.0046 | 93205152 | 0 | False |
| recovery_b8_deadline | 0.4099 | 0.0053 | 93205152 | 0 | False |
| recovery_b8_poll | 0.4040 | 0.0046 | 93205152 | 0 | False |

## Unresolved execution availability

The first output at or after logical time 20,000 is followed by a simulated crash before completion recording. It is triggered at each method's own first eligible output after that fixed threshold; exact failure instants therefore differ. Durable stages retain an uncertain reservation and stop further outputs, while the volatile current receiver loses memory. This is a diagnostic intervention, not an identical-wall-time causal treatment or another real SIGKILL experiment.

| variant | coverage | error | repeated_outputs | expired_outputs | cooldown_violations |
| --- | --- | --- | --- | --- | --- |
| clock_b0_poll | 0.0389 | 0.0000 | 0 | 0 | 0 |
| clock_b16_poll | 0.0203 | 0.0000 | 0 | 0 | 0 |
| current_b0_poll | 0.9870 | 0.0062 | 18 | 0 | 18 |
| durable_b0_poll | 0.0389 | 0.0000 | 0 | 0 | 0 |
| recovery_b16_deadline | 0.0230 | 0.0000 | 0 | 0 | 0 |
| recovery_b16_poll | 0.0203 | 0.0000 | 0 | 0 | 0 |

## Examples, assumptions, and reproducibility

4 representative timelines were selected by fixed criteria: earliest scored command for specified method/scenario/reason combinations, with deterministic sensor/seed tie breaks. The plotting script also saves their complete source traces and interval metadata. These include feasible windows missed by polling, empty cooldown windows, recovery rejection, and unresolved execution when present.

Run `docker compose run --rm -T project-shell make timing-feasibility`. See [PROTOCOL.md](PROTOCOL.md). CSVs, compressed command ledgers, source fingerprints, and selected examples are under `results/metrics/timing_feasibility/`. Figures are under `results/figures/timing_feasibility/`.

All main replays have zero actual clock offset and vary assumed B in {0,1,4,8,16} seconds. This investigates cost as a function of a hypothetical verified bound; neither the sensor cadence nor these results establish that bound in a deployment. Prior clock-offset/crash findings remain applicable. The same SQLite reservation implementation runs in memory during replay; previous disk/SIGKILL evidence is not relabeled as a new physical or network experiment. All historical sensor periods have been reused. Three paired new network seeds and crossed day/seed bootstrap intervals (1,000 draws) are limited retrospective uncertainty estimates, not simultaneous guarantees.
