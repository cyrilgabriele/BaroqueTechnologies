# Baroque

Baroque is a Python project for building and cleaning benchmark ETF market data.
The current data pipeline downloads daily OHLCV bars for `SPY` and `QQQ` from
Alpaca, stores one raw CSV per symbol, and builds a cleaned flat panel dataset.

## Prerequisites

- Python `>=3.14`
- [`uv`](https://docs.astral.sh/uv/) for dependency management
- Alpaca market data API credentials

The Python dependencies are declared in `pyproject.toml`:

- `pandas`
- `pyyaml`

## Setup

From the project root, install the Python environment:

```bash
uv sync
```

Create a `.env` file with your Alpaca credentials:

```bash
APCA_API_KEY_ID=your_api_key
APCA_API_SECRET_KEY=your_api_secret
```

The data pipeline reads these variables from the shell environment or from the
`.env` file configured in `src/config/data/indices.yaml`.

## Data Configuration

The benchmark dataset is configured in:

```text
src/config/data/indices.yaml
```

The current dataset definition is:

- Source: Alpaca stock bars API, `https://data.alpaca.markets/v2/stocks`
- Symbols: `SPY`, `QQQ`
- Timeframe: daily bars, `1Day`
- Feed: `iex`
- Adjustment: `all`
- Start date: `max`, resolved by the ingest script to `1900-01-01`
- End date: `today`, resolved at runtime
- Raw output directory: `data/raw/indices`
- Cleaned output file: `data/processed/indices_panel.csv`

With the current config loaders, these `data/...` paths resolve from the
workspace directory that contains this `baroque` checkout. From this directory,
that means:

```text
../data/raw/indices
../data/processed/indices_panel.csv
```

The cleaned panel keeps these columns:

```text
date, timestamp, symbol, open, high, low, close, volume, trade_count, vwap
```

## Download Raw Data

Run the ingest script from the project root:

```bash
uv run python src/data/data_ingest/ingest_data.py
```

This downloads daily bars for every symbol configured under `bars.symbols` in
`src/config/data/indices.yaml`.

The script writes one CSV per symbol:

```text
../data/raw/indices/SPY.csv
../data/raw/indices/QQQ.csv
```

Each raw file contains:

```text
date, timestamp, symbol, open, high, low, close, volume, trade_count, vwap
```

## Clean Data

After the raw CSV files exist, build the cleaned panel:

```bash
uv run python src/data/data_engineering/data_cleaning.py
```

By default this reads the symbols configured under `cleaning.symbols` in
`src/config/data/indices.yaml` and writes:

```text
../data/processed/indices_panel.csv
```

The cleaning step:

- validates that every required column is present
- normalizes symbol casing
- parses and validates dates and timestamps
- coerces price columns to floats
- coerces `volume` and `trade_count` to integers
- rejects missing values, duplicate dates, invalid OHLC relationships, and
  negative volume or trade counts
- trims small isolated edge segments and rejects unresolved history gaps

To clean a subset of symbols:

```bash
uv run python src/data/data_engineering/data_cleaning.py --symbols SPY
```

To write to a custom output path:

```bash
uv run python src/data/data_engineering/data_cleaning.py --output ../data/processed/custom_panel.csv
```

To keep only dates shared by all requested symbols:

```bash
uv run python src/data/data_engineering/data_cleaning.py --shared-dates-only
```

## Expected Workflow

Use this sequence for a fresh checkout:

```bash
uv sync
printf "APCA_API_KEY_ID=your_api_key\nAPCA_API_SECRET_KEY=your_api_secret\n" > .env
uv run python src/data/data_ingest/ingest_data.py
uv run python src/data/data_engineering/data_cleaning.py
```

After that, `../data/processed/indices_panel.csv` is ready for downstream research
or modeling.
