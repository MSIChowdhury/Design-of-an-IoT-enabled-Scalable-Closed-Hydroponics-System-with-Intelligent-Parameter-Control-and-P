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
- `src/aasvr/loaders.py` and `src/aasvr/schemas.py`: canonical dataset loading/schema helpers for hydroponic logs and external process-control benchmark files that are placed locally under `data/raw/`.
- `src/aasvr/prepare.py`: real hydroponic Experiment 1 preprocessing; keeps `EC`, `pH`, `Humidity`, `Air_Temp`, `Water_Temp`, and `CO2` for primary analysis and excludes `Water_Level` because the raw values are not calibrated.
- `configs/`: YAML manifests for AASVR parameters, baselines, hydroponic datasets, and external process-control benchmark datasets.
- `scripts/`: reproducible command-line pipeline for dataset checks, toy preparation, method execution, synthetic fault injection, metrics, tables, figures, and manuscript checks.
- `scripts/10_run_ablation.py` and `scripts/11_statistical_analysis.py`: hydroponic Experiment 1 robustness layer for AASVR component ablations, bootstrap confidence intervals, method ranks, sensor-wise summaries, and fault-type summaries.
- External dataset scripts are availability-aware: place local CSV files under the configured `data/raw/<dataset>/` directory, then run `make real` to prepare, replay methods, score native labels, and include them in cross-dataset tables. Public easy-access routes currently include HAI and SKAB, with supported paths for MetroPT-3, BATADAL, and a small TEP CSV subset.
- External benchmark acquisition defaults to the `paper` subset profile, which writes notes and subset-protocol tables without downloading very large public archives. Use `--profile full --download` only as an explicit opt-in.
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

Run the locally available real-data pipeline:

```bash
docker compose run --rm project-shell make real
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
- Treat `data/raw/hydroponic/Hydroponics Data First Trial.csv` as local raw Experiment 1 data if present. It is ignored by git and should not be committed.
- Exclude `Water_Level` from primary hydroponic analysis until a defensible calibration/physical mapping is available.
- Preserve binary CAD files unless the user explicitly asks for CAD changes.
- Keep `Paper Files/` easy to view and edit after Docker/LaTeX runs: ownership should be the workspace user/group (`vsj23:vsj23` in this checkout), directories should allow `u+rwX,g+rwX,o+rX`, and files should allow user/group writes plus world read access. If Docker creates root-owned LaTeX outputs, repair ownership and permissions before finishing the task.

## Verification Notes

- Python notebook dependencies are captured in `requirements.txt`.
- The Docker image includes Python/Jupyter dependencies and GNU Octave for MATLAB-like execution.
- The static dashboard can be served from `Code Files/Web Interface` through the `web` compose service.
- Full notebook and MATLAB verification requires the missing CSV datasets referenced above.
- The AASVR code path supports a toy smoke test with `python scripts/run_all.py --toy` and `make all`.
- The real hydroponic Experiment 1 path supports `python scripts/run_all.py --available-real` and `make real` when the local raw CSV exists.

## Change Log

- 2026-05-18: Added `AGENTS.md` project memory, container-first workflow, Docker configuration, Python dependency manifest, and Docker ignore rules.
- 2026-05-18: Documented that every completed change set should be committed, pushed to the configured remote, and recorded in this file.
- 2026-05-18: Added AASVR research package scaffold, dataset/method configs, reproducible scripts, tests, result/data placeholders, and ISA Transactions manuscript/submission artifacts.
- 2026-05-18: Strengthened AASVR with actuator-consistency trust components, expanded baseline behavior, canonical dataset loaders, event/control-safety metrics, synthetic fault grids, additional tests, and literature-backed manuscript sections.
- 2026-05-18: Added real hydroponic Experiment 1 preprocessing, availability-aware real-data pipeline commands, external dataset acquisition notes/config metadata, and a documented decision to exclude uncalibrated `Water_Level` from primary analysis.
- 2026-05-18: Added windowed synthetic-fault method-comparison metrics for hydroponic Experiment 1 so paper results are not dominated by physical-range rule labels.
- 2026-05-18: Updated AASVR evaluation to score anomaly rejection with `gate_result == reject` while keeping `alert` as the maintenance-escalation signal.
- 2026-05-18: Added hydroponic AASVR synthetic-fault parameter sweep for `scale_multiplier`, `q_min`, and `transient_limit` with a control-aware objective.
- 2026-05-17: Added the next robustness iteration: AASVR ablations, bootstrap uncertainty, method ranking, sensor-wise/fault-type analysis outputs, and real-pipeline table/figure hooks.
- 2026-05-17: Made `scripts/` importable during pytest by adding package metadata and including the repo root on pytest's Python path.
- 2026-05-17: Removed a stale unused tuning-script import so the project lint check passes for the analysis pipeline.
- 2026-05-17: Added an uncommanded-trend guard to AASVR for slow monotonic drift faults that stay inside physical range and per-sample rate gates, plus an ablation variant that disables the guard.
- 2026-05-18: Added manual hydroponic event-label merging, AASVR-driven annotation template generation, generic CSV external-dataset preparation, availability-aware external replay/scoring, and cross-dataset table/figure hooks.
- 2026-05-18: Added a defensible benchmark-subset protocol and safer download profiles so TEP/WUR/HAI/SWaT/WaDi/DAMADICS can be documented without requiring huge archive downloads by default.
- 2026-05-18: Added a real HAI 21.03 paper-subset preparation path, timestamp-level label alignment, and corrected the cross-dataset benchmark table to use hydroponic synthetic-fault results rather than rule-label replay as the hydroponic headline.
- 2026-05-18: Added timestamp-level multivariate scoring for native attack-label datasets such as HAI, using a fixed 30% sensor-stream fraction rule for the headline external benchmark table.
- 2026-05-18: Added SKAB, MetroPT-3, BATADAL, and small TEP CSV dataset configs; implemented SKAB and MetroPT-3 preparation routes; extended downloader, run pipeline, tests, README, and manuscript text; and generated a SKAB native-label benchmark result with AASVR ranked first by balanced accuracy under the fixed 30% timestamp aggregation rule.
- 2026-05-18: Added native-label aggregation-threshold sensitivity analysis for external timestamp-level datasets so HAI/SKAB results report the fixed 30% headline rule plus recall, specificity, and balanced-accuracy tradeoffs across 10%--90% sensor-fraction thresholds.
- 2026-05-18: Added a new ISA Transactions AASVR paper package under `Paper Files/` with author and blinded LaTeX entry points, focused BibTeX references, TikZ architecture/state-machine diagrams, copied paper figures, manifest, figure audit, editor notes, and Docker/Make TeX build support.
- 2026-05-18: Replaced the original `Paper Files/elsarticle-template-num.tex` entry point with a compatibility wrapper to the new `main_aasvr.tex` manuscript so the legacy filename opens the current AASVR paper.
- 2026-05-18: Normalized `Paper Files/` ownership and permissions for easy viewing/editing after Docker-generated LaTeX outputs, and recorded the permission convention as a standing workflow rule.
