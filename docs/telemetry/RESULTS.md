# Telemetry feasibility results

This is a new computational fidelity study. No measured crop, dosing, energy, or closed-loop safety improvement is inferred.

**No policy met the joint validation requirements on every network profile.** All reported operating points are explicitly diagnostic; the study is not yet a positive submission result.

The simple edge-event policy reduced modeled bytes by 96.9% and retained 93.6–98.0% coverage on impaired links. State snapshots retained 98.3–99.1% coverage, with mean modeled byte savings of -17.6% (negative means increased traffic) and a worst-profile undesirable-command rate of 2.24% per reference opportunity. These results favor investigating reliable event delivery before adding snapshot complexity. They do not establish novel superiority, physical safety, or energy savings. Payload encoding and untested retransmission/cancellation protocols could change the tradeoff.

Input SHA-256: `6c034bed3948172e88d5ec9caf1885efe14795e4041c6a4b9cf2decc356e6a71`. CPU: AMD Ryzen 7 9800X3D 8-Core Processor. Controller tick: 16 seconds. The complete chronological validation/evaluation blocks are used; source gaps are retained and evidence expires after 120 seconds. Previously used data: this remains retrospective evaluation.

## Selection and evaluation

Settings were locked using validation only. A policy must attain the requested coverage and at most 1% unnecessary/wrong-direction authorizations per reference opportunity on **every** validation network profile. No setting is chosen anew for each evaluation network. Infeasible policies are shown at their validation-maximum-minimum-coverage setting, explicitly as diagnostics.

The table shows the 95% validation target and 64-second event-matching deadline. Byte savings are relative to full reporting on the same network. Values are fractions. Validation has one network realization; evaluation has three different realizations per impaired profile and one deterministic ideal profile. Inference resamples source days jointly across sensors and seeds, not packets as independent experiments.

| network | policy | setting | selection_status | coverage | undesirable_fraction | byte_savings |
| --- | --- | --- | --- | --- | --- | --- |
| burst_outage | delta | h600_d2 | infeasible_diagnostic | 0.5994 | 0.0059 | 0.8894 |
| delay_reorder | delta | h600_d2 | infeasible_diagnostic | 0.6052 | 0.0115 | 0.8893 |
| ideal | delta | h600_d2 | infeasible_diagnostic | 0.6720 | 0.0046 | 0.8894 |
| lossy | delta | h600_d2 | infeasible_diagnostic | 0.6003 | 0.0066 | 0.8893 |
| burst_outage | edge_events | h16_d1 | infeasible_diagnostic | 0.9615 | 0.0069 | 0.9694 |
| delay_reorder | edge_events | h16_d1 | infeasible_diagnostic | 0.9797 | 0.0068 | 0.9695 |
| ideal | edge_events | h16_d1 | infeasible_diagnostic | 1.0000 | 0.0000 | 0.9694 |
| lossy | edge_events | h16_d1 | infeasible_diagnostic | 0.9358 | 0.0067 | 0.9694 |
| burst_outage | full | h16_d1 | infeasible_diagnostic | 0.7269 | 0.0077 | 0.0000 |
| delay_reorder | full | h16_d1 | infeasible_diagnostic | 0.9462 | 0.0131 | 0.0000 |
| ideal | full | h16_d1 | infeasible_diagnostic | 1.0000 | 0.0000 | 0.0000 |
| lossy | full | h16_d1 | infeasible_diagnostic | 0.9468 | 0.0080 | 0.0000 |
| burst_outage | periodic | h600_d1 | infeasible_diagnostic | 0.8544 | 0.0045 | 0.9721 |
| delay_reorder | periodic | h600_d1 | infeasible_diagnostic | 0.8858 | 0.0071 | 0.9718 |
| ideal | periodic | h600_d1 | infeasible_diagnostic | 0.8799 | 0.0044 | 0.9721 |
| lossy | periodic | h600_d1 | infeasible_diagnostic | 0.8363 | 0.0046 | 0.9719 |
| burst_outage | stateful | h32_d1 | infeasible_diagnostic | 0.9834 | 0.0220 | -0.1761 |
| delay_reorder | stateful | h32_d1 | infeasible_diagnostic | 0.9869 | 0.0224 | -0.1758 |
| ideal | stateful | h32_d1 | infeasible_diagnostic | 1.0000 | 0.0000 | -0.1761 |
| lossy | stateful | h32_d1 | infeasible_diagnostic | 0.9908 | 0.0217 | -0.1764 |
| burst_outage | threshold | h600_d1 | infeasible_diagnostic | 0.8081 | 0.0079 | 0.9653 |
| delay_reorder | threshold | h600_d1 | infeasible_diagnostic | 0.8233 | 0.0154 | 0.9652 |
| ideal | threshold | h600_d1 | infeasible_diagnostic | 0.8367 | 0.0000 | 0.9653 |
| lossy | threshold | h600_d1 | infeasible_diagnostic | 0.7905 | 0.0080 | 0.9652 |

The other target (99%), 16/180-second deadlines, explicit opportunity counts, unwanted-action counts, receiver contract counters, latency, and all settings are in the local CSV outputs. A coverage deficit is not repaired by post-hoc threshold adjustment.

## Paired controller-state comparison

Stateful minus each baseline, with two-sided 95% source-day bootstrap intervals. These compare validation-selected operating points, not identical achieved coverage or bandwidth. They do not establish equivalence or superiority on their own.

| target | network | baseline | coverage_difference | ci_low | ci_high |
| --- | --- | --- | --- | --- | --- |
| 0.9500 | burst_outage | threshold | 0.1753 | 0.1220 | 0.2412 |
| 0.9500 | burst_outage | edge_events | 0.0218 | 0.0138 | 0.0305 |
| 0.9500 | delay_reorder | threshold | 0.1637 | 0.1118 | 0.2286 |
| 0.9500 | delay_reorder | edge_events | 0.0073 | 0.0016 | 0.0184 |
| 0.9500 | ideal | threshold | 0.1633 | 0.1189 | 0.2254 |
| 0.9500 | ideal | edge_events | 0.0000 | 0.0000 | 0.0000 |
| 0.9500 | lossy | threshold | 0.2003 | 0.1523 | 0.2664 |
| 0.9500 | lossy | edge_events | 0.0550 | 0.0487 | 0.0602 |
| 0.9900 | burst_outage | threshold | 0.1753 | 0.1213 | 0.2411 |
| 0.9900 | burst_outage | edge_events | 0.0218 | 0.0140 | 0.0300 |
| 0.9900 | delay_reorder | threshold | 0.1637 | 0.1089 | 0.2365 |
| 0.9900 | delay_reorder | edge_events | 0.0073 | 0.0015 | 0.0181 |
| 0.9900 | ideal | threshold | 0.1633 | 0.1215 | 0.2228 |
| 0.9900 | ideal | edge_events | 0.0000 | 0.0000 | 0.0000 |
| 0.9900 | lossy | threshold | 0.2003 | 0.1511 | 0.2652 |
| 0.9900 | lossy | edge_events | 0.0550 | 0.0481 | 0.0605 |

## Measured protocol implementation

Two actual processes exchanged 1,000 acknowledged UDP sample messages on local loopback after 100 warm-up messages. Median RTT: 0.0109 ms; p95: 0.0112 ms; p99: 0.0141 ms. Application payload plus acknowledgment bytes: 75675. Network impairments in the trace benchmark are **simulated**, not measured radio behavior. The loopback probe is a separate implementation measurement; its ACK traffic is not silently included in the one-way replay protocol.

## Interpretation boundaries

The full-stream reference is a specified software controller, not historical actuator ground truth. The source trajectory is unchanged by replayed commands. All senders observe all locally available measurements: savings concern communication, not sensing energy. Policy payloads use compact JSON; wire-byte accounting adds a modeled 28-byte IPv4/UDP header and counts duplicate copies, but excludes link-layer overhead, encryption, retransmissions, and connection management. Alternative encodings may alter the tradeoff.

All primary traces and large outputs remain local. The protocol is documented in [PROTOCOL.md](PROTOCOL.md). Reproduce with `docker compose run --rm -T project-shell make telemetry-feasibility`.
