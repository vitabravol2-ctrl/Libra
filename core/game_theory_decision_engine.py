from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.datapack import MultiTimeframeState


@dataclass
class PaperTradeIntent:
    allowed: bool
    side: str
    confidence: int
    reason: str
    risk_level: str


@dataclass
class GameTheoryDecisionResult:
    global_score: int
    decision: str
    confidence: int
    market_regime: str
    dominant_side: str
    agreement_score: int
    conflict_score: int
    risk_level: str
    execution_ready: bool
    scenario_type: str
    explanations: list[str] = field(default_factory=list)
    strongest_reasons: list[str] = field(default_factory=list)
    blocked_reasons: list[str] = field(default_factory=list)
    timeframe_weights: dict[str, float] = field(default_factory=dict)
    long_allowed: bool = False
    short_allowed: bool = False
    paper_trade_intent: PaperTradeIntent | None = None


class GameTheoryDecisionEngine:
    TREND_WEIGHTS = {"WEEK": 0.25, "DAY": 0.25, "HOUR": 0.25, "10 MIN": 0.15, "1 MIN": 0.10}
    MICRO_WEIGHTS = {"WEEK": 0.10, "DAY": 0.15, "HOUR": 0.20, "10 MIN": 0.30, "1 MIN": 0.25}

    def __init__(self) -> None:
        self._last_regime = "UNKNOWN"
        self._last_decision = "WAIT"

    def evaluate(self, multi_state: MultiTimeframeState, timeframe_results: dict[str, dict[str, Any]]) -> GameTheoryDecisionResult:
        weights, regime = self._weights_and_regime(multi_state, timeframe_results)
        trap_tags = self._trap_scenarios(timeframe_results)
        weighted = self._weighted_score(timeframe_results, weights)
        agreement = multi_state.agreement_score
        conflict = multi_state.conflict_score
        dominant = multi_state.dominant_direction

        quality_ok = all(v.get("quality_score", 0) >= 45 or v.get("health_status") == "DISABLED" for v in timeframe_results.values())
        health_ok = all(v.get("health_status") in {"HEALTHY", "DISABLED"} for v in timeframe_results.values())

        confidence = max(1, min(100, int(100 - conflict * 0.8)))
        explanations = [f"weighted_score={weighted}", f"agreement={agreement}", f"conflict={conflict}", f"regime={regime}"]
        strongest = [f"dominant_direction={dominant}"]
        blocked: list[str] = []

        if regime == "CHAOS":
            confidence = max(1, confidence - 25)
            blocked.append("chaos_regime")
        if trap_tags:
            confidence = max(1, confidence - min(30, len(trap_tags) * 8))
            explanations.append(f"trap_detected={','.join(trap_tags)}")
            strongest.append(f"trap_risk={len(trap_tags)}")

        if conflict >= 45:
            blocked.append("timeframe_conflict")

        long_allowed = weighted >= 65 and dominant != "DOWN"
        short_allowed = weighted <= 35 and dominant != "UP"

        if 36 <= weighted <= 64:
            decision = "WAIT"
        elif long_allowed:
            decision = "LONG"
        elif short_allowed:
            decision = "SHORT"
        else:
            decision = "WAIT"

        # pullback / reversal-aware overrides
        if dominant == "UP" and timeframe_results.get("10 MIN", {}).get("direction") == "DOWN":
            regime = "PULLBACK"
            long_allowed = weighted >= 60
            if long_allowed:
                decision = "LONG"
                strongest.append("pullback_inside_bullish_structure")
        if dominant == "DOWN" and timeframe_results.get("10 MIN", {}).get("direction") == "UP":
            regime = "PULLBACK"
            short_allowed = weighted <= 40
            if short_allowed:
                decision = "SHORT"
                strongest.append("pullback_inside_bearish_structure")

        execution_ready = quality_ok and health_ok and conflict < 45 and regime != "CHAOS" and len(trap_tags) < 2
        if not execution_ready:
            blocked.append("execution_blocked")

        risk_level = "LOW" if execution_ready and confidence >= 70 else "MEDIUM" if confidence >= 45 else "HIGH"
        scenario_type = "TRAP_RISK" if trap_tags else regime

        if self._last_regime != regime:
            explanations.append(f"market_regime_changed:{self._last_regime}->{regime}")
            self._last_regime = regime
        if self._last_decision != decision:
            explanations.append(f"decision_changed:{self._last_decision}->{decision}")
            self._last_decision = decision

        intent = PaperTradeIntent(
            allowed=execution_ready and decision in {"LONG", "SHORT"},
            side=decision if decision in {"LONG", "SHORT"} else "WAIT",
            confidence=confidence,
            reason=strongest[0] if strongest else "no_reason",
            risk_level=risk_level,
        )

        return GameTheoryDecisionResult(
            global_score=weighted,
            decision=decision,
            confidence=confidence,
            market_regime=regime,
            dominant_side=dominant,
            agreement_score=agreement,
            conflict_score=conflict,
            risk_level=risk_level,
            execution_ready=execution_ready,
            scenario_type=scenario_type,
            explanations=explanations,
            strongest_reasons=strongest,
            blocked_reasons=sorted(set(blocked)),
            timeframe_weights=weights,
            long_allowed=long_allowed,
            short_allowed=short_allowed,
            paper_trade_intent=intent,
        )

    def _weights_and_regime(self, multi_state: MultiTimeframeState, timeframe_results: dict[str, dict[str, Any]]) -> tuple[dict[str, float], str]:
        conflict = multi_state.conflict_score
        micro_active = timeframe_results.get("1 MIN", {}).get("quality_score", 0) >= 45
        if conflict >= 60:
            return self.MICRO_WEIGHTS, "CHAOS"
        if conflict <= 25 and multi_state.dominant_direction == "UP":
            return self.TREND_WEIGHTS, "TREND_UP"
        if conflict <= 25 and multi_state.dominant_direction == "DOWN":
            return self.TREND_WEIGHTS, "TREND_DOWN"
        if micro_active and conflict <= 40:
            return self.MICRO_WEIGHTS, "EXPANSION"
        if conflict >= 40:
            return self.MICRO_WEIGHTS, "REVERSAL_RISK"
        return self.TREND_WEIGHTS, "RANGE"

    @staticmethod
    def _trap_scenarios(timeframe_results: dict[str, dict[str, Any]]) -> list[str]:
        tags: list[str] = []
        states = [v.get("microstructure_context", {}).get("context_state", "") for v in timeframe_results.values()]
        for state in states:
            if state in {"fake_breakout", "fake_breakdown"}:
                tags.append(state)
            if state == "rejection":
                tags.append("liquidity_grab")
            if state == "weak_buyers":
                tags.append("weak_breakout")
                tags.append("trapped_buyers")
            if state == "weak_sellers":
                tags.append("weak_breakdown")
                tags.append("trapped_sellers")
            if state in {"buyers_absorbed", "sellers_absorbed"}:
                tags.append("exhaustion_move")
        return sorted(set(tags))

    @staticmethod
    def _weighted_score(timeframe_results: dict[str, dict[str, Any]], weights: dict[str, float]) -> int:
        acc = 0.0
        total = 0.0
        for tf, w in weights.items():
            tf_data = timeframe_results.get(tf)
            if not tf_data:
                continue
            score = tf_data.get("score")
            if isinstance(score, (int, float)):
                acc += float(score) * w
                total += w
        if total <= 0:
            return 50
        return max(1, min(100, round(acc / total)))
