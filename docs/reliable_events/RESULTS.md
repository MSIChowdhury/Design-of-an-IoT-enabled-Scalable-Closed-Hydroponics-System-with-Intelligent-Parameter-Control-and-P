# Reliable command-event delivery results

**The reliable protocol passed the declared 95% coverage / 1% error requirements on all validation and evaluation profiles.** This is computational command fidelity, not physical plant safety, a prospective replication, or established research novelty.

## Evaluation results

The original source blocks, six sensors, controller timings, forward network profiles, seeds, 64-second matching deadline, and 95%/99% targets are preserved. The new reverse channel is impaired as well. Byte savings include forward commands, retries, cancellations, duplicate copies, and all ACK datagrams, each with the same modeled 28-byte IPv4/UDP header. Values below are fractions; negative byte savings would mean increased traffic.

| network | policy | setting | status | coverage | undesirable_fraction | byte_savings |
| --- | --- | --- | --- | --- | --- | --- |
| burst_outage | reliable_events | r32_n2 | selected | 0.9676 | 0.0060 | 0.9071 |
| delay_reorder | reliable_events | r32_n2 | selected | 0.9798 | 0.0056 | 0.8959 |
| ideal | reliable_events | r32_n2 | selected | 1.0000 | 0.0000 | 0.9500 |
| lossy | reliable_events | r32_n2 | selected | 0.9815 | 0.0065 | 0.9041 |
| burst_outage | without_acknowledgments | r32_n2 | selected | 0.9676 | 0.0060 | 0.9421 |
| delay_reorder | without_acknowledgments | r32_n2 | selected | 0.9798 | 0.0056 | 0.9421 |
| ideal | without_acknowledgments | r32_n2 | selected | 1.0000 | 0.0000 | 0.9421 |
| lossy | without_acknowledgments | r32_n2 | selected | 0.9815 | 0.0065 | 0.9421 |
| burst_outage | without_cancellation | r32_n2 | selected | 0.9676 | 0.0066 | 0.9079 |
| delay_reorder | without_cancellation | r32_n2 | selected | 0.9798 | 0.0065 | 0.8967 |
| ideal | without_cancellation | r32_n2 | selected | 1.0000 | 0.0000 | 0.9508 |
| lossy | without_cancellation | r32_n2 | selected | 0.9814 | 0.0073 | 0.9048 |

Removing ACKs produced identical measured coverage and undesirable-command rates on every profile. The ACK-free variant saved 94.21%–94.21% of modeled wire bytes. Receipt observability should therefore be distinguished from improvements in command fidelity.

No tested policy met the 99% target across all validation profiles. The 95% result is a point-estimate feasibility criterion, not a confidence-bound guarantee.

Validation choices were saved before evaluation, but this is an **adaptive retrospective follow-up**: prior results on these evaluation periods motivated the protocol. The evaluation set is not newly untouched evidence. All three new policies use the same receiver and bounded-retry machinery; removing cancellation or ACKs provides component comparisons. Neither ablation is silently replaced by a weaker discard-on-cooldown receiver.

## Paired uncertainty

Reliable protocol minus baseline; two-sided percentile 95% intervals from 1,000 joint source-day resamples. All sensors and network seeds for a day stay together. Settings are selected independently per policy from the same validation grid; these are comparisons of tuned variants rather than every parameter held fixed.

| target | network | baseline | metric | difference | low | high | source_days |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.9500 | burst_outage | edge_events | coverage | 0.0061 | 0.0021 | 0.0120 | 10 |
| 0.9500 | burst_outage | edge_events | undesirable_fraction | -0.0009 | -0.0018 | 0.0000 | 10 |
| 0.9500 | burst_outage | without_cancellation | coverage | 0.0000 | 0.0000 | 0.0000 | 10 |
| 0.9500 | burst_outage | without_cancellation | undesirable_fraction | -0.0006 | -0.0011 | 0.0000 | 10 |
| 0.9500 | burst_outage | without_acknowledgments | coverage | 0.0000 | 0.0000 | 0.0000 | 10 |
| 0.9500 | burst_outage | without_acknowledgments | undesirable_fraction | 0.0000 | 0.0000 | 0.0000 | 10 |
| 0.9500 | delay_reorder | edge_events | coverage | 0.0001 | 0.0000 | 0.0003 | 10 |
| 0.9500 | delay_reorder | edge_events | undesirable_fraction | -0.0012 | -0.0020 | -0.0003 | 10 |
| 0.9500 | delay_reorder | without_cancellation | coverage | 0.0000 | 0.0000 | 0.0000 | 10 |
| 0.9500 | delay_reorder | without_cancellation | undesirable_fraction | -0.0009 | -0.0015 | -0.0002 | 10 |
| 0.9500 | delay_reorder | without_acknowledgments | coverage | 0.0000 | 0.0000 | 0.0000 | 10 |
| 0.9500 | delay_reorder | without_acknowledgments | undesirable_fraction | 0.0000 | 0.0000 | 0.0000 | 10 |
| 0.9500 | ideal | edge_events | coverage | 0.0000 | 0.0000 | 0.0000 | 10 |
| 0.9500 | ideal | edge_events | undesirable_fraction | 0.0000 | 0.0000 | 0.0000 | 10 |
| 0.9500 | ideal | without_cancellation | coverage | 0.0000 | 0.0000 | 0.0000 | 10 |
| 0.9500 | ideal | without_cancellation | undesirable_fraction | 0.0000 | 0.0000 | 0.0000 | 10 |
| 0.9500 | ideal | without_acknowledgments | coverage | 0.0000 | 0.0000 | 0.0000 | 10 |
| 0.9500 | ideal | without_acknowledgments | undesirable_fraction | 0.0000 | 0.0000 | 0.0000 | 10 |
| 0.9500 | lossy | edge_events | coverage | 0.0457 | 0.0405 | 0.0495 | 10 |
| 0.9500 | lossy | edge_events | undesirable_fraction | -0.0002 | -0.0011 | 0.0007 | 10 |
| 0.9500 | lossy | without_cancellation | coverage | 0.0001 | 0.0000 | 0.0003 | 10 |
| 0.9500 | lossy | without_cancellation | undesirable_fraction | -0.0008 | -0.0015 | -0.0001 | 10 |
| 0.9500 | lossy | without_acknowledgments | coverage | 0.0000 | 0.0000 | 0.0000 | 10 |
| 0.9500 | lossy | without_acknowledgments | undesirable_fraction | 0.0000 | 0.0000 | 0.0000 | 10 |
| 0.9900 | burst_outage | edge_events | coverage | 0.0070 | 0.0028 | 0.0121 | 10 |
| 0.9900 | burst_outage | edge_events | undesirable_fraction | -0.0006 | -0.0012 | 0.0000 | 10 |
| 0.9900 | burst_outage | without_cancellation | coverage | 0.0000 | 0.0000 | 0.0000 | 10 |
| 0.9900 | burst_outage | without_cancellation | undesirable_fraction | -0.0006 | -0.0012 | 0.0000 | 10 |
| 0.9900 | burst_outage | without_acknowledgments | coverage | 0.0000 | 0.0000 | 0.0000 | 10 |
| 0.9900 | burst_outage | without_acknowledgments | undesirable_fraction | 0.0000 | 0.0000 | 0.0000 | 10 |
| 0.9900 | delay_reorder | edge_events | coverage | 0.0012 | 0.0000 | 0.0032 | 10 |
| 0.9900 | delay_reorder | edge_events | undesirable_fraction | -0.0015 | -0.0028 | -0.0006 | 10 |
| 0.9900 | delay_reorder | without_cancellation | coverage | 0.0000 | 0.0000 | 0.0000 | 10 |
| 0.9900 | delay_reorder | without_cancellation | undesirable_fraction | -0.0011 | -0.0017 | -0.0004 | 10 |
| 0.9900 | delay_reorder | without_acknowledgments | coverage | 0.0000 | 0.0000 | 0.0000 | 10 |
| 0.9900 | delay_reorder | without_acknowledgments | undesirable_fraction | 0.0000 | 0.0000 | 0.0000 | 10 |
| 0.9900 | ideal | edge_events | coverage | 0.0000 | 0.0000 | 0.0000 | 10 |
| 0.9900 | ideal | edge_events | undesirable_fraction | 0.0000 | 0.0000 | 0.0000 | 10 |
| 0.9900 | ideal | without_cancellation | coverage | 0.0000 | 0.0000 | 0.0000 | 10 |
| 0.9900 | ideal | without_cancellation | undesirable_fraction | 0.0000 | 0.0000 | 0.0000 | 10 |
| 0.9900 | ideal | without_acknowledgments | coverage | 0.0000 | 0.0000 | 0.0000 | 10 |
| 0.9900 | ideal | without_acknowledgments | undesirable_fraction | 0.0000 | 0.0000 | 0.0000 | 10 |
| 0.9900 | lossy | edge_events | coverage | 0.0508 | 0.0442 | 0.0564 | 10 |
| 0.9900 | lossy | edge_events | undesirable_fraction | -0.0006 | -0.0012 | 0.0001 | 10 |
| 0.9900 | lossy | without_cancellation | coverage | 0.0001 | 0.0000 | 0.0003 | 10 |
| 0.9900 | lossy | without_cancellation | undesirable_fraction | -0.0009 | -0.0019 | 0.0000 | 10 |
| 0.9900 | lossy | without_acknowledgments | coverage | 0.0000 | 0.0000 | 0.0000 | 10 |
| 0.9900 | lossy | without_acknowledgments | undesirable_fraction | 0.0000 | 0.0000 | 0.0000 | 10 |

## Executable protocol and real UDP check

Stable command IDs and revision-specific ACKs support retry without reexecution. A cancellation creates a higher-revision tombstone even when it arrives before the command. ACK of a lower revision cannot silence cancellation retries. Original creation and source times never change during retry. Receipt ACK does not certify execution; cancellation cannot undo an action already emitted. Output cooldown is authoritative, and only a still-valid command can execute after waiting for it.

A two-process UDP loopback exercise sent 1000 measured datagrams after 100 warm-up messages, including deliberate duplicates and cancellation-before-command. Receiver totals: 275 distinct commands emitted, 275 future commands cancelled, 550 repeated/older-revision packets suppressed. Median RTT 0.0109 ms; p95 0.0125 ms; p99 0.0194 ms. These are host loopback measurements with logical controller times, not radio or Raspberry Pi measurements.

## Limitations and artifacts

Unacknowledged cancellation can arrive too late to prevent an action; the study measures that remaining error rather than claiming zero unsafe commands. A 128-second outage exceeds the 64-second command lifetime, making some event loss unavoidable without changing requirements. Controller clocks are synchronized, event IDs are monotonic, and process restart persistence and malicious-packet handling are outside the tested scope. Receiver memory is bounded to the latest command ID/revision and one pending command; state is not persisted across restart. No capacity contention, encryption overhead, sensing-energy measurements, actual dosing, or crop outcomes are evaluated.

Generated outputs: `results/metrics/reliable_events/` and `results/figures/reliable_events/`. The previous telemetry outputs are preserved. Reproduce with `docker compose run --rm -T project-shell make reliable-events`. See [PROTOCOL.md](PROTOCOL.md).
