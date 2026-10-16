# Post hoc error and support audit

This is an additional descriptive audit performed after the fixed study. It changes no labels, trained models, thresholds or primary endpoints.

The cohort contains 874 spatial components, including 141 with a clear-cut label. The largest component contains 45 points. 0 exact feature-trajectory duplicate clusters were found; none crosses outer folds. 215 source-event keys were checked; none crosses folds.

The review list contains 81 locations misclassified by at least two of three full-label CNN seeds or at least two of three full-label SSL seeds. These are review candidates, not corrected labels. Open `experiments/paper_v4/review_candidates.geojson` in QGIS; per-model probabilities and source metadata are retained.

## Full-label CNN by source campaign and target year
| Stratum | N | Stable / cut | Macro-F1 | AP |
|---|---:|---:|---:|---:|
| dataset 1 | 290 | 211 / 79 | 0.9421 | 0.9599 |
| dataset 2 | 1829 | 1641 / 188 | 0.9236 | 0.9164 |
| dataset 3 | 94 | 85 / 9 | 0.9277 | 0.9926 |
| year 2018 | 645 | 577 / 68 | 0.9168 | 0.9058 |
| year 2019 | 388 | 312 / 76 | 0.9426 | 0.9459 |
| year 2020 | 328 | 263 / 65 | 0.9418 | 0.9542 |
| year 2021 | 286 | 246 / 40 | 0.9444 | 0.9472 |
| year 2022 | 265 | 253 / 12 | 0.8188 | 0.7450 |
| year 2023 | 301 | 286 / 15 | 0.9279 | 1.0000 |



All four primary methods at both label budgets are recorded in `support_error_audit.json`. The table uses the existing pooled out-of-fold predictions; it is not a leave-campaign-out or forward-time validation. Confidence intervals are not added to these post hoc subgroup summaries.

## Raw-data reproduction

`data_reproduction_audit.json` records an isolated rebuild from pinned original Parquet files and an exact comparison of every processed array and sample-provenance entry. The manifest checksum is recorded at final audit time; it was not part of the original pre-score training signature.
