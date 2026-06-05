# Production Chain Mapping

This repository mirrors the roles described in Chapter 1.3.1 of *Advances in Financial Machine Learning*.

- `afml_pipeline/data_structuring`: data engineering seat – bars, rolls, volatility signature plots.
- `afml_pipeline/labeling`: labeling researchers – triple-barrier, meta labels.
- `afml_pipeline/weighting_stationarity`: weighting + stationarity team – uniqueness, fracdiff, sequential bootstrap.
- `afml_pipeline/feature_library`: feature catalog contributions.
- `afml_pipeline/evaluation_pipeline`: modelers + risk team – purged CV, feature importance, backtesting, bet sizing.

`run_pipeline.py` ties everything into the end-to-end research workflow as each chapter is implemented.
