"""Binance historical kline provider."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from config_loader import DataIngestConfig
from providers.base import BarRow


class BinanceProvider:
    name = "binance"

    def __init__(self, config: DataIngestConfig) -> None:
        self.config = config
        self.field_mapping = config.raw_field_mapping
        if config.market_data_endpoint is None or config.interval is None:
            raise RuntimeError(
                "Binance bar requests require market_data_endpoint and bars.interval."
            )
        if not self.field_mapping:
            raise RuntimeError("Binance configs must declare raw_kline_fields.")

    def fetch_symbol_bars(self, symbol: str, start: str, end: str) -> list[BarRow]:
        rows: list[BarRow] = []
        start_ms = self._date_to_start_ms(start)
        end_ms = self._date_to_end_ms(end)

        while start_ms <= end_ms:
            payload = self._get_klines(symbol, start_ms, end_ms)
            if not payload:
                break

            rows.extend(self._normalise_kline(symbol, kline) for kline in payload)

            last_open_time = int(payload[-1][0])
            next_start_ms = last_open_time + 1
            if next_start_ms <= start_ms or len(payload) < self.config.limit:
                break

            start_ms = next_start_ms

        return rows

    def _get_klines(self, symbol: str, start_ms: int, end_ms: int) -> list[list[Any]]:
        params: dict[str, str | int] = {
            "symbol": symbol.upper(),
            "interval": self.config.interval or "",
            "startTime": start_ms,
            "endTime": end_ms,
            "limit": self.config.limit,
        }
        if self.config.time_zone is not None:
            params["timeZone"] = self.config.time_zone

        url = (
            f"{self.config.api_base_url}{self.config.market_data_endpoint}"
            f"?{urlencode(params)}"
        )
        request = Request(url, headers={"accept": "application/json"}, method="GET")

        try:
            with urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Binance request failed with HTTP {exc.code} for {url}: {body}"
            ) from exc
        except URLError as exc:
            raise RuntimeError(f"Failed to reach Binance for {url}: {exc.reason}") from exc

        if not isinstance(payload, list):
            raise RuntimeError(f"Unexpected Binance response for {symbol.upper()}: {payload}")

        return payload

    def _normalise_kline(self, symbol: str, kline: list[Any]) -> BarRow:
        row: BarRow = {"symbol": symbol.upper()}

        for field in self.field_mapping:
            if not field.get("keep", False):
                continue

            index = int(field["index"])
            output_name = str(field["output_name"])
            field_type = str(field["type"])
            value = kline[index]
            row[output_name] = self._coerce_value(value, field_type)

        timestamp = str(row.get("timestamp", ""))
        if "date" not in row:
            row["date"] = timestamp[:10]

        return row

    @staticmethod
    def _coerce_value(value: Any, field_type: str) -> str | int | float:
        if field_type == "datetime_ms":
            timestamp = datetime.fromtimestamp(
                int(value) / 1000,
                tz=timezone.utc,
            )
            return timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
        if field_type == "float":
            return float(value)
        if field_type == "int":
            return int(value)
        if field_type == "str":
            return str(value)

        raise ValueError(f"Unsupported Binance field type: {field_type}")

    @staticmethod
    def _date_to_start_ms(date_value: str) -> int:
        parsed_date = date.fromisoformat(date_value)
        parsed_datetime = datetime.combine(parsed_date, datetime.min.time(), timezone.utc)
        return int(parsed_datetime.timestamp() * 1000)

    @staticmethod
    def _date_to_end_ms(date_value: str) -> int:
        parsed_date = date.fromisoformat(date_value) + timedelta(days=1)
        parsed_datetime = datetime.combine(parsed_date, datetime.min.time(), timezone.utc)
        return int(parsed_datetime.timestamp() * 1000) - 1
