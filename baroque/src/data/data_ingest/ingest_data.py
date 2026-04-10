"""Fetch daily benchmark ETF bars from Alpaca and store them under data/raw/indices."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from config_loader import DataIngestConfig, load_data_ingest_config


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        os.environ.setdefault(key, value)


def get_alpaca_credentials(config: DataIngestConfig) -> tuple[str, str]:
    load_env_file(config.env_file)

    api_key = os.environ.get("APCA_API_KEY_ID")
    api_secret = os.environ.get("APCA_API_SECRET_KEY")
    if not api_key or not api_secret:
        raise RuntimeError(
            "Missing Alpaca credentials. Set APCA_API_KEY_ID and "
            "APCA_API_SECRET_KEY in the environment or in .env."
        )

    return api_key, api_secret


def resolve_start_date(start: str, earliest_request_date: str) -> str:
    if start.strip().lower() == "max":
        return earliest_request_date

    return start


def build_bars_url(
    *,
    config: DataIngestConfig,
    symbol: str,
    start: str,
    end: str,
    page_token: str | None,
) -> str:
    params = {
        "timeframe": config.timeframe,
        "start": start,
        "end": end,
        "adjustment": config.adjustment,
        "feed": config.feed,
        "limit": config.limit,
    }
    if page_token:
        params["page_token"] = page_token

    symbol_path = quote(symbol.upper(), safe="")
    return f"{config.api_base_url}/{symbol_path}/bars?{urlencode(params)}"


def api_get_json(url: str, api_key: str, api_secret: str) -> dict:
    request = Request(
        url,
        headers={
            "accept": "application/json",
            "APCA-API-KEY-ID": api_key,
            "APCA-API-SECRET-KEY": api_secret,
        },
        method="GET",
    )

    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Alpaca request failed with HTTP {exc.code} for {url}: {body}"
        ) from exc
    except URLError as exc:
        raise RuntimeError(f"Failed to reach Alpaca for {url}: {exc.reason}") from exc


def fetch_symbol_bars(
    *,
    config: DataIngestConfig,
    symbol: str,
    start: str,
    end: str,
    api_key: str,
    api_secret: str,
) -> list[dict]:
    all_bars: list[dict] = []
    page_token: str | None = None

    while True:
        url = build_bars_url(
            config=config,
            symbol=symbol,
            start=start,
            end=end,
            page_token=page_token,
        )
        payload = api_get_json(url, api_key, api_secret)
        bars = payload.get("bars", [])
        all_bars.extend(bars)

        page_token = payload.get("next_page_token")
        if not page_token:
            break

    return all_bars


def normalise_bar(symbol: str, bar: dict) -> dict[str, str | int | float]:
    timestamp = bar.get("t", "")
    return {
        "date": timestamp[:10],
        "timestamp": timestamp,
        "symbol": symbol.upper(),
        "open": bar.get("o", ""),
        "high": bar.get("h", ""),
        "low": bar.get("l", ""),
        "close": bar.get("c", ""),
        "volume": bar.get("v", ""),
        "trade_count": bar.get("n", ""),
        "vwap": bar.get("vw", ""),
    }


def write_csv(
    output_dir: Path, symbol: str, rows: Iterable[dict[str, str | int | float]]
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{symbol.upper()}.csv"
    fieldnames = [
        "date",
        "timestamp",
        "symbol",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "trade_count",
        "vwap",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return output_path


def main() -> None:
    config = load_data_ingest_config()
    api_key, api_secret = get_alpaca_credentials(config)
    start = resolve_start_date(config.start_date, config.earliest_request_date)

    for symbol in config.symbols:
        bars = fetch_symbol_bars(
            config=config,
            symbol=symbol,
            start=start,
            end=config.end_date,
            api_key=api_key,
            api_secret=api_secret,
        )
        if not bars:
            raise RuntimeError(
                f"No bars returned for {symbol.upper()} between {start} and {config.end_date}."
            )

        output_path = write_csv(
            config.output_dir,
            symbol,
            [normalise_bar(symbol, bar) for bar in bars],
        )
        print(f"Wrote {len(bars)} rows to {output_path}")


if __name__ == "__main__":
    main()
