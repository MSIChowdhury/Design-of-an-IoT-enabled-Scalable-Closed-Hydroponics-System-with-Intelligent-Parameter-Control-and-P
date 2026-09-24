# Timing feasibility and component-isolation protocol

This sensitivity study is specified before execution. It does not select or tune a new deployment protocol. It keeps the existing source/controller, 64-second command lifetime, 120-second source freshness, 600-second cooldown, two transmissions 32 seconds apart, and independent opportunity scoring. Source periods are retrospectively reused.

```bash
docker compose run --rm -T project-shell make timing-feasibility
```

## Components and assumptions

The fixed stages are:

1. `current`: volatile receiver, no heartbeat recovery or uncertainty margin.
2. `durable`: the SQLite reservation/uncertain-output mechanism, persisted identity and cooldown, no clock/dispatch margin and no heartbeat recovery. Pending unreserved intent is abandoned on restart. Uncertain execution remains blocked.
3. `clock`: durable stage plus the one-second dispatch margin and clock bound B. The B=0 row isolates the dispatch margin from a nonzero clock margin.
4. `recovery`: clock stage plus the existing fresh-evidence heartbeats, first-contact barrier, and recovery gates.

These stages have different contracts; removing a guard is an ablation, not a claim of equal safety. No physical actuator execution is observed. SQLite is in-memory for the replay, with the same reservation code as the existing disk-backed crash tests. Those previous process tests are not represented as newly executed network/physical experiments.

Evaluate assumed relative clock bounds B ∈ {0,1,4,8,16} seconds for the clock and recovery stages. Actual replay offset is zero throughout, so every B contains it. This isolates margin cost; it does not measure synchronization accuracy or validate actual deployment bounds. Sensor sampling cadence does not determine clock uncertainty. A practical guarantee requires independent evidence of a maintained clock bound and an output-adapter deadline.

## Isolate output scheduling

Both policies process the same sensor updates and network packets on the existing 16-second clock. `poll` also checks output on those ticks. `deadline` additionally sets an output timer at the earliest admissible time of its current pending command. It does not see packets or measurements early. At ties, source/packet processing and cancellation precede output.

For arrival `a`, command creation `c`, supporting measurement time `s`, persisted cooldown endpoint `q`, clock bound B and dispatch margin D, the interval is:

`E=max(a,c+B,q+B)`, `L=min(c+64,s+120)-B-D`.

- E > L: no timing-feasible output under this receiver's existing output history.
- E ≤ L but `16*ceil(E/16)>L`: a feasible timing interval contains no polling tick.
- Otherwise polling has a timing opportunity, though later cancellation/recovery can remove eligibility.

Intervals are recorded on first command receipt, before output. They are conditional on realized method history and are not global scheduling-optimality bounds. Earlier scheduling changes later cooldown history. The scheduler itself uses only information already received; future traces are used only for retrospective scoring and explanation.

## Fixed challenge and metrics

Use the full final chronological source block, six primary sensors, three new paired network seeds, five scenarios, and 24 component/bound/scheduler combinations: 2,160 replays. Networks are ideal, independent loss with delay, delay tails, correlated loss plus restart, and an uncertain-output diagnostic. The last scenario injects a crash after each method's first output at or after logical time 20,000, before durable completion recording. Exact output/crash instants can differ between methods; this is not a same-wall-time causal comparison. Durable stages must remain blocked when execution is unresolved.

Continuous-time action scoring preserves the original rule: one-to-one same-direction, same-reference-episode matching within 64 seconds, with unchanged warm-up/tail exclusions. Reference directions between source ticks are causal as-of values. Extra action-timer wakeups do not create extra source information. Undesirable actions are counted at their actual execution times.

Report absolute and paired scheduler intervals from 1,000 crossed source-day/network-seed bootstrap draws, preserving all sensors and paired methods. Three seeds limit tail inference; intervals are marginal, not simultaneous guarantees. Clock assumptions and missing external instrumentation stay explicit.

## Per-command explanation

Every scored reference command is saved in a compressed ledger, including first arrival, created/source times, receiver cooldown, E/L, timing feasibility, polling opportunity, readiness/barrier flags, terminal status, output time, and independent match status. Metadata identify the exact sensor, seed, scenario, component stage, and clock bound.

For unmatched commands, primary reason precedence is: unresolved execution; never received; recovery barrier; no fresh heartbeat/readiness; emitted outside the reference episode/deadline; cancellation or restart/disconnection abandonment; feasible interval missed by the polling grid; then empty-interval reasons (expired before arrival, clock/dispatch margin at arrival, cooldown, intrinsic clock window). These labels are terminal explanations, not an additive causal attribution. Overlapping flags and endpoints are retained. An unexplained terminal category fails report generation instead of silently disappearing.

The compressed ledgers must exactly reconcile with all reported opportunity denominators. Missing heartbeat includes absence of qualifying fresh evidence, not only a lost packet. A timing interval alone cannot prove that future cancellation or recovery would permit execution.

## Figures and frontier

Report component costs on the ideal link, full-recovery clock-bound/scheduler curves across all scenarios, command-reason counts, and representative timelines. Select earliest scored examples for predefined method/scenario/reason combinations, using deterministic sensor/seed ties; missing examples are not replaced with favorable cases.

The frontier reports worst coverage/error across the four routine profiles plus bytes and structural violations. The unresolved-output scenario remains explicit in a separate table because blocking there is an intended part of the contract. Pareto screening is restricted to the same stage and clock bound: it never equates a weaker guarantee with a stronger one. No operating point is selected for deployment from these results.
