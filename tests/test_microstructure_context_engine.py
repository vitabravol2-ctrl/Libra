from datetime import datetime, timezone

from core.datapack import CandleStats, HealthStatus, MarketDataPack
from core.microstructure_context_engine import MicrostructureContextEngine
from core.probability_engine import ProbabilityEngine


def mk(candle_stats, volatility, bias):
    return MarketDataPack("BTCUSDT", datetime.now(timezone.utc).isoformat(), datetime.now(timezone.utc).isoformat(), "test", HealthStatus.HEALTHY, 100000, 0.0, volatility, 10, 1000, bias, candle_stats, "1 MIN", 100, 1)


def test_wick_rejection_and_fake_breakdown():
    pack = mk(CandleStats(100, 110, 90, 108, 1000, 20, 8, 1, 9, 1, 0.9), {"candle_expansion": 1.1, "candle_compression": 0.1}, {"bullish_pressure": 0.6, "bearish_pressure": 0.4, "bias_score": 62})
    r = MicrostructureContextEngine().evaluate(pack)
    assert "wick_rejection" in r.warnings
    assert r.context_state in {"fake_breakdown", "reclaim", "rejection"}


def test_compression_and_expansion_detected():
    engine = MicrostructureContextEngine()
    c = CandleStats(100, 101, 99.9, 100.2, 1000, 1.1, 0.2, 0.3, 0.6, 1, 0.6)
    r1 = engine.evaluate(mk(c, {"candle_expansion": 0.9, "candle_compression": 0.6}, {"bullish_pressure": 0.5, "bearish_pressure": 0.5, "bias_score": 50}))
    r2 = engine.evaluate(mk(c, {"candle_expansion": 1.4, "candle_compression": 0.1}, {"bullish_pressure": 0.7, "bearish_pressure": 0.3, "bias_score": 65}))
    assert r1.context_state == "compression"
    assert r2.context_state in {"impulse_up", "expansion"}


def test_final_score_bounds():
    pack = mk(CandleStats(100, 105, 95, 102, 1000, 10, 2, 2, 3, 1, 0.7), {"volatility_score": 99, "candle_expansion": 2.0, "candle_compression": 0.0}, {"bias_score": 99, "bullish_pressure": 0.9, "bearish_pressure": 0.1})
    result = ProbabilityEngine().evaluate({"symbol": "BTCUSDT", "current_price": 100000.0, "timestamp": "2026-01-01T00:00:00+00:00", "timeframes": {"1 MIN": pack}})
    assert 1 <= result["timeframes"]["1 MIN"]["final_score"] <= 100
