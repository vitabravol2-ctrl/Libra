from core.decision_tree import DecisionTreeEngine
from core.market_regime import MarketRegime, MarketRegimeResult


def _run(regime: MarketRegime):
    return DecisionTreeEngine().evaluate(MarketRegimeResult(regime=regime, confidence=75, reason="test"))


def test_trend_up_wait_pullback_long() -> None:
    assert _run(MarketRegime.TREND_UP).action == "WAIT_PULLBACK_LONG"


def test_trend_down_wait_pullback_short() -> None:
    assert _run(MarketRegime.TREND_DOWN).action == "WAIT_PULLBACK_SHORT"


def test_range_wait_range_edge() -> None:
    assert _run(MarketRegime.RANGE).action == "WAIT_RANGE_EDGE"


def test_chaos_do_not_trade() -> None:
    assert _run(MarketRegime.CHAOS).action == "DO_NOT_TRADE"


def test_v050_never_creates_entry_action() -> None:
    result = _run(MarketRegime.UNKNOWN)
    assert "ENTRY" not in result.action
