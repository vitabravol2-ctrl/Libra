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
    fill_probability: float
    slippage_risk: float
    spread_capture_score: int
    timeout_quality: int
    partial_fill_risk: float
    final_execution_score: int
    reason: str
    metrics: dict[str, Any] = field(default_factory=dict)


class ExecutionQualityEngine:
    def analyze(self, snapshot: dict, regime_result: dict, liquidity_result: dict, confirmation_result: dict, microstructure_result: dict, entry_decision: dict) -> ExecutionQualityResult:
        bid_q = float(snapshot.get("bid_queue_size", snapshot.get("bid_volume", 100.0)))
        ask_q = float(snapshot.get("ask_queue_size", snapshot.get("ask_volume", 100.0)))
        priority = float(snapshot.get("queue_priority", 0.5))
        nearby_liq = float(snapshot.get("nearby_resting_liquidity", (bid_q + ask_q) / 2))

        queue_pressure = bid_q / max(ask_q, 1.0) if (entry_decision.get("side") == "LONG") else ask_q / max(bid_q, 1.0)
        queue_score = int(max(0, min(100, 40 * priority + 30 * min(1.5, queue_pressure) + 30 * min(1.0, nearby_liq / 200.0))))

        spread = float(snapshot.get("spread", 99.0))
        spread_stability = float(snapshot.get("spread_stability", 0.8))
        quote_mov_freq = float(snapshot.get("quote_move_frequency", 0.5))
        flicker = float(snapshot.get("quote_flicker", 0.2))
        maker_score = int(max(0, min(100, 45 * (1.0 - min(1.0, spread / 4.0)) + 25 * spread_stability + 20 * (1.0 - quote_mov_freq) + 10 * (1.0 - flicker))))

        liq_thin = float(snapshot.get("liquidity_thinness", max(0.0, 1 - (bid_q + ask_q) / 500.0)))
        aggr_flow = float(snapshot.get("aggressive_flow", abs(float(snapshot.get("aggressive_buys", 0.0)) - float(snapshot.get("aggressive_sells", 0.0))) / 200.0))
        vol_burst = float(snapshot.get("volatility_burst", float(snapshot.get("volatility", 20.0)) / 100.0))
        vacuum = float(snapshot.get("vacuum_zone_risk", 0.2))
        slippage_risk = max(0.0, min(1.0, 0.35 * liq_thin + 0.25 * aggr_flow + 0.25 * vol_burst + 0.15 * vacuum))

        fill_probability = max(0.0, min(1.0, 0.45 * (queue_score / 100.0) + 0.35 * (maker_score / 100.0) + 0.20 * (1.0 - slippage_risk)))

        fees_ticks = float(snapshot.get("fees_ticks", 1.0))
        queue_delay = float(snapshot.get("queue_delay_risk", 1.0 - priority))
        adverse = float(snapshot.get("adverse_move_risk", 0.2))
        spread_edge_ticks = max(0.0, spread * 10.0 - fees_ticks - (slippage_risk * 4.0) - (queue_delay * 2.0) - (adverse * 2.0))
        spread_capture_score = int(max(0, min(100, spread_edge_ticks * 8)))

        momentum = float(snapshot.get("momentum", 0.2))
        continuation = float(snapshot.get("continuation_quality", float(confirmation_result.get("score", 50)) / 100.0))
        timeout_quality = int(max(0, min(100, 40 * momentum + 35 * continuation + 25 * (maker_score / 100.0))))

        partial_fill_risk = max(0.0, min(1.0, 1.0 - fill_probability + queue_delay * 0.3))

        final_execution_score = int(round(max(0.0, min(100.0,
            0.2 * queue_score + 0.2 * maker_score + 0.2 * fill_probability * 100 + 0.15 * (100 - slippage_risk * 100) + 0.15 * spread_capture_score + 0.1 * timeout_quality
        ))))

        if final_execution_score <= 25:
            state = ExecutionQualityState.UNTRADEABLE
        elif final_execution_score <= 45:
            state = ExecutionQualityState.POOR
        elif final_execution_score <= 65:
            state = ExecutionQualityState.FAIR
        elif final_execution_score <= 85:
            state = ExecutionQualityState.GOOD
        else:
            state = ExecutionQualityState.EXCELLENT

        reason = "execution_ok"
        if queue_score < 30:
            reason = "queue_terrible"
        elif fill_probability < 0.45:
            reason = "fill_probability_low"
        elif spread_capture_score < 35:
            reason = "spread_harvest_negative"
        elif slippage_risk > 0.65:
            reason = "slippage_risk_high"
        elif maker_score < 35:
            reason = "quotes_unstable"

        return ExecutionQualityResult(
            state=state,
            queue_score=queue_score,
            maker_score=maker_score,
            fill_probability=round(fill_probability, 4),
            slippage_risk=round(slippage_risk, 4),
            spread_capture_score=spread_capture_score,
            timeout_quality=timeout_quality,
            partial_fill_risk=round(partial_fill_risk, 4),
            final_execution_score=final_execution_score,
            reason=reason,
            metrics={"queue_pressure": round(queue_pressure, 4), "spread_edge_ticks": round(spread_edge_ticks, 4)},
        )
