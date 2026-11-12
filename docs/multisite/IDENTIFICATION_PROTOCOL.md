# EC dose-response identification check: frozen protocol

Declared 2026-11-12. Committed before any dynamics, dose-response or model fit
has been computed on the Pompeo (S1) data. What has already been seen, all
under `PROTOCOL.md`: fault-prevalence fractions, counts of logged dose requests
and their flagged-source fractions, firmware-rule agreement, and gating-replay
counts for all four trials (T1–T4). No EC trajectory, response to a dose or
water top-up, or time-series plot has been inspected. T3–T4 are therefore
not pristine data, but they have not been used for anything this protocol
estimates. This must be disclosed in any manuscript.

Purpose: a go/no-go check of whether a dose-driven EC simulator can be
identified from logged requests and validated on held-out trials. It is not
an algorithm evaluation. No gating method is run here.

## Data

- S1 trials T1–T4, lines 1–4, parsed with `read_s1_trial` from
  `scripts/74_multisite_audit.py` (same exclusions).
- Resample per line to 1-min bins. `EC` = median of the bin's readings.
  `N` = number of logged nutrient requests (`EC_Dose_k` > 0) in the bin.
  `W` = number of logged water top-ups (`Water_Dose_k` > 0) in the bin.
- **Clean bins:** at least one reading, and no reading in the bin flagged
  out-of-range, bound or spike under the frozen `flags` definition (EC range
  [0, 200000] uS/cm). Flagged bins are fault data for the later simulator
  and are excluded from identification. A bin without readings is a gap.

## Model (fixed form)

Per line: `EC[k+1] = EC[k] + a * N[k-d] + b * W[k-d] + c + e[k]`.
`a` is EC gain per nutrient request, `b` per water top-up, `c` drift per
minute (uptake/evaporation), and `d` the input delay in minutes.
- Fit by ordinary least squares on one-step differences, using only pairs
  where bins k, k+1 and the delayed input bin are clean.
- **Training:** T1 + T2 pooled per line. **Test:** T3 and T4 separately per
  line, giving 8 test cells.
- Delay `d` is chosen from {0, 1, 2, 5, 10} per line by the training-only
  30-min simulation RMSE defined below. No parameter is refitted on test data.

Known confound, stated in advance: the firmware doses when EC < 1100, so low
EC causes doses and regression toward the mean can bias `a`. The open-loop
multi-step validation below is the guard. The result is not reinterpreted if
`a` is biased.

## Validation (open-loop simulation)

Start points every 30 min where the full horizon of H minutes consists of
clean, gap-free bins. Simulate from the measured EC at the start, using the
logged inputs only and never the measured EC afterwards. Score the absolute
error at the horizon end. Horizons H = 10, 30, 60 min; **H = 30 is primary**.

Comparators, each evaluated on the same start points:
- **Hold:** EC stays at its start value.
- **Drift-only:** `a = b = 0`, with `c` refitted on training.

## Go/no-go criterion (primary)

**GO** if both hold:
1. In >= 6 of 8 test cells, the simulator's H = 30 RMSE is <= 0.8 x the Hold
   RMSE **and** below the drift-only RMSE.
2. In >= 3 of 4 lines, the training estimate of `a` is positive with a 95 %
   CI excluding 0 (HC1-robust OLS standard errors).

Otherwise **NO-GO**: the dose response is not identifiable well enough to
build a validated simulator. That result is reported as is. Cells with
< 20 valid start points are "not testable" and count as non-passing.

## Secondary (reported, no gate)

H = 10 and H = 60 results. The same model fitted to pH with logged acid
requests (pH range [0, 14]). Because the pH firmware rule is unverified, pH
results are labelled exploratory.

## Rules

One run of `scripts/76_ec_identification.py` after this commit. Outputs go to
`results/multisite/identification_*.csv` and `docs/multisite/IDENTIFICATION_RESULTS.md`.
Any later change is labelled post-hoc and both versions are reported.
