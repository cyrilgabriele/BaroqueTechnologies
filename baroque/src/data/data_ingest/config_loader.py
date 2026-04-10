"""Load and normalise YAML config for historical data ingestion."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_CONFIG_PATH = REPO_ROOT / "baroque" / "src" / "config" / "data" / "indices.yaml"


@dataclass(frozen=True)
class DataIngestConfig:
    env_file: Path
    output_dir: Path
    api_base_url: str
    timeframe: str
    feed: str
    adjustment: str
    limit: int
    symbols: tuple[str, ...]
    start_date: str
    end_date: str
    earliest_request_date: str


def _resolve_repo_path(path_value: str) -> Path:
    return REPO_ROOT / path_value


def _normalise_end_date(raw_end_date: str) -> str:
    if str(raw_end_date).strip().lower() == "today":
        return date.today().isoformat()

    return str(raw_end_date)


def load_data_ingest_config(config_path: Path = DEFAULT_CONFIG_PATH) -> DataIngestConfig:
    with config_path.open(encoding="utf-8") as config_file:
        raw_config = yaml.safe_load(config_file)

    paths = raw_config["paths"]
    alpaca = raw_config["alpaca"]
    bars = raw_config["bars"]

    return DataIngestConfig(
        env_file=_resolve_repo_path(str(paths["env_file"])),
        output_dir=_resolve_repo_path(str(paths["output_dir"])),
        api_base_url=str(alpaca["api_base_url"]),
        timeframe=str(alpaca["timeframe"]),
        feed=str(alpaca["feed"]),
        adjustment=str(alpaca["adjustment"]),
        limit=int(alpaca["limit"]),
        symbols=tuple(str(symbol).upper() for symbol in bars["symbols"]),
        start_date=str(bars["start_date"]),
        end_date=_normalise_end_date(str(bars["end_date"])),
        earliest_request_date=str(bars["earliest_request_date"]),
    )
