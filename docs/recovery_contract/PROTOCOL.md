# Frozen recovery-contract protocol

This is a separate version and evaluation, specified before the challenge run. No parameters are selected on the new results. Existing sensor periods remain reused retrospectively. Reproduce inside Docker:

```bash
docker compose run --rm -T project-shell make recovery-contract
```

## Assumptions and implementation obligations

- One active receiver and one monotonically numbered sender per journal. No concurrent replicas/split brain, ID reset, malicious packets, journal deletion, corruption, or failed durable storage.
- Sender-relative receiver clock error is known to remain within ±16 seconds. This is an input assumption, not something traffic alone establishes. Invalid-clock indications and backward receiver time latch a persistent block.
- The output adapter must emit within one second of the authorization clock reading or definitively never emit later. This includes reservation/storage latency before calling the adapter. Python callbacks and observed timing percentiles alone do not enforce this bound; a production adapter needs an enforceable deadline contract.
- True physical actuator execution is unavailable. Outputs are software issuance events; physical exactly-once execution is not claimed.

The new `RecoveryReceiver` uses a single-row SQLite journal with FULL synchronous commits. It retains command identity/revision, pending/terminal state, conservative cooldown expiry, recovery barrier, and uncertainty. The full-history simulation uses the same journal transactions in memory, preserving the database connection through receiver reconstruction. Separate real child-process SIGKILL tests reopen a disk journal. Process-kill durability is not a hardware power-loss guarantee.

## State and recovery contract

| Situation | Behavior |
| --- | --- |
| New accepted command | Persist ID/revision and pending command |
| Before software output | Commit reserved/blocked state and conservative next-allowed time |
| Output adapter returns | Commit emitted status; unblock future eligibility |
| Crash after acceptance but before reservation | Abandon pending intent on restart; do not replay it |
| Crash after reservation or after output before completion commit | Preserve uncertain identity/payload and block all future outputs |
| Retry after completion | Suppress using durable ID/revision |
| Restart or heartbeat timeout | Require fresh evidence and a command newer than the recovery barrier |
| Unknown execution outcome | No automatic timeout/reset; independent reconciliation is required and not implemented |

For receiver time `r`, uncertainty `B=16`, dispatch bound `D=1`, authorization requires:

- `r-B >= created` (not early anywhere in the clock interval).
- `r+B+D <= min(created+64, source+120)` (expiry/freshness valid through dispatch).
- `r-B >= next_allowed`.

Before output, persist `next_allowed = r+B+D+600`. This can delay or suppress commands even under ideal communication. The experiment measures that availability loss rather than relaxing the checks.

Heartbeat messages are sent every 32 seconds only when source evidence is finite and fresh. A 96-second silence while ready triggers recovery. On restart or detected silence, persist a barrier at `r+B`; after silence, first returning contact advances the barrier to that contact's `r+B`. The returning packet cannot itself establish post-contact freshness. Readiness requires a source timestamp strictly after the barrier. Commands also need creation and source timestamps after the barrier. A heartbeat does not resurrect an old command, refresh its original expiry, or clear uncertain execution. The sender's fixed reference controller remains responsible for newly eligible commands, with unchanged persistence/cooldown.

## Fixed comparison and challenge

Compare recovery V2, the previous cancellation/no-ACK candidate, and same-receiver plain repetition. All use the original two transmissions 32 seconds apart, 64-second command expiry, 120-second source freshness, and reference controller. V2's heartbeats are a necessary additional cost and are counted explicitly. Neither baseline is silently given V2's recovery guarantees.

Use all six primary channels and the existing full final chronological source block. Matching remains one-to-one within the reference episode and 64-second deadline, with existing warm-up/tail rules. Four new seeds and thirteen specified scenarios include new outage phases, correlated losses, clock offsets, restarts and combined faults. Twelve scenarios satisfy the ±16-second clock assumption. One -48-second offset deliberately violates it and is reported separately, never discarded. Restart period is 2,704 seconds with phase 592 seconds (first restart at 3,296 seconds).

Report coverage, undesirable commands per opportunity, bytes including all lost/heartbeat traffic, and structural duplicate/expiry/cooldown/recovery-barrier violations. Structural observers do not change method behavior. Structural counts include warm-up/tail; opportunity scoring does not. The recovery-barrier metric is inapplicable to the old protocols; their zero field is a storage convention, not a correctness claim.

The stopping criterion is zero observed structural violations in all in-contract replay cases and all specified crash checks, conditional on the assumptions. Availability is reported independently, including failure of the old 95% coverage/1% undesirable-command thresholds. Crossed day/seed bootstrap intervals are marginal and keep all sensors and paired policies together; no simultaneous safety guarantee or zero failure probability is inferred.

### Correctness revision audit

After the first complete run, review identified a missing first-contact freshness barrier: a heartbeat generated after timeout but delayed until reconnection could restore readiness. Added the barrier above and a directed regression test, then reran the entire unchanged grid and crash probe. No parameters or scenario membership were tuned. First-run outputs, manifest, and receiver source are preserved locally under `results/metrics/recovery_contract/initial_barrier_audit/`. The final run is a correctness reanalysis on the same schedules, not newly independent validation.

## Actual crash and storage experiment

Five boundaries are tested five times each: before receipt, after acceptance, after reservation, after output, and after completion commit. A child process receives SIGKILL at the boundary; a new process context reopens its journal, tries the same command, then offers a much later valid command. Output is recorded independently in an fsynced mock-actuator append-only file. The two ambiguous boundaries must remain blocked even for the new command. Other cases can resume only with fresh evidence and a new ID.

Measure 100 disk-backed reserve/output/commit operations after ten warm-ups. Report median/p95/p99/max latency and environment. The measured mock output is not an actuator feedback channel. No storage/clock bound is inferred merely because the observed operations were fast. Existing two-container UDP results belong to the preceding version; V2 is not represented as having repeated that network execution study.
