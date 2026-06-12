"""Provider contract for historical bar ingestion."""

from __future__ import annotations

from typing import Protocol


BarRow = dict[str, str | int | float]


class HistoricalBarProvider(Protocol):
    """Fetch source data and return normalized rows for raw CSV storage."""

    name: str

    def fetch_symbol_bars(self, symbol: str, start: str, end: str) -> list[BarRow]:
        """Return normalized bars for one symbol between start and end dates."""
