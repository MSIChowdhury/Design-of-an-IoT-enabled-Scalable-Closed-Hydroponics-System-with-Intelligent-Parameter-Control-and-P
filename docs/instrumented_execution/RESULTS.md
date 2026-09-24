# Local instrumented execution: measured results

Scope: three Docker containers on one host, UDP command transport, SQLite FULL journals, and an independent durable mock-output ledger. No physical actuator was connected. Unmodified prepared historical values selected controller inputs; their historical timestamps remain separate from new local execution timestamps.

## Actual measurements

- 300 measured transactions; 30 warmup transactions excluded from timing summaries.
- 5 deliberately dropped command packets; 6 deliberately suppressed output ACKs among scheduled measured transactions. These are injected conditions, not measured natural loss rates.
- 90 clock exchanges; verified same kernel boot and equal time-namespace offsets for all endpoints. Offset intervals containing zero: 90/90.
- 15/15 actual SIGKILL/restart checks passed across five crash boundaries.
- 6/6 uncertain-output followups (including warmup) remained blocked, with no second mock output. Independent lookup is observer evidence and does not automatically restore authority.
- Receiver timer lateness above the prespecified 5 ms budget: 0/295. Authorization-to-mock-record delay above 1 s: 0/295. Observed maxima do not establish hard bounds.

| profile | metric | n | p50_ms | p95_ms | p99_ms | max_ms |
|---|---|---|---|---|---|---|
| cpu_contention | journal_total_s | 100 | 20.420 | 22.440 | 22.462 | 22.491 |
| cpu_contention | timer_lateness_s | 100 | 0.056 | 0.058 | 0.059 | 0.061 |
| cpu_contention | output_delay_s | 100 | 6.877 | 8.801 | 9.042 | 10.081 |
| idle | journal_total_s | 100 | 14.066 | 17.343 | 18.807 | 20.149 |
| idle | timer_lateness_s | 100 | 0.055 | 0.345 | 1.579 | 3.156 |
| idle | output_delay_s | 100 | 5.704 | 7.524 | 8.286 | 9.153 |
| injected_delay_loss | journal_total_s | 95 | 14.042 | 16.844 | 17.918 | 18.360 |
| injected_delay_loss | timer_lateness_s | 95 | 0.057 | 0.249 | 0.668 | 1.085 |
| injected_delay_loss | output_delay_s | 95 | 5.739 | 6.805 | 7.470 | 7.521 |

All timing values above are milliseconds. Output timing ends at the mock ledger insertion timestamp, before its commit; adapter RTT includes the durable commit and acknowledgment. Journal timing measures save transactions, while acceptance also includes construction/opening overhead. Each transaction uses a distinct stream/journal to isolate crash boundaries; this is not sustained controller-throughput evidence. CPU contention is one busy process pinned to the receiver CPU, not a worst-case load guarantee.

## Fixed-candidate trace extrapolation

270 replays: five unchanged receiver/scheduling candidates × six sensors × three local profiles × three cyclic phases. Each profile repeats its 100 measured rows over the historical evaluation block. Phases are dependent sensitivity settings, not independent deployments. Reference opportunities and matching remain independent of receiver decisions.

| profile | candidate | coverage_pct | undesirable_pct | cooldown_violations | expired_outputs | missing_output_acks |
|---|---|---|---|---|---|---|
| cpu_contention | current_b0_poll | 99.33 | 0.58 | 0 | 0 | 0 |
| cpu_contention | durable_b0_poll | 99.33 | 0.58 | 0 | 0 | 0 |
| cpu_contention | recovery_b16_deadline | 64.97 | 0.67 | 0 | 0 | 0 |
| cpu_contention | recovery_b16_poll | 48.90 | 1.00 | 0 | 0 | 0 |
| cpu_contention | recovery_b1_deadline | 96.61 | 0.60 | 0 | 0 | 0 |
| idle | current_b0_poll | 99.33 | 0.58 | 0 | 0 | 0 |
| idle | durable_b0_poll | 99.33 | 0.58 | 0 | 0 | 0 |
| idle | recovery_b16_deadline | 64.97 | 0.67 | 0 | 0 | 0 |
| idle | recovery_b16_poll | 48.90 | 1.00 | 0 | 0 | 0 |
| idle | recovery_b1_deadline | 96.61 | 0.60 | 0 | 0 | 0 |
| injected_delay_loss | current_b0_poll | 99.18 | 0.55 | 0 | 0 | 720 |
| injected_delay_loss | durable_b0_poll | 1.57 | 0.00 | 0 | 0 | 18 |
| injected_delay_loss | recovery_b16_deadline | 5.79 | 0.00 | 0 | 0 | 18 |
| injected_delay_loss | recovery_b16_poll | 0.95 | 0.00 | 0 | 0 | 18 |
| injected_delay_loss | recovery_b1_deadline | 1.56 | 0.00 | 0 | 0 | 18 |

Packet intake retains the previous 16 s polling model. Even a positive submillisecond delay can defer intake one tick; this is a modeling assumption, not a measured edge-device intake period. Receiver timer lateness and output delay are carried together from the first command receipt's trace row. The volatile baseline excludes measured journal-write costs it does not perform. Sender timer jitter is reported but not applied to historical creation times; the measured network term starts at actual sending. Observer-confirmed mock effects are scored even when acknowledgment is missing. Durable candidates then block indefinitely because reconciliation is unimplemented. No loss is imputed as zero delay, no measured maximum is substituted for a contract bound, and clock bounds B=1/B=16 remain hypothetical.

Cooldown/expiry columns count modeled output-timestamp violations over the full replay, including warmup/tail; coverage and undesirable-output percentages exclude those edges. Undesirable means output direction disagrees with the fixed historical reference at output time. The reference is a surrogate, not physical ground truth. Byte counts in local CSV outputs are modeled protocol traffic, not instrumentation-wire measurements.

Paired source-day bootstrap intervals are saved in `results/metrics/instrumented_execution/paired_day_intervals.csv`; phases and sensors remain together within resampled days. These intervals describe historical block variation conditional on these repeated short traces; they do not quantify deployment/network uncertainty.

## Evidence boundary and next decision

The independent-device 1 ms clock budget and maximum 32 s interruption assumption remain **unverified**. Same-host clock exchanges and host NTP status cannot establish either. Process-kill tests do not establish power-loss durability, reboot clock continuity, physical actuation, or closed-loop plant safety.

These results support a reproducible software execution/recovery experiment. Missing output acknowledgments expose the availability cost of conservative unresolved-execution blocking. Any deployable recovery proposal needs explicit independent reconciliation evidence; silently retrying or resetting would change the contract. Before making an edge-deployment claim, repeat the frozen protocol on separately clocked devices and a timestamped physical/mock interface. No algorithm was retuned using these results.
