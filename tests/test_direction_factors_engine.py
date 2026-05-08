from datetime import datetime, timezone

from core.datapack import CandleStats, HealthStatus, MarketDataPack
from core.direction_factors_engine import DirectionFactorsEngine


def _pack(direction: int = 1) -> MarketDataPack:
    return MarketDataPack(
        symbol="BTCUSDT", timestamp=datetime.now(timezone.utc).isoformat(), server_time=datetime.now(timezone.utc).isoformat(), source="test",
        health_status=HealthStatus.HEALTHY, price=100000, spread_placeholder=0.0,
        volatility={"candle_expansion": 1.4, "candle_compression": 0.1, "volatility_score": 65}, momentum=20 * direction, volume=1000,
        direction_bias={"bullish_pressure": 0.7 if direction > 0 else 0.3, "bearish_pressure": 0.3 if direction > 0 else 0.7, "bias_score": 70 if direction > 0 else 30},
        candle_stats=CandleStats(100, 112, 95, 110 if direction > 0 else 96, 1000, 17, 10, 2, 5, direction, 0.9 if direction > 0 else 0.2),
        timeframe="1 MIN", latency_ms=100, stale_seconds=1,
    )


def test_bullish_gives_up_pressure():
    r = DirectionFactorsEngine().evaluate(_pack(1))
    assert r.total_up_points > r.total_down_points
    assert 1 <= r.final_factor_score <= 100


def test_bearish_gives_down_pressure():
    r = DirectionFactorsEngine().evaluate(_pack(-1))
    assert r.total_down_points > r.total_up_points
