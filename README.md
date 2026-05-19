# AASVR Hydroponic Closed-Loop Control Study

## Overview

This repository supports a reproducible research article on **Actuation-Aware Sensor Validation and Rectification (AASVR)** for closed-loop measurement and control systems. The hydroponic system is the primary deployment testbed, and the current analysis focuses on whether sensor validation, rectification, persistence logic, and actuation authorization reduce anomaly pass-through and false actuation.

## Authors

- MD. Sameer Iqbal Chowdhury - Department of Robotics and Mechatronics Engineering, University of Dhaka, Bangladesh
- Mikdam-Al-Maad Ronoue - Department of Robotics and Mechatronics Engineering, University of Dhaka, Bangladesh

## Supervisors

- Dr. Lafifa Jamal - Department of Robotics and Mechatronics Engineering, University of Dhaka, Bangladesh
- Dr. Md Asaduzzaman - Department of Agriculture and Food Technology, Kyoto University of Advanced Sciences

## Current Research Focus

1. Streaming AASVR implementation for sensor validation and rectification.
2. Hydroponic Experiment 1 preprocessing and reproducible Docker pipeline.
3. Synthetic fault injection for spikes, dropout, drift, bias, noise bursts, and steps.
4. Baseline comparison against thresholding, moving filters, Hampel, Kalman, EWMA, CUSUM, and PCA-style monitoring.
5. Ablation, bootstrap confidence intervals, sensor-wise summaries, and fault-type summaries.
6. Availability-aware external benchmark scaffolding for TEP, WUR, HAI, SKAB, MetroPT-3, BATADAL, SWaT, WaDi, and DAMADICS when raw files are placed locally.
7. A documented benchmark-subset protocol so external validation is smaller, reproducible, and not cherry-picked.

## Reproducible Workflow

Run all project work through Docker:

```bash
docker compose run --rm project-shell make real
```

Prepare absence-safe templates and status tables for the remaining deployment
evidence limitations:

```bash
docker compose run --rm project-shell make optional-evidence
docker compose run --rm project-shell make water-calibration
```

These commands define the future actuator-state log, independent reference
measurement, and water-level calibration schemas. If the optional local CSV files
are absent, they write explicit status outputs and leave the current benchmark
unchanged.

Generate the external benchmark acquisition notes and subset protocol without downloading large archives:

```bash
docker compose run --rm project-shell make subset-protocol
```

The locally available hydroponic feed is expected at:

```text
data/raw/hydroponic/Hydroponics Data First Trial.csv
```

Optional local evidence files can be added next to the feed as
`actuator_state_log.csv`, `reference_measurements.csv`, and
`water_level_calibration.csv`.

Raw and generated data are ignored by git. External benchmark raw files should be placed under their configured `data/raw/<dataset>/` directories and regenerated locally.

Run the exhaustive hydroponic stress-test protocol in shards. The `mini` profile
is a smoke test; the `exhaustive` profile defines the full factorial protocol
used for final resubmission runs:

```bash
docker compose run --rm project-shell make exhaustive-mini
docker compose run --rm project-shell make exhaustive-grid
docker compose run --rm project-shell python scripts/27_run_exhaustive_benchmark.py \
  --profile exhaustive --split test --shard-index 0 --shard-count 32
docker compose run --rm project-shell python scripts/29_aggregate_exhaustive_results.py \
  --profile exhaustive --split test
```

The exhaustive profile spans the six primary hydroponic sensors, fourteen fault
classes, four magnitude levels, eight durations, and 50 disjoint insertion
windows per cell for each tune/validation/test split. It produces 403,200
trial descriptors before method expansion and is intentionally shardable so it
can run on a workstation or cluster without changing the protocol.

Large public archives are not downloaded by default. The paper workflow uses the `paper` profile, which documents fixed subset rules for defensible cross-domain validation. SKAB is compact enough to clone directly; MetroPT-3 is manageable but still downloaded only when requested. Full TEP/WUR archive download remains an explicit opt-in through `scripts/download_datasets.py --profile full --download`.

## Current Hydroponic Synthetic-Fault Result

Current manuscript-facing results are generated from the hydroponic Experiment 1
synthetic-fault benchmark and are written to `results/tables/`. The current paper
uses AASVR-R as the main method and reports the held-out benchmark in
`Paper Files/main_aasvr.tex`.

These results are synthetic-fault benchmark results, not agronomic causality
claims. Crop-yield and dashboard material are retained only as deployment context.
The optional agronomic linkage pipeline uses the per-plant harvest sheet at
`data/raw/hydroponic/Agronomic Data.csv`; for a normalized replacement, generate the template with
`python scripts/22_prepare_agronomic.py --write-template` or copy
`configs/templates/agronomic_harvest_template.csv`.

The current public external benchmark path also supports the HAI `21.03/test1` paper subset. Native HAI attack labels are timestamp-level, so the headline HAI table uses a timestamp-level multivariate score: a timestamp is flagged when at least 30% of sensor streams reject/alert. In the latest local run, AASVR had the highest HAI balanced accuracy among implemented methods, but the result should be framed as cross-domain stress testing rather than a dominance claim.

The SKAB public process-loop benchmark is now supported as the primary easy-access external dataset. Native SKAB labels are also timestamp-level, so the same 30% multivariate aggregation rule is used for the headline comparison. In the latest local run, AASVR had the highest SKAB balanced accuracy among implemented methods, with high recall and a high false-positive rate that should be discussed as a sensitivity/specificity tradeoff.

For native timestamp-label datasets, the pipeline also reports an aggregation-threshold sensitivity analysis. The fixed 30% rule remains the headline protocol, while the sensitivity table shows how recall, specificity, false-positive rate, and balanced accuracy change when the required fraction of rejecting/alerting sensor streams is varied.

## Acknowledgements

We gratefully acknowledge the financial support provided
by the ICT Division under the Ministry of Communications
and Information Technology, People's Republic of Bangladesh. This research was fully funded
under the ICT Innovation Fund arranged by the ICT Division.
