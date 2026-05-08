from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EntryDecision:
    allowed: bool
    side: str
    entry_price: float
    tp_price: float
    sl_price: float
    timeout_seconds: int
    reason: str
    metrics: dict[str, Any] = field(default_factory=dict)


class EntryGate:
    def evaluate(
        self,
        regime: str,
        liquidity_status: str,
        confirmation_status: str,
        confirmation_score: int,
        spread: float,
        freshness_ms: int,
        side: str,
        price: float,
        threshold: int = 70,
        max_spread: float = 2.5,
        max_freshness_ms: int = 1500,
        tick_size: float = 0.1,
        tp_mode: str = "adaptive",
        adaptive_tp: bool = True,
        fee_ticks: int = 8,
        buffer_ticks: int = 4,
        timeout_seconds: int = 30,
    ) -> EntryDecision:
        if regime == "CHAOS":
            return self._blocked(side, price, timeout_seconds, "blocked_regime_chaos")
        if liquidity_status != "READY":
            return self._blocked(side, price, timeout_seconds, "blocked_liquidity_not_ready")
        if confirmation_status != "READY":
            return self._blocked(side, price, timeout_seconds, "blocked_confirmation_not_ready")
        if confirmation_score < threshold:
            return self._blocked(side, price, timeout_seconds, "blocked_score_below_threshold")
        if spread > max_spread:
            return self._blocked(side, price, timeout_seconds, "blocked_wide_spread")
        if freshness_ms > max_freshness_ms:
            return self._blocked(side, price, timeout_seconds, "blocked_stale_data")

        tp_ticks = self._tp_ticks(spread=spread, score=confirmation_score, mode=tp_mode, adaptive_tp=adaptive_tp, fee_ticks=fee_ticks, buffer_ticks=buffer_ticks)
        sl_ticks = max(12, int(round(tp_ticks * 0.55)))

        tp_delta = tp_ticks * tick_size
        sl_delta = sl_ticks * tick_size

        if side == "SHORT":
            tp_price = price - tp_delta
            sl_price = price + sl_delta
        else:
            tp_price = price + tp_delta
            sl_price = price - sl_delta

        return EntryDecision(
            allowed=True,
            side=side,
            entry_price=price,
            tp_price=round(tp_price, 2),
            sl_price=round(sl_price, 2),
            timeout_seconds=timeout_seconds,
            reason="entry_allowed",
            metrics={"tp_ticks": tp_ticks, "sl_ticks": sl_ticks, "order_type": "LIMIT", "execution": "PAPER"},
        )

    def _blocked(self, side: str, price: float, timeout_seconds: int, reason: str) -> EntryDecision:
        return EntryDecision(False, side or "NONE", price, 0.0, 0.0, timeout_seconds, reason, {})

    def _tp_ticks(self, spread: float, score: int, mode: str, adaptive_tp: bool, fee_ticks: int, buffer_ticks: int) -> int:
        floor = max(20, fee_ticks + int(round(spread * 2)) + buffer_ticks)
        if mode == "conservative":
            return max(40, floor)
        if not adaptive_tp:
            return max(30, floor)
        if score >= 90:
            return max(floor, 40)
        if score >= 80:
            return max(floor, 32)
        return max(floor, 24)
