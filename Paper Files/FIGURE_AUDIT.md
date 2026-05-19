# Figure Audit

| Figure file | Source | Format | Referenced in `main_aasvr.tex` | Notes |
|---|---|---:|---|---|
| `figure/aasvr_architecture.tikz` | New TikZ source | Vector | Yes | Main architecture figure; redesigned as a two-row flow so labels remain readable in one column. |
| `figure/aasvr_state_machine.tikz` | New TikZ source | Vector | Yes | State machine figure for Normal, Suspect transient, Persistent deviation, Accepted regime shift, and Fault-alert. |
| `figure/hydroponic_system_architecture.tikz` | New TikZ source | Vector | Yes | Restores the hydroponic system as the primary engineered platform while showing where AASVR sits in the control loop; routing was adjusted to reduce arrow/text overlap. |
| `figure/hydro_exp1_synthetic_balanced_accuracy.pdf` | Generated from analysis pipeline | Vector PDF | Yes | Main method-comparison plot; includes classical filters, process-monitoring baselines, and one-class ML baselines. |
| `figure/hydro_exp1_balanced_accuracy_ci.pdf` | Generated from analysis pipeline | Vector PDF | Yes | Bootstrap uncertainty plot. |
| `figure/external_aasvr_threshold_sensitivity.pdf` | Generated from analysis pipeline | Vector PDF | No | Retained for supplementary stress-test discussion; removed from the main manuscript because HAI/SKAB direct transfer is weak. |
| `figure/cross_dataset_rank_plot.pdf` | Generated from analysis pipeline | Vector PDF | No | Retained as a diagnostic only; removed from the main manuscript because rank averaging across label semantics is not defensible as a headline result. |
| `figure/hydro_exp1_ph_trace.pdf` | Generated from analysis pipeline | Vector PDF | Yes | Representative trace only; not used as a ground-truth label. |
| `figure/hydro_exp1_co2_trace.pdf` | Generated from analysis pipeline | Vector PDF | Yes | Second representative trace to make gas-actuation behavior visible. |
| `figure/hydro_exp1_fault_type_heatmap.pdf` | Generated from analysis pipeline | Vector PDF | Yes | Fault-type comparison across methods; supports the more detailed results section. |
| `figure/fullsystemactual.JPG` | Legacy manuscript asset | Raster JPG | Yes | Used as real-deployment evidence; not a standalone contribution. |
| `figure/agronomic_parameters_violinplots_new.pdf` | Legacy manuscript asset | Vector PDF | No | Retained for supplementary use; the main paper now uses a short deployment note instead of the multi-panel crop figure. |
| `figure/Full_System_Final.pdf` | Legacy manuscript asset | Vector PDF | No | Retained for possible expanded system-description section. |
| `figure/agronomic_parameters_violinplots.pdf` | Legacy manuscript asset | Vector PDF | No | Older agronomic export retained for comparison; not used in the current draft. |

Color use is restrained and semantic in the TikZ figures. The main analysis plots are now included as PDF exports, with PNG counterparts retained for quick preview.
