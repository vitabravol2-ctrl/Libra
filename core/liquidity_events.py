from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class LiquidityEvent(str, Enum):
    SWEEP_LOW_RECLAIM = "SWEEP_LOW_RECLAIM"
    SWEEP_HIGH_REJECT = "SWEEP_HIGH_REJECT"
    NONE = "NONE"


@dataclass
class LiquidityEventResult:
    event: LiquidityEvent
    state: str
    reason: str


class LiquidityEventDetector:
    def detect(self, snapshot: dict) -> LiquidityEventResult:
        sweep_low = bool(snapshot.get("sweep_low", False))
        reclaim = bool(snapshot.get("reclaim", False))
        sweep_high = bool(snapshot.get("sweep_high", False))
        reject = bool(snapshot.get("reject", False))

        if sweep_low and reclaim:
            return LiquidityEventResult(LiquidityEvent.SWEEP_LOW_RECLAIM, "READY", "long_liquidity_confirmed")
        if sweep_high and reject:
            return LiquidityEventResult(LiquidityEvent.SWEEP_HIGH_REJECT, "READY", "short_liquidity_confirmed")
        return LiquidityEventResult(LiquidityEvent.NONE, "WAIT", "no_liquidity_event")
