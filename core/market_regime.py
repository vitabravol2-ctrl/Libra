from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MarketRegime(str, Enum):
    TREND_UP = "TREND_UP"
    TREND_DOWN = "TREND_DOWN"
    RANGE = "RANGE"
    CHAOS = "CHAOS"
    UNKNOWN = "UNKNOWN"


@dataclass
class MarketRegimeResult:
    regime: MarketRegime
    confidence: int
    reason: str
    metrics: dict[str, Any] = field(default_factory=dict)


class MarketRegimeDetector:
    def analyze(self, market_snapshot: dict[str, Any]) -> MarketRegimeResult:
        stale = bool(market_snapshot.get("is_stale", False))
        missing = bool(market_snapshot.get("has_missing_data", False))
        volatility = float(market_snapshot.get("volatility", 0.0))
        directional_pressure = float(market_snapshot.get("directional_pressure", 0.0))
        higher_micro_highs = bool(market_snapshot.get("higher_micro_highs", False))
        lower_micro_lows = bool(market_snapshot.get("lower_micro_lows", False))
        range_width = float(market_snapshot.get("range_width", 0.0))
        trend_strength = float(market_snapshot.get("trend_strength", abs(directional_pressure)))

        metrics = {
            "stale": stale,
            "missing": missing,
            "volatility": volatility,
            "directional_pressure": directional_pressure,
            "higher_micro_highs": higher_micro_highs,
            "lower_micro_lows": lower_micro_lows,
            "range_width": range_width,
            "trend_strength": trend_strength,
        }

        if stale or missing:
            regime = MarketRegime.CHAOS if stale else MarketRegime.UNKNOWN
            return MarketRegimeResult(regime=regime, confidence=90, reason="stale_or_missing_data", metrics=metrics)
        if volatility >= 85:
            return MarketRegimeResult(regime=MarketRegime.CHAOS, confidence=88, reason="excessive_volatility", metrics=metrics)
        if directional_pressure >= 0.55 and higher_micro_highs:
            return MarketRegimeResult(regime=MarketRegime.TREND_UP, confidence=80, reason="upward_pressure_with_higher_highs", metrics=metrics)
        if directional_pressure <= -0.55 and lower_micro_lows:
            return MarketRegimeResult(regime=MarketRegime.TREND_DOWN, confidence=80, reason="downward_pressure_with_lower_lows", metrics=metrics)
        if range_width <= 25 and trend_strength <= 0.35:
            return MarketRegimeResult(regime=MarketRegime.RANGE, confidence=72, reason="narrow_range_without_direction", metrics=metrics)
        return MarketRegimeResult(regime=MarketRegime.UNKNOWN, confidence=55, reason="regime_not_clear", metrics=metrics)
