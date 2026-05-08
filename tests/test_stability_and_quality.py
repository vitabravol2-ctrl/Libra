from datetime import datetime, timezone

from core.candle_aggregator import aggregate_1m_to_10m
from core.data_quality_engine import DataQualityEngine
from core.datapack import CandleStats, HealthStatus, MarketDataPack
from core.log_deduplicator import LogDeduplicator
from core.score_stabilizer import ScoreStabilizer
from core.timeframe_registry import TIMEFRAME_REGISTRY


def make_pack(tf: str, health: HealthStatus = HealthStatus.HEALTHY):
    return MarketDataPack(
        symbol="BTCUSDT", timestamp=datetime.now(timezone.utc).isoformat(), server_time=datetime.now(timezone.utc).isoformat(), source="test",
        health_status=health, price=100000, spread_placeholder=0.0, volatility={"volatility_score": 60}, momentum=10, volume=1000,
        direction_bias={"bias_score": 60}, candle_stats=CandleStats(100,110,90,105,100,20,5,2,3,1,0.75), timeframe=tf, latency_ms=50, stale_seconds=10,
        raw={"close_time": datetime.now(timezone.utc).isoformat(), "klines": [[0,100,110,90,105,1, int(datetime.now(timezone.utc).timestamp()*1000)] for _ in range(60)]}
    )


def test_log_dedup_suppresses_repeated_warnings():
    d = LogDeduplicator()
    assert d.should_emit("WARN:A", 60) is True
    assert d.should_emit("WARN:A", 60) is False


def test_score_stabilizer_hysteresis_and_spike():
    s = ScoreStabilizer()
    first = s.stabilize("1 MIN", 46)
    second = s.stabilize("1 MIN", 64)
    assert first.direction == "DOWN"
    assert second.direction in {"DOWN", "NEUTRAL"}
    assert "score_spike" in second.warnings


def test_10m_registry_correct():
    assert TIMEFRAME_REGISTRY["10 MIN"].interval == "10m"


def test_aggregate_1m_to_10m():
    candles = []
    for i in range(10):
        candles.append([i, str(100 + i), str(110 + i), str(90 - i), str(101 + i), str(2), i + 1])
    agg = aggregate_1m_to_10m(candles)
    assert len(agg) == 1
    c = agg[0]
    assert float(c[1]) == 100
    assert float(c[4]) == 110
    assert float(c[2]) == 119
    assert float(c[3]) == 81
    assert float(c[5]) == 20


def test_1sec_disabled_not_error():
    q = DataQualityEngine().evaluate(make_pack("1 SEC", health=HealthStatus.DISABLED), [], 0, 5, False)
    assert q.status == "WAITING_FOR_WS"
