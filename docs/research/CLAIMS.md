# Claim-to-evidence map

The manuscript's material contribution is a retrospective authorization audit.
Every physical or generalization claim below remains outside that scope.

| Claim | Authoritative evidence | Current judgment | Limit |
| --- | --- | --- | --- |
| Public log has 121,244 analyzed rows; supplied feeds.csv is a duplicate | `reproduction/report.json`, raw-file SHA-256 and full normalized comparison in script 72 | Reproduced | One deployment; timezone/header changes do not create independence |
| Original naive pH 655/125 and range-plus-persistence 417/0 total/flagged commands | `reproduction/deployment_audit.csv`, byte equality to current table, script 68 | Reproduced | Reconstructed commands; bound/spike flags are not confirmed faults |
| Original naive CO2 2149/219 and range-plus-persistence 456/9 | Same deterministic table and executable-direction tests | Reproduced | Raise-only actuator; no measured command or dose record |
| Legacy proxy counts reproduce historical firmware behavior | Original method description versus script 68; focused reviewer check | Unsupported | Omits alpha bands; re-estimates xi/psi; uses held-estimate persistence; cooling/CO2 cooldown is assumed |
| Zero pH flags is robust across supervisor timings | `sensitivity/full_cells.csv`, 54 nonzero pH cells and maximum three flags | Falsified | Original 32/64/600/8 setting remains zero |
| EC zero flags survives the declared grid | Same full cells; all 108 EC attribution cells zero | Supported within grid | Range flags are partly structural; unknown in-range errors remain unidentified |
| Flagged pH/CO2 counts decrease throughout the specified grid | Paired same-setting naive/gated counts in all full cells | Supported descriptively | Reductions in count are not useful-action coverage or physical benefit |
| LiveGate is overall best | Frozen `docs/livegate/PROTOCOL.md`, `RESULTS.md`, original decision-rule tables | Rejected by frozen criterion | No new untouched holdout exists here |
| Controlled and follow-up comparisons are reproducible | `controlled_reproduction.json`; script 75; all 11 comparison CSVs and original three checks pass | Reproduced | A rerun does not supply independent confirmation or novelty |
| Liveness suppresses stuck-source commands at little availability cost | Follow-up paired intervals and stuck coverage 0.982 versus 0.273 | Rejected as a low-cost improvement | 79.3% source-command reduction accompanies large availability loss |
| Poor observed temperature regulation | Valid-reading occupancy table and raw traces | Descriptive support | Missing time and absent calibration/duty data prevent cause diagnosis |
| Gate improves crop yield | Agronomic sheet plus study design | Unsupported | Seven plants share one treatment system; simultaneous treatment changes |
| Mock reconciliation establishes field-safe physical exactly-once execution | Existing crash probes and durable mock ledger | Unsupported | Physical execution/record atomicity and independent device clocks unverified |
| Agricultural fault diagnosis/control-input separation is new here | Complete Ferentinos2003 and SensorTalk texts; companion2003 supervisor abstract | Rejected as a broad priority claim | Current manuscript asks the narrower held-source/authorization-accounting question; Q1 novelty still unestablished |
| Newly located public chamber/reference logs provide validated confirmation | `REFERENCE_CANDIDATE_SCREEN.md`, source/header-only screen and pinned GitHub metadata | Not yet established | No numerical outcomes read; clock/calibration/channel contract unresolved; environmental reference does not cover pH/EC or observed delivery |
| Manuscript is ready for a reputable Q1 submission | Complete coverage, nearest-work comparison, robustness, skeptical review, rebuilt PDFs and final requirements audit | Not yet established | Journal fit and acceptance cannot be inferred from a green test suite |
