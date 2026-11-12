# EC dose-response identification check: results

Single run of `scripts/76_ec_identification.py` (commit 8dafb5f) under the
protocol frozen at commit 3d0c76a. Outputs: `results/multisite/identification_*`.

## Decision: NO-GO

| Criterion | Required | Observed |
| --- | --- | --- |
| Test cells where the 30-min simulation RMSE is <= 0.8 x Hold and below drift-only | >= 6 of 8 | **0 of 8** |
| Lines with training dose gain `a` > 0 (95 % CI excludes 0) | >= 3 of 4 | 3 of 4 (lines 2, 3, 4) |

The fitted dose-driven model never beat "EC stays where it is" on held-out
trials T3–T4. The best case was a tie: line 2 T4 at 9.25 versus 9.31 µS/cm.
In line 4 T3, the simulator error was 37.6 µS/cm versus 4.3 µS/cm for Hold.

## Why

- **Estimated effect per nutrient request: −0.02 to +0.55 µS/cm.** Typical
  30-min EC variation on clean data is 4–11 µS/cm. Each request adds 1.5 mL
  of concentrate. That is too small, relative to sensor noise and unlogged
  dynamics (uptake, temperature, reservoir volume), to identify at the
  10–60 min horizons the protocol specified.
- The firmware doses whenever EC < 1100. Doses are therefore confounded with
  the EC state (protocol caveat). The fitted gains differ by more than 10x
  across lines and do not transfer between trials.
- pH (exploratory): fitted acid-dose effects of order 1e-4 pH units per
  request. All models were indistinguishable from Hold.

## Consequence

A dose-driven simulator **cannot be identified and validated** from these
logs. Any simulator that predicts what fault-driven doses did to the nutrient
solution would have to assume its gains and dynamics. That reintroduces the
circularity the check was designed to rule out. The protocol forbids refitting
on longer horizons or other model forms. Such work would also reuse T3–T4,
which now serve as test data.

The magnitudes are not reinterpreted to estimate harm from the flagged
requests in `RESULTS.md`. The model failed validation, so those
numbers are not evidence.

A pandas FutureWarning about the downcasting of `fillna` appeared during the
run. It does not change the boolean mask used here.
