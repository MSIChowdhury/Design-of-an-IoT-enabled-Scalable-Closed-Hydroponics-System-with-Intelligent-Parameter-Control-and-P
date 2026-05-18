# AGENTS.md

## Project Summary

This repository documents and supports an IoT-enabled scalable closed hydroponics system with intelligent parameter control and persistent sensing error resilience. The root paper, `Automated_Hydroponics_Paper__Measurement_.pdf`, describes a closed Nutrient Film Technique (NFT) hydroponics system for lettuce growth that monitors and controls electrical conductivity, pH, humidity, air temperature, water temperature, water level, and CO2 concentration.

The research compares the proposed automated treatment against soil-based and manual Deep Water Culture (DWC) controls. It also includes machine-learning work for control-action classification and an optimization-based persistent sensor-error resilience algorithm.

## Repository Map

- `README.md`: high-level project overview, authorship, features, experiment summary, ML results, and error-resilience summary.
- `Automated_Hydroponics_Paper__Measurement_.pdf`: project paper/preprint with system motivation, methodology, experiments, and results.
- `Code Files/Web Interface/index.html`: static dashboard page embedding ThingSpeak charts/widgets and polling a local Flask endpoint at `http://192.168.1.2:5000`.
- `Code Files/Web Interface/automated-hydroponics-data-40ded0143ddf.json`: Google service-account credential file. Treat this as sensitive and rotate/revoke it if it is real.
- `Code Files/Jupyter Notebooks/Automated Hydroponics System Sensor Data Analysis.ipynb`: sensor-data analysis notebook using `pandas`, `matplotlib`, and `seaborn`; expects `feeds (2).csv`.
- `Code Files/Jupyter Notebooks/Xgboost Regressor for Automatic Hydroponics System Growth Parameter Control.ipynb`: synthetic dataset generation, XGBoost regressor training/evaluation, hyperparameter search, model export, and model reload examples; expects generated files such as `Sample_Data_5000.csv`, `Sample_Data_50000.csv`, and `xgboost_regressor_model.json`.
- `Code Files/MATLAB Codes/Error_Resilience_Algorithm_Optimisation.m`: MATLAB optimization script for alpha/beta sensor-error resilience parameters across EC, pH, air temperature, water temperature, water level, and CO2. It currently contains absolute Windows paths for input/output CSVs that should be parameterized before automated container runs.
- `3D CAD Files/`: SolidWorks parts and assemblies for the hydroponics piping/tube structure. These are binary CAD assets and are not runnable inside the software container.
- `src/aasvr/`: reproducible Python implementation of Actuation-Aware Sensor Validation and Rectification (AASVR), baseline wrappers, toy data, fault injection, and metrics.
- `configs/`: YAML manifests for AASVR parameters, baselines, hydroponic datasets, and external process-control benchmark datasets.
- `scripts/`: reproducible command-line pipeline for dataset checks, toy preparation, method execution, synthetic fault injection, metrics, tables, figures, and manuscript checks.
- `manuscript/`: ISA Transactions scaffold including anonymized manuscript, title page, highlights, cover letter, data statement, and rewrite notes.

## Container-First Workflow

Run all software workflows through Docker so the project stays contained and reproducible.

Build the image:

```bash
docker compose build
```

Start JupyterLab for notebooks:

```bash
docker compose up jupyter
```

Then open `http://localhost:8888`. The compose file disables the token for local development only.

Serve the web dashboard:

```bash
docker compose up web
```

Then open `http://localhost:8080`.

Open an interactive project shell:

```bash
docker compose run --rm project-shell
```

Run the AASVR toy reproducibility pipeline:

```bash
docker compose run --rm project-shell make all
```

Run MATLAB-like scripts with Octave from inside the container when compatible:

```bash
docker compose run --rm project-shell octave "Code Files/MATLAB Codes/Error_Resilience_Algorithm_Optimisation.m"
```

The current MATLAB script uses absolute Windows file paths and may require edits before it runs in Octave or a Linux container.

## Development Rules

- Prefer Docker/Compose commands for all project execution, notebook work, static dashboard serving, and MATLAB-like script checks.
- Keep project state reproducible by committing source, configuration, and documentation changes.
- Push every completed change set to the configured remote repository after verification.
- Record every project-maintenance change in the change log below, including container, documentation, dependency, and workflow updates.
- Do not commit new secrets. The existing Google service-account JSON appears sensitive; avoid copying it into derived files, logs, screenshots, or documentation.
- Do not assume missing datasets are available. The notebooks reference CSV files that are not currently present in the repository.
- Do not commit raw external benchmark datasets, request-access SWaT/WaDi files, or generated large outputs. Use local `data/raw/` placement and scripts/configs to reproduce.
- Preserve binary CAD files unless the user explicitly asks for CAD changes.

## Verification Notes

- Python notebook dependencies are captured in `requirements.txt`.
- The Docker image includes Python/Jupyter dependencies and GNU Octave for MATLAB-like execution.
- The static dashboard can be served from `Code Files/Web Interface` through the `web` compose service.
- Full notebook and MATLAB verification requires the missing CSV datasets referenced above.
- The AASVR code path supports a toy smoke test with `python scripts/run_all.py --toy` and `make all`.

## Change Log

- 2026-05-18: Added `AGENTS.md` project memory, container-first workflow, Docker configuration, Python dependency manifest, and Docker ignore rules.
- 2026-05-18: Documented that every completed change set should be committed, pushed to the configured remote, and recorded in this file.
- 2026-05-18: Added AASVR research package scaffold, dataset/method configs, reproducible scripts, tests, result/data placeholders, and ISA Transactions manuscript/submission artifacts.
