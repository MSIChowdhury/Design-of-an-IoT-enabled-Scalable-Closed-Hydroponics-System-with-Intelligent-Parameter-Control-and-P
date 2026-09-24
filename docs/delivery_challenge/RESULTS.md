# Frozen command-delivery challenge results

The candidate passed the 95% coverage / 1% undesirable-command **point criteria in 16/25 scenarios**. Its marginal 95% intervals lie entirely within both limits in 4/25 scenarios. These are per-scenario intervals, not simultaneous guarantees over the suite.

No settings were tuned on these results. Candidate and simple repetition both use two transmissions 32 seconds apart, original 64-second expiry, the identical receiver, and a 600-second cooldown. The candidate additionally sends cancellation; the acknowledged comparator adds receipt ACKs. Clock-offset and restart scenarios deliberately violate the current implementation assumptions.

## Operating boundary (candidate)

Fractions below are coverage and undesirable commands per reference opportunity. Bytes include all offered command/cancellation/ACK payloads plus 28-byte IPv4/UDP headers, including lost traffic. Extra bytes compare with the same-receiver plain repetition baseline. Structural violation counts cover the entire replay, including warm-up/tail, and are separate from opportunity-based scoring.

| scenario | coverage | coverage_low | coverage_high | error | error_low | error_high | extra_bytes_pct | repeated_outputs | expired_outputs | cooldown_violations | point_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| asymmetric | 0.9840 | 0.9770 | 0.9908 | 0.0059 | 0.0024 | 0.0099 | 0.3517 | 0 | 0 | 0 | True |
| clock_+16 | 0.9856 | 0.9788 | 0.9922 | 0.0065 | 0.0022 | 0.0111 | 0.3517 | 0 | 0 | 0 | True |
| clock_+64 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.3517 | 0 | 0 | 0 | False |
| clock_-16 | 0.9879 | 0.9817 | 0.9942 | 0.0088 | 0.0036 | 0.0146 | 0.3517 | 0 | 44 | 0 | True |
| clock_-64 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.3517 | 0 | 0 | 0 | False |
| correlated_192 | 0.8896 | 0.8654 | 0.9120 | 0.0057 | 0.0017 | 0.0097 | 0.3517 | 0 | 0 | 0 | False |
| correlated_32 | 0.9561 | 0.9446 | 0.9669 | 0.0062 | 0.0018 | 0.0108 | 0.3517 | 0 | 0 | 0 | True |
| correlated_96 | 0.9136 | 0.8973 | 0.9331 | 0.0055 | 0.0016 | 0.0096 | 0.3517 | 0 | 0 | 0 | False |
| delay_tail | 0.7330 | 0.7085 | 0.7515 | 0.0044 | 0.0014 | 0.0076 | 0.3517 | 0 | 0 | 0 | False |
| ideal | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.3517 | 0 | 0 | 0 | True |
| iid_10 | 0.9763 | 0.9672 | 0.9844 | 0.0053 | 0.0020 | 0.0087 | 0.3517 | 0 | 0 | 0 | True |
| iid_20 | 0.9443 | 0.9312 | 0.9589 | 0.0050 | 0.0019 | 0.0083 | 0.3517 | 0 | 0 | 0 | False |
| outage_128_phase_0 | 0.9676 | 0.9599 | 0.9756 | 0.0059 | 0.0021 | 0.0100 | 0.3517 | 0 | 0 | 0 | True |
| outage_128_phase_1733 | 0.9621 | 0.9500 | 0.9716 | 0.0061 | 0.0019 | 0.0106 | 0.3517 | 0 | 0 | 0 | True |
| outage_128_phase_317 | 0.9575 | 0.9463 | 0.9685 | 0.0063 | 0.0022 | 0.0106 | 0.3517 | 0 | 0 | 0 | True |
| outage_256_phase_0 | 0.9417 | 0.9310 | 0.9530 | 0.0049 | 0.0005 | 0.0093 | 0.3517 | 0 | 0 | 0 | False |
| outage_256_phase_1733 | 0.9367 | 0.9169 | 0.9515 | 0.0055 | 0.0021 | 0.0092 | 0.3517 | 0 | 0 | 0 | False |
| outage_256_phase_317 | 0.9173 | 0.8966 | 0.9344 | 0.0062 | 0.0022 | 0.0105 | 0.3517 | 0 | 0 | 0 | False |
| outage_32_phase_0 | 0.9870 | 0.9808 | 0.9933 | 0.0065 | 0.0019 | 0.0114 | 0.3517 | 0 | 0 | 0 | True |
| outage_32_phase_1733 | 0.9870 | 0.9809 | 0.9933 | 0.0065 | 0.0020 | 0.0114 | 0.3517 | 0 | 0 | 0 | True |
| outage_32_phase_317 | 0.9870 | 0.9810 | 0.9931 | 0.0065 | 0.0022 | 0.0107 | 0.3517 | 0 | 0 | 0 | True |
| outage_64_phase_0 | 0.9801 | 0.9727 | 0.9871 | 0.0062 | 0.0017 | 0.0108 | 0.3517 | 0 | 0 | 0 | True |
| outage_64_phase_1733 | 0.9789 | 0.9702 | 0.9870 | 0.0065 | 0.0023 | 0.0111 | 0.3517 | 0 | 0 | 0 | True |
| outage_64_phase_317 | 0.9775 | 0.9680 | 0.9857 | 0.0065 | 0.0024 | 0.0109 | 0.3517 | 0 | 0 | 0 | True |
| restart_hourly | 0.9875 | 0.9816 | 0.9938 | 0.0063 | 0.0017 | 0.0110 | 0.3517 | 111 | 0 | 840 | True |

## Does cancellation add value?

Cancellation's paired error-difference interval excludes zero in the favorable direction in **4/25 scenarios**. This count is descriptive and unadjusted for multiple comparisons. Do not infer equivalence from intervals containing zero, or general superiority from selected favorable rows. Coverage and byte costs must also be considered.

| scenario | baseline | metric | difference | low | high |
| --- | --- | --- | --- | --- | --- |
| asymmetric | plain_repetition | coverage | 0.0001 | 0.0000 | 0.0006 |
| asymmetric | plain_repetition | error | -0.0009 | -0.0019 | 0.0000 |
| clock_+16 | plain_repetition | coverage | 0.0000 | 0.0000 | 0.0000 |
| clock_+16 | plain_repetition | error | -0.0006 | -0.0016 | 0.0000 |
| clock_+64 | plain_repetition | coverage | 0.0000 | 0.0000 | 0.0000 |
| clock_+64 | plain_repetition | error | 0.0000 | 0.0000 | 0.0000 |
| clock_-16 | plain_repetition | coverage | 0.0000 | 0.0000 | 0.0000 |
| clock_-16 | plain_repetition | error | -0.0006 | -0.0015 | 0.0000 |
| clock_-64 | plain_repetition | coverage | 0.0000 | 0.0000 | 0.0000 |
| clock_-64 | plain_repetition | error | 0.0000 | 0.0000 | 0.0000 |
| correlated_192 | plain_repetition | coverage | 0.0000 | 0.0000 | 0.0000 |
| correlated_192 | plain_repetition | error | -0.0008 | -0.0018 | 0.0000 |
| correlated_32 | plain_repetition | coverage | 0.0002 | 0.0000 | 0.0008 |
| correlated_32 | plain_repetition | error | -0.0009 | -0.0020 | -0.0001 |
| correlated_96 | plain_repetition | coverage | 0.0000 | 0.0000 | 0.0000 |
| correlated_96 | plain_repetition | error | -0.0006 | -0.0015 | 0.0000 |
| delay_tail | plain_repetition | coverage | 0.0000 | 0.0000 | 0.0000 |
| delay_tail | plain_repetition | error | -0.0012 | -0.0023 | -0.0002 |
| ideal | plain_repetition | coverage | 0.0000 | 0.0000 | 0.0000 |
| ideal | plain_repetition | error | 0.0000 | 0.0000 | 0.0000 |
| iid_10 | plain_repetition | coverage | 0.0001 | 0.0000 | 0.0006 |
| iid_10 | plain_repetition | error | -0.0012 | -0.0026 | -0.0002 |
| iid_20 | plain_repetition | coverage | 0.0004 | 0.0000 | 0.0010 |
| iid_20 | plain_repetition | error | -0.0015 | -0.0030 | -0.0003 |
| outage_128_phase_0 | plain_repetition | coverage | 0.0000 | 0.0000 | 0.0000 |
| outage_128_phase_0 | plain_repetition | error | -0.0005 | -0.0013 | 0.0000 |
| outage_128_phase_1733 | plain_repetition | coverage | 0.0000 | 0.0000 | 0.0000 |
| outage_128_phase_1733 | plain_repetition | error | -0.0004 | -0.0010 | 0.0000 |
| outage_128_phase_317 | plain_repetition | coverage | 0.0000 | 0.0000 | 0.0000 |
| outage_128_phase_317 | plain_repetition | error | -0.0004 | -0.0014 | 0.0000 |
| outage_256_phase_0 | plain_repetition | coverage | 0.0002 | 0.0000 | 0.0009 |
| outage_256_phase_0 | plain_repetition | error | -0.0007 | -0.0016 | 0.0000 |
| outage_256_phase_1733 | plain_repetition | coverage | 0.0000 | 0.0000 | 0.0000 |
| outage_256_phase_1733 | plain_repetition | error | -0.0004 | -0.0013 | 0.0000 |
| outage_256_phase_317 | plain_repetition | coverage | 0.0000 | 0.0000 | 0.0000 |
| outage_256_phase_317 | plain_repetition | error | -0.0004 | -0.0014 | 0.0000 |
| outage_32_phase_0 | plain_repetition | coverage | 0.0000 | 0.0000 | 0.0000 |
| outage_32_phase_0 | plain_repetition | error | -0.0006 | -0.0016 | 0.0000 |
| outage_32_phase_1733 | plain_repetition | coverage | 0.0000 | 0.0000 | 0.0000 |
| outage_32_phase_1733 | plain_repetition | error | -0.0006 | -0.0016 | 0.0000 |
| outage_32_phase_317 | plain_repetition | coverage | 0.0000 | 0.0000 | 0.0000 |
| outage_32_phase_317 | plain_repetition | error | -0.0006 | -0.0015 | 0.0000 |
| outage_64_phase_0 | plain_repetition | coverage | 0.0001 | 0.0000 | 0.0004 |
| outage_64_phase_0 | plain_repetition | error | -0.0008 | -0.0018 | 0.0000 |
| outage_64_phase_1733 | plain_repetition | coverage | 0.0000 | 0.0000 | 0.0000 |
| outage_64_phase_1733 | plain_repetition | error | -0.0006 | -0.0016 | 0.0000 |
| outage_64_phase_317 | plain_repetition | coverage | 0.0000 | 0.0000 | 0.0000 |
| outage_64_phase_317 | plain_repetition | error | -0.0006 | -0.0016 | 0.0000 |
| restart_hourly | plain_repetition | coverage | 0.0000 | 0.0000 | 0.0000 |
| restart_hourly | plain_repetition | error | -0.0006 | -0.0015 | 0.0000 |

## Assumption counterexamples

- Restart followed by the same command ID executes it again: **True**. Volatile duplicate protection and cooldown are lost.
- A -64-second receiver clock offset permits a command arriving at true time 96 seconds to execute at receiver time 32 seconds despite its 64-second lifetime: **True**.

These deterministic counterexamples demonstrate failure modes, not their frequency in a deployment. No automatic recovery or persistence fix was added after seeing the challenge.

## Actual two-container UDP execution

| scenario | policy | opportunities | coverage | undesirable_fraction | sent_udp_bytes | ack_bytes | processing_p99_us | tick_lateness_p99_ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ideal | candidate | 9 | 1.0000 | 0.0000 | 3518 | 0 | 40.9610 | 0.0611 |
| ideal | plain_repetition | 9 | 1.0000 | 0.0000 | 3418 | 0 | 40.2439 | 0.0634 |
| ideal | acknowledged | 9 | 1.0000 | 0.0000 | 1943 | 1602 | 41.4070 | 0.0626 |
| iid_10 | candidate | 9 | 0.4444 | 0.2222 | 2923 | 0 | 38.1300 | 0.0603 |
| iid_10 | plain_repetition | 9 | 0.4444 | 0.2222 | 2823 | 0 | 27.5182 | 0.0566 |
| iid_10 | acknowledged | 9 | 0.4444 | 0.2222 | 2923 | 2464 | 27.3193 | 0.0590 |
| delay_tail | candidate | 9 | 0.0000 | 0.1111 | 3518 | 0 | 43.2360 | 0.0641 |
| delay_tail | plain_repetition | 9 | 0.0000 | 0.1111 | 3418 | 0 | 36.0110 | 0.0633 |
| delay_tail | acknowledged | 9 | 0.0000 | 0.1111 | 3518 | 2932 | 32.8680 | 0.0710 |
| asymmetric | candidate | 9 | 0.4444 | 0.2222 | 3041 | 0 | 38.7294 | 0.0632 |
| asymmetric | plain_repetition | 9 | 0.4444 | 0.2222 | 2941 | 0 | 44.1584 | 0.0655 |
| asymmetric | acknowledged | 9 | 0.4444 | 0.2222 | 3041 | 2553 | 31.2290 | 0.0537 |
| correlated_96 | candidate | 9 | 0.4444 | 0.2222 | 3518 | 0 | 39.4580 | 0.0612 |
| correlated_96 | plain_repetition | 9 | 0.4444 | 0.2222 | 3418 | 0 | 34.4408 | 0.0607 |
| correlated_96 | acknowledged | 9 | 0.4444 | 0.2222 | 3518 | 2930 | 30.7623 | 0.0609 |

The probe uses six historical windows selected before execution for maximum direction changes among fixed windows with a reference command. This is a purposive execution check, not a random or independent sample of the deployment. Sender and receiver run in separate Docker containers with actual UDP datagrams on a bridge network. A client-side application relay applies seeded delay and loss; this is not kernel netem or radio testing. Logical time runs 1000x faster; receiver ticks occur eight logical seconds after source ticks. Actual OS scheduling and datagram processing can therefore affect command outcomes. Forward sent UDP bytes exclude packets dropped before the socket; simulated offered bytes include them. Reverse packets traverse the socket before relay impairment. No energy or physical-actuator claims follow.

Receiver peak RSS range: 102.7–102.7 MiB. This includes Python/import overhead and is the process-lifetime high-water mark, not isolated protocol memory. Detailed timing, CPU, byte counters, environment, and action logs are saved with the CSV outputs.

## Evidence limits and reproduction

This is a frozen **new network challenge on previously reused historical sensor periods**. It is not independent physical replication or a newly untouched sensor dataset. Four new network seeds are paired across methods; all six sensors share exogenous network conditions. Crossed day/seed bootstrap resamples days and network seeds independently, retaining all sensors and paired policies together (1,000 replicates). Only four network seeds limit tail uncertainty; no distribution-free bound is claimed. Repeated seeds do not add physical deployments. All 25 scenarios and all comparator results remain in `summary.csv`; no failed scenario is discarded.

See [PROTOCOL.md](PROTOCOL.md) for the frozen design and reproduction command. Machine-readable outputs are under `results/metrics/delivery_challenge/`; plots are under `results/figures/delivery_challenge/`. The frozen manifest hashes source, configuration, and dataset before execution.
