# Research audit cycle 2: timing and flag sensitivity

Frozen at 2026-11-12 21:25:37 UTC, before pilot or full-grid execution.
This is a post-hoc robustness study of already revealed data. It is not a new
independent validation, a detector search, or an extension of frozen LiveGate.

## Hypothesis and competing explanation

H-AUDIT: The observed zero flagged-source pH/EC authorizations with range plus
32 s persistence is robust across plausible supervisor timing and descriptive
spike definitions in this one deployment. Prediction: the range-plus-persistence
arm retains zero pH/EC flagged-source counts throughout the declared grid.
Any nonzero cell falsifies that strong prediction; report its parameters and
narrow the claim. Even zero throughout would not establish physical fault
prevention, correct dosing, or transfer to other logs.

Competing explanation: zero counts arise from one favorable phase of the
cooldown and persistence relative to the flagged readings, or from an arbitrary
eight-scale spike definition. Held-reading age can reschedule commands too.
Out-of-range rejection alone is structurally guaranteed by a range gate and
does not establish novelty or correct classification of in-range faults.

## Design

Use the reproduced public processed log, all 121,244 rows and five actuated
channels. Exclude uncalibrated Water_Level and unactuated humidity from command
analysis. Preserve each channel's executable directions and deployed setpoints,
reset persistence/held values across gaps over 120 s, and preserve cooldown
across gaps using the existing shared implementation. No injected faults and
no changes to measured values, gate fitting, or LiveGate outputs.

Arms: naive, range only, and range plus persistence. Persistence is 16/32/64/96 s
for the third arm and zero for the first two. Maximum held age is 32/64/128 s;
cooldown is 300/600/1200 s. Descriptive spike cutoff is 6/8/10 times the existing
robust scale, with the existing centred nine-sample median and fallback scale.
Cutoffs alter attribution only, not any online gating decision. A reading is
attributed to exactly one category: out of range, physical bound, or in-range
non-bound spike. A flagged reading is not an independently diagnosed failure.

Pilot: all five channels, persistence 32 s, hold 64 s, all three cooldowns and
three spike definitions. If the original 32/64/600/8 cell does not reproduce,
stop and investigate. If a complete run is projected below 10 CPU-minutes from
the pilot, execute the entire grid with the unchanged script. Resource-only
decision; neither a favorable nor an unfavorable pilot result changes the grid.

## Outcomes, analysis and stopping

Primary outcome: the complete range of flagged-source pH/EC counts for the
range-plus-persistence arm, including all cells that falsify zero. Secondary:
separate flag-category counts, total counts, flagged fractions, and retained
authorization counts relative to naive at the same timing. Retention is not
useful-command coverage because independent reference opportunities are absent.
CO2 and cooling-channel results describe controller-specific boundaries.

Report every cell (including duplicate negative-control cells) and minima/maxima
by sensor/arm. No winner selection, significance testing or synthetic inflation
of sample size. The sample is the entire available log from one deployment;
the sensitivity cells are deterministic scenarios, not independent replicates.
No confidence interval can turn them into a population of deployments. Preserve
the original result, pilot, full results, runtime, hashes, and any failures.
Stop after this grid and skeptical review; revise or narrow the manuscript
using the observed envelope, then refresh the literature and backlog.
