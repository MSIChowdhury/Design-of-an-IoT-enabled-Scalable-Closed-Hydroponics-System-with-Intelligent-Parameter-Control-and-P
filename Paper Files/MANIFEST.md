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

- `figure/hydro_exp1_synthetic_balanced_accuracy.png` and `.pdf`: hydroponic synthetic-fault method comparison.
- `figure/hydro_exp1_balanced_accuracy_ci.png` and `.pdf`: bootstrap confidence interval figure.
- `figure/hydro_exp1_ablation_balanced_accuracy.png`: ablation bar chart, retained for optional supplementary use.
- `figure/cross_dataset_rank_plot.png` and `.pdf`: retained as a generated diagnostic only; removed from the main manuscript because cross-domain rank averaging is not used as evidence.
- `figure/external_aasvr_threshold_sensitivity.png` and `.pdf`: native-label aggregation sensitivity figure retained for supplementary stress-test discussion only.
- `figure/hydro_exp1_ph_trace.png` and `.pdf`: representative pH replay trace.
- `figure/hydro_exp1_co2_trace.png` and `.pdf`: representative CO2 replay trace.
- `figure/hydro_exp1_fault_type_heatmap.png` and `.pdf`: fault-type by method balanced-accuracy heatmap.
- `figure/hydro_exp1_operating_tradeoff.png` and `.pdf`: replay false-authorized-actuation versus missed-authorization operating-point sweep.
- `figure/fullsystemactual.JPG`: real hydroponic deployment photograph used in the main manuscript.
- `figure/agronomic_parameters_violinplots_new.pdf`: secondary agronomic operation-evidence figure retained for supplementary use only.

## Legacy figures retained from the earlier manuscript package

- `figure/Full_System_Final.pdf`: original system wiring diagram.
- `figure/fullsystemactual.JPG`: photograph of the physical system, now used in the main hydroponic-system section.
- `figure/tripartiate_data_collection.drawio.pdf`: original data-collection diagram.
- `figure/agronomic_parameters_violinplots.pdf` and `figure/agronomic_parameters_violinplots_new.pdf`: agronomic visualizations retained as secondary context only; the current main manuscript uses a short non-causal deployment note instead of the multi-panel agronomic figure.

## Build command

From the repository root:

```bash
docker compose run --rm project-shell make paper
```

The build target compiles `main_aasvr.tex` and `main_aasvr_blinded.tex` with `latexmk`.

## Current revision focus

The current manuscript revision is a reviewer-response tightening pass: the conservative
AASVR-R operating point is now justified for slow hydroponic pH/EC dosing, the diagnostic-
excitation replay is elevated as the demonstrated stuck/weak-response mitigation pathway,
data availability wording follows the Elsevier data-statement model, and manuscript checks
guard against wrong-journal template footers and legacy P1/P2/P3 header mistakes.
