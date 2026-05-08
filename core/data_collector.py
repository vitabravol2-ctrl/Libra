"""Data collection module for BTCUSDT probability engine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen
import json


BINANCE_BASE_URL = "https://api.binance.com"
DEFAULT_TIMEFRAMES: dict[str, str] = {
    "DAY": "1d",
    "HOUR": "1h",
    "10 MIN": "10m",
    "1 MIN": "1m",
}


@dataclass
class TimeframeData:
    timeframe: str
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    quote_volume: float
    candle_count: int
    price_change: float
    candle_direction: int
    volatility: float
    high_low_range: float
    close_position: float
    momentum: float
    simple_delta: float
    last_n_candles_bias: float
    timestamp: str


class DataCollector:
    def __init__(self, symbol: str = "BTCUSDT", timeframes: dict[str, str] | None = None, candle_limit: int = 50, timeout: int = 10) -> None:
        self.symbol = symbol
        self.timeframes = timeframes or DEFAULT_TIMEFRAMES
        self.candle_limit = candle_limit
        self.timeout = timeout

    def collect(self) -> dict[str, Any]:
        ticker = self._get_ticker_price()
        result: dict[str, Any] = {"symbol": self.symbol, "current_price": ticker, "timestamp": datetime.now(timezone.utc).isoformat(), "timeframes": {}}
        for label, interval in self.timeframes.items():
            klines = self._get_klines(interval)
            result["timeframes"][label] = self._normalize_klines(label, klines)
        return result

    def _http_get_json(self, path: str, params: dict[str, Any]) -> Any:
        url = f"{BINANCE_BASE_URL}{path}?{urlencode(params)}"
        with urlopen(url, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def _get_ticker_price(self) -> float:
        data = self._http_get_json("/api/v3/ticker/price", {"symbol": self.symbol})
        return float(data["price"])

    def _get_klines(self, interval: str) -> list[list[Any]]:
        return self._http_get_json("/api/v3/klines", {"symbol": self.symbol, "interval": interval, "limit": self.candle_limit})

    def _normalize_klines(self, timeframe: str, klines: list[list[Any]]) -> TimeframeData:
        latest = klines[-1]
        open_price = float(latest[1]); high_price = float(latest[2]); low_price = float(latest[3]); close_price = float(latest[4])
        volume = float(latest[5]); quote_volume = float(latest[7])
        candle_count = len(klines)
        price_change = close_price - open_price
        candle_direction = 1 if price_change > 0 else (-1 if price_change < 0 else 0)
        high_low_range = max(high_price - low_price, 1e-8)
        volatility = high_low_range / max(open_price, 1e-8)
        close_position = (close_price - low_price) / high_low_range
        closes = [float(k[4]) for k in klines]
        momentum = closes[-1] - closes[-5] if candle_count >= 5 else closes[-1] - closes[0]
        simple_delta = sum((closes[i] - closes[i - 1]) for i in range(1, len(closes)))
        last_window = min(10, candle_count)
        bullish = sum(1 for k in klines[-last_window:] if float(k[4]) > float(k[1]))
        bearish = sum(1 for k in klines[-last_window:] if float(k[4]) < float(k[1]))
        last_n_candles_bias = (bullish - bearish) / max(last_window, 1)
        ts = datetime.fromtimestamp(latest[6] / 1000, tz=timezone.utc).isoformat()
        return TimeframeData(timeframe, open_price, high_price, low_price, close_price, volume, quote_volume, candle_count, price_change, candle_direction, volatility, high_low_range, close_position, momentum, simple_delta, last_n_candles_bias, ts)
