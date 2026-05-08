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
from core.timeframe_registry import TIMEFRAME_REGISTRY

BINANCE_BASE_URL = "https://api.binance.com"


class DataCollector:
    def __init__(self, symbol: str = "BTCUSDT", timeout: int = 10) -> None:
        self.symbol = symbol
        self.timeout = timeout
        self.volatility_engine = VolatilityEngine()
        self.bias_engine = BiasEngine()

    def collect(self) -> dict[str, Any]:
        ticker = self._get_ticker_price()
        server_time = self._get_server_time()
        result: dict[str, Any] = {"symbol": self.symbol, "current_price": ticker, "timestamp": datetime.now(timezone.utc).isoformat(), "server_time": server_time, "source": "binance-public-api", "timeframes": {}, "telemetry": {"api_status": "OK"}}
        for label, cfg in TIMEFRAME_REGISTRY.items():
            start = time.perf_counter()
            if not cfg.enabled:
                result["timeframes"][label] = MarketDataPack(self.symbol, datetime.now(timezone.utc).isoformat(), server_time, "binance-public-api", HealthStatus.DISABLED, ticker, 0.0, {}, 0.0, 0.0, {}, CandleStats(0,0,0,0,0,0,0,0,0,0,0), label, 0.0, 0.0, warnings=["WAITING_FOR_WS", "EXPERIMENTAL"], raw={"interval": "1s-simulated"})
                continue
            try:
                klines = self._get_klines(cfg.interval, cfg.candle_limit)
                result["timeframes"][label] = self._build_market_datapack(cfg.interval, label, ticker, server_time, klines, start, cfg.stale_threshold_sec, cfg.latency_threshold_ms)
                result["timeframes"][label].raw["klines"] = klines
            except Exception as exc:  # noqa: BLE001
                result["timeframes"][label] = MarketDataPack(self.symbol, datetime.now(timezone.utc).isoformat(), server_time, "binance-public-api", HealthStatus.ERROR, ticker, 0.0, {}, 0.0, 0.0, {}, CandleStats(0,0,0,0,0,0,0,0,0,0,0), label, (time.perf_counter()-start)*1000, 0.0, errors=[str(exc)])
        return result

    def _build_market_datapack(self, interval: str, timeframe: str, ticker: float, server_time: str, klines: list[list[Any]], tf_start: float, stale_threshold: int, latency_threshold: int) -> MarketDataPack:
        latest = klines[-1]
        open_price = float(latest[1]); high_price = float(latest[2]); low_price = float(latest[3]); close_price = float(latest[4]); volume = float(latest[5])
        close_ts = datetime.fromtimestamp(latest[6] / 1000, tz=timezone.utc); now = datetime.now(timezone.utc)
        stale_seconds = max(0.0, (now - close_ts).total_seconds()); latency_ms = (time.perf_counter() - tf_start) * 1000
        health = self._health_status(latency_ms, stale_seconds, stale_threshold, latency_threshold)
        closes = [float(k[4]) for k in klines]
        return MarketDataPack(self.symbol, now.isoformat(), server_time, "binance-public-api", health, ticker, 0.0, self.volatility_engine.calculate(klines), (closes[-1]-closes[0]), volume, self.bias_engine.calculate(klines), CandleStats(open_price, high_price, low_price, close_price, volume, max(high_price-low_price, 1e-8), abs(close_price-open_price), max(0.0, high_price-max(open_price, close_price)), max(0.0, min(open_price, close_price)-low_price), 1 if close_price>open_price else -1 if close_price<open_price else 0, (close_price-low_price)/max(high_price-low_price, 1e-8)), timeframe, round(latency_ms,2), round(stale_seconds,2), warnings=["spread_placeholder_used"], raw={"interval": interval, "close_time": close_ts.isoformat()})

    def _health_status(self, latency_ms: float, stale_seconds: float, stale_threshold: int, latency_threshold: int) -> HealthStatus:
        if stale_seconds > stale_threshold: return HealthStatus.STALE
        if latency_ms > latency_threshold: return HealthStatus.DELAYED
        return HealthStatus.HEALTHY

    def _http_get_json(self, path: str, params: dict[str, Any]) -> Any:
        url = f"{BINANCE_BASE_URL}{path}?{urlencode(params)}"
        with urlopen(url, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def _get_ticker_price(self) -> float: return float(self._http_get_json("/api/v3/ticker/price", {"symbol": self.symbol})["price"])
    def _get_server_time(self) -> str: return datetime.fromtimestamp(self._http_get_json("/api/v3/time", {})["serverTime"]/1000, tz=timezone.utc).isoformat()
    def _get_klines(self, interval: str, limit: int) -> list[list[Any]]: return self._http_get_json("/api/v3/klines", {"symbol": self.symbol, "interval": interval, "limit": limit})
