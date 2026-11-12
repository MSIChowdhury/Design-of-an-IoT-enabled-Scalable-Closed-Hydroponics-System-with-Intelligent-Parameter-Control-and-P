# Research audit cycle 1: reproduction and evidence independence

Frozen at 2026-11-12 21:22:27 UTC, before executing the baseline reproduction below.
The raw-feed equivalence check had already been run and revealed identical data;
it is an exploratory provenance finding, not a preregistered test.

The objective remains the complete research/manuscript task in the user attachment.
This cycle establishes what can currently be trusted; it does not declare Q1
publication readiness or create an independent validation set.

## Questions and predictions

R1: Does current raw-data preprocessing and executable-command replay reproduce
the public manuscript's supporting tables? Predict exact equality of the processed
121,244-row frame and the two deterministic CSV tables after their documented
serialization. Failure requires investigating and disclosing discrepancies before
changing scientific claims.

R2 (already explored): Does the newly accessible `data/Actual/feeds.csv` add
independent evidence? Every timestamp (converted to UTC), entry identifier, and
sensor value equals the public CSV after normalizing the four column names.
Therefore it cannot be used as an untouched holdout or second deployment.

## Design and controls

Use git HEAD `cbf7149` and the existing local Docker image; record the full image
ID, package versions, raw hashes, source hashes, command, times, and output hashes.
Run `prepare_hydro_exp1` into a temporary directory. Import the existing audit
runner unchanged and redirect only SOURCE, TABLE and BAND to temporary paths.
Compare with the current processed frame and frozen CSV files. Original data,
tables, configuration, and LiveGate artifacts must remain unchanged.

Primary endpoints are exact DataFrame equality and byte equality of the audit
and valid-reading occupancy CSVs. All 30 sensor-by-arm audit rows and all five
occupancy rows are included. No statistical hypothesis test is appropriate for
deterministic reproduction. This uses the whole available log; there is no new
sample-size claim and no independence assumption between samples.

Run the full repository test suite and lint once. Test success verifies software
checks, not calibration, physical execution, external validity, or novelty. A
failure is retained and investigated; do not tune a method to make reproduction
or scientific outcomes appear favorable. One rerun is justified only after a
disclosed implementation/environment correction.

## Resources and stopping rule

Pilot: direct import and raw-feed comparison already succeeded in Docker.
Budget: existing local CPU/container only, no paid access, purchases, downloads of
large datasets, or new data collection. Expected runtime under five minutes for
this reproduction; interrupt and inspect if unexpectedly expensive. Stop this
cycle after recording all endpoints and the skeptical review, then choose the
next informative experiment from the backlog. Reproduction is not confirmation
on independent data. Preserve every attempt and report null/failed results.
