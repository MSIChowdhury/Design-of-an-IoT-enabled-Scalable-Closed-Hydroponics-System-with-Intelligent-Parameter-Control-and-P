# Bounded reconciliation protocol

Freeze all source, configuration, and prior measured-transaction hashes before execution. Preserve the earlier replay and instrumented results. Use unchanged reference opportunities, source series, measured timing traces, candidates, phases, sender constraints, and output scoring. No detector/control tuning.

## Recovery contract

The receiver binds its journal to a stream and identifies an uncertain reserved command by ID plus a digest of ID, direction, creation, and source timestamps. Only the configured trusted local mock channel and verified shared clock domain may supply terminal evidence. This is not cryptographic authentication or a cross-device clock conversion.

A completed record must match stream/ID/digest/domain, contain a finite execution timestamp within the command lifetime/freshness window and not in the future, and contain no contradictory cancellation fence. Resolve the reservation atomically, retain the larger of the previous reserved cooldown and confirmed output time plus cooldown, and impose a new source-evidence barrier. Full-recovery candidates also require a new heartbeat. Never retransmit the old command.

A cancellation record must match identity and explicitly prove a permanent actuator-side fence with no output timestamp. The mock's single-writer SQLite transaction serializes execution with cancellation, retaining an immutable tombstone even when cancellation precedes the delayed request. Cancellation never overrides completed execution. Preserve the previous conservative cooldown; only a fresh justified command with a new ID can execute afterward.

Not found, pending, unavailable, mismatched, contradictory, invalid-time, or late evidence leaves permission blocked. Invalid receiver clocks cannot be repaired using execution evidence. Allow four queries, 16 s apart, within 64 s from the first lookup; persist attempts before sending. Exhaustion remains blocked for independent/operator intervention, not automatic reset. The mock maintains records indefinitely for this experiment; production retention, authenticated storage, reboot epochs, and physical effect/database atomicity remain outside scope.

## Actual local tests

Run a controller process against an independent UDP/SQLite mock process in Docker. Exercise lost output ACKs, not-found followed by delayed arrival/execution, cancellation before arrival and after acceptance, actual mock process failure after acceptance before output, dropped lookup replies, mismatched and contradictory replies, and actual receiver SIGKILL immediately before/after the reconciliation commit. Repeat each case three times. Verify independent effect counts, blocked/resolved state, no old-command adapter reinvocation, and persistent records after restart. Use 0.2 s local cooldown to keep component tests short; historical replay retains 600 s. Unit tests use exact synthetic times to verify cooldown and fresh-source eligibility.

The atomic completed ledger transition is the mock effect itself, not a physical pump movement. An actual actuator needs a defensible independent execution record; a database marker alone cannot guarantee physical completion.

## Paired historical benchmark

Run all five prior blocking/volatile candidates unchanged across three measured profiles, six sensors, three phases (270 baseline replays). For four durable/recovery candidates add reconciliation with available evidence on all three profiles (216 replays). On the impaired profile add four adverse lookup conditions: first 32 s unavailable, permanently unavailable, wrong event ID, and contradictory completion/fence (288 additional replays). Total: 774.

A simulated independent mock record is generated from observer-visible output timestamps. It does not read reference decisions or future outputs. Lookup replies arrive at the next 16 s intake tick; this conservative latency and outage conditions are declared simulation assumptions, not extrapolated from the fast local UDP measurements. Preserve the previously measured command impairment traces. Query traffic is counted separately, including failed requests, then added to command traffic. Evidence availability is therefore a new explicitly modeled input.

Require exact reproduction of the previous baseline summary counts before interpreting new results. Report coverage and undesirable outputs, duplicate/expiry/cooldown violations, resolved/unresolved episodes, recovery time, and added traffic. Bootstrap paired historical days with phases/sensors together; conditional intervals do not establish network/deployment generality. Preserve unfavorable results. Code/data hashes are checked after execution.
