# Recovery-contract assessment

The implementation meets the finite structural stopping criterion within its declared assumptions, but it fails the original availability target. It should not replace the current version as a claimed overall performance improvement.

## What was executed

The final run contains 936 replays: thirteen scenarios × four network seeds × six sensors × three policies. Twelve scenarios satisfy the declared ±16-second relative clock bound; one -48-second scenario intentionally violates it. The same historical source block is reused. Five crash boundaries were each exercised five times using real SIGKILL and disk-backed SQLite, followed by reopening, duplicate retry, and a later new command. All 25 cases passed. All 107 repository tests passed.

An initial full run was preserved before a correctness revision: the first returning contact after a heartbeat timeout now advances the recovery barrier. A directed test catches the previously possible acceptance of pre-contact evidence. Final results rerun the unchanged grid after that correction; this is explicitly retrospective correctness reanalysis rather than an untouched validation claim.

## Structural outcome

Across the twelve in-contract scenarios:

| Output violation | Current cancellation protocol | Recovery V2 |
| --- | ---: | ---: |
| Repeated command output | 334 | 0 |
| Expired/freshness-invalid output | 88 | 0 |
| Cooldown violation | 2,208 | 0 |

V2 also emitted no commands violating its recovery barrier. These are aggregated replay counts, not independent physical incidents. The baseline has no recovery barrier, so its corresponding zero CSV field is not evidence of passing that requirement.

After crashes at reservation/output boundaries, all ten affected trials remained explicitly uncertain and blocked the later command. Five had no mock output, five had one. The protocol did not guess which outcome occurred and did not retry either uncertain operation. No independent reconciliation mechanism was implemented.

In the deliberately out-of-contract -48-second clock case, V2 produced **1,091 expired outputs**. This demonstrates why the clock-error bound must be established and monitored outside the protocol; a configured number is not evidence that the real clock satisfies it.

## Availability and traffic cost

| Scenario | Current coverage | V2 coverage |
| --- | ---: | ---: |
| Ideal | 100.00% | 49.94% |
| 10% independent loss | 97.51% | 46.32% |
| 20% independent loss | 94.69% | 42.34% |
| Long delay | 78.19% | 22.25% |
| Restart schedule | 98.67% | 50.33% |

V2 fails the original 95% coverage threshold in all twelve in-contract scenarios. Its offered traffic is **9.89×** the current no-ACK cancellation protocol because it adds fresh-evidence heartbeats. These heartbeats are not free, and loss of availability must not be hidden behind fewer undesirable commands.

The ideal-link loss is understandable from the specified timing rules. For a persistent request, a first command created at time 32 can emit at time 48 after the uncertainty check. Its conservative next-allowed value is `48 + 16 + 1 + 600 = 665`. The next reference command appears at tick 640 and expires at time 704. At tick 672, the lower clock bound is 656, too early for the cooldown. At tick 688, the upper clock bound plus dispatch margin is 705, too late for expiry. That opportunity is lost. The 16-second execution grid, 64-second lifetime, uncertainty margin, and independent reference cadence interact to suppress approximately alternate persistent requests.

This is a limitation of this particular conservative implementation and its timing choices, not a proof that all restart-safe protocols must lose half their commands. No parameter was relaxed after seeing the result.

## Engineering and publication consequence

The result supports a clear account of software output reservation, unresolved execution, and conditional clock/expiry guarantees. It does not support a superior hydroponic controller, physical exactly-once execution, or a plant-safety claim. A practical integration must establish a bounded output adapter and clock service, and specify how uncertain execution can be reconciled with independent evidence.

Disk-backed reservation → fsynced mock output → completion commit measured roughly 6.80 ms median and 8.16 ms p99 on this host. These measurements are not hard latency guarantees and do not include a physical actuator. The new version has not undergone a new two-container network execution experiment; its real execution evidence is the process-kill/storage probe.

See [full results and intervals](RESULTS.md) and [the reproducible contract](PROTOCOL.md). The underlying question is now whether a less conservative, explicitly justified timing implementation can preserve the demonstrated structural properties without these large availability and communication costs. That would be a new version requiring its own frozen evaluation, not a reason to omit this result.
