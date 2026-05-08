from core.confirmation_engine import ConfirmationEngine, ConfirmationStatus
from core.liquidity_events import LiquidityEventDetector
from core.market_regime import MarketRegimeDetector


def _regime_up():
    return MarketRegimeDetector().analyze({"directional_pressure": 0.8, "higher_micro_highs": True, "volatility": 20})


def _regime_down():
    return MarketRegimeDetector().analyze({"directional_pressure": -0.8, "lower_micro_lows": True, "volatility": 20})


def test_strong_bullish_confirmation():
    regime = _regime_up()
    liq = LiquidityEventDetector().analyze({"sweep_low": True, "reclaim": True}, regime)
    r = ConfirmationEngine().analyze({"bid_volume": 190, "ask_volume": 110, "aggressive_buys": 160, "aggressive_sells": 60, "micro_velocity": 0.8, "velocity_stability": 1.0, "spread": 0.9, "freshness_ms": 300}, regime, liq)
    assert r.status in {ConfirmationStatus.STRONG, ConfirmationStatus.READY}


def test_strong_bearish_confirmation():
    regime = _regime_down()
    liq = LiquidityEventDetector().analyze({"sweep_high": True, "reject": True}, regime)
    r = ConfirmationEngine().analyze({"bid_volume": 100, "ask_volume": 220, "aggressive_buys": 50, "aggressive_sells": 170, "micro_velocity": -0.9, "velocity_stability": 1.0, "spread": 1.0, "freshness_ms": 250}, regime, liq)
    assert r.status in {ConfirmationStatus.STRONG, ConfirmationStatus.READY}


def test_weak_confirmation():
    regime = _regime_up()
    liq = LiquidityEventDetector().analyze({"sweep_low": True, "reclaim": True}, regime)
    r = ConfirmationEngine().analyze({"bid_volume": 120, "ask_volume": 110, "aggressive_buys": 90, "aggressive_sells": 88, "micro_velocity": 0.2, "velocity_stability": 0.3, "spread": 2.4, "freshness_ms": 1400}, regime, liq)
    assert r.status == ConfirmationStatus.WEAK


def test_spread_blocked():
    regime = _regime_up()
    liq = LiquidityEventDetector().analyze({"sweep_low": True, "reclaim": True}, regime)
    r = ConfirmationEngine().analyze({"spread": 3.0, "freshness_ms": 400}, regime, liq)
    assert r.status == ConfirmationStatus.BLOCKED


def test_stale_blocked():
    regime = _regime_up()
    liq = LiquidityEventDetector().analyze({"sweep_low": True, "reclaim": True}, regime)
    r = ConfirmationEngine().analyze({"spread": 1.0, "freshness_ms": 5000}, regime, liq)
    assert r.status == ConfirmationStatus.BLOCKED


def test_chaos_blocked():
    regime = MarketRegimeDetector().analyze({"volatility": 99})
    liq = LiquidityEventDetector().analyze({}, regime)
    r = ConfirmationEngine().analyze({"spread": 1.0, "freshness_ms": 300}, regime, liq)
    assert r.status == ConfirmationStatus.BLOCKED


def test_unknown_blocked():
    regime = MarketRegimeDetector().analyze({"volatility": 10})
    liq = LiquidityEventDetector().analyze({}, regime)
    r = ConfirmationEngine().analyze({"spread": 1.0, "freshness_ms": 300}, regime, liq)
    assert r.status == ConfirmationStatus.BLOCKED


def test_thresholds():
    e = ConfirmationEngine()
    assert e._status_from_score(30) == ConfirmationStatus.WEAK
    assert e._status_from_score(31) == ConfirmationStatus.BUILDING
    assert e._status_from_score(56) == ConfirmationStatus.STRONG
    assert e._status_from_score(76) == ConfirmationStatus.READY
