from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RepriceDecision:
    should_reprice: bool
    should_cancel: bool
    retries: int
    new_price: float
    reason: str
    metrics: dict[str, Any] = field(default_factory=dict)


class RepriceEngine:
    def evaluate(self, current_price: float, best_bid: float, best_ask: float, previous_best_bid: float, previous_best_ask: float, queue_score: int, spread: float, retries: int, max_retries: int = 3, tick_size: float = 0.1) -> RepriceDecision:
        moved_away = best_bid < previous_best_bid or best_ask > previous_best_ask
        spread_collapsed = spread <= tick_size
        queue_bad = queue_score < 35
        if retries >= max_retries:
            return RepriceDecision(False, False, retries, current_price, "max_retries_reached")
        if moved_away or spread_collapsed or queue_bad:
            direction = -1 if best_bid < previous_best_bid else 1 if best_ask > previous_best_ask else 0
            new_price = round(current_price + direction * tick_size, 2)
            return RepriceDecision(True, True, retries + 1, new_price, "reprice_triggered", {"moved_away": moved_away, "spread_collapsed": spread_collapsed, "queue_bad": queue_bad})
        return RepriceDecision(False, False, retries, current_price, "keep_order")
