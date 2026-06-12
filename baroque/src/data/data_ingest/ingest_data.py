"""Fetch historical bars from a configured provider and store raw CSV files."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Iterable

from config_loader import DataIngestConfig, load_data_ingest_config
from providers import get_provider
from providers.base import BarRow


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch historical bars and store them as raw CSV files."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to the data ingest YAML config. Defaults to the ETF config.",
    )
    return parser.parse_args()


def resolve_start_date(start: str, earliest_request_date: str) -> str:
    if start.strip().lower() == "max":
        return earliest_request_date

    return start


def write_csv(
    output_dir: Path,
    symbol: str,
    rows: Iterable[BarRow],
    fieldnames: tuple[str, ...],
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{symbol.upper()}.csv"

    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    return output_path


def ingest_data(config: DataIngestConfig) -> None:
    provider = get_provider(config)
    start = resolve_start_date(config.start_date, config.earliest_request_date)

    for symbol in config.symbols:
        rows = provider.fetch_symbol_bars(symbol, start, config.end_date)
        if not rows:
            raise RuntimeError(
                f"No bars returned for {symbol.upper()} between {start} and "
                f"{config.end_date} from {provider.name}."
            )

        output_path = write_csv(
            config.output_dir,
            symbol,
            rows,
            config.output_columns,
        )
        print(f"Wrote {len(rows)} rows to {output_path}")


def main() -> None:
    args = parse_args()
    if args.config is not None:
        config = load_data_ingest_config(args.config)
        ingest_data(config)
    else: raise Exception("Config missing!")


if __name__ == "__main__":
    main()
