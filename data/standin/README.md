# Synthetic stand-in for the hydroponic sensor log

**This is synthetic data, not measurements.** The 30-day deployment sensor log
(experiment 2, 121,244 rows at about 16 s) is publicly available at
`data/raw/hydroponic/Hydroponics Data First Trial.csv` in this repository. Every
result reported in the manuscript was computed on that measured log, not on this file.

`hydro_standin.csv.gz` mirrors the log's layout (timestamp, entry_id, EC, pH,
Humidity, Air_Temp, Water_Temp, CO2), its 16 s cadence, and its aggregate
behavior, so the full pipeline and benchmark can run without the measured data.
The generator (`src/aasvr/standin.py`) is fitted only to aggregate statistics:
hour-of-day medians, lag-1 residual dynamics, quantization step, spike and
out-of-range rates, and gap frequency/length. No measured sample is copied.

- `standin_profile.json`: the fitted aggregate profile.
- `standin_vs_deployment_summary.csv`: per-channel median, IQR, lag-1
  autocorrelation, spike rate, out-of-range rate, and gap count for the measured
  log and the stand-in.

Regenerate with `docker compose run --rm project-shell make standin` (requires the
measured log). To run the benchmark protocol on the stand-in:
`docker compose run --rm project-shell make standin-smoke`.
