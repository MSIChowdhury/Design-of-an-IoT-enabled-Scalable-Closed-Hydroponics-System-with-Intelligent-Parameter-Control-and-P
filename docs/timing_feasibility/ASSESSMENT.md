# Timing-study assessment

The study identifies a substantial scheduling defect and separates it from persistence cost, but it does not establish a deployable operating point meeting all the original targets.

## What was completed

There are 2,160 replays and 1,241,280 scored command records across the fixed component/clock-bound/scheduler grid. All records reconcile with the aggregate opportunity counts, and clustered matched/error counts reconcile with raw results. No command was left in an unexplained terminal category. Source/configuration fingerprints were verified unchanged after execution. All 114 tests passed.

The command count repeats the same physical source periods across methods, scenarios, and seeds; it is not a count of independent observations. Output timing is simulated. No hardware clock accuracy or timer precision was measured.

## Persistence is not the main modeled availability cost

On the ideal link, the current receiver and the durable-only ablation both achieve **100% coverage**, with identical offered network bytes. Under 10% loss plus delay, both achieve **96.97%**. Under correlated loss plus periodic restart, coverage is **91.83% current versus 91.71% durable-only**; the durable-only variant eliminates the observed duplicate and cooldown violations in that zero-actual-clock-offset replay.

This supports retaining persistence as a useful primitive. It does not make the durable-only ablation a substitute for clock/recovery guarantees: those protections are intentionally disabled. Nor does it mean disk writes are free: journal operations use in-memory SQLite in this replay, and the preceding study's disk latency evidence remains separate.

Adding a one-second dispatch margin already reduces coverage on impaired links even at B=0. For example, the clock-stage B=0 polling ablation gives **90.90%** with independent loss plus delay versus **96.97%** for durable-only. A packet processed exactly at its nominal expiry can no longer be authorized when one further second must remain for dispatch. Polling quantization, cooldown, and dispatch margins interact; clock error alone is not the entire cost.

## Deadline-aware scheduling helps under identical assumptions

For the full recovery contract with assumed B=16 seconds:

| Scenario | Polling coverage | Deadline-timer coverage |
| --- | ---: | ---: |
| Ideal | 49.94% | 66.73% |
| 10% loss plus delay | 46.05% | 52.10% |
| Long-delay profile | 21.27% | 22.72% |
| Correlated loss plus restart | 45.77% | 52.08% |

The ideal-link gain is **16.79 percentage points**, with a paired marginal 95% interval of **16.22–17.30 points**. Paired scheduler byte counts are identical in every scenario/component/bound cell. The full recovery contract still uses 9.89× the current protocol's offered bytes because its heartbeat traffic remains unchanged.

No duplicate, expired, or cooldown-violating outputs were observed for durable/clock/recovery stages in this zero-actual-offset replay, including the deadline scheduler. This is finite conditional evidence, not a claim that unknown clock errors or unbounded output adapters are safe.

For ideal-link recovery B=16 polling, 4,764 missed command records receive the primary explanation “polling missed a feasible interval.” A broader overlapping interval flag identifies 4,809 misses with a feasible arrival-conditioned window containing no polling tick; some also have a cancellation or other higher-priority terminal explanation. The distinction prevents double counting or treating a timing window as sufficient authorization.

The [681,687]-second example demonstrates a real scheduling opportunity. Executing at 681 changes the next cooldown, however, so it can make a later command infeasible. The first-arrival interval analysis is conditional on each method's output history, not a proof of a globally optimal schedule or a count of commands that can all be rescued simultaneously.

## Smaller clock bounds are assumptions, not measured improvements

With full recovery and deadline scheduling, ideal-link coverage is **97.45% at assumed B=0**, **97.36% at B=1**, **96.78% at B=4**, **85.21% at B=8**, and **66.73% at B=16**. These curves describe hypothetical maintained bounds; no setting was selected as deployment-ready.

Even with the strongest hypothetical clock information (B=0), full recovery reaches only **86.76%** on independent loss plus delay and **51.42%** on the long-delay profile. Better synchronization alone therefore does not solve the communication, dispatch, and recovery costs under the current requirements. No tested variant satisfies 95% coverage, at most 1% undesirable outputs, and zero observed structural violations across all four routine profiles.

The uncertain-output scenario remains separate and visible: durable stages block after an unresolved reservation, leaving only the early part of the replay served. Output scheduling cannot resolve missing execution evidence, and a timer reset would weaken the contract rather than repair that problem.

## Implication

The defensible result is now more specific: durable state can retain useful command coverage, while coarse polling and conservative timing/recovery rules impose distinct, measurable costs. Deadline scheduling recovers some availability without adding network traffic or relaxing the tested timing checks, but it does not restore the original performance target.

A practical operating claim needs measured clock and adapter bounds, requirements compatible with actual communication delays, and independent resolution of uncertain execution. This study supplies the diagnostic evidence and conditional tradeoff curves; it does not establish those external facts or journal-level novelty.

See [full results](RESULTS.md), [protocol](PROTOCOL.md), and generated figures under `results/figures/timing_feasibility/`. All compressed ledgers remain locally reproducible under `results/metrics/timing_feasibility/ledgers/`.
