"""Data collection module for BTCUSDT probability engine."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen
import json
import time

from core.bias_engine import BiasEngine
from core.datapack import CandleStats, HealthStatus, MarketDataPack
from core.volatility_engine import VolatilityEngine


BINANCE_BASE_URL = "https://api.binance.com"
DEFAULT_TIMEFRAMES: dict[str, str] = {
    "DAY": "1d",
    "HOUR": "1h",
    "10 MIN": "10m",
    "1 MIN": "1m",
}


class DataCollector:
    def __init__(self, symbol: str = "BTCUSDT", timeframes: dict[str, str] | None = None, candle_limit: int = 50, timeout: int = 10) -> None:
        self.symbol = symbol
        self.timeframes = timeframes or DEFAULT_TIMEFRAMES
        self.candle_limit = candle_limit
        self.timeout = timeout
        self.volatility_engine = VolatilityEngine()
        self.bias_engine = BiasEngine()

    def collect(self) -> dict[str, Any]:
        collect_start = time.perf_counter()
        ticker = self._get_ticker_price()
        server_time = self._get_server_time()
        result: dict[str, Any] = {
            "symbol": self.symbol,
            "current_price": ticker,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "server_time": server_time,
            "source": "binance-public-api",
            "timeframes": {},
            "telemetry": {"api_status": "OK", "refresh_started": datetime.now(timezone.utc).isoformat()},
        }
        for label, interval in self.timeframes.items():
            tf_start = time.perf_counter()
            try:
                klines = self._get_klines(interval)
                pack = self._build_market_datapack(label, interval, ticker, server_time, klines, tf_start)
            except Exception as exc:  # noqa: BLE001
                now = datetime.now(timezone.utc).isoformat()
                pack = MarketDataPack(
                    symbol=self.symbol,
                    timestamp=now,
                    server_time=server_time,
                    source="binance-public-api",
                    health_status=HealthStatus.ERROR,
                    price=ticker,
                    spread_placeholder=0.0,
                    volatility={},
                    momentum=0.0,
                    volume=0.0,
                    direction_bias={},
                    candle_stats=CandleStats(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
                    timeframe=label,
                    latency_ms=(time.perf_counter() - tf_start) * 1000,
                    stale_seconds=0.0,
                    errors=[str(exc)],
                    warnings=[],
                )
            result["timeframes"][label] = pack

        result["telemetry"]["total_latency_ms"] = round((time.perf_counter() - collect_start) * 1000, 2)
        return result

    def _build_market_datapack(self, timeframe: str, interval: str, ticker: float, server_time: str, klines: list[list[Any]], tf_start: float) -> MarketDataPack:
        latest = klines[-1]
        open_price = float(latest[1]); high_price = float(latest[2]); low_price = float(latest[3]); close_price = float(latest[4]); volume = float(latest[5])
        high_low_range = max(high_price - low_price, 1e-8)
        body_size = abs(close_price - open_price)
        upper_wick = max(0.0, high_price - max(open_price, close_price))
        lower_wick = max(0.0, min(open_price, close_price) - low_price)
        direction = 1 if close_price > open_price else -1 if close_price < open_price else 0
        close_position = (close_price - low_price) / high_low_range
        closes = [float(k[4]) for k in klines]
        momentum = closes[-1] - closes[-5] if len(closes) >= 5 else closes[-1] - closes[0]

        close_ts = datetime.fromtimestamp(latest[6] / 1000, tz=timezone.utc)
        now = datetime.now(timezone.utc)
        stale_seconds = max(0.0, (now - close_ts).total_seconds())
        latency_ms = (time.perf_counter() - tf_start) * 1000
        health = self._health_status(interval, latency_ms, stale_seconds)

        volatility = self.volatility_engine.calculate(klines)
        direction_bias = self.bias_engine.calculate(klines)
        return MarketDataPack(
            symbol=self.symbol,
            timestamp=now.isoformat(),
            server_time=server_time,
            source="binance-public-api",
            health_status=health,
            price=ticker,
            spread_placeholder=0.0,
            volatility=volatility,
            momentum=momentum,
            volume=volume,
            direction_bias=direction_bias,
            candle_stats=CandleStats(open_price, high_price, low_price, close_price, volume, high_low_range, body_size, upper_wick, lower_wick, direction, close_position),
            timeframe=timeframe,
            latency_ms=round(latency_ms, 2),
            stale_seconds=round(stale_seconds, 2),
            errors=[],
            warnings=["spread_placeholder_used"],
            raw={"interval": interval, "close_time": close_ts.isoformat()},
        )

    def _health_status(self, interval: str, latency_ms: float, stale_seconds: float) -> HealthStatus:
        stale_thresholds = {"1m": 120, "10m": 900, "1h": 5400, "1d": 172800}
        delayed_threshold_ms = 1500
        threshold = stale_thresholds.get(interval, 300)
        if stale_seconds > threshold:
            return HealthStatus.STALE
        if latency_ms > delayed_threshold_ms:
            return HealthStatus.DELAYED
        return HealthStatus.HEALTHY

    def _http_get_json(self, path: str, params: dict[str, Any]) -> Any:
        url = f"{BINANCE_BASE_URL}{path}?{urlencode(params)}"
        with urlopen(url, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def _get_ticker_price(self) -> float:
        data = self._http_get_json("/api/v3/ticker/price", {"symbol": self.symbol})
        return float(data["price"])

    def _get_server_time(self) -> str:
        data = self._http_get_json("/api/v3/time", {})
        return datetime.fromtimestamp(data["serverTime"] / 1000, tz=timezone.utc).isoformat()

    def _get_klines(self, interval: str) -> list[list[Any]]:
        return self._http_get_json("/api/v3/klines", {"symbol": self.symbol, "interval": interval, "limit": self.candle_limit})
