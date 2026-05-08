from core.liquidity_events import LiquidityEvent, LiquidityEventDetector
from core.market_regime import MarketRegime, MarketRegimeResult


def rr(regime: MarketRegime) -> MarketRegimeResult:
    return MarketRegimeResult(regime=regime, confidence=70, reason="test")


def test_range_lower_touch_long():
    r = LiquidityEventDetector().analyze({"touch_lower_boundary": True}, rr(MarketRegime.RANGE))
    assert r.event == LiquidityEvent.RANGE_LOW_TOUCH
    assert r.setup_side == "LONG"


def test_range_upper_touch_short():
    r = LiquidityEventDetector().analyze({"touch_upper_boundary": True}, rr(MarketRegime.RANGE))
    assert r.event == LiquidityEvent.RANGE_HIGH_TOUCH
    assert r.setup_side == "SHORT"


def test_trend_up_sweep_without_reclaim_wait_reclaim():
    r = LiquidityEventDetector().analyze({"sweep_low": True, "reclaim": False}, rr(MarketRegime.TREND_UP))
    assert r.reason == "wait_reclaim"


def test_trend_up_sweep_with_reclaim_long_setup():
    r = LiquidityEventDetector().analyze({"sweep_low": True, "reclaim": True}, rr(MarketRegime.TREND_UP))
    assert r.event == LiquidityEvent.SWEEP_LOW_RECLAIM
    assert r.metrics["setup"] == "LONG_SETUP"


def test_trend_down_sweep_without_reject_wait_reject():
    r = LiquidityEventDetector().analyze({"sweep_high": True, "reject": False}, rr(MarketRegime.TREND_DOWN))
    assert r.reason == "wait_reject"


def test_trend_down_sweep_with_reject_short_setup():
    r = LiquidityEventDetector().analyze({"sweep_high": True, "reject": True}, rr(MarketRegime.TREND_DOWN))
    assert r.event == LiquidityEvent.SWEEP_HIGH_REJECT
    assert r.metrics["setup"] == "SHORT_SETUP"


def test_chaos_blocked():
    r = LiquidityEventDetector().analyze({}, rr(MarketRegime.CHAOS))
    assert r.event == LiquidityEvent.BLOCKED


def test_unknown_blocked():
    r = LiquidityEventDetector().analyze({}, rr(MarketRegime.UNKNOWN))
    assert r.event == LiquidityEvent.BLOCKED
