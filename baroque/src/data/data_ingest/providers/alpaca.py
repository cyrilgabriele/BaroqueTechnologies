"""Alpaca historical bar provider."""

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from config_loader import DataIngestConfig
from providers.base import BarRow


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


class AlpacaProvider:
    name = "alpaca"

    def __init__(self, config: DataIngestConfig) -> None:
        self.config = config
        self.api_key, self.api_secret = self._get_credentials()

    def _get_credentials(self) -> tuple[str, str]:
        if self.config.env_file is None:
            raise RuntimeError("Alpaca configs must declare paths.env_file.")

        load_env_file(self.config.env_file)

        api_key = os.environ.get("APCA_API_KEY_ID")
        api_secret = os.environ.get("APCA_API_SECRET_KEY")
        if not api_key or not api_secret:
            raise RuntimeError(
                "Missing Alpaca credentials. Set APCA_API_KEY_ID and "
                "APCA_API_SECRET_KEY in the environment or in .env."
            )

        return api_key, api_secret

    def _build_bars_url(
        self,
        *,
        symbol: str,
        start: str,
        end: str,
        page_token: str | None,
    ) -> str:
        if (
            self.config.timeframe is None
            or self.config.adjustment is None
            or self.config.feed is None
        ):
            raise RuntimeError(
                "Alpaca bar requests require timeframe, adjustment, and feed."
            )

        params = {
            "timeframe": self.config.timeframe,
            "start": start,
            "end": end,
            "adjustment": self.config.adjustment,
            "feed": self.config.feed,
            "limit": self.config.limit,
        }
        if page_token:
            params["page_token"] = page_token

        symbol_path = quote(symbol.upper(), safe="")
        return f"{self.config.api_base_url}/{symbol_path}/bars?{urlencode(params)}"

    def _get_json(self, url: str) -> dict:
        request = Request(
            url,
            headers={
                "accept": "application/json",
                "APCA-API-KEY-ID": self.api_key,
                "APCA-API-SECRET-KEY": self.api_secret,
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

    def fetch_symbol_bars(self, symbol: str, start: str, end: str) -> list[BarRow]:
        rows: list[BarRow] = []
        page_token: str | None = None

        while True:
            url = self._build_bars_url(
                symbol=symbol,
                start=start,
                end=end,
                page_token=page_token,
            )
            payload = self._get_json(url)
            bars = payload.get("bars", [])
            rows.extend(self._normalise_bar(symbol, bar) for bar in bars)

            page_token = payload.get("next_page_token")
            if not page_token:
                break

        return rows

    @staticmethod
    def _normalise_bar(symbol: str, bar: dict) -> BarRow:
        timestamp = str(bar.get("t", ""))
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
