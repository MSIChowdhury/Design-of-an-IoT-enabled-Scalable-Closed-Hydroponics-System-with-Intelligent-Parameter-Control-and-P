# Data Layout

Do not commit raw third-party datasets or sensitive hydroponic exports.

Expected local layout:

```text
data/
  raw/
    hydroponic/
      experiment_1.csv
      experiment_1_events.csv
      experiment_2.csv
      experiment_2_events.csv
    swat/
    wadi/
    tep/
    damadics/
    wur/
  interim/
  processed/
  synthetic/
```

Use `python scripts/01_validate_data_layout.py` to check which datasets are present.
Use `python scripts/run_all.py --toy` to run the full pipeline on generated toy data.

