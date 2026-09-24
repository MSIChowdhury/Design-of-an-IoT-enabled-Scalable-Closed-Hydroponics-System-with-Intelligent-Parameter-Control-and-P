# Recovery-contract results

**Conditional structural criterion: passed in the tested in-contract cases.** This reports finite software tests under the declared assumptions, not a physical exactly-once or plant-safety guarantee. The recovery version met the original 95% coverage / 1% undesirable-command point criteria in **0/12 in-contract scenarios**. No parameters were retuned.

## Structural failures, kept separate from availability

An initial complete run exposed a review gap in the recovery contract: first returning contact now advances the freshness barrier, requiring subsequently generated evidence. The receiver and a directed test were corrected, and this report comes from rerunning the full unchanged grid and crash probe. No parameters were retuned. Initial outputs/source are archived under `initial_barrier_audit/`; the final run is correctness reanalysis, not an untouched validation claim.

Counts aggregate all six streams and four seeds across the twelve in-contract scenarios, including warm-up/tail. They are replay counts rather than independent physical incidents. The observer detects violations but never vetoes an output. Baselines do not implement a recovery barrier, so their stale-recovery column is not applicable and is recorded as zero rather than evidence of recovery correctness.

| policy | repeated_outputs | expired_outputs | cooldown_violations | stale_recovery_outputs |
| --- | --- | --- | --- | --- |
| current | 334 | 88 | 2208 | 0 |
| plain_repetition | 334 | 88 | 2212 | 0 |
| recovery_v2 | 0 | 0 | 0 | 0 |

## Coverage, error, and cost

All rows, including the explicitly unsupported -48-second clock-offset case, are retained. Coverage and error are fractions; error is unnecessary/wrong-direction outputs per reference opportunity. Traffic is offered serialized payload plus 28-byte IPv4/UDP overhead, including lost packets. V2 adds 32-second fresh-evidence heartbeats, which are counted; current/plain repetition do not use them. Coverage matching uses the unchanged independent reference controller and 64-second deadline.

| scenario | in_contract | coverage | coverage_low | coverage_high | current_coverage | error | traffic_multiple | structural_violations | point_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| clock_minus16 | True | 0.4949 | 0.4891 | 0.4984 | 0.9874 | 0.0032 | 9.8913 | 0 | False |
| clock_plus16 | True | 0.2438 | 0.2262 | 0.2588 | 0.9851 | 0.0018 | 9.8913 | 0 | False |
| combined | True | 0.4687 | 0.4599 | 0.4797 | 0.9282 | 0.0039 | 9.8913 | 0 | False |
| correlated_160 | True | 0.4572 | 0.4436 | 0.4666 | 0.9036 | 0.0041 | 9.8913 | 0 | False |
| correlated_64 | True | 0.4558 | 0.4438 | 0.4653 | 0.9271 | 0.0038 | 9.8913 | 0 | False |
| delay_tail | True | 0.2225 | 0.2077 | 0.2379 | 0.7819 | 0.0015 | 9.8913 | 0 | False |
| ideal | True | 0.4994 | 0.4951 | 0.5048 | 1.0000 | 0.0000 | 9.8913 | 0 | False |
| iid_10 | True | 0.4632 | 0.4511 | 0.4719 | 0.9751 | 0.0041 | 9.8913 | 0 | False |
| iid_20 | True | 0.4234 | 0.4130 | 0.4325 | 0.9469 | 0.0039 | 9.8913 | 0 | False |
| outage_224 | True | 0.4610 | 0.4497 | 0.4687 | 0.9236 | 0.0041 | 9.8913 | 0 | False |
| outage_96 | True | 0.4743 | 0.4645 | 0.4815 | 0.9684 | 0.0038 | 9.8913 | 0 | False |
| outside_clock_bound | False | 0.3645 | 0.3500 | 0.3775 | 0.3095 | 0.0049 | 9.8913 | 1091 | False |
| restart | True | 0.5033 | 0.4971 | 0.5112 | 0.9867 | 0.0041 | 9.8913 | 0 | False |

## Real process crashes and disk durability

| stage | trials | passed | old_outputs | new_outputs | uncertain |
| --- | --- | --- | --- | --- | --- |
| before_receive | 5 | 5 | 0 | 5 | 0 |
| after_accept | 5 | 5 | 0 | 5 | 0 |
| after_reserve | 5 | 5 | 0 | 0 | 5 |
| after_output | 5 | 5 | 5 | 0 | 5 |
| after_commit | 5 | 5 | 5 | 5 | 0 |

Each test sends SIGKILL to a separate child process, reopens its SQLite journal, retries the original command, then offers a later new command. The mock output is an independently fsynced append-only file. The five boundaries are before receipt, after accepted-state commit, after reservation commit, after output but before completion commit, and after completion commit. Crashes around reservation/output remain uncertain and block even the later command. This intentionally sacrifices availability instead of guessing what happened. An independent reconciliation path is not implemented; elapsed time alone cannot clear uncertainty.

Disk-backed reservation → fsynced mock output → completion commit took median **6.802 ms**, p95 **6.932 ms**, p99 **8.158 ms**, maximum **8.670 ms** over 100 measured operations after 10 warm-ups. Host storage measurements do not establish a hard real-time bound or real actuator execution. The historical benchmark uses the same SQLite transactions in memory, retaining the connection across receiver reconstruction; disk/process durability is tested separately.

## Contract and argument

Assume one active receiver, durable untampered journal storage, monotonic sender IDs/timestamps, receiver time `r` with true sender-relative time in `[r-B,r+B]`, and an output adapter that emits within `D` seconds or definitively cannot emit later. Here `B=16 s`, `D=1 s`. The adapter bound is an external integration obligation, not established by average timing tests.

Before output, require `r-B >= command_created`, `r+B+D <= min(command_created+64, source_time+120)`, and `r-B >= persisted_next_allowed`. Reserve identity and `persisted_next_allowed=r+B+D+600` durably before output. These inequalities prevent early/expired output and shortened cooldown within the bounds. A crash leaves either a committed reservation (uncertain and blocked) or a completed identity (never replayed). Accepted but unreserved commands are abandoned at restart. This protects software output issuance; physical exactly-once execution still requires actuator-side support or feedback.

Restart or a 96-second heartbeat timeout sets a durable recovery barrier at the receiver's current upper time bound. First returning contact after silence advances that barrier again, so the returning packet cannot itself restore readiness. Resumption requires a fresh source timestamp and a newly eligible command strictly after the barrier. Old IDs, original timestamps, and expiration are never renewed. Recovery readiness is volatile and must be reestablished after each restart. Clock-invalid indications or backward receiver time latch a block; an undetected violation of the assumed clock bound is not made safe by configuration alone.

## Paired availability/error uncertainty

Crossed source-day and seed resampling (1,000 draws) retains all sensors and paired methods together. Intervals are marginal, not simultaneous guarantees; four network seeds limit tail inference. Structural zero counts are not assigned a zero-risk claim. Current versus recovery changes persistence, uncertainty handling, and heartbeat recovery together; this is a complete contract comparison, not an isolated cancellation ablation.

| scenario | baseline | metric | difference | low | high |
| --- | --- | --- | --- | --- | --- |
| clock_minus16 | current | coverage | -0.4925 | -0.5016 | -0.4847 |
| clock_minus16 | current | error | -0.0057 | -0.0100 | -0.0022 |
| clock_plus16 | current | coverage | -0.7413 | -0.7588 | -0.7249 |
| clock_plus16 | current | error | -0.0048 | -0.0089 | -0.0013 |
| combined | current | coverage | -0.4595 | -0.4732 | -0.4453 |
| combined | current | error | -0.0044 | -0.0086 | -0.0011 |
| correlated_160 | current | coverage | -0.4464 | -0.4612 | -0.4344 |
| correlated_160 | current | error | -0.0018 | -0.0035 | -0.0005 |
| correlated_64 | current | coverage | -0.4713 | -0.4890 | -0.4550 |
| correlated_64 | current | error | -0.0022 | -0.0040 | -0.0004 |
| delay_tail | current | coverage | -0.5594 | -0.5823 | -0.5344 |
| delay_tail | current | error | -0.0028 | -0.0051 | -0.0009 |
| ideal | current | coverage | -0.5006 | -0.5049 | -0.4952 |
| ideal | current | error | 0.0000 | 0.0000 | 0.0000 |
| iid_10 | current | coverage | -0.5119 | -0.5223 | -0.5034 |
| iid_10 | current | error | -0.0028 | -0.0051 | -0.0008 |
| iid_20 | current | coverage | -0.5235 | -0.5381 | -0.5085 |
| iid_20 | current | error | -0.0021 | -0.0038 | -0.0008 |
| outage_224 | current | coverage | -0.4626 | -0.4709 | -0.4526 |
| outage_224 | current | error | -0.0016 | -0.0029 | -0.0005 |
| outage_96 | current | coverage | -0.4941 | -0.5019 | -0.4867 |
| outage_96 | current | error | -0.0027 | -0.0044 | -0.0010 |
| outside_clock_bound | current | coverage | 0.0550 | 0.0133 | 0.0869 |
| outside_clock_bound | current | error | -0.0016 | -0.0056 | 0.0007 |
| restart | current | coverage | -0.4833 | -0.4898 | -0.4752 |
| restart | current | error | -0.0023 | -0.0046 | -0.0004 |

## Reproduce and interpret

Run `docker compose run --rm -T project-shell make recovery-contract`. The source periods are retrospectively reused; new seeds and fault schedules do not create independent physical deployments. This version is stored separately and prior results are preserved. No actual dosing, power-loss/storage-corruption test, networked-actuator execution guarantee, or journal-loss/split-brain protection is claimed. No new two-container UDP benchmark was run for V2; the new execution evidence is the disk-backed SIGKILL probe.

See [PROTOCOL.md](PROTOCOL.md). Generated CSVs, the frozen configuration/source manifest, and machine details are under `results/metrics/recovery_contract/`; the comparison plot is under `results/figures/recovery_contract/`.
