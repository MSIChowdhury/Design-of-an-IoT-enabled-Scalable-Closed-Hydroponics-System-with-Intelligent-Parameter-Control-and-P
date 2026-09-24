# Reliable command-event delivery protocol

This follow-up implements the compact-event direction identified by the telemetry feasibility study. It leaves the existing telemetry and manuscript outputs intact and adds a separate reliable-delivery study.

```bash
docker compose run --rm -T project-shell make reliable-events
```

The Make target generates the preceding telemetry baselines if absent. The runner verifies baseline data, configuration, and implementation fingerprints and checks that old/new reference-opportunity populations are identical before comparing results.

## Unchanged experimental population and constraints

The same six channels, complete chronological validation/evaluation blocks, 16-second controller ticks, 32-second persistence, 600-second output cooldown, 120-second source freshness, 64-second command lifetime, and network profiles from `configs/experiments/telemetry.yaml` are used. No fault-detector or plant-response claim is added. The source stream is converted causally to a fixed controller clock, and reference actions never change the historical trajectory.

The prior evaluation results motivated this follow-up. These periods are therefore **adaptively reused retrospective evaluation data**, not newly untouched observations. Current protocol settings are selected on validation and saved before evaluation, but that does not erase the previous research history.

The selection rules remain at least 95% or 99% command-event coverage within 64 seconds and at most 1% unnecessary/wrong-direction commands per reference opportunity on every validation network. All four networks must share one setting per policy. Choose the feasible setting with the lowest total modeled bytes; keep infeasible settings explicitly diagnostic. Delay sensitivities remain 16, 64, and 180 seconds. These are engineering comparison settings, not agronomically certified tolerances.

## Sender state and retries

The sender runs the same full-stream reference controller. Each emitted command gets a monotonic event ID, revision zero, original creation time, original supporting-measurement timestamp, and signed action. Retry sends exactly the same command envelope; no timestamp, expiry, or evidence age is refreshed.

Retry intervals are 16 and 32 seconds; the maximum total transmissions per revision are 2, 3, and 5, including the first send. No send occurs after the original command's 64-second lifetime. A receipt ACK stops retries only if it matches both the current event ID and revision. An ACK reports receipt/disposition, not measured actuation.

The sender continues observing the current command until expiry even after its receipt was acknowledged. If the currently supported direction changes—including becoming in-band or unknown because evidence expires—the sender replaces revision zero with a revision-one cancellation. That revision receives its own bounded retry allowance but shares the original command's absolute expiry. ACK of revision zero cannot stop revision-one retries.

## Receiver state and cancellation

The receiver keeps only the latest event ID, its highest revision, its disposition, one pending command, and the next permitted output time. This is a constant number of records, not an unbounded set of past event IDs. Monotonic IDs and synchronized clocks are assumptions; persistence across process restart is not implemented.

| Input/state | Receiver behavior |
| --- | --- |
| ID older than latest ID | Reject as superseded; return corresponding ACK |
| Same ID, old or repeated revision | Do not update evidence or emit again; ACK current disposition |
| Cancellation before command | Store a higher-revision tombstone; later original command cannot execute |
| Cancellation while command is pending | Clear the pending command; retain output cooldown |
| Cancellation after output | Report already executed; count late cancellation; never claim rollback |
| Command beyond lifetime or source freshness | Mark expired; reject retries without renewing validity |
| Valid command during cooldown | Hold one pending command until cooldown ends or validity expires |
| Valid pending command when cooldown ends | Emit once; advance cooldown; retain terminal disposition |

All arrivals due on one receiver control tick are processed before output eligibility is checked. This permits a cancellation already received on that tick to veto the pending command. It cannot use future information or undo an earlier tick's action.

The exactly-once property is **at-most-once output under retries within one process lifetime**, not guaranteed delivery or proof of physical actuator execution. A network outage can make a command expire without execution. The software is not claimed resistant to malicious envelopes, compromised clocks, or resets that erase protocol state.

## Both network directions and all traffic are counted

Forward impairments use exactly the previous study's exogenous tick-indexed random draws. The new reverse ACK channel uses a separate reproducible random stream, the same configured loss/delay/duplication profile, and the same burst-outage periods. There is no free reliable ACK channel. Tick-indexed conditions are shared across sensor replays; correlated sensor outcomes are kept together in uncertainty analysis.

Commands, retransmissions, cancellations, ACKs, lost datagrams, and duplicated copies are all included in byte totals. Actual compact JSON serialization supplies payload length, plus the same modeled 28-byte IPv4/UDP header. Bytes are modeled network traffic, not measured radio traffic. Link-layer overhead, authentication/encryption, contention, sensing/CPU energy, and connection management remain excluded.

The old full-reporting and edge-event baselines are reused only after population/configuration checks. Their one-way byte totals have no ACKs because those policies do not send them. The new protocol explicitly pays for the feedback it uses.

## Component comparisons

- `reliable_events`: bounded retries, receipt ACKs, cancellation, expiry, idempotence, and cooldown-safe pending output.
- `without_cancellation`: identical retry/ACK machinery but no cancellation messages.
- `without_acknowledgments`: bounded repeated transmissions and cancellation, but no ACK traffic or early ACK-based stopping.

Every policy is tuned over the same retry grid. These are comparisons of tuned variants; they do not hold all selected hyperparameters fixed by assumption. In this run the 95% target selected the same 32-second/two-transmission setting for all three, making that comparison especially direct.

The command-event counts are scored independently of tested methods, with one-to-one same-episode/direction matching. Source-day bootstrap intervals keep all sensors and network seeds for a day together. Report both coverage and undesirable-command differences against the original edge-event baseline and the two new variants. No claim of equivalence follows merely from overlapping intervals.

## Real protocol execution check

A separate two-process UDP loopback probe uses the actual encoder and receiver. Each cycle transmits a command, its duplicate, a cancellation for the next command, and that cancelled command. Twenty-five warm-up cycles precede 250 measured cycles (100 warm-up and 1,000 measured datagrams). ACK identities and cancellation dispositions are checked. The receiver must emit 275 distinct commands, cancel 275 commands, and suppress 550 repeated/old-revision packets over the whole probe.

Controller time in this probe is logical; packet transport and round-trip timings are real local UDP. It verifies executable behavior, not radio performance, physical dosing, or the simulated impairment distribution. Focused tests separately cover lost ACKs, cancellation reordering, expiry, cooldown deferral, at-most-once output, and causality.

## Interpreting the completed run

Passing the 95% point-estimate requirements across these profiles establishes a useful feasibility result under the declared workload. It is not a distribution-free guarantee, a prospective replication, or an originality claim for standard retry/ACK mechanisms. The 99% requirement remains separately evaluated and must not be silently relaxed. A 128-second outage is longer than the 64-second command lifetime; some loss is unavoidable under those constraints.

Component evidence is central: if omitting ACKs achieves the same measured outcomes with fewer bytes, prefer that simpler bounded-redundancy configuration when receipt observability is not required. Cancellation's benefit is measured separately, and late cancellation remains a limitation.
