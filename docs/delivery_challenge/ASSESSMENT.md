# Assessment of the frozen challenge

The challenge was completed without changing the frozen candidate or tuning on its results. It supports a limited cancellation benefit and exposes failures that prevent a broad robustness claim.

## Main findings

| Question | Observed result |
| --- | --- |
| Does the candidate pass the original point targets everywhere? | No: 16 of 25 scenarios pass. Restricting to the 20 scenarios without clock/restart assumption violations, 13 pass. |
| Do uncertainty bounds support those thresholds everywhere? | No: only 4 of 25 scenarios have marginal 95% intervals wholly within both limits. These are not simultaneous guarantees. |
| Does plain repetition perform similarly? | It passes the same 16 point criteria; only 1 scenario has both intervals within the limits. This difference in interval classifications is not itself a significance test. |
| Does cancellation reduce undesirable commands? | Point reductions are 0–0.145 percentage points, costing 0.352% more offered bytes than plain repetition. Four of 25 paired error intervals exclude zero favorably, without multiple-comparison adjustment. |
| Does cancellation materially improve coverage? | Differences from plain repetition range from 0 to 0.0363 percentage points. |
| Do acknowledgments rescue the failing scenarios? | No: the acknowledged comparator also passes 16 point criteria and 4 interval criteria. |

The candidate's coverage is 97.63% with 10% independent packet loss, but 94.43% with 20% independent loss. Correlated outages with mean bad runs of 96 and 192 seconds reduce coverage to 91.36% and 88.96%. The long-delay scenario gives 73.30% coverage. Hourly 256-second outages give 91.73%–94.17%, depending on phase. All three fixed policies encounter these limitations.

## Event-quality metrics miss structural failures

With hourly receiver restarts, the candidate still reports 98.75% coverage and 0.63% undesirable commands per reference opportunity, yet emits **111 repeated commands and 840 cooldown violations** across the four-seed, six-sensor replay. These are replay counts, not unique physical events. Restart erases the receiver's volatile high-water mark and lockout state.

A clock 16 seconds behind produces **44 truly expired outputs**, despite point coverage/error metrics passing. Clock offsets of either sign with magnitude 64 seconds suppress all scored actions in these particular traces. The separate directed counterexample shows that a clock behind can also accept a truly expired command when its first arrival is sufficiently delayed. Clock-related behavior depends on arrival timing; suppression is not a general safety guarantee.

Therefore a “point pass” in the results table is only a coverage/error pass. It does not certify expiry, duplicate, or cooldown correctness under violated assumptions.

## The real network check is unfavorable too

The two-container UDP probe ran all 15 policy/scenario combinations on six prespecified change-heavy historical windows. Each combination had only **nine eligible reference events**, so fractions are descriptive, not deployment performance estimates.

All policies matched 9/9 events without impairment. With the configured independent loss plus delay, asymmetric link, or correlated loss plus delay, each matched 4/9 with two undesirable commands. Under the delay-tail profile each matched 0/9 with one undesirable command. Receiver message-processing p99 was approximately 27–44 microseconds; process-lifetime peak RSS was approximately 103 MiB including Python/import overhead. Fast software processing did not prevent decision failures when messages arrived after the supporting conditions changed.

An additional offline audit replayed the same selected windows with the challenge model and reproduced the candidate's matched/error counts for all five profiles (9/0, 4/2, 0/1, 4/2, 4/2). This supports consistency of the execution probe; it does not make its nine events representative. Real socket scheduling, the half-tick receiver phase, and accelerated time remain stated limitations.

## Publication consequence

These results do not justify marketing the current protocol as universally robust or claiming a substantial new algorithmic advantage over plain repetition. The most defensible current contribution is an empirical study of command validity, retransmission, cancellation, and their operating limits on retrospective hydroponic workloads.

A subsequent engineering revision would need to preserve duplicate/cooldown state across restart and specify an enforceable clock/expiry contract. Treat that as a new version, with new challenge realizations and explicit state-loss/clock-failure tests; do not overwrite this frozen result. Cancellation may remain useful, but its small observed gain should not carry the entire novelty claim.

See [full results](RESULTS.md), [frozen protocol](PROTOCOL.md), and the generated operating-boundary figure under `results/figures/delivery_challenge/`.
