# Figure Audit

| Figure file | Source | Format | Referenced in `main_aasvr.tex` | Notes |
|---|---|---:|---|---|
| `figure/aasvr_architecture.tikz` | New TikZ source | Vector | Yes | Main architecture figure; inherits LaTeX fonts and uses semantic colors. |
| `figure/aasvr_state_machine.tikz` | New TikZ source | Vector | Yes | State machine figure for Normal, Suspect transient, Persistent deviation, Accepted regime shift, and Fault-alert. |
| `figure/hydro_exp1_synthetic_balanced_accuracy.png` | Generated from analysis pipeline | Raster PNG | Yes | Acceptable as a plot export; should be regenerated from scripts for final revision if data change. |
| `figure/hydro_exp1_balanced_accuracy_ci.png` | Generated from analysis pipeline | Raster PNG | Yes | Bootstrap uncertainty plot. |
| `figure/external_aasvr_threshold_sensitivity.png` | Generated from analysis pipeline | Raster PNG | Yes | External native-label aggregation-threshold sensitivity. |
| `figure/cross_dataset_rank_plot.png` | Generated from analysis pipeline | Raster PNG | Yes | Used as an orientation figure, not a leaderboard claim. |
| `figure/hydro_exp1_ph_trace.png` | Generated from analysis pipeline | Raster PNG | Yes | Representative trace only; not used as a ground-truth label. |
| `figure/Full_System_Final.pdf` | Legacy manuscript asset | Vector PDF | No | Retained for possible expanded system-description section. |
| `figure/fullsystemactual.JPG` | Legacy manuscript asset | Raster JPG | No | Retained for application context, not used in the current method-focused draft. |
| `figure/agronomic_parameters_violinplots*.pdf` | Legacy manuscript asset | Vector PDF | No | Retained as secondary agronomic context only. |

Color use is restrained and semantic in the TikZ figures. The raster plots should be reviewed visually before submission and regenerated as vector PDF if the journal production workflow requires it.
