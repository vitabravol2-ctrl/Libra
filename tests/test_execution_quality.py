from core.entry_gate import EntryGate
from core.execution_quality import ExecutionQualityEngine, ExecutionQualityState
from core.paper_position import PaperPositionEngine


def _snapshot(**kw):
    base = {
        "spread": 1.0,
        "bid_volume": 240,
        "ask_volume": 120,
        "queue_priority": 0.8,
        "nearby_resting_liquidity": 250,
        "spread_stability": 0.9,
        "quote_move_frequency": 0.2,
        "quote_flicker": 0.1,
        "volatility": 20,
        "momentum": 0.8,
        "continuation_quality": 0.85,
    }
    base.update(kw)
    return base


def test_execution_quality_excellent_path():
    r = ExecutionQualityEngine().analyze(_snapshot(), {}, {}, {"score": 88}, {}, {"side": "LONG"})
    assert r.state in {ExecutionQualityState.GOOD, ExecutionQualityState.EXCELLENT}
    assert r.fill_probability > 0.5


def test_slippage_risk_high_when_thin_and_volatile():
    r = ExecutionQualityEngine().analyze(_snapshot(bid_volume=20, ask_volume=20, volatility=95, aggressive_flow=1.0, vacuum_zone_risk=1.0), {}, {}, {"score": 60}, {}, {"side": "LONG"})
    assert r.slippage_risk > 0.6


def test_entry_blocked_by_poor_execution():
    eq = ExecutionQualityEngine().analyze(_snapshot(bid_volume=20, ask_volume=300, queue_priority=0.1, spread=3.8), {}, {}, {"score": 55}, {}, {"side": "LONG"})
    d = EntryGate().evaluate("TREND_UP", "READY", "READY", 85, 1.0, 500, "LONG", 64000.0, execution_quality=eq.__dict__)
    assert d.allowed is False


def test_entry_allowed_excellent_execution():
    eq = ExecutionQualityEngine().analyze(_snapshot(), {}, {}, {"score": 90}, {}, {"side": "LONG"})
    d = EntryGate().evaluate("TREND_UP", "READY", "READY", 85, 1.0, 500, "LONG", 64000.0, execution_quality=eq.__dict__)
    assert d.allowed is True


def test_partial_fill_and_adaptive_timeout():
    eq = ExecutionQualityEngine().analyze(_snapshot(), {}, {}, {"score": 90}, {}, {"side": "LONG"})
    pe = PaperPositionEngine()
    pe.open("LONG", 1.0, 100.0, 102.0, 99.0, 0, execution_quality=eq.__dict__)
    p = pe.update(100.2, 10, 1.0, 500, "TREND_UP", False, 0.8, 8, timeout_quality=eq.timeout_quality)
    assert p.partial_fill_pct >= 0
    assert p.metrics["adaptive_timeout"] >= 5
