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
    filled_size: float = 0.0
    remaining_size: float = 0.0
    avg_entry_price: float = 0.0
    avg_exit_price: float = 0.0
    partial_fill_pct: float = 0.0
    execution_score: int = 0
    fill_probability: float = 0.0
    spread_capture_score: int = 0
    metrics: dict[str, Any] = field(default_factory=dict)


class PaperPositionEngine:
    def __init__(self, tick_size: float = 0.1) -> None:
        self.tick_size = tick_size
        self.position = PaperPositionState()

    def open(self, side: str, size: float, entry_price: float, tp_price: float, sl_price: float, now_ts: int, execution_quality: dict | None = None) -> PaperPositionState:
        eq = execution_quality or {}
        self.position = PaperPositionState(
            state="OPEN",
            side=side,
            size=size,
            entry_price=entry_price,
            tp_price=tp_price,
            sl_price=sl_price,
            opened_ts=now_ts,
            filled_size=round(size*float(eq.get("fill_probability",1.0)),8),
            remaining_size=round(size-max(0.0, round(size*float(eq.get("fill_probability",1.0)),8)),8),
            avg_entry_price=entry_price,
            execution_score=int(eq.get("final_execution_score",0)),
            fill_probability=float(eq.get("fill_probability",0.0)),
            spread_capture_score=int(eq.get("spread_capture_score",0)),
            partial_fill_pct=round(float(eq.get("fill_probability",1.0))*100,2),
        )
        return self.position

    def update(self, price: float, now_ts: int, spread: float, freshness_ms: int, regime: str, structure_break: bool, momentum: float, timeout_seconds: int, timeout_quality: int = 50) -> PaperPositionState:
        p = self.position
        if p.state == "CLOSED":
            return p
        p.state = "HOLD"
        p.hold_seconds = max(0, now_ts - p.opened_ts)
        sign = 1 if p.side == "LONG" else -1
        p.pnl = (price - p.entry_price) * sign * p.size
        p.pnl_ticks = int(round(((price - p.entry_price) * sign) / self.tick_size))

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
        adaptive_timeout = int(round(timeout_seconds * (0.7 + timeout_quality / 100.0)))
        p.metrics["adaptive_timeout"] = adaptive_timeout
        if p.remaining_size > 0 and p.hold_seconds > 0:
            fill_step = min(p.remaining_size, p.size * max(0.02, min(0.2, momentum * 0.2)))
            if fill_step > 0:
                p.filled_size = round(p.filled_size + fill_step, 8)
                p.remaining_size = round(max(0.0, p.size - p.filled_size), 8)
                p.partial_fill_pct = round((p.filled_size / max(p.size, 1e-9)) * 100, 2)
                p.avg_entry_price = round((p.avg_entry_price + price) / 2, 2)
        elif p.filled_size > 0 and reason and p.avg_exit_price == 0.0:
            p.avg_exit_price = price
        if p.filled_size == 0:
            reason = "timeout_unfilled_exit"
        elif p.hold_seconds >= adaptive_timeout or momentum < 0.05:
            reason = "timeout_exit"

        if reason:
            p.state = "EXIT"
            p.exit_reason = reason
            p.state = "CLOSED"
        return p
