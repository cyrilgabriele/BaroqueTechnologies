# Changelog

Track what was changed, why it was changed, and any important notes.

## Entry Format

```markdown
### [YYYY-MM-DD] - [Contributor Name]

#### What
- List changes here

#### Why
- Explain reasoning

#### Remarks
- Optional notes, issues, or future work
```

---

### [2026-04-10] - Cyril Gabriele

#### What
- Reviewed the current Baroque data pipeline and raw benchmark ETF inputs for `SPY` and `QQQ`.
- Confirmed that the raw daily index data lives under `data/raw/indices/` and identified a data-quality issue in `SPY.csv`: an isolated `2018-11-01` row outside the main continuous history.
- Implemented the first cleaning layer for the index dataset in [`baroque/src/data/data_engineering/data_cleaning.py`](/Users/cyrilgabriele/Documents/Private/00_projects/finance/BaroqueTechnologies/baroque/src/data/data_engineering/data_cleaning.py).
- Built a flat canonical panel dataset with one row per `(date, symbol)` instead of a wide or permanently multi-indexed representation.
- Kept the canonical panel unbalanced by design, while also adding an optional `--shared-dates-only` filter for pair-analysis convenience.
- Added validation and coercion logic for required columns, symbol consistency, `date` / `timestamp` agreement, numeric type parsing, duplicate date detection, basic OHLCV sanity checks, and isolated edge-segment trimming for broken history.
- Explicitly trimmed the lone bad `SPY` observation on `2018-11-01`, leaving aligned continuous history for both `SPY` and `QQQ` from `2020-07-27` to `2026-04-09`.
- Wrote the cleaned panel to [`data/processed/indices_panel.csv`](/Users/cyrilgabriele/Documents/Private/00_projects/finance/BaroqueTechnologies/data/processed/indices_panel.csv).
- Refactored hardcoded cleaning constants out of the module and moved them into the shared YAML config at [`baroque/src/config/data/indices.yaml`](/Users/cyrilgabriele/Documents/Private/00_projects/finance/BaroqueTechnologies/baroque/src/config/data/indices.yaml).
- Added a dedicated config loader for the data-engineering layer in [`baroque/src/data/data_engineering/config_loader.py`](/Users/cyrilgabriele/Documents/Private/00_projects/finance/BaroqueTechnologies/baroque/src/data/data_engineering/config_loader.py), following the same pattern already used by data ingest.
- Updated [`baroque/pyproject.toml`](/Users/cyrilgabriele/Documents/Private/00_projects/finance/BaroqueTechnologies/baroque/pyproject.toml) to declare `pandas` and `PyYAML` as project dependencies.
- Synced the Baroque virtual environment and verified the cleaner using both the system interpreter and `baroque/.venv/bin/python`.

#### Why
- The project roadmap calls for building a clean panel dataset before feature engineering, targets, and backtesting.
- A long flat panel is the simplest format for immediate `SPY` / `QQQ` relationship work while still scaling cleanly to a future multi-stock universe.
- Keeping the canonical dataset unbalanced avoids over-constraining future research when more symbols are added.
- Moving cleaning parameters into YAML removes brittle hardcoded values from the script and keeps ingest and cleaning driven by the same configuration source.
- Explicit validation was necessary to catch bad history early, because one broken bar can contaminate all downstream lagged and rolling features.

#### Remarks
- The current cleaned pair dataset contains `2866` rows total: `1433` for `SPY` and `1433` for `QQQ`.
- The optional shared-dates-only output is currently identical to the unbalanced panel because both symbols fully overlap after cleaning.
- The next logical step is to engineer pair-focused historical features on top of this cleaned panel, using only backward-looking information.
