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
- `configs/methods/baselines.yaml`: baseline comparison manifest. The hydroponic synthetic-fault benchmark now includes raw thresholding, the original manuscript method, moving average/median, Hampel, Kalman, EWMA, CUSUM, PCA-style residual monitoring, Isolation Forest, One-Class SVM, and LOF. Full-feed hydroponic replay is intentionally limited by `full_replay` so large baseline-decision CSVs are not regenerated unless explicitly requested.
- `scripts/14_tune_baselines.py`: validation-split baseline tuner. It tunes baseline hyperparameters with the same control-aware objective family used for AASVR before held-out test scoring.
- `scripts/10_run_ablation.py` and `scripts/11_statistical_analysis.py`: hydroponic Experiment 1 robustness layer for AASVR component ablations, bootstrap confidence intervals, method ranks, sensor-wise summaries, and fault-type summaries.
- `configs/experiments/exhaustive_hydro.yaml` and `scripts/26_build_exhaustive_fault_grid.py`--`scripts/29_aggregate_exhaustive_results.py`: exhaustive hydroponic stress-test protocol, shardable benchmark runner, AASVR-R sweep runner, and aggregation utilities. The `mini` profile is a smoke test; the `exhaustive` profile defines 403200 tune/validation/test trial descriptors before method expansion.
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

Run the exhaustive hydroponic benchmark smoke test:

```bash
docker compose run --rm project-shell make exhaustive-mini
```

Build the full exhaustive trial descriptor grid without executing method replays:

```bash
docker compose run --rm project-shell make exhaustive-grid
```

Run the full exhaustive benchmark in shards, then aggregate completed shards:

```bash
docker compose run --rm project-shell python scripts/27_run_exhaustive_benchmark.py --profile exhaustive --split test --shard-index 0 --shard-count 32
docker compose run --rm project-shell python scripts/29_aggregate_exhaustive_results.py --profile exhaustive --split test
```

For long exhaustive runs in this Codex environment, keep the launcher attached
to a persistent exec session rather than relying on detached `nohup` children.
The detached children can be reaped when the tool call ends. Use:

```bash
env PROFILE=exhaustive SHARDS=128 PARALLEL=8 SPLITS='tune validation test' scripts/30_launch_exhaustive_benchmark.sh
env PROFILE=exhaustive SPLIT=validation SETTING_SHARDS=512 TRIAL_SHARDS=16 PARALLEL=4 scripts/31_launch_exhaustive_sweep.sh
```

The worker scripts `scripts/32_exhaustive_benchmark_worker.sh` and
`scripts/33_exhaustive_sweep_worker.sh` are available for ordinary terminal
sessions where background processes persist normally.

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
- Do not commit exhaustive benchmark generated grids, shards, or aggregate CSVs under `data/synthetic/` or `results/`; they are reproducible outputs and can become very large.
- Treat `data/raw/hydroponic/Hydroponics Data First Trial.csv` as local raw Experiment 1 data if present. It is ignored by git and should not be committed.
- Treat `data/raw/hydroponic/Agronomic Data.csv` as the authoritative per-plant harvest sheet for agronomic linkage when present. The parser supports the current wide two-experiment export plus normalized template/ANOVA exports. Keep TNL/NL10 as counts, and interpret linkage outputs as mechanistic deployment context rather than causal yield evidence.
- Optional limitation-closing hydroponic files are supported but not required: `data/raw/hydroponic/actuator_state_log.csv`, `data/raw/hydroponic/reference_measurements.csv`, and `data/raw/hydroponic/water_level_calibration.csv`. Generate schemas with `make optional-evidence` and `make water-calibration`; missing files should produce explicit absence-status outputs rather than breaking the benchmark.
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
- 2026-05-18: Rebalanced the ISA manuscript so the closed-loop hydroponic NFT platform, hardware/control architecture, deployment photograph, and agronomic operation evidence remain visible while AASVR stays the central research contribution.
- 2026-05-18: Expanded the ISA manuscript math formulation, references, hydroponic sensor/fault/tuning comparisons, highlights file, and float barriers to keep figures before references.
- 2026-05-18: Expanded the hydroponic synthetic-fault comparison to include one-class ML baselines, regenerated cleaner PDF/PNG plots, bolded best table metrics, resized/reworked TikZ figures to avoid overlap, and strengthened the manuscript framing so the hydroponic measurement-to-actuation failure problem leads into AASVR before cross-domain stress tests.
- 2026-05-18: Addressed reviewer-methodology concerns by adding deterministic tune/validation/test synthetic-fault splits, documenting the fault-injection protocol, tuning baselines on the validation split, wrapping all baselines in the same persistence/cooldown actuation supervisor, adding GLR and recursive PCA-style residual baselines, adding paired Wilcoxon/Holm and sensor-fault Benjamini-Hochberg tests, and updating the ISA manuscript/PDFs with held-out results and more cautious external-benchmark interpretation.
- 2026-05-19: Implemented the Round 2 final-submission revision: added a conservative stuck-value AASVR guard with tests and ablation output, added paired effect-size reporting, added lightweight external AASVR threshold-adaptation artifacts while demoting weak HAI/SKAB results to supplementary stress-test limitations, expanded the ISA manuscript with detection-delay/false-actuation-SD reporting and a bounded-rectification boundedness remark, and added LaTeX font/Unicode settings to prevent broken ligature extraction.
- 2026-05-19: Implemented the Round 3 final polish plan: rewrote the abstract without detailed numerical metrics, formalized the bounded-rectification statement as an informal proposition, clarified Holm correction families, added a tied-validation-setting consistency note, made the stuck-at false-actuation tail explicit, and tightened ablation/caption framing for final ISA-style submission.
- 2026-05-19: Implemented the Round 4 reviewer pass: corrected one-class baseline cooldown supervision, added an optional actuator-response residual hook with tests, expanded AASVR tuning, added component-contribution, objective-sensitivity, tuning-transfer, drift-stress, trial-level CI, sign-test, and effect-size outputs, and rewrote the ISA manuscript to emphasize AASVR as a formal measurement-to-actuation supervisor rather than an overclaimed point detector.
- 2026-05-19: Implemented the second-round reviewer revision: added AASVR audit-trail outputs, harmonized full-test component rows with the main benchmark, added supplementary Graph-AASVR residual experiments that showed higher recall but excessive false positives, added graph/audit table hooks and figure assets, expanded paired-effect reporting in the manuscript, and clarified trust-score, replay-authorization, and graph-transfer limitations.
- 2026-05-19: Replaced the graph-extension direction with AASVR-R as the main method: added actuator-response reliability memory, risk-aware authorization thresholds, response-replay benchmarking, response-residual figures/tables, AASVR-R statistical comparisons, updated architecture diagrams and PDFs, and removed the tracked Graph-AASVR experiment script from the paper path.
- 2026-05-19: Implemented and tested an optional AASVR-R2 robustness/efficiency variant with calibration-prefix robust gates, sequential response evidence, Beta response-reliability memory, and compact diagnostics. Held-out results did not justify replacing AASVR-R, so manuscript-facing statistics remain anchored on AASVR-R while R2 stays available in reproducibility outputs for future tuning.
- 2026-05-19: Added a validation-selected two-sided CUSUM residual gate to AASVR-R to improve small persistent shift detection without changing the response-aware authorization layer. Full held-out replay improved AASVR-R balanced accuracy above LOF while preserving low false-authorized actuation; updated manuscript math, tables, figures, and PDFs accordingly.
- 2026-05-19: Investigated stuck-at mitigation after the CUSUM improvement. An indefinite stuck latch improved stuck recall but collapsed specificity, so it was rejected. Added a bounded stuck-latch mechanism with tests, but validation selected zero latch samples; the limitation remains an identifiability issue without excitation, reference sensing, or real actuator-response logs.
- 2026-05-19: Added diagnostic-excitation replay for future actuator-state logging. Safe diagnostic pulses produced no false response residuals in healthy trials and detected stuck or weak diagnostic responses across primary sensors; updated metric/table hooks and manuscript text accordingly.
- 2026-05-19: Added the agronomic linkage plan implementation: per-plant harvest schema/template, validation and processed outputs, exposure-linkage metrics that connect AASVR-R decisions to P1 full-cycle deployment context without causal yield claims, table/figure hooks, tests, and manuscript protocol text.
- 2026-05-19: Updated the agronomic pipeline to parse the locally provided `Agronomic Data.csv` wide two-experiment harvest export directly, generated the 63-record agronomic processed/linkage outputs, and added actual harvest/linkage tables to the ISA manuscript without causal yield claims.
- 2026-05-19: Added absence-safe optional-evidence support for remaining limitations: actuator-state log, independent reference measurement, and water-level calibration schemas; real actuator-response scoring and water-level calibration utilities; Docker Make targets, tests, README/data documentation, and manuscript text specifying how future deployments can convert current counterfactual limitations into measured evidence.
- 2026-05-19: Addressed third-round AASVR-R reviewer concerns by reframing counterfactual response replay as a capability demonstration, adding missed authorization opportunity and authorization counts to agronomic linkage, labeling sign-test correction and BA-difference variance in paired statistics, relabeling ablations around AASVR-R, adding response-parameter and water-level calibration details, moving the audit trail near the headline benchmark, and rebuilding the author/blinded PDFs.
- 2026-05-19: Added the exhaustive hydroponic benchmark protocol: expanded fault injection types, full-factorial/shardable trial-grid generation, AASVR-R sweep generation, shard aggregation with per-cell counts and bootstrap intervals, Make targets, tests, README documentation, and manuscript text reframing novelty around the supervisor interface while noting the exhaustive run as the final large-scale sensitivity protocol.
- 2026-05-19: Added persistent-session launch scripts for the full exhaustive benchmark and AASVR-R sweep, worker variants for ordinary terminal sessions, a benchmark aggregation monitor, and ignored local run logs/PID files.
- 2026-05-20: Implemented the ISA polish revision plan: added full-split ablations, lockout-only component checks, trial counts, focused CUSUM and response-memory sensitivity outputs, regenerated paper tables/figures, and revised the manuscript to frame AASVR-R as a controller-facing supervisor with honest LOF/OC-SVM, exhaustive-profile, counterfactual-response, and stuck-at limitations.
- 2026-05-20: Reframed the ISA AASVR-R manuscript around replay tradeoffs, corrected the validation objective to penalize missed-authorization and unsafe-rate terms, retuned AASVR-R/baselines on the full validation split, regenerated statistics, and compressed main-paper floats toward the 30-page target.
- 2026-05-20: Addressed the Round 2 review follow-up by adding an independent actuator-log reconstruction/scoring path, actuator-response summary table hooks, tests and documentation for measured command-state evidence, and manuscript revisions for the AASVR-R tradeoff, trust-score scope, exhaustive-profile status, dataset-release statement, retuning note, and per-cell caveats.
- 2026-05-27: Added preemptive ISA revision artifacts for the unavailable actuator logs: evidence-status reporting, held-out replay operating-tradeoff sweeps, manuscript figure/table hooks, and stricter replay-only wording for false-authorized actuation.
- 2026-05-31: Implemented the next ISA reviewer-response hardening pass: added hydroponic-specific justification for the conservative AASVR-R operating point, elevated diagnostic-excitation replay as the stuck/weak-response mitigation demonstration, tightened data-availability wording, guarded against wrong-journal template footers and legacy P1/P2/P3 table-header mistakes, and documented that the old root hydroponics PDF should not be submitted unless regenerated from corrected editable source.
