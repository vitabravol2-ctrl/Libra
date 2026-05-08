from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RepriceDecision:
    should_reprice: bool
    action: str
    reason: str
    retries: int
    new_price: float
    metrics: dict[str, Any] = field(default_factory=dict)


class RepriceEngine:
    def evaluate(self, order_price: float, best_bid: float, best_ask: float, previous_spread: float, current_spread: float, queue_score: int, retries: int, side: str) -> RepriceDecision:
        moved_away = (side == "LONG" and best_bid > order_price) or (side == "SHORT" and best_ask < order_price)
        spread_collapsed = current_spread < max(0.2, previous_spread * 0.5)
        queue_bad = queue_score < 35
        if moved_away or spread_collapsed or queue_bad:
            new_price = best_bid if side == "LONG" else best_ask
            return RepriceDecision(True, "cancel_reprice_retry", "reprice_triggered", retries + 1, round(new_price, 2), {"moved_away": moved_away, "spread_collapsed": spread_collapsed, "queue_bad": queue_bad})
        return RepriceDecision(False, "keep_order", "price_ok", retries, order_price, {"moved_away": moved_away, "spread_collapsed": spread_collapsed, "queue_bad": queue_bad})
