from core.confirmation_engine import ConfirmationEngine
from core.decision_pipeline import DecisionPipeline
from core.entry_gate import EntryGate
from core.exit_manager import ExitManager
from core.liquidity_events import LiquidityEvent, LiquidityEventDetector
from core.market_regime import MarketRegime, MarketRegimeDetector


def test_trend_up_detection():
    r = MarketRegimeDetector().analyze({"directional_pressure": 0.7, "higher_micro_highs": True, "volatility": 20})
    assert r.regime == MarketRegime.TREND_UP


def test_trend_down_detection():
    r = MarketRegimeDetector().analyze({"directional_pressure": -0.7, "lower_micro_lows": True, "volatility": 20})
    assert r.regime == MarketRegime.TREND_DOWN


def test_range_detection():
    r = MarketRegimeDetector().analyze({"range_width": 20, "trend_strength": 0.2, "volatility": 20})
    assert r.regime == MarketRegime.RANGE


def test_chaos_detection():
    r = MarketRegimeDetector().analyze({"volatility": 95})
    assert r.regime == MarketRegime.CHAOS


def test_sweep_low_reclaim():
    r = LiquidityEventDetector().analyze({"sweep_low": True, "reclaim": True}, MarketRegimeDetector().analyze({"directional_pressure": 0.8, "higher_micro_highs": True}))
    assert r.event == LiquidityEvent.SWEEP_LOW_RECLAIM


def test_sweep_high_reject():
    r = LiquidityEventDetector().analyze({"sweep_high": True, "reject": True}, MarketRegimeDetector().analyze({"directional_pressure": -0.8, "lower_micro_lows": True}))
    assert r.event == LiquidityEvent.SWEEP_HIGH_REJECT


def test_confirmation_scoring():
    regime = MarketRegimeDetector().analyze({"directional_pressure": 0.8, "higher_micro_highs": True, "volatility": 20})
    liq = LiquidityEventDetector().analyze({"sweep_low": True, "reclaim": True}, regime)
    r = ConfirmationEngine().analyze({"bid_volume": 170, "ask_volume": 100, "aggressive_buys": 140, "aggressive_sells": 80, "micro_velocity": 0.9, "velocity_stability": 1.0, "spread": 1.0, "freshness_ms": 500}, regime, liq)
    assert r.score >= 56


def test_entry_blocked_if_score_lt_70():
    d = EntryGate().evaluate("TREND_UP", "SWEEP_LOW_RECLAIM", 65, True, True)
    assert d.allowed is False


def test_exit_by_tp():
    d = ExitManager().evaluate("LONG", 3, False, 5, False)
    assert d.reason == "tp_3_ticks"


def test_exit_by_timeout():
    d = ExitManager().evaluate("LONG", 0, False, 45, False)
    assert d.reason == "timeout_exit"


def test_exit_by_emergency():
    d = ExitManager().evaluate("SHORT", 0, False, 2, True)
    assert d.reason == "emergency_exit"


def test_pipeline_runs_deterministic_path():
    p = DecisionPipeline().run({
        "directional_pressure": 0.8, "higher_micro_highs": True, "volatility": 20,
        "sweep_low": True, "reclaim": True,
        "orderbook_imbalance": 0.9, "aggressive_trades": 0.9, "velocity": 0.9,
        "spread": 1.0, "freshness_ms": 500,
    })
    assert p.entry["allowed"] is False
    assert p.entry["reason"] == "not_implemented"
