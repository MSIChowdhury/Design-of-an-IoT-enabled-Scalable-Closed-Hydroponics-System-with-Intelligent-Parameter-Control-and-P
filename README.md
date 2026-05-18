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
6. Availability-aware external benchmark scaffolding for TEP, WUR, HAI, SWaT, WaDi, and DAMADICS when raw files are placed locally.
7. A documented benchmark-subset protocol so external validation is smaller, reproducible, and not cherry-picked.

## Reproducible Workflow

Run all project work through Docker:

```bash
docker compose run --rm project-shell make real
```

Generate the external benchmark acquisition notes and subset protocol without downloading large archives:

```bash
docker compose run --rm project-shell make subset-protocol
```

The locally available hydroponic feed is expected at:

```text
data/raw/hydroponic/Hydroponics Data First Trial.csv
```

Raw and generated data are ignored by git. External benchmark raw files should be placed under their configured `data/raw/<dataset>/` directories and regenerated locally.

Large public archives are not downloaded by default. The paper workflow uses the `paper` profile, which documents fixed subset rules for defensible cross-domain validation. Full TEP/WUR archive download remains an explicit opt-in through `scripts/download_datasets.py --profile full --download`.

## Current Hydroponic Synthetic-Fault Result

Current AASVR performance on the hydroponic Experiment 1 synthetic-fault benchmark:

- Balanced accuracy: 0.859
- Recall: 0.839
- Specificity: 0.880
- Mean false actuations per trial: 0.145
- Bootstrap 95% CI for balanced accuracy: 0.844 to 0.874

These results are synthetic-fault benchmark results, not agronomic causality claims. Crop-yield and dashboard material are retained only as deployment context.

## Acknowledgements

We gratefully acknowledge the financial support provided
by the ICT Division under the Ministry of Communications
and Information Technology, People's Republic of Bangladesh. This research was fully funded
under the ICT Innovation Fund arranged by the ICT Division.
