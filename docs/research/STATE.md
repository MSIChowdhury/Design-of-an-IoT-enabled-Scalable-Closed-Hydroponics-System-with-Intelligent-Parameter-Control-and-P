# Research state: 12 November 2026

The reproducible draft package concerns a deployment-specific fault-to-authorization
audit. The full user objective remains incomplete. A third consecutive evidence-gap
audit now supports blocked status; see [the stopping audit](STOPPING_AUDIT.md).
Neither Q1 publication readiness nor whole-repository inspection is established.

## Current evidence

The public experiment-2 sensor log contains 121,244 rows with no missing cells,
duplicate rows, duplicate timestamps or duplicate entry IDs. Missing *time*
remains substantial: 194 gaps over 120 s account for about 23% of elapsed time.
Zero missing CSV cells therefore does not mean complete deployment coverage.
The newly accessible `data/Actual/feeds.csv` is exactly the same observations
after four header aliases and UTC normalization; it is not independent evidence.
The authors authorized publication of the already tracked sensor and harvest
files. The additional local copy is left untracked and unchanged. Third-party
data remain local under their respective permissions. Independent actuator,
reference-measurement and water-level-calibration files are absent.

Cycle 1 reproduced every processed row and both deterministic manuscript audit
tables exactly, without modifying original artifacts. See
[the protocol](CYCLE_01_PROTOCOL.md), [report](reproduction/report.json), and
[attempts](attempts.csv). The first reproduction launcher failed at an import
before executing the audit; its correction changed only the launcher. All 176
then-present tests passed. Initial lint failed on an existing root-owned cache;
`--no-cache` passed. Both failures are retained, not treated as scientific results.

Cycle 2 executed its declared pilot and full grid: 1,620 attribution cells,
including repeated control cells, from one log. Its broad zero-pH-flag prediction
was falsified. Range plus persistence produced 0--3 flagged-source pH commands;
54 of 108 pH attribution cells were nonzero. EC remained zero. Compared with
naive at the same timing and attribution definition, flagged command counts fell
98.1--100% for pH and 87.1--99.7% for CO2. These count reductions coexist with
substantial authorization loss and cannot identify physical benefit. The full
grid took 14.0 s; no settings were selected or suppressed after seeing results.
See [the protocol](CYCLE_02_PROTOCOL.md) and [all cells](sensitivity/full_cells.csv).

Cycle 3 reran the frozen controlled comparison and its separately labelled
post-hoc follow-up into an isolated output directory. All eight follow-up CSVs
and three recomputed table CSVs agreed to the declared 1e-12 tolerance; the
original summary, selections and windows also passed their reproduction checks.
The run took 363.9 s with 1.11 GiB peak process RSS. Original locked/follow-up
artifacts and method/configuration hashes remained unchanged. See
[the protocol](CYCLE_03_PROTOCOL.md) and [report](controlled_reproduction.json).
This reproduces the negative overall comparison, not independent validation.

## Contribution and selection

The strongest present question is how actuator direction, held-source provenance
and supervisor timing change reconstructed commands in an observed deployment.
The project does not establish a better detector. Locked LiveGate failed its
overall criterion; the added direct baselines remain post-hoc. The skeptical
[review](REVIEW_2026-11-12.md) identified nearby hydroponic FDD from 2003 and
2025 and CEA residual FDI from 2026. The manuscript now acknowledges this prior
work and narrows its gap. The final source-description check also found that
the legacy comparator omits alpha-dependent actuation bands and substitutes
elapsed persistence on held estimates. It is now labelled a legacy-gate proxy.
The common 600 s cooldown is documented for pH/EC dosing; its extension to
CO2/cooling is a replay assumption. Its counts cannot recover verified
firmware behavior. Only prose/docstrings and the figure label changed; frozen
numerical outputs and algorithm logic were preserved. Citation metadata and access limits are recorded in
`literature_metadata.json`, `reviewer_literature.csv` and `reviewer_search_log.csv`.
No absence of a correction or retraction is guaranteed by an unsuccessful search.

Distinct alternatives are tracked in [the backlog](hypotheses.csv), including
communication/recovery software, agronomic causality and sensor liveness. A
reviewer completed the historical source/results comparison before final ranking.
Durable mock-ledger recovery is genuine software evidence but does not establish
new physical exactly-once execution or a novel general RPC principle.

## Literature and reference-data follow-up

The next goal turn revalidated the pushed worktree and classified the preceding
turn as progress. The reviewer then read the complete Ferentinos 2003 and
SensorTalk scientific texts and traced directly relevant predecessors. The
manuscript now explicitly acknowledges actuator-input diagnosis, reference
routing during calibration, and the 2003 Biosystems Engineering supervisor.
The nutrient-recycling citation now identifies its editorial article type.
The [separate follow-up review](LITERATURE_FOLLOWUP_2026-11-12.md) preserves the
original access history and distinguishes full text from excerpts and new leads.

All 23 active bibliography DOIs now have retrieved Crossref metadata, including
the separately checked new companion citation. No update links were registered
in the checked records. Crossmark explicitly reported the two recent nearest
papers current at access time; this resolves an ambiguous secondary badge, not
all possible correction/retraction uncertainty. SensorTalk's version history
does disclose a revised 2019 version without an explained change list.

A government-hosted JCR 2024 export adds explicit JIF categories/quartiles for
all three shortlisted journals. Relevant rows were visually checked on pages
3 and 137, not all 785 pages. This establishes the stated historical edition;
latest authenticated JCR/SCImago access remains unavailable. The shortlist keeps
database, year, category and source limitations separate.

A newly located 2024 study links public 2022 chamber data with a separate
environmental reference. It is a conditional independent-data candidate, so
the evidence gap must not be described as absence of all public hydroponic data.
Under a timestamped [eligibility screen](CYCLE_04_ELIGIBILITY.md), three small
firmware sources, timestamp expressions and three T1 headers were inspected.
No numerical sensor/reference outcomes were read or scored; T2--T4 remain
unopened. The checked metadata do not establish reference clock/calibration
bounds, and the environmental reference does not cover pH/EC. The
[screening decision](REFERENCE_CANDIDATE_SCREEN.md) records the contract and
parser/provenance issues that must be resolved before a confirmation protocol.
No new independent confirmation is claimed from a file tree or header.

## Coverage and remaining work

The initial inventory recorded 3,350 hashed accessible files (6.34 GB), with
explicit credential/cache exclusions. `inventory.csv` and its timestamped
summary contain the refreshed package snapshot. Hashing is not reading.
`coverage.csv` and `reviewer_coverage.csv` identify actual inspection depth. New
research records and isolated reproduction outputs are included in the refresh.
Unreviewed files stay unreviewed; generated traces and binary assets require
appropriate metadata, sampling and visual inspection rather than false claims
of line-by-line reading. The review is not exhaustive literature coverage.

The subsequent full reviewer pass covers all 33 current source modules, 26 test
files, 28 configurations and 77 scripts, plus the existing study reports and
small result tables. Its 349-row ledger distinguishes full reads, proven
identical archived copies, complete diffs and partial reads. All 13 notebook
source/markdown extracts and both historical manuscript PDF texts were read;
notebook outputs were catalogued but not reproduced. The raw-data profile now
covers 79 CSV/CSV.gz files: 53 parsed datasets and 26 unavailable Git LFS
pointers. The normalized harvest sheet has 63 unique plant records; experiment
2 has seven plants per treatment, and its recorded fresh-mass means/SDs agree
with the current manuscript. Wide-sheet blank/header rows are formatting, not
duplicate plants.

Read-only metadata inspection covers 952 binary assets, including every local
SQLite table's row count. It does not establish full journal-content integrity,
CAD geometry, model validity or physical execution. Ten larger historical
tables received explicitly partial inspection; large traces/ledgers, vendor
sources, and portions of generic writing guides remain outside full-content
reading. These limits are not hidden behind the inventory count. The author
PDF (26 pages) and blinded PDF (25 pages) were built and visually inspected;
the final bibliography and proxy-description changes were re-rendered and checked. Poppler is
now installed by Dockerfile, and strict checks on both PDFs, all 178 tests and
lint pass in the rebuilt image. LaTeX underfull-box warnings remain but no
clipping/overlap was seen. See the final [requirements audit](REQUIREMENTS.csv).

## Stopping condition and next action

The user-requested scientific completion standard is not met. The stronger
predeclared zero-pH prediction failed, the narrower descriptive envelope is
post-hoc, independent confirmation is absent, and distinct Q1-level novelty
remains unestablished. The alternative feed supplies no new observations, and
the available external benchmarks cannot establish hydroponic physical effects.
The reviewer explicitly reached the same conclusion. Additional replay or
retuning on these backgrounds would not close that evidence gap.

The initial goal turn made substantive progress, including executed reproduction,
an informative falsification, revised manuscript, package verification, and
coverage records. The following turn closed literature/metadata gaps, revised
the manuscript and screened a new public source without opening its outcomes.
The third consecutive goal turn revalidated the same missing reference/physical
evidence contract. No new data files or reference/actuator logs appeared; the
public candidate's pinned commit and all frozen numerical artifacts remained
unchanged, and no process is running. The [stopping audit](STOPPING_AUDIT.md)
records why further local replay cannot meet the independent-confirmation
requirement and supports marking the goal blocked, not complete or paused.
Resume when the required provenance or independently instrumented evidence is
available. Revalidate it and start a fresh blocked-audit sequence on resumption.
Do not restart or retune frozen methods, reuse revealed evaluation as confirmation,
or declare completion because the draft builds.

The minimum new physical evidence remains independently calibrated pH/EC
references, observed command/relay or delivered-volume records, and frozen
comparisons across independent benchtop sessions. No hardware purchase,
collection expense or submission is authorized or performed.

The verified scientific package is committed and pushed; see [delivery verification](DELIVERY.json). The untracked user input remains unchanged. GitHub reported 20 dependency alerts during push (10 high, 8 moderate, 2 low); they were not triaged in this research cycle and are not asserted to be independently confirmed vulnerabilities.
