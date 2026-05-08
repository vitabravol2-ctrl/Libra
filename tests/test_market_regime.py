from core.market_regime import MarketRegime, MarketRegimeDetector


def test_trend_up_detected_on_rising_micro_flow() -> None:
    r = MarketRegimeDetector().analyze({"directional_pressure": 0.8, "higher_micro_highs": True, "volatility": 30, "range_width": 40})
    assert r.regime == MarketRegime.TREND_UP


def test_trend_down_detected_on_falling_micro_flow() -> None:
    r = MarketRegimeDetector().analyze({"directional_pressure": -0.8, "lower_micro_lows": True, "volatility": 30, "range_width": 40})
    assert r.regime == MarketRegime.TREND_DOWN


def test_range_detected_on_sideways_market() -> None:
    r = MarketRegimeDetector().analyze({"directional_pressure": 0.1, "volatility": 20, "range_width": 10, "trend_strength": 0.1})
    assert r.regime == MarketRegime.RANGE


def test_chaos_detected_on_high_volatility_or_stale() -> None:
    detector = MarketRegimeDetector()
    assert detector.analyze({"volatility": 95}).regime == MarketRegime.CHAOS
    assert detector.analyze({"is_stale": True}).regime == MarketRegime.CHAOS


def test_unknown_has_no_entry_permission() -> None:
    r = MarketRegimeDetector().analyze({"directional_pressure": 0.2, "volatility": 40, "range_width": 50})
    assert r.regime == MarketRegime.UNKNOWN
