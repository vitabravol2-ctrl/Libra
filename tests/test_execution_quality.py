from core.execution_quality import ExecutionQualityEngine, ExecutionQualityState
from core.entry_gate import EntryGate


class Obj:
    vacuum_score = 10
    continuation_score = 80


def test_execution_quality_excellent():
    s = {"spread": 0.8, "bid_volume": 100, "ask_volume": 90, "queue_priority": 0.9, "spread_stability": 0.95, "quote_move_frequency": 0.1, "quote_flicker": 0.05, "liquidity_thinness": 0.1, "aggressive_flow": 0.1, "volatility_burst": 0.1, "momentum": 0.8}
    r = ExecutionQualityEngine().analyze(s, None, None, None, Obj(), None)
    assert r.state in {ExecutionQualityState.GOOD, ExecutionQualityState.EXCELLENT}
    assert r.fill_probability >= 50


def test_execution_quality_poor_blocks_entry():
    s = {"spread": 2.8, "bid_volume": 700, "ask_volume": 800, "queue_priority": 0.1, "spread_stability": 0.2, "quote_move_frequency": 0.9, "quote_flicker": 0.9, "liquidity_thinness": 0.9, "aggressive_flow": 0.9, "volatility_burst": 0.9, "momentum": 0.1}
    r = ExecutionQualityEngine().analyze(s, None, None, None, Obj(), None)
    d = EntryGate().evaluate("TREND_UP", "READY", "READY", 90, 1.0, 500, "LONG", 64000.0, execution_quality=r.__dict__)
    assert d.allowed is False


def test_spread_harvest_and_slippage_bounds():
    s = {"spread": 1.0, "expected_slippage_ticks": 6.0, "liquidity_thinness": 1.0, "aggressive_flow": 1.0, "volatility_burst": 1.0}
    r = ExecutionQualityEngine().analyze(s, None, None, None, Obj(), None)
    assert 0 <= r.slippage_risk <= 100
    assert 0 <= r.spread_capture_score <= 100
