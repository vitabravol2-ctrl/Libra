from datetime import datetime, timezone

from core.data_quality_engine import DataQualityEngine
from core.datapack import CandleStats, HealthStatus, MarketDataPack
from core.probability_engine import ProbabilityEngine
from core.timeframe_registry import TIMEFRAME_REGISTRY


def make_pack(tf: str, health: HealthStatus = HealthStatus.HEALTHY, price: float = 100000):
    return MarketDataPack(
        symbol="BTCUSDT", timestamp=datetime.now(timezone.utc).isoformat(), server_time=datetime.now(timezone.utc).isoformat(), source="test",
        health_status=health, price=price, spread_placeholder=0.0, volatility={"volatility_score": 60}, momentum=10, volume=1000,
        direction_bias={"bias_score": 60}, candle_stats=CandleStats(100,110,90,105,100,20,5,2,3,1,0.75), timeframe=tf, latency_ms=50, stale_seconds=10,
        raw={"close_time": datetime.now(timezone.utc).isoformat(), "klines": [[0,100,110,90,105,1, int(datetime.now(timezone.utc).timestamp()*1000)] for _ in range(60)]}
    )


def test_timeframe_registry_contains_week_and_1sec():
    assert "WEEK" in TIMEFRAME_REGISTRY and TIMEFRAME_REGISTRY["WEEK"].interval == "1w"
    assert "1 SEC" in TIMEFRAME_REGISTRY and TIMEFRAME_REGISTRY["1 SEC"].enabled is False


def test_bad_data_returns_no_data():
    engine = ProbabilityEngine()
    bad = make_pack("1 MIN", health=HealthStatus.ERROR, price=0)
    result = engine.evaluate({"symbol":"BTCUSDT","current_price":100000.0,"timestamp":"2026-01-01T00:00:00+00:00","timeframes":{"1 MIN":bad}})
    assert result["timeframes"]["1 MIN"]["direction"] == "NO_DATA"


def test_quality_score_engine():
    q = DataQualityEngine().evaluate(make_pack("DAY"), [[0,100,110,90,105,1,1] for _ in range(50)], 90, 172800, True)
    assert 1 <= q.quality_score <= 100


def test_multitimeframe_state_builds():
    engine = ProbabilityEngine()
    tfs = {"WEEK": make_pack("WEEK"), "1 SEC": make_pack("1 SEC", health=HealthStatus.DISABLED)}
    result = engine.evaluate({"symbol":"BTCUSDT","current_price":100000.0,"timestamp":"2026-01-01T00:00:00+00:00","timeframes":tfs})
    state = result["multi_timeframe_state"]
    assert state.dominant_direction in {"UP", "DOWN", "MIXED"}
    assert "1 SEC" in state.disabled_timeframes
