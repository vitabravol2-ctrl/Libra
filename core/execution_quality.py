from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ExecutionQualityState(Enum):
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    FAIR = "FAIR"
    POOR = "POOR"
    UNTRADEABLE = "UNTRADEABLE"


@dataclass
class ExecutionQualityResult:
    state: ExecutionQualityState
    queue_score: int
    maker_score: int
    fill_probability: int
    slippage_risk: int
    spread_capture_score: int
    timeout_quality: int
    partial_fill_risk: int
    final_execution_score: int
    reason: str
    metrics: dict[str, Any] = field(default_factory=dict)


class ExecutionQualityEngine:
    def analyze(self, snapshot: dict[str, Any], regime_result: Any, liquidity_result: Any, confirmation_result: Any, microstructure_result: Any, entry_decision: Any) -> ExecutionQualityResult:
        bid_queue = float(snapshot.get("bid_queue_size", snapshot.get("bid_volume", 0.0)))
        ask_queue = float(snapshot.get("ask_queue_size", snapshot.get("ask_volume", 0.0)))
        queue_priority = float(snapshot.get("queue_priority", 0.5))
        resting = float(snapshot.get("nearby_resting_liquidity", bid_queue + ask_queue))
        queue_score = int(max(0, min(100, 55 + (queue_priority * 35) - ((bid_queue + ask_queue) / max(1.0, resting)) * 25)))

        spread = float(snapshot.get("spread", 99.0))
        spread_stability = float(snapshot.get("spread_stability", 0.5))
        quote_move_freq = float(snapshot.get("quote_move_frequency", 0.5))
        flicker = float(snapshot.get("quote_flicker", 0.0))
        maker_score = int(max(0, min(100, 90 - spread * 12 + spread_stability * 20 - quote_move_freq * 22 - flicker * 30)))

        thinness = float(snapshot.get("liquidity_thinness", 0.3))
        agg_flow = abs(float(snapshot.get("aggressive_flow", 0.2)))
        burst = float(snapshot.get("volatility_burst", 0.2))
        vacuum = float(getattr(microstructure_result, "vacuum_score", 20)) / 100.0
        slippage_risk = int(max(0, min(100, 15 + thinness * 30 + agg_flow * 20 + burst * 25 + vacuum * 30)))

        fill_probability = int(max(0, min(100, queue_score * 0.45 + maker_score * 0.3 + (100 - slippage_risk) * 0.25)))
        partial_fill_risk = int(max(0, min(100, 100 - fill_probability + thinness * 20 + flicker * 10)))

        fee_bps = float(snapshot.get("fee_bps", 4.0))
        expected_slippage_ticks = float(snapshot.get("expected_slippage_ticks", slippage_risk / 20))
        adverse_risk = float(snapshot.get("adverse_move_risk", max(0.0, (100 - maker_score) / 100)))
        spread_edge = max(0.0, spread - (fee_bps / 10.0) - expected_slippage_ticks * 0.1 - adverse_risk)
        spread_capture_score = int(max(0, min(100, spread_edge * 35 + fill_probability * 0.3 - slippage_risk * 0.2)))

        momentum = float(snapshot.get("momentum", 0.2))
        continuation = int(getattr(microstructure_result, "continuation_score", 50))
        timeout_quality = int(max(0, min(100, 25 + momentum * 35 + continuation * 0.25 + maker_score * 0.2)))

        score = int(round(queue_score * 0.17 + maker_score * 0.17 + fill_probability * 0.2 + (100 - slippage_risk) * 0.17 + spread_capture_score * 0.17 + timeout_quality * 0.12))
        score = max(0, min(100, score))

        state = ExecutionQualityState.UNTRADEABLE
        if score >= 86:
            state = ExecutionQualityState.EXCELLENT
        elif score >= 66:
            state = ExecutionQualityState.GOOD
        elif score >= 46:
            state = ExecutionQualityState.FAIR
        elif score >= 26:
            state = ExecutionQualityState.POOR

        reason = "execution_ok"
        if maker_score < 35:
            reason = "quotes_unstable"
        elif fill_probability < 45:
            reason = "fill_probability_low"
        elif spread_capture_score < 35:
            reason = "spread_harvest_negative"
        elif slippage_risk > 70:
            reason = "slippage_risk_high"
        elif queue_score < 30:
            reason = "queue_deteriorated"

        metrics = {
            "bid_queue_size": bid_queue,
            "ask_queue_size": ask_queue,
            "queue_priority": queue_priority,
            "spread": spread,
            "spread_stability": spread_stability,
            "quote_flicker": flicker,
        }
        return ExecutionQualityResult(state, queue_score, maker_score, fill_probability, slippage_risk, spread_capture_score, timeout_quality, partial_fill_risk, score, reason, metrics)
