# Baroque

Baroque is a Python project for ingesting, cleaning, and researching historical
market data. The data pipeline is provider-based: a YAML config selects the data
source, the generic ingest script dispatches to the matching provider, and the
cleaning layer builds a flat panel dataset for downstream strategy research.

The current ingest providers are:

- Alpaca stock bars for benchmark ETF data such as `SPY` and `QQQ`
- Binance klines for crypto data such as `BTCUSDT`

## Prerequisites

- Python `>=3.14`
- [`uv`](https://docs.astral.sh/uv/) for dependency management
- Alpaca market data API credentials only when ingesting Alpaca data

The Python dependencies are declared in `pyproject.toml`:

- `pandas`
- `pyyaml`

## Setup

From the `baroque` package directory, install the Python environment:

```bash
uv sync
```

For Alpaca ingest, create a `.env` file with your Alpaca credentials:

```bash
APCA_API_KEY_ID=your_api_key
APCA_API_SECRET_KEY=your_api_secret
```

The Alpaca provider reads these variables from the shell environment or from the
`.env` file configured in `src/config/data/etf_data_config.yaml`.

Binance public kline ingest does not require API credentials.

## Data Configuration

Data ingest and cleaning are driven by YAML files under:

```text
src/config/data/
```

Current configs:

```text
src/config/data/etf_data_config.yaml
src/config/data/btc_data_config.yaml
```

Each config defines:

- the provider section, such as `alpaca` or `binance`
- raw output paths under `paths`
- bar symbols, dates, and interval/timeframe under `bars`
- raw CSV columns under `output_columns` when the source needs a custom schema
- cleaning input, output, required columns, numeric types, and gap rules under
  `cleaning`

The config loaders resolve `data/...` paths from the workspace directory that
contains this `baroque` checkout. In this repository layout, that means outputs
are written next to the package directory:

```text
data/raw/indices/
data/raw/crypto/
data/processed/
```

## Provider Architecture

The ingest entrypoint is intentionally generic:

```text
src/data/data_ingest/ingest_data.py
```

It loads the YAML config, asks the provider registry for the matching provider,
fetches normalized rows for each symbol, and writes raw CSV files.

Provider-specific API logic lives under:

```text
src/data/data_ingest/providers/
```

Current provider files:

```text
providers/alpaca.py
providers/binance.py
```

The provider factory is exposed from `providers/__init__.py` as `get_provider`.
This keeps `ingest_data.py` independent from source-specific classes. Adding a
new source should only require a new provider module, a registry entry, and a
YAML config.

## Ingest ETF Data From Alpaca

From the workspace root, run:

```bash
baroque/.venv/bin/python baroque/src/data/data_ingest/ingest_data.py \
  --config baroque/src/config/data/etf_data_config.yaml
```

Or from the `baroque` package directory:

```bash
uv run python src/data/data_ingest/ingest_data.py \
  --config src/config/data/etf_data_config.yaml
```

This writes one raw CSV per symbol:

```text
data/raw/indices/SPY.csv
data/raw/indices/QQQ.csv
```

The ETF raw files keep:

```text
date, timestamp, symbol, open, high, low, close, volume, trade_count, vwap
```

## Ingest BTC Data From Binance

From the workspace root, run:

```bash
baroque/.venv/bin/python baroque/src/data/data_ingest/ingest_data.py \
  --config baroque/src/config/data/btc_data_config.yaml
```

Or from the `baroque` package directory:

```bash
uv run python src/data/data_ingest/ingest_data.py \
  --config src/config/data/btc_data_config.yaml
```

This fetches Binance daily klines for `BTCUSDT` and writes:

```text
data/raw/crypto/BTCUSDT.csv
```

The BTC raw file keeps:

```text
date, timestamp, symbol, open, high, low, close
```

The Binance field mapping is configured in `raw_kline_fields` inside
`btc_data_config.yaml`.

## Clean Data

After raw CSV files exist, build the cleaned panel with the same config.

ETF panel:

```bash
baroque/.venv/bin/python baroque/src/data/data_engineering/data_cleaning.py \
  --config baroque/src/config/data/etf_data_config.yaml
```

BTC panel:

```bash
baroque/.venv/bin/python baroque/src/data/data_engineering/data_cleaning.py \
  --config baroque/src/config/data/btc_data_config.yaml
```

The default cleaned outputs are:

```text
data/processed/indices_panel.csv
data/processed/btc_panel.csv
```

The cleaning step:

- validates that every configured required column is present
- normalizes symbol casing
- parses and validates dates and timestamps
- coerces configured float columns
- coerces configured integer columns
- rejects missing values, duplicate dates, and invalid OHLC relationships
- rejects negative `volume` and `trade_count` values when those columns exist
- trims small isolated edge segments and rejects unresolved history gaps

To clean a subset of symbols:

```bash
baroque/.venv/bin/python baroque/src/data/data_engineering/data_cleaning.py \
  --config baroque/src/config/data/etf_data_config.yaml \
  --symbols SPY
```

To write to a custom output path:

```bash
baroque/.venv/bin/python baroque/src/data/data_engineering/data_cleaning.py \
  --config baroque/src/config/data/btc_data_config.yaml \
  --output data/processed/custom_btc_panel.csv
```

To keep only dates shared by all requested symbols:

```bash
baroque/.venv/bin/python baroque/src/data/data_engineering/data_cleaning.py \
  --config baroque/src/config/data/etf_data_config.yaml \
  --shared-dates-only
```

## Expected Workflows

ETF workflow:

```bash
cd baroque
uv sync
printf "APCA_API_KEY_ID=your_api_key\nAPCA_API_SECRET_KEY=your_api_secret\n" > .env
uv run python src/data/data_ingest/ingest_data.py --config src/config/data/etf_data_config.yaml
uv run python src/data/data_engineering/data_cleaning.py --config src/config/data/etf_data_config.yaml
```

BTC workflow:

```bash
cd baroque
uv sync
uv run python src/data/data_ingest/ingest_data.py --config src/config/data/btc_data_config.yaml
uv run python src/data/data_engineering/data_cleaning.py --config src/config/data/btc_data_config.yaml
```

After these workflows, the cleaned panels under `data/processed/` are ready for
downstream feature engineering, backtesting, and strategy research.
