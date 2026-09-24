# Decision-preserving telemetry feasibility protocol

This study tests the proposed communication direction independently of the existing fault-detector manuscript. It asks whether a remote controller can reproduce a full-stream reference controller while receiving fewer bytes. It does not infer better physical control, calibrated sensing, crop yield, or energy savings.

## Reproduction and evidence

```bash
docker compose run --rm -T project-shell make telemetry-feasibility
```

The input is the locally available `data/processed/hydro_exp1_measurements.parquet`. Six primary channels are used; uncalibrated water level remains excluded. Data collection/preprocessing predates this study. Timestamps and measurements, including natural gaps and existing measurement errors, remain unchanged. No synthetic sensor faults are introduced into this communication experiment.

The source timeline is divided by elapsed duration at 40% and 70%. The first 40% is reserved as development; the entire next 30% is validation and the final 30% evaluation. These data have been used in prior research iterations, so the split is retrospective, not an untouched prospective test. The first observation inside each block initializes that block; no context crosses its boundary.

A fixed 16-second controller clock uses only the most recent recorded observation available at each tick. Source timestamps are retained; reuse never refreshes source age. Multiple observations between controller ticks are reduced to the latest available value. Thus the reference is the **specified 16-second software controller**, not every acquisition sample or the unknown historical controller. This causal conversion adds at most one tick of scheduling delay. Controller ticks continue through natural data gaps; the last observation expires after 120 seconds. Time is relative to block start, and sender/receiver clocks are assumed synchronized. Clock-drift robustness has not been established.

## Reference and sender policies

All policies use configured control bands, 32-second persistence, and 600-second output cooldown. Applying that cooldown to all six channels is a standardized workload choice; only the pH/EC ten-minute lockout has the prior deployment motivation. Every sender observes the full locally available stream and uses the same reference clock. Savings concern communication, not sensor sampling.

| Policy | Trigger and payload |
| --- | --- |
| Full reporting | Every new source observation available on a controller tick; source timestamp and value |
| Periodic | Current available measurement at the configured heartbeat |
| Send-on-change (`delta`) | Value change exceeds the configured threshold, or heartbeat expires |
| Threshold plus heartbeat | Control-band direction changes, or heartbeat expires |
| Edge command events | Entire reference controller runs at the sender; send each command event with its identity and creation/evidence times |
| Stateful snapshots | Same trigger as threshold plus heartbeat; additionally send direction, persistence-start time, next virtual authorization time, and any contemporaneous command event |

The stateful candidate uses **the same triggering rule** as the threshold baseline. This isolates timer-state synchronization and charges its larger serialized payload. It does not get a hidden acknowledgment channel or privileged future knowledge. The edge-event baseline explicitly tests the simpler solution of running the entire controller locally. It reports computational command events; no actuator was physically commanded.

## Network and message accounting

Four declared network profiles are used: ideal delivery; 8–64-second delay with possible reordering and duplicate copies; 5% random loss with 8–32-second delay and duplication; and a 128-second outage once per simulated hour with 8–32-second ordinary delay. Profiles are simulation assumptions, not fitted descriptions of the historical network. Source data gaps are not classified as measured packet losses.

Random draws are indexed by sender clock tick, not by the policy's packet count, so policies share exogenous network conditions. The same tick-level draws are shared across sensor streams; packet losses are therefore correlated across sensors rather than independent physical replications. Validation uses one fixed seed for each impaired profile; evaluation uses three different seeds. Ideal delivery is deterministic and counted only once. Each stream is simulated independently with no shared link-capacity constraint or contention; shared-budget scheduling is future work, not a result of this run.

Datagrams enter a delivery priority queue; arrivals are processed at receiver controller ticks. Reordering can result from different delays. All pending arrivals at a tick are delivered before the receiver's timer update. Packets beyond block end cannot affect scored results, and the last 192 seconds are reserved for matching follow-up.

Actual compact JSON serialization determines application payload bytes. A modeled 28-byte IPv4/UDP header is added per transmitted datagram, including lost datagrams and duplicated network copies. These are modeled network bytes, not measured radio traffic. Link-layer overhead, encryption, retransmission, ACKs, connection management, radio listening, and CPU energy are excluded. All policies use the same encoding conventions. Binary encodings may materially change the snapshot tradeoff.

## Common receiver contracts

The executable receiver and tests enforce these rules:

- Receive and processing time is monotonic.
- Older or duplicate message sequence numbers cannot update state.
- Evidence older than 120 seconds cannot update state or authorize an action.
- An explicit command event expires 64 seconds after creation, independently of evidence age.
- The same explicit command-event identity cannot be executed again, including if resent with a different sequence number.
- Snapshots cannot shorten the output device's outstanding 600-second cooldown.
- A command arriving shortly before cooldown expires can wait in a single pending slot. It executes only while both command and evidence remain valid. Measurement-driven pending commands also require the current receiver estimate to retain the matching direction.
- Missing telemetry eventually expires; it does not become a new measurement or proof of sensor failure.

The pending slot avoids weakening the simple event baseline by discarding slightly early, jittered commands. Earlier exploratory outputs using immediate discard are archived locally under `results/run_metadata/telemetry_initial_drop_on_lockout/`; only the final pending-command receiver is reported.

The receiver's virtual controller and its output lockout are separate. A snapshot updates virtual state from the sender, but the local output lockout remains authoritative. Event-only receivers have no continuous measurement stream; they can validate command age and identity but cannot infer subsequent process changes. This limitation is included in their error measurements.

These are executable, tested software properties. This work does **not** claim formal model checking, plant safety, restart persistence, malicious-payload resistance, clock-drift tolerance, or bounded-memory operation over an indefinite deployment. The current receiver keeps event identities for the replay lifetime.

## Scoring and validation selection

Scoring starts 600 seconds after block initialization and stops 192 seconds before block end. Traffic accounting covers the whole block, including initialization and follow-up, for every policy.

Reference command events define opportunities independently of each policy. A policy command matches at most one reference command, in the same continuous control-band direction episode, at or after reference eligibility and within the selected 16-, 64-, or 180-second deadline. An action cannot be reused. Commands before a reference event receive no credit for that future event. Evaluation uses the unchanged reference trajectory; policy commands do not change it.

Coverage is matched events divided by reference events. A wrong-direction command opposes a nonzero reference direction; an unnecessary command occurs when the reference direction is zero, including when source information has expired. Both counts are reported separately. The declared error constraint uses their sum divided by reference opportunities. Extra same-direction commands and phase shifts are additionally exposed by authorization counts and exact tick-level action disagreement. Low error frequency alone does not establish useful behavior.

The primary selection deadline is 64 seconds. For each policy and coverage target (95%, 99%), select the lowest-byte setting meeting both that coverage and at most 1% unnecessary/wrong-direction commands per opportunity on **every** validation network. One common setting must serve all network profiles. Search grids for heartbeats and delta thresholds are in `configs/experiments/telemetry.yaml`.

If no setting is feasible, retain the setting with the highest worst-profile validation coverage, breaking ties by lower worst-profile error, lower total bytes, and setting name. Label this an infeasible diagnostic; do not relax targets or promote it into a successful result. Evaluation executes only locked settings plus the full-reporting baseline. Both targets may select the same setting and are not independent replications.

Report per-network outcomes and source-day cluster bootstrap intervals. Day resampling retains all sensors and seed realizations jointly. Paired comparisons of snapshots against threshold-plus-heartbeat and edge events use the same day clusters and reference opportunities. Intervals are two-sided 95% percentile intervals from 1,000 resamples. Packet counts are not treated as independent experiments. The single historical dataset and limited evaluation days constrain generalization.

## Measured software probe

A separate two-process UDP loopback experiment uses the same message encoding and receiver, sends 100 warm-up plus 1,000 measured sample messages, and records acknowledged round-trip time and actual application bytes. This demonstrates executable protocol processing on the available host. It is not the impaired trace network, a Raspberry Pi benchmark, or a radio-energy experiment. The ACK-based probe is intentionally separate from the one-way trace protocol.

## Decision criterion

Continue toward a paper only if controller-state synchronization or another clearly specified mechanism offers a practically useful communication/fidelity advantage against the strong simple policies. If event-only control or threshold-plus-heartbeat explains the benefit, report that outcome and simplify the direction. Do not describe an infeasible operating point as meeting the original requirements.
