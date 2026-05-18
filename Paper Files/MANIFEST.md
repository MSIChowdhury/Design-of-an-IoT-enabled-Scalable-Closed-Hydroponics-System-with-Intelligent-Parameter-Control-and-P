# AASVR Paper Manifest

## Primary LaTeX sources

- `main_aasvr.tex`: author-visible ISA Transactions draft for the AASVR method paper.
- `main_aasvr_blinded.tex`: double-anonymized wrapper that compiles the same paper with author information removed.
- `aasvr_references.bib`: focused bibliography for the AASVR manuscript.

## TikZ/vector sources

- `figure/aasvr_architecture.tikz`: AASVR measurement-to-actuation architecture diagram.
- `figure/aasvr_state_machine.tikz`: AASVR persistence state-machine diagram.

## Result figures copied into the paper package

- `figure/hydro_exp1_synthetic_balanced_accuracy.png`: hydroponic synthetic-fault method comparison.
- `figure/hydro_exp1_balanced_accuracy_ci.png`: bootstrap confidence interval figure.
- `figure/hydro_exp1_ablation_balanced_accuracy.png`: ablation bar chart, retained for optional use.
- `figure/cross_dataset_rank_plot.png`: available-dataset method ranking figure.
- `figure/external_aasvr_threshold_sensitivity.png`: native-label aggregation sensitivity figure.
- `figure/hydro_exp1_ph_trace.png`: representative pH replay trace.

## Legacy figures retained from the earlier manuscript package

- `figure/Full_System_Final.pdf`: original system wiring diagram.
- `figure/fullsystemactual.JPG`: photograph of the physical system.
- `figure/tripartiate_data_collection.drawio.pdf`: original data-collection diagram.
- `figure/agronomic_parameters_violinplots.pdf` and `figure/agronomic_parameters_violinplots_new.pdf`: agronomic visualizations retained as secondary context only.

## Build command

From the repository root:

```bash
docker compose run --rm project-shell make paper
```

The build target compiles `main_aasvr.tex` and `main_aasvr_blinded.tex` with `latexmk`.
