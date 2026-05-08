from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MarketRegime(str, Enum):
    TREND_UP = "TREND_UP"
    TREND_DOWN = "TREND_DOWN"
    RANGE = "RANGE"
    CHAOS = "CHAOS"


@dataclass
class MarketRegimeResult:
    regime: MarketRegime
    confidence: int
    reason: str
    metrics: dict[str, Any] = field(default_factory=dict)


class MarketRegimeDetector:
    def analyze(self, market_snapshot: dict[str, Any]) -> MarketRegimeResult:
        volatility = float(market_snapshot.get("volatility", 0.0))
        directional_pressure = float(market_snapshot.get("directional_pressure", 0.0))
        higher_micro_highs = bool(market_snapshot.get("higher_micro_highs", False))
        lower_micro_lows = bool(market_snapshot.get("lower_micro_lows", False))
        range_width = float(market_snapshot.get("range_width", 100.0))
        trend_strength = float(market_snapshot.get("trend_strength", abs(directional_pressure)))

        if volatility >= 85:
            return MarketRegimeResult(MarketRegime.CHAOS, 90, "chaotic_volatility")
        if directional_pressure >= 0.55 and higher_micro_highs:
            return MarketRegimeResult(MarketRegime.TREND_UP, 78, "bullish_trend")
        if directional_pressure <= -0.55 and lower_micro_lows:
            return MarketRegimeResult(MarketRegime.TREND_DOWN, 78, "bearish_trend")
        if range_width <= 25 and trend_strength <= 0.35:
            return MarketRegimeResult(MarketRegime.RANGE, 72, "range_conditions")
        return MarketRegimeResult(MarketRegime.CHAOS, 55, "unclear_defaults_to_no_trade")
