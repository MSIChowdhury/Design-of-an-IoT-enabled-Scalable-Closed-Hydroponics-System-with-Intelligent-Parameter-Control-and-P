# LiveGate locked comparison protocol

Written and committed before LiveGate was run on the measured log. Code:
`src/aasvr/livegate.py`, `scripts/66_livegate_benchmark.py`; config:
`configs/experiments/livegate.yaml`; command: `make livegate`.

## Status of the data

Retrospective. The experiment-2 log (2024-02-27 to 2024-03-28) was analysed in
earlier studies, including the same development/validation/evaluation time blocks.
This comparison is therefore not on untouched data, and any claim must say so.

## Motivation (from the measured log, before LiveGate existed)

The CO2 sensor sat exactly at its 5000 ppm full scale for up to 1,915 consecutive
samples, while a working EC sensor never repeated a value more than 7 samples in
development data. Range checks accept such readings, and persistence-based gates
treat them as confirmed. No compared method models whether the sensor is alive.

## Method (fixed)

- Per-sensor robust (Huber) forecaster of the deviation from the trusted level
  (mean of the last 5 accepted readings), using level trend, time of day, and the
  other four controlled channels (winsorized at development 1st/99th percentiles).
- Split-conformal consistency threshold: the (1 - ε) quantile, with finite-sample
  correction, of clean scores from the last 25% of development data.
- Liveness: reject while the current run of identical readings has smoothed
  empirical survival below ε under development-data runs of clean readings.
- Re-anchoring: a surprising but live reading becomes trusted after
  `clip(1 + ceil(log2(score / q)), 2, 8)` mutually consistent readings.
- ε ∈ {0.002, 0.01, 0.05} plays the role of the baselines' threshold multipliers;
  persistence {0, 32, 96} s and maximum age {64, 320} s are shared by all methods.
- Ablations: `livegate_no_liveness`, `livegate_no_forecast`.

One design change was made before any measured-data run: anchoring the forecast on
a 5-sample level instead of the single last value. It fixed cascading rejections
found by the synthetic unit tests. The benchmark was smoke-tested only on the
synthetic stand-in.

## Comparison (fixed)

- 13 comparators: always-deny, persistence-only, Hampel, CUSUM, LOF, Kalman, EWMA,
  moving median, GLR, and three AASVR-R arms, all on the reanalysis replay.
- Deployed setpoints: pH 5.8-6.5, EC 1000-1500 µS/cm, CO2 1900-2100 ppm, water
  18-22 °C, air 20-26 °C. Humidity is excluded because it is not actuated.
- Scenarios: the 11 reanalysis scenarios plus `saturation` (reading pinned at the
  declared physical maximum for 30 samples).
- Validation picks each method's setting per coverage target (0.5, 0.8, 0.95) with
  the existing lexicographic rule. Evaluation is scored once with those settings.

## Decision rules (fixed)

At each coverage target, among methods that were feasible on validation, compare
evaluation undesirable authorizations per trial (unnecessary plus wrong direction)
at the 180-s deadline:

1. **LiveGate best at a target**: it has the lowest evaluation undesirable rate among
   feasible methods, with evaluation coverage no more than 0.02 below the best
   feasible coverage.
2. **Clearly best at a target**: rule 1 holds, and the source-day paired 95%
   interval of (runner-up − LiveGate) undesirable excludes zero.
3. **Overall claim**: "best" only if rule 1 holds at every target where LiveGate is
   feasible, and LiveGate is feasible wherever any non-trivial baseline is.
   Otherwise the result is reported as mixed or negative, as it falls.

Secondary, reported regardless of outcome: per-scenario results (especially
stuck and saturation), ablations, and the real-log audit. The audit counts
authorizations driven by certain faults (out-of-range or exactly-full-scale
readings) on the unmodified evaluation-period log.

Nothing in this protocol is changed after the measured-data run. Any later
variant is a new, separately labelled analysis.
