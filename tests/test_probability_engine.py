from datetime import datetime, timedelta, timezone

from core.bias_engine import BiasEngine
from core.data_collector import DataCollector
from core.datapack import CandleStats, HealthStatus, MarketDataPack
from core.probability_engine import ProbabilityEngine
from core.volatility_engine import VolatilityEngine


def make_pack(direction: int = 1) -> MarketDataPack:
    return MarketDataPack(
        symbol="BTCUSDT",
        timestamp=datetime.now(timezone.utc).isoformat(),
        server_time=datetime.now(timezone.utc).isoformat(),
        source="test",
        health_status=HealthStatus.HEALTHY,
        price=100000,
        spread_placeholder=0.0,
        volatility={"volatility_score": 60},
        momentum=50 if direction > 0 else -50,
        volume=1000,
        direction_bias={"bias_score": 65 if direction > 0 else 35},
        candle_stats=CandleStats(100, 110, 90, 108 if direction > 0 else 92, 1000, 20, 8, 2, 2, direction, 0.9 if direction > 0 else 0.1),
        timeframe="DAY",
        latency_ms=100,
        stale_seconds=10,
    )


def test_probability_engine_up_bias():
    engine = ProbabilityEngine()
    result = engine.evaluate({"symbol": "BTCUSDT", "current_price": 100000.0, "timestamp": "2026-01-01T00:00:00+00:00", "timeframes": {"DAY": make_pack(1)}})
    assert result["timeframes"]["DAY"]["score"] > 50
    assert result["timeframes"]["DAY"]["direction"] == "UP"


def test_probability_engine_down_bias():
    engine = ProbabilityEngine()
    result = engine.evaluate({"symbol": "BTCUSDT", "current_price": 100000.0, "timestamp": "2026-01-01T00:00:00+00:00", "timeframes": {"DAY": make_pack(-1)}})
    assert result["timeframes"]["DAY"]["score"] < 50
    assert result["timeframes"]["DAY"]["direction"] == "DOWN"


def test_health_transitions():
    collector = DataCollector()
    assert collector._health_status("1m", 100, 30) == HealthStatus.HEALTHY
    assert collector._health_status("1m", 2000, 30) == HealthStatus.DELAYED
    assert collector._health_status("1m", 100, 1000) == HealthStatus.STALE


def test_volatility_calculation():
    engine = VolatilityEngine()
    klines = [[0, 100, 110, 95, 108, 10], [0, 108, 118, 100, 117, 12], [0, 117, 121, 116, 120, 15]]
    data = engine.calculate(klines)
    assert data["avg_range"] > 0
    assert 1 <= data["volatility_score"] <= 100


def test_bias_calculation():
    engine = BiasEngine()
    klines = [[0, 100, 110, 95, 108, 10], [0, 108, 118, 100, 117, 12], [0, 117, 121, 116, 120, 15]]
    data = engine.calculate(klines)
    assert data["bullish_pressure"] > data["bearish_pressure"]
    assert 1 <= data["bias_score"] <= 100
