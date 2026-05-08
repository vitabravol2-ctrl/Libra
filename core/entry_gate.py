from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EntryDecision:
    allowed: bool
    state: str
    side: str
    order_type: str
    reason: str


class EntryGate:
    def evaluate(self, regime: str, liquidity_event: str, score: int, data_fresh: bool, spread_normal: bool, threshold: int = 70) -> EntryDecision:
        return EntryDecision(False, "BLOCKED", "NONE", "LIMIT", "not_implemented")
