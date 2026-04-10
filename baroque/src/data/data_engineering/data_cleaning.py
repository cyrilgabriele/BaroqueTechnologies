"""Build a cleaned flat panel dataset from raw benchmark ETF bars."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import pandas as pd

from config_loader import DataCleaningConfig, load_data_cleaning_config


@dataclass(frozen=True)
class CleaningSummary:
    symbol: str
    rows_in: int
    rows_out: int
    start_date: str
    end_date: str
    dropped_dates: tuple[str, ...]


def parse_args(config: DataCleaningConfig) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a cleaned flat panel dataset from raw benchmark ETF bars."
    )
    parser.add_argument(
        "--symbols",
        nargs="+",
        default=list(config.symbols),
        help=(
            "Symbols to include in the panel. Defaults to the symbols declared in "
            "the cleaning config."
        ),
    )
    parser.add_argument(
        "--output",
        default=str(config.output_path),
        help=f"Output CSV path. Defaults to {config.output_path}.",
    )
    parser.add_argument(
        "--shared-dates-only",
        action="store_true",
        help=(
            "Optional convenience filter for pair analysis. When set, only keep "
            "dates shared by all requested symbols."
        ),
    )
    return parser.parse_args()


def load_symbol_frame(symbol: str, config: DataCleaningConfig) -> pd.DataFrame:
    path = config.input_dir / f"{symbol.upper()}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Raw data file not found for {symbol.upper()}: {path}")

    frame = pd.read_csv(path)
    missing_columns = [
        column for column in config.required_columns if column not in frame.columns
    ]
    if missing_columns:
        raise ValueError(
            f"{path} is missing required columns: {', '.join(missing_columns)}"
        )

    return frame.loc[:, list(config.required_columns)].copy()


def clean_symbol_frame(
    symbol: str, config: DataCleaningConfig
) -> tuple[pd.DataFrame, CleaningSummary]:
    frame = load_symbol_frame(symbol, config)
    if frame.empty:
        raise ValueError(f"{symbol.upper()} raw data file is empty.")

    rows_in = len(frame)
    symbol = symbol.upper()
    original_dates = tuple(frame["date"].astype(str).tolist())

    frame["symbol"] = frame["symbol"].astype(str).str.upper().str.strip()
    invalid_symbol_rows = frame["symbol"] != symbol
    if invalid_symbol_rows.any():
        bad_symbols = sorted(frame.loc[invalid_symbol_rows, "symbol"].unique().tolist())
        raise ValueError(
            f"{symbol} raw data contains mismatched symbols: {', '.join(bad_symbols)}"
        )

    frame["date"] = pd.to_datetime(frame["date"], format="%Y-%m-%d", errors="raise")
    parsed_timestamps = pd.to_datetime(frame["timestamp"], utc=True, errors="raise")
    frame["timestamp"] = parsed_timestamps.dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    timestamp_dates = parsed_timestamps.dt.strftime("%Y-%m-%d")
    declared_dates = frame["date"].dt.strftime("%Y-%m-%d")
    mismatched_dates = timestamp_dates != declared_dates
    if mismatched_dates.any():
        bad_rows = frame.loc[mismatched_dates, ["date", "timestamp"]].head(5)
        raise ValueError(
            f"{symbol} contains date/timestamp mismatches. Sample:\n{bad_rows}"
        )

    for column in config.float_columns:
        frame[column] = pd.to_numeric(frame[column], errors="raise")

    for column in config.integer_columns:
        values = pd.to_numeric(frame[column], errors="raise")
        non_integer_values = values % 1 != 0
        if non_integer_values.any():
            raise ValueError(f"{symbol} column {column} contains non-integer values.")
        frame[column] = values.astype("int64")

    if frame.isna().any().any():
        missing = frame.isna().sum()
        missing = missing[missing > 0].to_dict()
        raise ValueError(f"{symbol} contains missing values after coercion: {missing}")

    duplicate_dates = frame["date"].duplicated(keep=False)
    if duplicate_dates.any():
        duplicates = frame.loc[duplicate_dates, "date"].dt.strftime("%Y-%m-%d").tolist()
        raise ValueError(f"{symbol} contains duplicate dates: {duplicates[:10]}")

    frame = frame.sort_values("date").reset_index(drop=True)
    frame = trim_isolated_edge_segments(frame, symbol, config)
    validate_ohlcv_relationships(frame, symbol)

    frame["date"] = frame["date"].dt.strftime("%Y-%m-%d")
    summary = CleaningSummary(
        symbol=symbol,
        rows_in=rows_in,
        rows_out=len(frame),
        start_date=frame["date"].iloc[0],
        end_date=frame["date"].iloc[-1],
        dropped_dates=tuple(sorted(set(original_dates) - set(frame["date"]))),
    )
    return frame, summary


def trim_isolated_edge_segments(
    frame: pd.DataFrame,
    symbol: str,
    config: DataCleaningConfig,
) -> pd.DataFrame:
    gap_lengths = frame["date"].diff().dt.days.fillna(0)
    segment_starts = [
        0,
        *gap_lengths[
            gap_lengths > config.max_allowed_calendar_gap_days
        ].index,
    ]
    segment_ends = [*segment_starts[1:], len(frame)]
    segments = [
        frame.iloc[start:end].copy() for start, end in zip(segment_starts, segment_ends)
    ]

    if len(segments) == 1:
        return frame

    segments_to_drop: set[int] = set()
    if len(segments[0]) <= config.max_isolated_edge_rows:
        segments_to_drop.add(0)
    if len(segments[-1]) <= config.max_isolated_edge_rows:
        segments_to_drop.add(len(segments) - 1)

    remaining_segments = [
        segment for index, segment in enumerate(segments) if index not in segments_to_drop
    ]
    if len(remaining_segments) != 1:
        gap_descriptions = []
        for left, right in zip(segments, segments[1:]):
            gap_descriptions.append(
                f"{left['date'].iloc[-1].date()} -> {right['date'].iloc[0].date()}"
            )
        raise ValueError(
            f"{symbol} contains unresolved history gaps: {', '.join(gap_descriptions)}"
        )

    return remaining_segments[0].reset_index(drop=True)


def validate_ohlcv_relationships(frame: pd.DataFrame, symbol: str) -> None:
    high_too_low = frame["high"] < frame[["open", "close", "low"]].max(axis=1)
    low_too_high = frame["low"] > frame[["open", "close", "high"]].min(axis=1)
    negative_volume = frame["volume"] < 0
    negative_trade_count = frame["trade_count"] < 0

    invalid_rows = high_too_low | low_too_high | negative_volume | negative_trade_count
    if invalid_rows.any():
        sample = frame.loc[invalid_rows].head(5).to_dict("records")
        raise ValueError(f"{symbol} contains invalid OHLCV rows: {sample}")


def build_clean_panel(
    symbols: Sequence[str],
    config: DataCleaningConfig,
) -> tuple[pd.DataFrame, list[CleaningSummary]]:
    symbols = normalize_symbols(symbols)
    cleaned_frames: list[pd.DataFrame] = []
    summaries: list[CleaningSummary] = []

    for symbol in symbols:
        cleaned_frame, summary = clean_symbol_frame(symbol, config)
        cleaned_frames.append(cleaned_frame)
        summaries.append(summary)

    panel = pd.concat(cleaned_frames, ignore_index=True)
    panel = panel.sort_values(["date", "symbol"]).reset_index(drop=True)
    return panel, summaries


def normalize_symbols(symbols: Sequence[str]) -> list[str]:
    normalized_symbols: list[str] = []
    seen_symbols: set[str] = set()

    for symbol in symbols:
        normalized_symbol = symbol.upper()
        if normalized_symbol in seen_symbols:
            continue

        seen_symbols.add(normalized_symbol)
        normalized_symbols.append(normalized_symbol)

    if not normalized_symbols:
        raise ValueError("At least one symbol is required to build a panel.")

    return normalized_symbols


def filter_to_shared_dates(panel: pd.DataFrame, symbols: Sequence[str]) -> pd.DataFrame:
    selected_symbols = [symbol.upper() for symbol in symbols]
    subset = panel.loc[panel["symbol"].isin(selected_symbols)].copy()
    if subset.empty:
        raise ValueError("No rows left after filtering panel to the requested symbols.")

    date_counts = subset.groupby("date")["symbol"].nunique()
    shared_dates = date_counts[date_counts == len(set(selected_symbols))].index
    shared_panel = subset.loc[subset["date"].isin(shared_dates)].copy()
    return shared_panel.sort_values(["date", "symbol"]).reset_index(drop=True)


def write_panel(panel: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(output_path, index=False)


def print_summary(
    summaries: Sequence[CleaningSummary],
    panel: pd.DataFrame,
    *,
    output_path: Path,
    shared_dates_only: bool,
) -> None:
    mode_label = "shared-dates-only" if shared_dates_only else "unbalanced"
    print(
        f"Wrote {len(panel)} rows across {panel['symbol'].nunique()} symbols to "
        f"{output_path} ({mode_label} panel)."
    )

    for summary in summaries:
        dropped_count = summary.rows_in - summary.rows_out
        print(
            f"{summary.symbol}: {summary.rows_in} -> {summary.rows_out} rows, "
            f"{summary.start_date} to {summary.end_date}, dropped {dropped_count} rows."
        )
        if summary.dropped_dates:
            print(f"  dropped_dates={', '.join(summary.dropped_dates)}")


def main() -> None:
    config = load_data_cleaning_config()
    args = parse_args(config)
    symbols = normalize_symbols(args.symbols)
    output_path = Path(args.output)

    panel, summaries = build_clean_panel(symbols, config)
    if args.shared_dates_only:
        panel = filter_to_shared_dates(panel, symbols)

    write_panel(panel, output_path)
    print_summary(
        summaries,
        panel,
        output_path=output_path,
        shared_dates_only=args.shared_dates_only,
    )


if __name__ == "__main__":
    main()
