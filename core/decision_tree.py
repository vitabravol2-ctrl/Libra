from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.market_regime import MarketRegime, MarketRegimeResult


@dataclass
class DecisionTreeResult:
    regime: str
    allowed_direction: str
    next_required_event: str
    action: str
    score: int
    reason: str
    debug: dict[str, Any] = field(default_factory=dict)


class DecisionTreeEngine:
    def evaluate(self, regime_result: MarketRegimeResult) -> DecisionTreeResult:
        regime = regime_result.regime
        if regime == MarketRegime.TREND_UP:
            return DecisionTreeResult(regime=regime.value, allowed_direction="LONG", next_required_event="LIQUIDITY_SWEEP_LOW_RECLAIM", action="WAIT_PULLBACK_LONG", score=regime_result.confidence, reason=regime_result.reason, debug=regime_result.metrics)
        if regime == MarketRegime.TREND_DOWN:
            return DecisionTreeResult(regime=regime.value, allowed_direction="SHORT", next_required_event="LIQUIDITY_SWEEP_HIGH_REJECT", action="WAIT_PULLBACK_SHORT", score=regime_result.confidence, reason=regime_result.reason, debug=regime_result.metrics)
        if regime == MarketRegime.RANGE:
            return DecisionTreeResult(regime=regime.value, allowed_direction="BOTH_RANGE_EDGES", next_required_event="RANGE_BOUNDARY_TOUCH", action="WAIT_RANGE_EDGE", score=regime_result.confidence, reason=regime_result.reason, debug=regime_result.metrics)
        if regime == MarketRegime.CHAOS:
            return DecisionTreeResult(regime=regime.value, allowed_direction="NONE", next_required_event="STABILITY_RECOVERY", action="DO_NOT_TRADE", score=regime_result.confidence, reason=regime_result.reason, debug=regime_result.metrics)
        return DecisionTreeResult(regime=regime.value, allowed_direction="NONE", next_required_event="WAIT_FOR_CLEAR_REGIME", action="WAIT", score=regime_result.confidence, reason=regime_result.reason, debug=regime_result.metrics)
