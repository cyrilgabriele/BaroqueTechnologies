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

### [2026-06-16] - Cyril Gabriele

#### What
- Added the BTC RSI/ATR mean-reversion strategy feature panel script.
- Added a strategy-specific YAML config for the BTC RSI/ATR stop strategy.
- Kept shared cleaned BTC data strategy-neutral and wrote RSI/ATR features into a separate strategy feature panel.
- Added RSI(14), ATR(14), oversold armed state, buy signal, and buy-row-only initial stop price features.
- Updated Baroque domain language to distinguish **Cleaned Panel** from **Strategy Feature Panel**.

#### Why
- RSI, ATR, entry state, and stop-price helpers are strategy-specific and should not be baked into the shared cleaning layer.
- The first implementation should stay small while still producing the inputs needed for the RSI re-entry strategy.
- Computing the initial stop only on buy rows keeps trade-specific information explicit and avoids noisy hypothetical stop values.

#### Remarks
- The default stop multiple is `2.0 x ATR(14)`.
- Position sizing, trailing stops, exit simulation, and reward/risk filters are intentionally left for later backtesting work.

### [2026-06-12] - Cyril Gabriele

#### What
- Refactored data ingest into a provider-based architecture.
- Kept [`baroque/src/data/data_ingest/ingest_data.py`](/home/gabc/00_projects/BaroqueTechnologies/baroque/src/data/data_ingest/ingest_data.py) as the generic ingest entrypoint for config loading, provider dispatch, symbol iteration, and CSV writing.
- Added a provider contract in [`baroque/src/data/data_ingest/providers/base.py`](/home/gabc/00_projects/BaroqueTechnologies/baroque/src/data/data_ingest/providers/base.py).
- Added a provider registry/factory in [`baroque/src/data/data_ingest/providers/__init__.py`](/home/gabc/00_projects/BaroqueTechnologies/baroque/src/data/data_ingest/providers/__init__.py).
- Moved Alpaca-specific auth, request, pagination, and normalization logic into [`baroque/src/data/data_ingest/providers/alpaca.py`](/home/gabc/00_projects/BaroqueTechnologies/baroque/src/data/data_ingest/providers/alpaca.py).
- Implemented Binance kline ingestion in [`baroque/src/data/data_ingest/providers/binance.py`](/home/gabc/00_projects/BaroqueTechnologies/baroque/src/data/data_ingest/providers/binance.py), including date-to-millisecond conversion, pagination, configured field mapping, and normalized raw rows.
- Extended [`baroque/src/data/data_ingest/config_loader.py`](/home/gabc/00_projects/BaroqueTechnologies/baroque/src/data/data_ingest/config_loader.py) to validate exactly one supported provider, expose provider config, output columns, and raw Binance field mappings.
- Updated [`baroque/src/data/data_engineering/data_cleaning.py`](/home/gabc/00_projects/BaroqueTechnologies/baroque/src/data/data_engineering/data_cleaning.py) to accept `--config` and to validate `volume` / `trade_count` only when those columns exist.
- Updated [`baroque/src/data/data_engineering/config_loader.py`](/home/gabc/00_projects/BaroqueTechnologies/baroque/src/data/data_engineering/config_loader.py) to resolve relative config paths consistently.
- Updated [`baroque/README.md`](/home/gabc/00_projects/BaroqueTechnologies/baroque/README.md) with the provider architecture, Alpaca ETF commands, Binance BTC commands, and cleaning commands for both configs.

#### Why
- Multiple strategies will need multiple datasets and providers, so ingest should not remain coupled to Alpaca-specific request logic.
- Keeping source-specific API behavior inside provider modules makes the ingest entrypoint stable as new sources are added.
- Driving output columns and Binance raw field mapping from YAML keeps dataset shape explicit and avoids hardcoding source schemas in the generic pipeline.
- BTC data uses a slimmer schema than the ETF data, so cleaning validation needed to respect config-defined columns instead of assuming every raw panel has `volume` and `trade_count`.

#### Remarks
- Verified compilation for the data ingest and data engineering packages with `baroque/.venv/bin/python -m compileall`.
- Verified BTC and ETF config loading, Binance provider construction, Binance kline normalization, and BTC-style cleaning validation without live API calls.
- Live network ingestion against Binance and Alpaca was not run during this change.

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
