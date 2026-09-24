# What reconciliation changes

The earlier receiver prevented repeated uncertain execution by blocking indefinitely. The new implementation can restore permission using a matching, terminal record from the independent mock ledger. It never equates a timeout or absent record with failed execution. A permanent cancellation fence prevents a delayed old request from executing after permission is restored.

On the same impaired historical traces, durable polling coverage rose from **1.57% to 99.18%**, with **0.55% direction-disagreeing outputs** and **11.80% additional modeled protocol traffic**. Its 720 ambiguous-output episodes across the repeated sensor/phase replays were reconciled; none remained blocked at the end. The paired source-day bootstrap improvement was 97.61 percentage points (95% interval 95.61–99.01), conditional on these reused trajectories and the assumed lookup service.

With lookup replies unavailable for the first 32 seconds, coverage remained 99.18%, but modeled recovery from first lookup took 48 rather than 16 seconds and added traffic rose to 20.95%. These are simulation timings, not measured deployment recovery bounds. The long command cooldown makes these delays tolerable in this dataset; another controller or workload could behave differently.

Permanently unavailable, mismatched, and contradictory evidence preserved the block. Those cases retained 1.57% coverage and all 18 durable sensor/phase replays ended unresolved. This is an explicit dependence on independent execution evidence, not a universal solution to uncertain execution.

The clock-aware/full-recovery variants still incur substantial costs: available-evidence coverage was 48.37% for B=16 polling, 61.97% for B=16 deadline scheduling, and 96.26% for B=1 deadline scheduling. B remains a hypothetical interdevice clock bound. Reconciliation fixes the indefinite ambiguous-output block when evidence is available; it does not remove conservative timing and heartbeat constraints.

No duplicate, expired, or cooldown-violating outputs appeared across the 774 replays. All 270 original baseline rows reproduced exactly. Thirty actual local UDP cases passed, including six receiver SIGKILLs around recovery commit and three mock SIGKILLs after acceptance before execution. Exact-time tests separately verify cooldown, new-source requirements, persisted query budgets, and event-specific request/evidence binding. The baseline unresolved-state counter was added explicitly during verification; baseline actions and coverage were unchanged. Reported results use the final complete run.

## Scope of the contribution

This supports a reproducible software study of the tradeoff between uncertain execution, independent evidence, bounded recovery, and useful-action availability. The mechanism's assumptions and failure cases are now executable and auditable. It does not establish that hydroponic dosing was safer, that a real pump executed a command, or that another deployment would achieve the same coverage.

The mock effect and completed record are atomic in one SQLite transaction. Physical execution generally has a gap between electrical/mechanical effect and durable recording. A practical next experiment must define a real interface that can report event-specific completion and permanently fence a cancelled event, including behavior across power loss and independent clocks. If the available hardware cannot supply that evidence, uncertainty must remain explicit and recovery may require an operator or additional instrumentation.

In the generated comparison, `blocking` labels the unchanged comparison arm. The `current_b0_poll` receiver remains volatile and does not block on lost output ACKs; reconciliation bars are not applicable to it. The other four comparison receivers retain the original unresolved-execution block.
