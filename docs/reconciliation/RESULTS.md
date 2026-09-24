# Bounded reconciliation results

Implemented terminal-evidence recovery and permanent cancellation fences against an independent durable mock ledger. No detector, controller, sender, or clock-bound tuning was performed.

## Actual local execution checks

30/30 cases passed: ten scenarios × three repeats. Six actual receiver SIGKILLs exercised both sides of the atomic reconciliation commit; three actual mock SIGKILLs exercised accepted-but-not-yet-executed commands. Dropped output and lookup replies traveled through real UDP sockets. A not-found lookup did not restore authority before a delayed output arrived. Cancelled commands remained fenced when delayed requests subsequently arrived. Independent effect counts stayed at one for completed cases and zero for cancelled cases; no old command reinvoked the receiver adapter after recovery.

Local lookup RTT median/p95: 0.174/0.207 ms. These are component checks in Docker with a 0.2 s test cooldown, not deployment measurements. Historical replay retained 600 s cooldown. Recovery-duration measurements for these small cases include intentional waits and crash handling; the full records are in the snapshot.

## Paired historical results

774 replays completed. All 270 baseline rows reproduced the previous experiment exactly before the new comparisons were interpreted. Each aggregate row contains 10,344 scored opportunities: 3,448 unique historical opportunities reused at three cyclic phases. These are not independent physical trials.

| candidate | condition | coverage_pct | undesirable_pct | reconciled | unresolved | mean_recovery_seconds | added_traffic_pct |
|---|---|---|---|---|---|---|---|
| current_b0_poll | blocking | 99.18 | 0.55 | 0 | 0 | — | 0.00 |
| durable_b0_poll | available | 99.18 | 0.55 | 720 | 0 | 16.00 | 11.80 |
| durable_b0_poll | blocking | 1.57 | 0.00 | 0 | 18 | — | 0.00 |
| durable_b0_poll | contradictory | 1.57 | 0.00 | 0 | 18 | — | 1.17 |
| durable_b0_poll | delayed_32 | 99.18 | 0.55 | 720 | 0 | 48.00 | 20.95 |
| durable_b0_poll | unavailable | 1.57 | 0.00 | 0 | 18 | — | 0.45 |
| durable_b0_poll | wrong_id | 1.57 | 0.00 | 0 | 18 | — | 1.17 |
| recovery_b16_deadline | available | 61.97 | 0.73 | 273 | 0 | 16.00 | 0.45 |
| recovery_b16_deadline | blocking | 5.79 | 0.00 | 0 | 18 | — | 0.00 |
| recovery_b16_deadline | contradictory | 5.79 | 0.00 | 0 | 18 | — | 0.12 |
| recovery_b16_deadline | delayed_32 | 61.97 | 0.73 | 273 | 0 | 48.00 | 0.80 |
| recovery_b16_deadline | unavailable | 5.79 | 0.00 | 0 | 18 | — | 0.05 |
| recovery_b16_deadline | wrong_id | 5.79 | 0.00 | 0 | 18 | — | 0.12 |
| recovery_b16_poll | available | 48.37 | 0.95 | 354 | 0 | 16.00 | 0.59 |
| recovery_b16_poll | blocking | 0.95 | 0.00 | 0 | 18 | — | 0.00 |
| recovery_b16_poll | contradictory | 0.95 | 0.00 | 0 | 18 | — | 0.12 |
| recovery_b16_poll | delayed_32 | 48.37 | 0.95 | 354 | 0 | 48.00 | 1.04 |
| recovery_b16_poll | unavailable | 0.95 | 0.00 | 0 | 18 | — | 0.05 |
| recovery_b16_poll | wrong_id | 0.95 | 0.00 | 0 | 18 | — | 0.12 |
| recovery_b1_deadline | available | 96.26 | 0.61 | 690 | 0 | 16.00 | 1.14 |
| recovery_b1_deadline | blocking | 1.56 | 0.00 | 0 | 18 | — | 0.00 |
| recovery_b1_deadline | contradictory | 1.56 | 0.00 | 0 | 18 | — | 0.12 |
| recovery_b1_deadline | delayed_32 | 96.26 | 0.61 | 690 | 0 | 48.00 | 2.03 |
| recovery_b1_deadline | unavailable | 1.56 | 0.00 | 0 | 18 | — | 0.05 |
| recovery_b1_deadline | wrong_id | 1.56 | 0.00 | 0 | 18 | — | 0.12 |

Available-evidence replies were modeled at the next 16 s intake tick; delayed_32 withheld replies for the first 32 s. These are frozen simulation assumptions, separate from the measured local lookup RTT. Recovery time is measured from the first lookup until evidence commit, excluding the preceding remainder of a source tick and any remaining actuator cooldown. Unresolved counts are sensor/phase replays still blocked at the end (18 per candidate/condition). All completed recovery restores eligibility subject to cooldown and new source evidence; it does not immediately emit a dose.

Full-replay structural counts over this entire comparison: {"repeated_outputs": 0, "expired_outputs": 0, "cooldown_violations": 0}. No candidate is declared physically safe from these zero counts. Undesirable outputs are direction disagreements with the fixed historical surrogate at output time; low error from near-total suppression is not success. Paired source-day intervals remain conditional on reused traces and are included in the snapshot.

Added traffic includes modeled lookup requests and replies, including failed requests; it is expressed relative to the same candidate's original command/heartbeat bytes. Reply outage, wrong IDs, and contradictory evidence consume the four-query budget and leave authority blocked. An available execution record substantially improves availability, but does not remove clock-margin, heartbeat-barrier, or historical command-fidelity limitations.

## Evidence limits

The mock completion transition and effect record share one SQLite transaction. A physical actuator does not automatically offer that atomicity. The implementation trusts the configured local mock record and clock domain; authentication, malicious records, real actuator-state evidence, bounded storage retention, independent clocks, reboot epochs, power-loss durability, and plant safety are not established. Normal and cancellation-race tests do not prove all possible concurrent schedules.

The next physical-interface experiment must establish what independently confirms actual execution and what permanently prevents a delayed command after cancellation. Without those capabilities, the system must retain the unresolved block or require operator intervention. This result establishes a software recovery mechanism under an explicit evidence contract, not general exactly-once physical actuation.
