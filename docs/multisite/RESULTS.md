# Multi-site fault-to-actuation replication: results

Single run of `scripts/74_multisite_audit.py` (commit 7429fcb) under the
protocol frozen at commit 1a8281d (`PROTOCOL.md`, SHA-256 17d6de0f…4275).
Runtime 71 s in Docker. Tables: `results/multisite/`. Post-hoc diagnostics
(`scripts/75_multisite_posthoc.py`) are labelled as such and change no
frozen output.

## Headline

**The pre-registered replication criterion failed.** In S1 (Pompeo chamber), "range
check + 2-sample persistence" met the criterion (>= 90 % cut in flagged-source
commands and >= 80 % retention of unflagged commands) in **1 of 8**
trial x channel cells. **6 cells failed and 1 could not be tested.** So the index paper's
practical recommendation does not transfer to this site as stated.

The failure has one dominant mechanism. At S1 the flagged readings that
drive nutrient dosing are mostly **EC = 0 bound readings**. A zero reading is
in range and persists, so persistence cannot reject it. The declared fourth arm
(range + persistence + bound rejection) removed most of them. That arm was
declared and reported, but the criterion was not pre-registered for it.

## E3: reconstruction validity (firmware replay vs logged requests)

- **EC: replay reproduced the logged nutrient requests in 100.000 % of rows**
  in every trial and line (one row of 277,844 differed in T3 line 1). Where a
  controller logs its requests and its rule is known, reconstruction is exact.
  This is direct evidence for the index audit's replay method.
- **pH: the documented rule (acid when pH > 5.85) did not reproduce the logs.**
  Agreement was 56.5–99.4 % per line, and only T2 passed >= 95 %. *Post-hoc:*
  18–52 % of logged acid doses occurred at a same-row pH <= 5.85, and pH > 5.85
  rows often had no dose. A whole-day dosing pause explains only part of
  this. The sketch's toggled comment blocks suggest that the firmware differed
  from the published sketch. Per protocol, pH replay (E4) is labelled **rule
  unverified**. The E2 pH counts remain valid because they use logged requests.

## E2: observed requests whose source reading was flagged

| Site / unit | Channel | Logged requests | Flagged source | Fraction [day-cluster 95 % CI] |
| --- | --- | ---: | ---: | --- |
| S1 T1 | EC | 9,355 | 22 | 0.24 % [0.00, 5.0] |
| S1 T2 | EC | 29,999 | 346 | 1.15 % [0.02, 3.8] |
| S1 T3 | EC | 110,276 | 5,003 | 4.54 % [0.06, 17.8] |
| S1 T4 | EC | 2,260 | 26 | 1.15 % [0.23, 2.9] |
| S1 T1–T4 | pH (acid) | 4,019 / 16,035 / 15,094 / 1,484 | 22 / 7 / 35 / 4 | 0.04–0.55 % |
| S2 6 compartments | CO2 dosing intervals | 26,752–34,539 each | 85–1,940 | 0.26–6.96 % (spike flags only) |

These are **observed, logged actuation requests**, not reconstructions. In S1 T3,
thousands of nutrient-dose requests were issued while the EC probe read exactly
0 µS/cm. Each request was 0.5 mL of nutrient A plus 1 mL of nutrient B in the
firmware. Delivered volume was not measured. The intervals are wide because
the zero readings cluster on a few days.

In S2 (commercial), **no CO2 reading was out-of-range or at a bound** in any
compartment. All of its flags are heuristic spikes. With 5-min sampling during
active dosing and venting, those spikes are plausibly real CO2 dynamics rather
than faults. S2 therefore does not show fault-driven dosing. It shows that the
hard-fault classes seen at the low-cost sites were absent from this commercial
installation.

## E4: gating replay (S1, site-native timing: 10 s sampling, no cooldown)

| Trial / channel | Naive flagged → range+persistence flagged | Unflagged retention | Verdict | + bound rejection: flagged (retention) |
| --- | --- | ---: | --- | --- |
| T1 EC | 22 → 12 (−45 %) | 86.6 % | failed | 5 (86.7 %) |
| T2 EC | 346 → 327 (−5 %) | 92.9 % | failed | 15 (93.0 %) |
| T3 EC | 5,003 → 4,953 (−1 %) | 97.8 % | failed | 70 (97.8 %) |
| T4 EC | 26 → 8 (−69 %) | **2.6 %** | failed | 8 (2.6 %) |
| T1 pH* | 23 → 13 | 98.3 % | failed | 13 |
| T2 pH* | 18 → 0 | 95.2 % | **replicated** | 0 |
| T3 pH* | 11 → 8 | 98.1 % | failed | 8 |
| T4 pH* | 4 → 0 | 96.8 % | not testable (< 10) | 0 |

\*pH rule unverified (E3). Retention for the bound-rejection arm is computed
from the table as (commands − flagged) / naive unflagged.

- With bound rejection, flagged-source EC commands fell by 77 %, 96 %, 99 %
  and 69 % (T1–T4). Retention stayed at 87–98 % except in T4.
- In T4 EC, 2-sample persistence removed 97 % of unflagged commands. EC sat
  near the 1100 µS/cm threshold, so naive dosing chattered on single-sample
  crossings. Whether removing that chatter is a cost or a benefit cannot be
  decided without delivered-volume or reference data. Under the frozen
  criterion it counts as a failure.
- The secondary 600 s cooldown left most cells not testable (< 10 flagged).

## E1: fault prevalence

- **S1, low-cost Atlas EZO:** EC bound (zero) readings in 0–0.45 % of samples
  per line, with every T3 line affected. pH out-of-range readings were absent,
  and pH spikes were rare. Flat-line runs of 1 h or more covered up to 2.8 % of
  samples (T4 line 3 pH). Logging gaps took 4.5–21 % of elapsed time, and
  5,302 of 932,127 rows (0.57 %) were excluded because NaN readings dropped a
  field. 21 files had no data rows.
- **S2, commercial:** CO2 had 0 out-of-range and 0 bound readings, with
  0.15 % missing in every compartment (a shared outage).
- **S3, low-cost ESP8266:** TDS had 1.09 % out-of-range readings; pH 0.04 %.
  *Gap and flat-line endpoints are not estimable.* Timestamps have minute
  resolution with ~10 rows per minute, so the declared "10 x median interval"
  rule degenerates (median interval 0 s). This is a protocol limitation found
  after the run; it is not repaired here. The spike counts are sample-based
  and unaffected.

## What this changes for the manuscript

1. **New supported claim:** at an independent site with logged requests, a
   naive low-cost controller **did** issue nutrient-dose requests from
   physically implausible (zero) EC readings, at up to 4.5 % of requests per
   trial. Where the rule could be verified, replay matched the logs exactly
   (EC).
2. **Claim to withdraw or narrow:** "range check plus short persistence
   removes flagged-source commands" did not replicate. Persistent bound or
   stuck readings defeat persistence at both sites (index CO2 ceiling, S1 EC
   zero). Bound rejection is what helped at both, at a site-dependent
   availability cost. That conclusion is post-hoc relative to the
   pre-registered criterion and must be presented that way.
3. **Contrast:** hard-fault classes (impossible, zero or full-scale) were
   present at all three low-cost sites and absent from the commercial site.
   That makes four sites and three countries, but the units within each site
   share apparatus and are not independent facilities.

Limits: delivered volume, reference measurements and crop effects are not
observed at any site. The S1 firmware may differ from the published sketch.
S1 has no declared licence, so raw rows are not redistributed. S2's dosing
logic is undocumented.
