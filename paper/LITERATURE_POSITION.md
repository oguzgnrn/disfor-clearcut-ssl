# Literature position and claim boundaries

The intended contribution is a reproducible empirical audit of label efficiency and evaluation design, not a new Transformer architecture. No priority claim or state-of-the-art claim is made.

- **Zhang et al. 2025** applies a self-supervised Transformer to Sentinel-1 and Sentinel-2 time series for forest disturbance type detection in a subtropical ecosystem (title-level description; the full text could not be accessed, so no numbers or design details from it are cited). The Sentinel-2 masked reconstruction experiment here is not a reproduction of that system and its scores are not comparable.
- **Zerveas et al. 2021** establishes masked multivariate time-series representation learning as prior art. Masked reconstruction must not be presented as our invention.
- **Tseng et al. 2024** shows pretrained pixel time-series modeling with Presto. We did not benchmark pretrained foundation models; the manuscript cannot claim superiority over that family.
- **Saget et al. 2025** studies time-series augmentation in agricultural tasks. It motivates augmentation controls but does not substantiate performance in our forest task.
- **Viehweger et al. 2026** is the source dataset's current preprint, not an accepted dataset article. Official paper reports 3,822 points; the pinned dataset card says 3,823, while the actual table has 3,822. We use the inspected table count.
- **Roberts et al. 2017** supports structured validation. Five-kilometre grouping does not prove independence at every ecological scale. New folds cannot undo previous adaptive work on the same dataset.
- **Breiman 2001** motivates a strong tree baseline. **Guo et al. 2017** motivates evaluating calibration separately from classification. The primary cross-fitting analysis uses no fitted calibration; v3 calibration remains a secondary, previously developed engineering result.

Primary source metadata and links are stored in references.json and references.bib. No unavailable full text was represented as fully read. Search results and abstracts were not used to invent exact methodological details.

## References added 16 October 2026 (all DOI/metadata verified against Crossref or publisher pages)

- **Forest disturbance mapping lineage:** Hansen et al. 2013 (global forest cover change), Zhu & Woodcock 2014 (CCDC), Senf & Seidl 2021 (European disturbance regimes), Hirschmugl et al. 2017 (optical disturbance/degradation methods review; same group as the DISFOR authors), Wang et al. 2026 (global disturbance-type dataset, ESSD; the supervisor's suggested paper, inspected in QGIS).
- **Satellite time-series deep learning:** Pelletier et al. 2019 (TempCNN), Rußwurm & Körner 2020 (self-attention on raw optical series), Garnot et al. 2020 (PSE+TAE).
- **Masked / self-supervised pretraining:** He et al. 2022 (MAE), Yuan & Lin 2021 (SITS-BERT), Yuan et al. 2022 (SITS-Former), Cong et al. 2022 (SatMAE), Jakubik et al. 2023 (Prithvi). None of these is reproduced; they position masked reconstruction as established prior art and foundation models as an unaudited comparison family.
- **Spatial validation debate:** Ploton et al. 2020 and Meyer & Pebesma 2022 (random CV overstates map accuracy), Wadoux et al. 2021 (spatial CV is not always the right estimator — the appropriate design depends on the inference target). Our grouped folds target classification of new regions, not design-based map accuracy.
- **S1+S2 fusion applications suggested by the supervisor:** Maze et al. 2025 (Nile Delta), Vyas et al. 2024/25 (Punjab). They motivate the planned Sentinel-1 extension; they are not forest disturbance studies.
