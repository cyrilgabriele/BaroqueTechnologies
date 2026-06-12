"""Historical data provider registry."""

from __future__ import annotations

from config_loader import DataIngestConfig
from providers.alpaca import AlpacaProvider
from providers.base import HistoricalBarProvider
from providers.binance import BinanceProvider


def get_provider(config: DataIngestConfig) -> HistoricalBarProvider:
    if config.provider == AlpacaProvider.name:
        return AlpacaProvider(config)
    if config.provider == BinanceProvider.name:
        return BinanceProvider(config)

    raise ValueError(f"Unsupported data provider: {config.provider}")
