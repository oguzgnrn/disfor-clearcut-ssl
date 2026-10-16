# Claim ledger

| Claim | Measured evidence | Permitted interpretation |
|---|---|---|
| All 180 fits completed | `completion.json`, `runs/`, `verification.json` | Actual training; no simulated scores |
| SSL 0.8690 vs short Transformer 0.8322 at 20% labels | `analysis.json`, primary comparison | Conditional cohort-specific improvement; not general SSL superiority |
| Step-matched supervised 0.8987 exceeds SSL | `analysis.json`, exploratory control | Optimization budget materially changes ranking; no unique causal explanation |
| Full-label CNN 0.9299 | `analysis.json`, three pooled seed results | Mean across fixed spatial folds; not external test accuracy |
| Structured versus IID masking interval spans zero | `analysis.json`, exploratory comparison | No clear mask-design advantage here |
| Minimum cross-fold distance exceeds 5 km | `analysis.json`, folds | The stated graph rule is respected; no proof of spatial independence |
| Metadata/missingness carry predictive information | Diagnostic controls | Sampling-context diagnostic, not a causal shortcut percentage |
| 111 unused candidates include only one cut | `unused_probe_audit.json` | Insufficient independent positive support; no score reported |
| Recipes previously developed on the same source | `protocol.json` and earlier v2/v3 outputs | Retrospective audit, not untouched or nested external validation |
| Working engineering ensemble available | `models/advanced_v3/bundle.json` | Separate inference artifact, not the model evaluated by the new pooled audit |

Evidence paths in this table are relative to `experiments/paper_v4/` unless otherwise stated. Literature statements are linked to verified primary records in `references.json`; Zhang et al. is discussed only at the verified abstract-level scope. The dataset article is labeled a preprint under review. No unsupported first-of-kind or state-of-the-art claim is included.

## Declared extensions (added 16 October 2026)

| Claim | Measured evidence | Permitted interpretation |
|---|---|---|
| At 20 km grouping, SSL (0.8437) exceeds the step-matched control (0.8216) and CNN (0.7997); at 5 km the control leads (0.9017 vs 0.8726) | `experiments/paper_v5_exploratory/analysis.json`, seed 7 only, 75 fits | Descriptive sensitivity to the evaluation design; one seed; radius, folds and labeled subsets change together; no causal radius effect |
| 5 km seed-7 refits reproduce paper_v4 probabilities (max diff 2.2e-16) | `analysis.json` → `radius_5_v4_reproduction` | Reproduction check, not independent confirmation |
| Label-budget curve at 5/10/50% on identical folds and seeds | `experiments/paper_v6_label_curve/analysis.json`, 225 fits | Same cohort, same recipes; intervals at 5–10% are wide because few clear-cut components are labeled; trained on different hardware than v4 |
| Frozen Presto linear probe reaches ~0.71 macro-F1 at 20% labels | `experiments/presto_v1_exploratory/analysis.json` | Bounded exploratory note only; frozen encoder, missing modalities; not a foundation-model comparison |
