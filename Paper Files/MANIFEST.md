# AASVR Paper Manifest

## Primary LaTeX sources

- `main_aasvr.tex`: author-visible ISA Transactions draft for the AASVR method paper.
- `main_aasvr_blinded.tex`: double-anonymized wrapper that compiles the same paper with author information removed.
- `aasvr_references.bib`: focused bibliography for the AASVR manuscript.
- `highlights_aasvr_blinded.txt`: ISA-style blinded highlights for the revised submission package.

## TikZ/vector sources

- `figure/aasvr_architecture.tikz`: AASVR measurement-to-actuation architecture diagram.
- `figure/aasvr_state_machine.tikz`: AASVR persistence state-machine diagram.
- `figure/hydroponic_system_architecture.tikz`: hydroponic platform/control-loop architecture diagram.

## Result figures copied into the paper package

- `figure/hydro_exp1_synthetic_balanced_accuracy.png`: hydroponic synthetic-fault method comparison.
- `figure/hydro_exp1_balanced_accuracy_ci.png`: bootstrap confidence interval figure.
- `figure/hydro_exp1_ablation_balanced_accuracy.png`: ablation bar chart, retained for optional use.
- `figure/cross_dataset_rank_plot.png`: available-dataset method ranking figure.
- `figure/external_aasvr_threshold_sensitivity.png`: native-label aggregation sensitivity figure.
- `figure/hydro_exp1_ph_trace.png`: representative pH replay trace.
- `figure/hydro_exp1_co2_trace.png`: representative CO2 replay trace.
- `figure/hydro_exp1_fault_type_heatmap.png`: fault-type by method balanced-accuracy heatmap.
- `figure/fullsystemactual.JPG`: real hydroponic deployment photograph used in the main manuscript.
- `figure/agronomic_parameters_violinplots_new.pdf`: secondary agronomic operation-evidence figure.

## Legacy figures retained from the earlier manuscript package

- `figure/Full_System_Final.pdf`: original system wiring diagram.
- `figure/fullsystemactual.JPG`: photograph of the physical system, now used in the main hydroponic-system section.
- `figure/tripartiate_data_collection.drawio.pdf`: original data-collection diagram.
- `figure/agronomic_parameters_violinplots.pdf` and `figure/agronomic_parameters_violinplots_new.pdf`: agronomic visualizations retained as secondary context only; the `_new` version is used in the main manuscript with a non-causal caption.

## Build command

From the repository root:

```bash
docker compose run --rm project-shell make paper
```

The build target compiles `main_aasvr.tex` and `main_aasvr_blinded.tex` with `latexmk`.

## Current revision focus

The current manuscript revision expands the mathematical formulation, adds notation and
sensor/fault/tuning comparison tables, strengthens algorithm and hydroponics citations,
and places main figures/tables before the reference list with float barriers.
