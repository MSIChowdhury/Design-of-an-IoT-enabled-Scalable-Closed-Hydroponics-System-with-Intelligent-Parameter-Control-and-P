# Frozen delivery challenge protocol

This protocol was written before executing this challenge. It tests the previously selected candidate without tuning, narrowing the scenario list, or changing the 95% coverage / 1% undesirable-command criteria after seeing results.

Run from the host repository:

```bash
scripts/48_run_delivery_challenge.sh
```

The launcher runs computation in Docker, starts a separate Docker UDP receiver, executes the sender/impairment relay in another container, generates the report, and removes only its own receiver container. It does not operate physical actuators. Prior benchmark outputs and manuscript tables remain unchanged.

## Fixed candidate and controlled comparison

All policies use the current `EventSender`/`EventReceiver`, 32-second retry interval, at most two transmissions per revision, original 64-second command lifetime, 120-second source freshness, and 600-second receiver cooldown. Persistence remains 32 seconds and the controller tick 16 seconds.

- **candidate:** bounded repetition plus cancellation; no ACKs.
- **plain_repetition:** same sender, receiver, pending-command handling, original timestamps, expiry, cooldown, and duplicate protection; cancellation and ACKs disabled.
- **acknowledged:** candidate plus receipt ACKs and ACK-based retry stopping.

There is no selection stage. This corrects the earlier component comparison, whose no-cancellation policy also used ACKs. Cancellation may change command-retry traffic because it replaces obsolete commands; that is part of the intervention.

## New scenarios and reused source data

Use all six primary channels over the existing final chronological evaluation block, with the same causal as-of samples, warm-up, tail exclusion, reference controller, event matching, and 64-second deadline. These source periods have been examined before: **the network challenge is new, the physical observations are not**.

All 25 scenarios are specified in `configs/experiments/delivery_challenge.yaml` and expanded into the frozen manifest before execution:

- Ideal, 10% and 20% independent packet loss, delay tails up to 96 seconds, asymmetric reverse-channel loss/delay.
- Outages lasting 32/64/128/256 seconds every hour, at phases 0/317/1733 seconds. Both directions are unavailable during these outages.
- Correlated loss with mean bad runs of 32/96/192 seconds and mean good runs nine times longer; stationary initialization. Channels have separate Markov chains. Six sensors share network realizations.
- Receiver clock offsets -64/-16/+16/+64 seconds.
- Receiver restart every hour, erasing volatile duplicate memory and cooldown.

Four previously unused seeded network realizations (701–704 with the new base seed) are paired across policies. No claim that these exhaust realistic networks is made. Offset and restart cases intentionally violate implementation assumptions and are reported separately from delivery impairments. Directed counterexamples additionally test restart followed by a duplicate, and a truly expired packet accepted by a clock that runs behind.

## Outcomes and uncertainty

Report matched command-event coverage, undesirable commands per reference opportunity, modeled offered bytes including ACKs/cancellation/lost packets, duplicate outputs, true-time expired outputs, and cooldown violations. Observer state detects structural violations but never suppresses receiver actions. Structural counts include the entire replay; event scoring retains the existing warm-up and tail exclusions. Duplicate same-direction actions can evade the original undesirable-command metric, so these additional counters are essential.

Use 1,000 crossed bootstrap resamples of source days and network seeds, preserving all sensors and paired methods within a cell. Report absolute 95% percentile intervals and paired candidate-minus-baseline differences. Four seeds limit uncertainty about rare network behavior. Intervals are marginal per scenario, not familywise or distribution-free guarantees; favorable interval counts are descriptive and unadjusted. Report point-criterion passes separately from cases whose interval bounds satisfy the limits.

## Real UDP execution, not just replay

Select one 1,808-second historical window per sensor using the highest number of direction transitions among nonoverlapping windows containing a reference action (earliest tie). Selection occurs before delivery execution and is saved with source timestamps. This purposive selection stresses changes but does not create an unbiased deployment sample.

Execute all three policies across five declared scenarios in separate sender/receiver Docker containers using a bridge network and real UDP sockets. A client-side application relay injects loss and delayed/reordered delivery in both directions. It is not kernel `netem` and introduces no claim about a particular radio. Historical time is accelerated 1000x; receiver ticks are shifted by half a tick (eight logical seconds) to make source/receiver timing explicit. Score on an eight-second grid preserving those event times, with the same 600-second warm-up and 192-second tail exclusion. Record actual processing latency, scheduling lateness, CPU time, process-lifetime peak RSS, and UDP payload+IP/UDP-header bytes. Lower-layer bridge traffic is not measured.

Forward lost packets are dropped before the UDP socket; their offered bytes are recorded separately from emitted datagrams. Receiver ACKs cross the socket before reverse impairment in the relay. Byte counts from this execution probe and the replay's all-offered-byte convention must not be silently equated. A shared host monotonic clock synchronizes the accelerated probe; clock-offset stress is handled explicitly in the replay and counterexamples.

The small execution probe is a systems check, not statistical confirmation of the full-history replay. OS scheduling can change outcomes at this acceleration. No physical dosing, energy, prospective deployment, or originality claim follows from standard retry mechanisms.
