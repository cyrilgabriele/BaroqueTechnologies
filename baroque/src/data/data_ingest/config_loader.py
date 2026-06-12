"""Load and normalise YAML config for historical data ingestion."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[4]
SUPPORTED_PROVIDERS = ("alpaca", "binance")


@dataclass(frozen=True)
class DataIngestConfig:
    config_path: Path
    provider: str
    env_file: Path | None
    output_dir: Path
    provider_config: dict[str, Any]
    api_base_url: str
    market_data_endpoint: str | None
    timeframe: str | None
    interval: str | None
    feed: str | None
    adjustment: str | None
    limit: int
    symbols: tuple[str, ...]
    start_date: str
    end_date: str
    earliest_request_date: str
    time_zone: str | None
    output_columns: tuple[str, ...]
    raw_field_mapping: tuple[dict[str, Any], ...]


def _resolve_repo_path(path_value: str) -> Path:
    return REPO_ROOT / path_value


def resolve_config_path(config_path: Path) -> Path:
    if config_path.is_absolute():
        return config_path

    return REPO_ROOT / config_path


def _normalise_end_date(raw_end_date: str) -> str:
    if str(raw_end_date).strip().lower() == "today":
        return date.today().isoformat()

    return str(raw_end_date)


def load_data_ingest_config(config_path: Path) -> DataIngestConfig:
    config_path = resolve_config_path(config_path)
    with config_path.open(encoding="utf-8") as config_file:
        raw_config = yaml.safe_load(config_file)

    paths = raw_config["paths"]
    bars = raw_config["bars"]
    env_file = (
        _resolve_repo_path(str(paths["env_file"])) if "env_file" in paths else None
    )
    configured_providers = [
        provider_name
        for provider_name in SUPPORTED_PROVIDERS
        if provider_name in raw_config
    ]
    if len(configured_providers) != 1:
        raise ValueError(
            f"{config_path} must define exactly one supported data provider: "
            f"{', '.join(SUPPORTED_PROVIDERS)}."
        )

    if configured_providers[0] == "alpaca":
        provider = "alpaca"
        provider_config = raw_config["alpaca"]
        api_base_url = str(provider_config["api_base_url"])
        market_data_endpoint = None
        timeframe = str(provider_config["timeframe"])
        interval = None
        feed = str(provider_config["feed"])
        adjustment = str(provider_config["adjustment"])
        limit = int(provider_config["limit"])
        time_zone = None
    elif configured_providers[0] == "binance":
        provider = "binance"
        provider_config = raw_config["binance"]
        api_base_url = str(provider_config["api_base_url"])
        market_data_endpoint = str(provider_config["market_data_endpoint"])
        timeframe = None
        interval = str(bars["interval"])
        feed = None
        adjustment = None
        limit = int(provider_config["limit"])
        time_zone = str(bars.get("time_zone", "0"))
    else: 
        return KeyError("Provider not available!")
    
    return DataIngestConfig(
        config_path=config_path,
        provider=provider,
        env_file=env_file,
        output_dir=_resolve_repo_path(str(paths["output_dir"])),
        provider_config=provider_config,
        api_base_url=api_base_url,
        market_data_endpoint=market_data_endpoint,
        timeframe=timeframe,
        interval=interval,
        feed=feed,
        adjustment=adjustment,
        limit=limit,
        symbols=tuple(str(symbol).upper() for symbol in bars["symbols"]),
        start_date=str(bars["start_date"]),
        end_date=_normalise_end_date(str(bars["end_date"])),
        earliest_request_date=str(bars["earliest_request_date"]),
        time_zone=time_zone,
        output_columns=tuple(
            str(column)
            for column in raw_config.get(
                "output_columns",
                (
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
                ),
            )
        ),
        raw_field_mapping=tuple(
            dict(field) for field in raw_config.get("raw_kline_fields", ())
        ),
    )
