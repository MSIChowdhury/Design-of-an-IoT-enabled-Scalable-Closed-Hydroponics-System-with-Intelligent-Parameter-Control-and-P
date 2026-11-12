# Multi-site fault-to-actuation replication: frozen protocol

Declared 2026-11-12, committed to git before any numerical sensor or actuator
values from the external sources below were parsed or summarised. Seen so far:
publication/repository metadata, file trees, licences, CSV headers, the
documentation PDFs, and the complete Pompeo `Hydroponic_Control.ino` sketch.
One disclosure: printing the first 700 bytes of one Pompeo T1 file (03.05.2022)
to read its header also displayed the first twelve air-temperature/humidity
values of its first data row. Those channels are not endpoints below.

The index site (our experiment-2 log, `scripts/68_deployment_audit.py`) has
already been analysed. It supplies the frozen definitions and is reported as the
index, never as a replication. No external analysis is a confirmation of our
physical-effect claims; nothing here measures delivered volume or crop outcome.

## Sources

| ID | Source | Licence | Role |
| --- | --- | --- | --- |
| S1 | Pompeo et al. 2024, Front. Plant Sci., DOI 10.3389/fpls.2024.1270544; github.com/JeanPompeo/Hydroponic_Control_System_Chamber_1 at commit 9a38f79 | none declared: analyse locally, cite, never redistribute raw rows | Low-cost Atlas EZO pH/EC sensing with a naive firmware dosing rule and **logged dose requests**; 4 trials (T1 30 °C, T2 24 °C, T3 28 °C, T4 26 °C) x 4 nutrient lines |
| S2 | Autonomous Greenhouse Challenge 2nd edition (2019), 4TU DOI 10.4121/uuid:88d22c60-21b3-4ea8-90db-20249a5be2a7 (record 12764777 v2) | CC0 | Commercial process-computer greenhouse; 6 compartments, 5-min `CO2air`, `co2_dos` (computed CO2 dosing) and `co2_sp` setpoint; contrast site |
| S3 | Aquaponic pond IoT dataset, Mendeley Data yd36bx6f8f v2, file `pond_iot_2023_raw.csv` | CC BY 4.0 | Low-cost ESP8266 pH/TDS/temperature logger without a controller; fault prevalence only |

Excluded before outcome inspection:
- HydroGrowNet (Mendeley g6cm3v3wdp): hourly sensor data with KNN imputation and
  k-means outlier exclusion per its documentation, so raw faults are removed.
- Mendeley 96nj4yyzkg: no sensor data file, only a document.
- Public ThingSpeak hydroponic channels: no documented setpoints, actuators,
  sensors or provenance.

## Frozen definitions (inherited from the index audit)

- **Out-of-range:** finite reading outside the declared physical range.
  **Bound:** reading exactly equal to a declared range end. **Missing:** empty
  or non-numeric. **Spike:** `aasvr.standin._spikes` applied to in-range values
  (centred 9-sample rolling median, 8 x MAD), excluding out-of-range/bound
  samples, exactly as in the index. **Flat-line:** run of identical in-range
  values lasting >= 3600 s without a logging gap (`scripts/64` definition).
  **Gap:** consecutive timestamps further apart than 10 x the unit's median
  sampling interval. Flags are reading categories, not fault diagnoses.
- **Physical ranges** (manufacturer/measurement scale, not agronomic bands):
  Atlas EZO pH [0, 14]; Atlas EZO EC [0, 200000] uS/cm; S2 `CO2air` [0, 10000]
  ppm; S3 pH [0, 14], TDS [0, 1000] ppm, water temperature [-55, 125] C
  (DS18B20 scale). Ranges are fixed here and never changed after outcomes.
- **Timing scaled to sampling rate:** the index used 16 s sampling with 32 s
  persistence (2 samples), 64 s held-estimate age (4 samples) and a 120 s
  max-gap. Externally: persistence = 2 samples, max age = 4 samples,
  max-gap = 10 samples, each in seconds via the unit's median sampling interval.
  Cooldown: site-native (S1 firmware has none, so 0 s) as primary; the index
  600 s as a declared secondary.

## Endpoints

**E1 Fault prevalence (S1, S2, S3).** Per unit and sensor: fractions of
samples out-of-range, at bound, missing, spike, flat-line; gap fraction of
elapsed time. Units: S1 trial x line; S2 compartment; S3 whole file.

**E2 Observed flagged-source requests (S1 primary, S2 secondary).**
- S1: a logged dose request is a row with `pH_Dose_k` > 0 (acid) or
  `EC_Dose_k` > 0 (nutrient). Its source reading is the same row's
  `pH_LNS_k` / `EC_LNS_k`, which the firmware prints in the same loop before
  dosing. Report total requests and the fraction with an out-of-range, bound
  or spike source reading, per trial x line and pooled by trial.
- S2: an interval with `co2_dos` > 0 is a dosing interval; its source is that
  row's `CO2air`. Report the same fractions per compartment. The process
  computer's own control sensor/logic is undocumented, so S2 is descriptive.

**E3 Reconstruction validity (S1).** Replay the documented firmware rule
(acid when pH > 5.85; nutrient when EC < 1100) on each row's logged reading,
no persistence, no cooldown, and report agreement with the logged request
(fraction of rows with matching request/no-request, plus confusion counts).
Disagreement is reported as firmware/version mismatch, not corrected.

**E4 Gating replay (S1).** Using `aasvr.reanalysis.hold_estimate` and
`authorize` with the site-native directions (acid lowers pH: direction -1 when
pH > 5.85; nutrient raises EC: +1 when EC < 1100; bands pH [-inf, 5.85],
EC [1100, inf]), run four arms: naive; range check; range + 2-sample
persistence; range + persistence + bound rejection. Report commands and flagged-
source commands per arm, and unflagged-command retention relative to naive.

## Pre-declared replication criterion (S1 only, per trial x channel)

The index finding "range check plus short persistence removes most commands
sourced from flagged readings at modest command loss" is **replicated** in a
trial x channel cell when, under the primary timing, range + persistence cuts
flagged-source commands by >= 90 % relative to naive **and** keeps >= 80 % of
naive unflagged commands. Cells with < 10 naive flagged-source commands are
reported as "not testable", not as successes. The result is the count of
replicated / failed / not-testable cells out of 8 (4 trials x pH, EC; lines
pooled within trial because they share one chamber and logger). No pooled
p-value is computed. Every cell is published, including failures.

E3 passes if logged/replayed agreement >= 95 % of rows in each trial; a failure
is reported and E2 remains valid while E4 is labelled "rule unverified".

## Uncertainty and dependence

Lines within a trial share one chamber, logger and clock; compartments in S2
share one facility; trials share one apparatus. Units are not independent
facilities. Intervals: 95 % percentile day-cluster bootstrap (2000 resamples,
seed 20261112) within unit, pooling numerators and denominators. No interval
is presented as generalising to other deployments.

## Parsing and exclusion rules (fixed before parsing)

- S1: comma-separated with header line; strip whitespace. Rows whose field
  count differs from the header are excluded and counted per file (the sketch
  omits a field when a reading is NaN, so such rows are misaligned).
  Timestamps are naive local time as written. Files with no data rows are
  skipped and listed. All four trials are used; no trial is held out because
  no parameter is fitted.
- S2: `%time` is an Excel serial date; rows are kept as-is, empty cells are
  missing. All six compartments are used.
- S3: `created_date` parsed as written; `id` ignored.
- No row is removed, repaired, aligned or relabelled after outcomes are seen.
  Any parser bug found later is fixed, the full analysis is rerun, and both
  versions are reported.

## Stopping rule and reporting

One run of `scripts/74_multisite_audit.py` after this commit. Results go to
`results/multisite/` and `docs/multisite/RESULTS.md`, including failures and
not-testable cells. Any later analysis is labelled post-hoc.
