# Supplementary methods and reproduction guide

This supplement accompanies `manuscript.md`. The study is a retrospective empirical audit, not an untouched external benchmark. All numeric claims in the manuscript derive from `experiments/paper_v4/analysis.json`. The earlier v3 deployment ensemble is a separate engineering artifact.

## Reproduce the measured study

From the project root, use Python 3.11 and a clean environment:

```bash
python3.11 -m venv .venv-paper
.venv-paper/bin/python -m pip install -r requirements-lock.txt
.venv-paper/bin/python scripts/train_paper.py --workers 3
.venv-paper/bin/python scripts/analyze_paper.py
.venv-paper/bin/python scripts/verify_paper.py
.venv-paper/bin/python scripts/plot_paper.py
.venv-paper/bin/python scripts/compose_paper.py
.venv-paper/bin/python -m unittest discover -s tests -p test_paper.py -v
```

Completed run files are reused only if the frozen signature matches. To perform a genuinely fresh rerun, extract the supplied archive into a new directory and move its `experiments/paper_v4/runs` directory and `completion.json` outside that directory before invoking training. Preserve the originals for comparison. A new scientific protocol must use a new experiment version, not silently replace this study. The compact paper archive includes the eight paper-specific tests. The full project archive includes the 45 core tests, their additional legacy/raw-data dependencies, and the newly added product tests. The current combined test count and latest execution results are recorded in `reports/final_delivery_verification.json` in the full delivery; 45 is the earlier core count, not the final project total. The supplied processed NPZ is enough to reproduce fitting and analysis. Raw-source preparation and the unused-probe audit require the full project archive's original Parquet files.

Training used macOS 26.2 arm64, CPU execution, three worker processes and two PyTorch threads per worker. Exact numerical agreement across other operating systems, BLAS or PyTorch implementations is not guaranteed. The lock file records the tested Python package versions. Fit seconds are elapsed per task under concurrent execution, not independent hardware-normalized benchmarks. They include preparation and inference overhead. Do not sum them and call that total wall-clock runtime or energy use.

To edit the Word manuscript, install `requirements-paper.txt` and run `scripts/build_paper_docx.py`. The authoring script has no private runtime dependency. PDF export can use a compatible LibreOffice installation; the supplied PDF was exported with the bundled authoring runtime and visually checked. Figure PDFs preserve vector text and graphics. The JSON content source and Markdown are also supplied.

## Fixed protocol and outcomes

- Five group-stratified outer folds; random_state 4192026; seeds 7, 17, 27.
- Main methods: RF leaf 4, CNN width 64, Transformer width 48 and block-plus-band SSL Transformer width 48.
- Label fractions 0.2 and 1.0; per-class ceiling counts and shared nested identifiers.
- Neural classification: 40 epochs, AdamW, weight decay 0.01, batch size 64, clipping norm 1, inverse-frequency weighted cross-entropy, smoothing 0.02, random month removal probability 0.10.
- CNN: three residual blocks with two convolutions each, dilations 1/2/4, width 64, group normalization with four groups, GELU, dropout 0.20, learning rate 0.001.
- Transformer: two layers, width 48, four heads, feed-forward width 144, GELU, dropout 0.15, learning rate 0.0005, masked mean pooling.
- SSL: 60 reconstruction epochs, AdamW learning rate 0.001, Smooth L1 on hidden observed values, one contiguous 2–6 month block plus two channels. Classifier weights are reset to the paired initial state before fine-tuning.
- At 20% labels only: independent observed-cell SSL (probability 1/3), 320-epoch supervised Transformer, mask-only RF, and metadata-only RF.
- RF: 500 trees, minimum leaf size 4, max_features 0.7, balanced_subsample weights; no iterative epoch notion. Its run record's top-level `epochs=40` is the generic requested training argument; the fitted RF actually has `log.best_epoch=0` and an empty history. This field must not be read as forty RF training passes.
- Probability threshold 0.5 throughout. No calibration, validation labels, early stopping, or outcome-based fold/seed selection in this audit.

Nominal one-third masking equality holds in expectation across a fully observed grid. Contiguous blocks have nonuniform inclusion probabilities at calendar boundaries, and real observed support differs by month. The IID experiment is a nominal coverage control, not an exact per-sample hidden-cell matching experiment. This limitation is stated in the manuscript.

The step-matched control approximately equalizes optimizer-update counts, not FLOPs or supervised label exposure. In this dataset it receives 320 supervised epochs. It can therefore repeat each labeled sample more times. Its superior thresholded macro-F1 refutes a simple claim that the chosen SSL recipe is better than all similarly extended supervised training; it does not prove a unique causal mechanism.

## Evidence files

| Evidence | File |
|---|---|
| Frozen protocol and development history | `experiments/paper_v4/protocol.json` |
| Code/data/protocol hashes | `experiments/paper_v4/signature.json` |
| Every train/test identifier | `experiments/paper_v4/folds.json` |
| All 180 declared jobs | `experiments/paper_v4/jobs.json` |
| Per-fit labeled identifiers, losses and predictions | `experiments/paper_v4/runs/*.json` |
| Completion state | `experiments/paper_v4/completion.json` |
| Pooled metrics and paired intervals | `experiments/paper_v4/analysis.json` |
| Machine-readable pooled probabilities | `experiments/paper_v4/oof_predictions.npz` |
| Integrity and recomputation checks | `experiments/paper_v4/verification.json` |
| Unused-point support audit, deliberately unscored | `experiments/paper_v4/unused_probe_audit.json` |
| Earlier data filtering | `reports/disfor_preparation.json` |
| Source license | `data/disfor/LICENSE` |

The pooled NPZ contains `ids`, `y`, `groups`, and twelve method-budget probability arrays, each shaped (3, 2213). Row order follows seeds 7, 17, 27. Its 79,668 probabilities are repeated-model observations on 2,213 locations, not 79,668 independent samples. Metrics are calculated per seed after pooling all five held-out folds. Bootstrap draws keep seed replicates together and resample spatial components; they are conditional intervals for already fitted predictions.

## What this package does not establish

There is no new architecture, external field validation, national forest map, fire/disease benchmark, real-time warning system, SOTA comparison, public code DOI or journal acceptance. Recipes and cohort choices were developed on DISFOR before this audit, so new folds do not erase adaptive selection. The unused-location support audit has only one positive among 111 candidates and is not scored. Human author, institutional, funding and publication decisions are recorded separately in `AUTHOR_CONFIRMATION.md`.

## Additional final audit

See `ERROR_AUDIT.md` for descriptive campaign/year support and persistent-error review candidates. These post hoc checks do not replace the fixed main experiment. Run `scripts/audit_paper_errors.py` on the supplied cohort, or `scripts/audit_data_reproduction.py` with the full raw-data project.

## Turkish research report and local product

The supervisor presentation and full project deliveries also provide a [Turkish research and product report](../output/final/Orman_SSL_Arastirma_ve_Urun_Raporu.pdf), its [editable Word version](../output/final/Orman_SSL_Arastirma_ve_Urun_Raporu.docx), and a [meeting guide](../docs/GORUSME_AKISI_VE_SORULAR.md). The [product guide](../docs/URUN_KILAVUZU.md) explains the local application, started with `URUNU_AC.command` from the full project. These linked presentation/product files are separate from the compact scientific archive's minimum reproduction contents.

The local application performs inference with the previously trained ten-member `advanced_v3` ensemble. Its example set comprises the previously examined 486 locations. Running the application again reconstructs inputs and predictions from raw observations; it does not retrain the models or create a new external evaluation. The `paper_v4` results in this supplement concern the separate fixed-threshold cross-fitting experiment.

## Declared extensions: paper_v5 (grouping radius) and paper_v6 (label-budget curve)

Two extensions were declared and run after the frozen paper_v4 audit. Neither modifies any paper_v4 or product file; each has its own protocol, signature file, run records and verification output, and each refuses to run if a frozen v4 input changes.

**paper_v5_exploratory** regroups the identical cohort at 5, 10 and 20 km (transitive distance graph plus campaign 1/3 source events) and refits the five recipes on the induced five-fold partitions at 20% labels, seed 7 only (75 fits, every checkpoint retained with SHA-256). The 5 km, seed-7 fits reproduce the paper_v4 probabilities to within 2.2e-16. Files: `experiments/paper_v5_exploratory/{protocol,support_audit,groups,jobs,signature,analysis,verification,checkpoint_verification}.json`, `results.csv`, `runs/`, `checkpoints/`; Turkish report `docs/PAPER_V5_MEKANSAL_DUYARLILIK.md`.

```bash
.venv/bin/python scripts/scientific_v5.py prepare
.venv/bin/python scripts/scientific_v5.py train --workers 2
.venv/bin/python scripts/scientific_v5.py analyze
.venv/bin/python scripts/verify_spatial_v5.py            # --tolerance 1e-5 when reloading on a different OS/torch build
.venv/bin/python scripts/report_spatial_v5.py
```

**paper_v6_label_curve** adds the 5%, 10% and 50% label budgets on the frozen paper_v4 folds, seeds (7, 17, 27), nested label-allocation rule, recipes and 0.5 threshold, for RF, CNN, 40-epoch Transformer, block-and-band SSL and the step-matched Transformer (225 fits). Label subsets are declared in `label_allocation.json` before training and checked at fit time; 5% and 10% subsets are prefixes of the v4 20% subsets within each seed and class, and the 50% subset contains it. The analysis pools out-of-fold predictions per seed, reports mean ± SD over seeds and paired spatial-component bootstrap intervals (2,000 draws, seed 120926, identical construction to `analyze_paper.py`), and writes a combined curve with the v4 20% and 100% results. Files: `experiments/paper_v6_label_curve/{protocol,label_allocation,jobs,signature,preparation_event,execution,analysis,verification}.json`, `combined_curve.csv`, `oof_predictions.npz`, `runs/`.

```bash
.venv/bin/python scripts/label_curve_v6.py prepare
.venv/bin/python scripts/label_curve_v6.py train --workers 2
.venv/bin/python scripts/label_curve_v6.py analyze
.venv/bin/python scripts/plot_extensions.py              # paper/figures/04_label_curve, 05_radius
.venv/bin/python -m unittest tests.test_label_curve_v6 tests.test_scientific_v5 -v
```

The v6 fits were trained on a Linux x86-64 container (Python 3.13, PyTorch 2.14 CPU) rather than the macOS environment used for paper_v4; the platform is recorded in `execution.json`. Recipes, seeds and label identifiers are identical, so results are comparable up to float32-level platform differences; v6 checkpoints were not retained, exact recipes and seeds allow regeneration. Both extensions remain same-source retrospective analyses on the DISFOR cohort and are reported in Sections 5.1–5.2 of the manuscript with their limitations.

## Declared Türkiye zero-shot transfer probe (not yet executed)

`scripts/turkiye_zero_shot.py` freezes a candidate list from the Hansen Global Forest Change product (compact loss patches for 2019 to 2022 and loss-free forest, tree cover 2000 at least 50 percent, 5 km separation) inside five Turkish forest regions, fetches Sentinel-2 L2A observations from the Earth Search archive, builds inputs under the data contract (SCL 4/5, monthly median, BOA offset removed for processing baseline 04.00 and later), applies the frozen advanced_v3 bundle and optional full-cohort recipes, and reports macro-F1 with a 5 km component bootstrap. Launcher: `TURKIYE_TESTI_CALISTIR.command`. Pure helpers are unit tested in `tests/test_turkiye_zero_shot.py`. No result from this probe is cited anywhere until it has been run.
