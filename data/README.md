# Data Layout

Do not commit raw third-party datasets or sensitive hydroponic exports.

Expected local layout:

```text
data/
  raw/
    hydroponic/
      Hydroponics Data First Trial.csv
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
