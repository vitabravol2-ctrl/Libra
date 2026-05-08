from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from core.market_regime import MarketRegime, MarketRegimeResult


class LiquidityEvent(str, Enum):
    NONE = "NONE"
    RANGE_LOW_TOUCH = "RANGE_LOW_TOUCH"
    RANGE_HIGH_TOUCH = "RANGE_HIGH_TOUCH"
    SWEEP_LOW = "SWEEP_LOW"
    SWEEP_LOW_RECLAIM = "SWEEP_LOW_RECLAIM"
    SWEEP_HIGH = "SWEEP_HIGH"
    SWEEP_HIGH_REJECT = "SWEEP_HIGH_REJECT"
    BLOCKED = "BLOCKED"


@dataclass
class LiquidityEventResult:
    event: LiquidityEvent
    setup_side: str
    status: str
    confidence: int
    reason: str
    metrics: dict[str, Any] = field(default_factory=dict)


class LiquidityEventDetector:
    def analyze(self, snapshot: dict[str, Any], regime_result: MarketRegimeResult) -> LiquidityEventResult:
        touch_lower_boundary = bool(snapshot.get("touch_lower_boundary", False))
        touch_upper_boundary = bool(snapshot.get("touch_upper_boundary", False))
        sweep_low = bool(snapshot.get("sweep_low", False))
        reclaim = bool(snapshot.get("reclaim", False))
        sweep_high = bool(snapshot.get("sweep_high", False))
        reject = bool(snapshot.get("reject", False))

        regime = regime_result.regime

        if regime in {MarketRegime.CHAOS, MarketRegime.UNKNOWN}:
            return LiquidityEventResult(LiquidityEvent.BLOCKED, "NONE", "BLOCKED", 90, "blocked_by_regime", {"regime": regime.value})

        if regime == MarketRegime.RANGE:
            if touch_lower_boundary:
                return LiquidityEventResult(LiquidityEvent.RANGE_LOW_TOUCH, "LONG", "READY", 72, "possible_long_range_setup", {"setup": "LONG_SETUP"})
            if touch_upper_boundary:
                return LiquidityEventResult(LiquidityEvent.RANGE_HIGH_TOUCH, "SHORT", "READY", 72, "possible_short_range_setup", {"setup": "SHORT_SETUP"})
            return LiquidityEventResult(LiquidityEvent.NONE, "NONE", "WAIT", 60, "wait_range_boundary", {"wait": "WAIT_RANGE_BOUNDARY"})

        if regime == MarketRegime.TREND_UP:
            if sweep_low and reclaim:
                return LiquidityEventResult(LiquidityEvent.SWEEP_LOW_RECLAIM, "LONG", "READY", 80, "long_setup", {"setup": "LONG_SETUP"})
            if sweep_low:
                return LiquidityEventResult(LiquidityEvent.SWEEP_LOW, "LONG", "WAIT", 68, "wait_reclaim", {"wait": "WAIT_RECLAIM"})
            return LiquidityEventResult(LiquidityEvent.NONE, "LONG", "WAIT", 62, "wait_long_pullback", {"wait": "WAIT_LONG_PULLBACK"})

        if regime == MarketRegime.TREND_DOWN:
            if sweep_high and reject:
                return LiquidityEventResult(LiquidityEvent.SWEEP_HIGH_REJECT, "SHORT", "READY", 80, "short_setup", {"setup": "SHORT_SETUP"})
            if sweep_high:
                return LiquidityEventResult(LiquidityEvent.SWEEP_HIGH, "SHORT", "WAIT", 68, "wait_reject", {"wait": "WAIT_REJECT"})
            return LiquidityEventResult(LiquidityEvent.NONE, "SHORT", "WAIT", 62, "wait_short_pullback", {"wait": "WAIT_SHORT_PULLBACK"})

        return LiquidityEventResult(LiquidityEvent.BLOCKED, "NONE", "BLOCKED", 85, "unsupported_regime", {"regime": regime.value})
