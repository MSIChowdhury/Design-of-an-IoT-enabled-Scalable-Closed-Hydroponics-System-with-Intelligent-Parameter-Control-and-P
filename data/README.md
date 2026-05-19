# Data Layout

Do not commit raw third-party datasets or sensitive hydroponic exports.

Expected local layout:

```text
data/
  raw/
    hydroponic/
      Hydroponics Data First Trial.csv
      Agronomic Data.csv
      actuator_state_log.csv
      reference_measurements.csv
      water_level_calibration.csv
      experiment_1_events.csv
      experiment_2.csv
      experiment_2_events.csv
    swat/
    wadi/
    tep/
    hai/
    damadics/
    wur/
  interim/
  processed/
  synthetic/
```

Use `python scripts/01_validate_data_layout.py` to check which datasets are present.
Use `python scripts/run_all.py --toy` to run the full pipeline on generated toy data.
Use `python scripts/run_all.py --available-real` to run locally available real data.

For the current first-trial hydroponic feed, `Water_Level` is retained only in raw data
and excluded from primary analysis until calibration is available.

Optional limitation-closing files can be placed in `data/raw/hydroponic/`:

- `actuator_state_log.csv` records real actuator commands and measured actuator
  states so AASVR-R response residuals can be scored as measured deployment
  evidence rather than counterfactual replay.
- `reference_measurements.csv` records paired raw/reference sensor readings from
  a calibrated handheld or benchtop instrument.
- `water_level_calibration.csv` records raw water-level readings paired with a
  physical level in centimeters.

Generate empty schemas with:

```bash
python scripts/24_prepare_optional_evidence.py --write-templates
python scripts/25_calibrate_water_level.py --write-template
```

The optional parsers are absence-safe. Missing files produce status tables under
`results/run_metadata/` and do not change the primary AASVR-R benchmark.

The optional agronomic linkage pipeline uses per-plant harvest data at
`data/raw/hydroponic/Agronomic Data.csv`. It supports the current wide two-experiment
export, the compact ANOVA export, and the normalized template schema. Generate the
normalized schema with `python scripts/22_prepare_agronomic.py --write-template`, or
copy the tracked template at `configs/templates/agronomic_harvest_template.csv`, then
fill one row per plant.
TNL and NL10 must be recorded as counts, not centimeters. The linkage analysis is
mechanistic deployment context only; it must not be interpreted as causal evidence
that AASVR-R alone caused yield differences among P1, P2, and P3.

External dataset support is availability-aware. Place CSV files under the configured
`data/raw/<dataset>/` directory and rerun `make real`; missing datasets are skipped
without failing the hydroponic pipeline.

Use `python scripts/download_datasets.py --all --profile paper` to write acquisition
notes without downloading large archives. Use `--profile full --download` only when
you intentionally want full public archives such as the 133 GB DTU TEP data.
