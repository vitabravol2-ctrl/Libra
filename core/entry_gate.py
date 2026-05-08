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
        allowed_side = "NONE"
        if regime == "TREND_UP" and liquidity_event == "SWEEP_LOW_RECLAIM":
            allowed_side = "LONG"
        elif regime == "TREND_DOWN" and liquidity_event == "SWEEP_HIGH_REJECT":
            allowed_side = "SHORT"
        elif regime == "RANGE" and liquidity_event in {"SWEEP_LOW_RECLAIM", "SWEEP_HIGH_REJECT"}:
            allowed_side = "LONG" if liquidity_event == "SWEEP_LOW_RECLAIM" else "SHORT"

        if regime == "CHAOS":
            return EntryDecision(False, "BLOCKED", "NONE", "LIMIT", "chaos_regime")
        if allowed_side == "NONE":
            return EntryDecision(False, "WAIT", "NONE", "LIMIT", "regime_event_mismatch")
        if not (score > threshold and data_fresh and spread_normal):
            return EntryDecision(False, "BLOCKED", allowed_side, "LIMIT", "confirmation_gate_failed")
        return EntryDecision(True, "READY", allowed_side, "LIMIT", "entry_ready")
