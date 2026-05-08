from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PaperPositionState:
    state: str = "CLOSED"
    side: str = "FLAT"
    size: float = 0.0
    entry_price: float = 0.0
    tp_price: float = 0.0
    sl_price: float = 0.0
    opened_ts: int = 0
    exit_reason: str = ""
    pnl: float = 0.0
    pnl_ticks: int = 0
    hold_seconds: int = 0
    filled_qty: float = 0.0
    remaining_qty: float = 0.0
    avg_entry_price: float = 0.0
    avg_exit_price: float = 0.0
    partial_fill_pct: float = 0.0
    execution_score: int = 0
    fill_probability: int = 0
    spread_capture: int = 0
    metrics: dict[str, Any] = field(default_factory=dict)


class PaperPositionEngine:
    def __init__(self, tick_size: float = 0.1) -> None:
        self.tick_size = tick_size
        self.position = PaperPositionState()

    def open(self, side: str, size: float, entry_price: float, tp_price: float, sl_price: float, now_ts: int) -> PaperPositionState:
        self.position = PaperPositionState(
            state="OPEN",
            side=side,
            size=size,
            entry_price=entry_price,
            tp_price=tp_price,
            sl_price=sl_price,
            opened_ts=now_ts,
            filled_qty=size,
            remaining_qty=0.0,
            avg_entry_price=entry_price,
            partial_fill_pct=100.0,
        )
        return self.position

    def update(self, price: float, now_ts: int, spread: float, freshness_ms: int, regime: str, structure_break: bool, momentum: float, timeout_seconds: int, execution_quality: dict[str, Any] | None = None) -> PaperPositionState:
        p = self.position
        if p.state == "CLOSED":
            return p
        p.state = "HOLD"
        p.hold_seconds = max(0, now_ts - p.opened_ts)
        sign = 1 if p.side == "LONG" else -1
        p.pnl = (price - p.entry_price) * sign * p.size
        p.pnl_ticks = int(round(((price - p.entry_price) * sign) / self.tick_size))
        if execution_quality:
            p.execution_score = int(execution_quality.get("final_execution_score", 0))
            p.fill_probability = int(execution_quality.get("fill_probability", 0))
            p.spread_capture = int(execution_quality.get("spread_capture_score", 0))
            p.partial_fill_pct = max(0.0, min(100.0, float(execution_quality.get("fill_probability", 100))))
            p.filled_qty = round(p.size * p.partial_fill_pct / 100.0, 6)
            p.remaining_qty = round(max(0.0, p.size - p.filled_qty), 6)

        reason = ""
        if spread > 4.0 or freshness_ms > 2000 or regime == "CHAOS":
            reason = "emergency_exit"
        elif abs(price - p.entry_price) >= 12.0:
            reason = "violent_move_exit"
        elif structure_break:
            reason = "structure_break_exit"
        elif p.side == "LONG" and price >= p.tp_price or p.side == "SHORT" and price <= p.tp_price:
            reason = "tp_exit"
        elif p.side == "LONG" and price <= p.sl_price or p.side == "SHORT" and price >= p.sl_price:
            reason = "sl_exit"
        elif p.hold_seconds >= timeout_seconds or momentum < 0.05:
            reason = "timeout_exit"

        if reason:
            p.state = "EXIT"
            p.exit_reason = reason
            p.avg_exit_price = price
            p.state = "CLOSED"
        return p
