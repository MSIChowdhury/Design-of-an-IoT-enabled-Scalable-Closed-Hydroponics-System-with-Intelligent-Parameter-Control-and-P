# Assessment of the local execution evidence

The experiment moves the work beyond simulated instantaneous output: separate Docker processes recorded real transport, timer, storage, mock-effect, and acknowledgment timestamps, and a supervised receiver survived actual process kills with its persistent contract intact. It does not replace the hypothetical interdevice clock bound or establish physical execution.

The main finding is **execution ambiguity, not local compute speed**. An independently recorded output with a lost acknowledgment leaves the receiver unable to distinguish successful output from failure using its own evidence. Conservatively blocking is correct under the existing contract, but causes severe availability loss when the short impaired trace is repeated over a long historical block. The mock lookup demonstrates that useful reconciliation evidence could exist; it is deliberately not wired into automatic recovery.

## What the comparison establishes

- Idle and CPU-contention trace replays both preserve 99.33% coverage for volatile and durable-only polling. Journal persistence itself is not the principal availability loss in these conditions.
- Under the hypothetical B=16 s clock bound, deadline scheduling improves coverage from 48.90% to 64.97% with the same measured trace and modeled traffic. B=1 s deadline coverage reaches 96.61%, but the smaller bound remains unverified for independently clocked hardware.
- Under injected packet/ACK loss, durable-only coverage falls to 1.57%; full recovery variants span 0.95–5.79%. Every sensor/phase eventually encounters uncertain execution and blocks. The volatile baseline retains 99.18% coverage but has no comparable unresolved-execution protection. Its availability is not proof of correctness after ambiguous output.
- No duplicate, expired, or cooldown-violating modeled outputs were observed in this trace grid. That result is conditional on the measured short traces, shared actual clock, unchanged model assumptions, and lack of hardware failures; it is not a deployment safety guarantee.

The injected profile combines a fixed ingress delay, forward omissions, and missing output acknowledgments. Its aggregate loss cannot isolate all three causes experimentally. The paired code tests isolate the missing-ACK mechanism, while full per-command ledgers show later commands blocked. The higher coverage of one conservative variant under this profile reflects when it first encounters an ACK-loss row, not evidence that stronger clock restrictions generally improve availability. Three cyclic phases are too few to establish a general network distribution.

The historical source is the existing **prepared** parquet, not new raw acquisition. Each comparison reuses the same 3,448 unique reference opportunities at three trace phases (10,344 scored opportunities in its aggregate row). Unmodified means no additional corruption in this experiment; it does not mean calibrated ground truth or absence of earlier preprocessing. Historical plant trajectories are unchanged by mock/replayed commands.

## Reproducibility and measurement context

Final collection: 300 measured isolated transactions plus 30 warmups, 90 clock exchanges, and 15 actual SIGKILL/restart cases. The host exposed an AMD Ryzen 7 9800X3D and 16 logical CPUs; the receiver was pinned to CPU 0. The contention profile pinned one busy process to the same CPU. Endpoints used single-threaded request loops; offline replay used four worker processes. This does not establish Raspberry Pi or deployed-controller performance.

Observed environment: Linux 7.0.0-31-generic x86_64, Python 3.11, SQLite 3.46.1, NumPy 1.26.4, pandas 2.2.3, SciPy 1.13.1, Matplotlib 3.10.3. Detailed clock/environment metadata and host NTP status remain in the local output directory.

An initial strict namespace-identity check stopped before measurement. Inspection showed distinct Linux time namespaces on the same kernel boot with identical zero offsets. The corrected check compares kernel boot plus namespace offsets and retains namespace identifiers separately. It does not infer shared clocks from small observed RTT. The full run was repeated after correcting report wording about the prepared historical source; the published summary uses the final collection only, without pooling earlier timing samples.

The frozen manifest records source/configuration/protocol fingerprints before collection and was verified before and after all 270 replays. Compact snapshots accompany this document; transaction traces, journals, and 270 compressed command ledgers remain local and are reproducible. The complete test suite passed 131 tests, including five zero-timing equivalence checks against the earlier replay and a late-wakeup expiry check. Repository-wide Ruff checks passed.

## Next robust step

Specify and test a **bounded reconciliation contract** for ambiguous output before adding another detection algorithm. Define what independent, event-specific evidence is sufficient to mark a command completed, establish the last output timestamp/cooldown, or require operator intervention. Include lost, late, mismatched, contradictory, and unavailable lookup responses, repeated restarts during reconciliation, and a mock failure after accepting a command but before producing its effect. Do not let elapsed time alone restore authority.

This is a next experiment, not an implemented recovery claim. Its comparison should hold the current sender, reference opportunities, command constraints, and impairment schedule fixed. Only after that mechanism demonstrates both structural correctness and useful recovery should a second-machine/edge-device experiment test the remaining clock and outage assumptions. The present result supports a software execution/availability study; it does not yet justify a closed-loop control or physical exactly-once paper claim.
