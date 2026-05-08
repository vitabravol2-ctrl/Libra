from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ConfirmationResult:
    score: int
    data_fresh: bool
    spread_normal: bool
    state: str


class ConfirmationEngine:
    def evaluate(self, snapshot: dict) -> ConfirmationResult:
        imbalance = float(snapshot.get("orderbook_imbalance", 0.0))
        aggressive = float(snapshot.get("aggressive_trades", 0.0))
        velocity = float(snapshot.get("velocity", 0.0))
        spread = float(snapshot.get("spread", 99.0))
        freshness_ms = int(snapshot.get("freshness_ms", 999999))

        spread_normal = spread <= 2.0
        data_fresh = freshness_ms <= 1500

        raw = 40 * imbalance + 30 * aggressive + 20 * velocity
        score = max(0, min(100, int(raw + (10 if spread_normal else 0))))
        state = "READY" if (score > 70 and spread_normal and data_fresh) else "WAIT"
        return ConfirmationResult(score=score, data_fresh=data_fresh, spread_normal=spread_normal, state=state)
