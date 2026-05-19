# Editor Notes

- The current paper draft is hydroponic-system first while keeping AASVR as the research contribution. It intentionally demotes the web dashboard, XGBoost classifier, and crop-yield superiority claims.
- The latest revision makes the method section more mathematical: it now separates gates, trust scores, state transitions, rectification, and actuation authorization with explicit notation.
- The related-work and system sections now cite the main algorithms and hydroponic control context more directly, including one-class anomaly baselines. Keep adding primary references as coauthors identify journal-specific gaps.
- The current reviewer-response revision adds GLR and recursive PCA-style residual baselines, but the recursive PCA implementation is intentionally lightweight and should be described as a streaming residual baseline rather than a full multivariate industrial DPCA study.
- The Round 2 revision adds a conservative stuck-value guard. It only modestly improves stuck-at behavior and should be framed as mitigation, not as a solved stuck-sensor problem.
- Main comparison plots and tables are kept before the references with float barriers, matching the requested ISA-style article flow. Best table entries are bolded where the direction is unambiguous.
- Main generated plots are included as PDF exports for cleaner journal rendering, with PNG previews retained in the figure folder.
- The NFT platform, sensors, actuators, Raspberry Pi/Arduino control stack, and deployment photograph should remain visible before the abstract AASVR formulation.
- Hydroponic water level is excluded from primary analysis because the raw values are not defensibly calibrated.
- Hydroponic scoring relies on synthetic fault injection over real signal backgrounds because independent reference instruments are unavailable for every sensor at every time point.
- The hydroponic synthetic-fault benchmark now includes raw thresholding, the original manuscript method, moving average/median, Hampel, Kalman, EWMA, CUSUM, PCA-style residual monitoring, GLR, recursive PCA-style residual monitoring, Isolation Forest, One-Class SVM, and LOF. Full-feed one-class ML replay is intentionally not used as a headline result because it is much more expensive and produces large decision traces; the held-out synthetic-fault benchmark is the defensible comparison layer.
- Synthetic-fault trials are split deterministically into tune, validation, and test splits. AASVR and all baselines are tuned on validation and reported on held-out test rows.
- False-actuation comparisons now use the same persistence/cooldown authorization supervisor for every baseline, so the detector comparison and supervisor contribution are not conflated.
- HAI and SKAB are supplementary external stress tests, not main evidence. Validation-selected aggregation thresholds remain weak, so the main paper should not present them as cross-domain success.
- The agronomic trial is confounded by treatment differences. It should be presented only as full-cycle deployment context unless a stronger experimental design is added.
- The cross-dataset mean-rank plot and agronomic violin plots are generated artifacts only; they are intentionally not part of the main manuscript argument.
- The current draft is closer to a final submission: it includes paired effect-size reporting, a bounded-rectification boundedness remark, and ligature-safe PDF font setup. Coauthor scientific review should still check whether the stuck-at limitation language is acceptable.
