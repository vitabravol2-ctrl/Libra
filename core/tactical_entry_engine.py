from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.datapack import MultiTimeframeState
from core.game_theory_decision_engine import GameTheoryDecisionResult


@dataclass
class TacticalEntryResult:
    entry_allowed: bool
    side: str
    entry_type: str
    confidence: str
    macro_direction: str
    pullback_state: str
    micro_trigger: str
    target_ticks: int
    stop_ticks: int
    expected_move_strength: str
    entry_window_open: bool
    tactical_score: int
    reasons: list[str] = field(default_factory=list)
    blocked_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class TacticalEntryEngine:
    MICRO_LONG = {"momentum_flip", "reclaim", "buyers_absorbed", "micro_breakout", "rejection"}
    MICRO_SHORT = {"weak_buyers", "sellers_absorbed", "micro_breakdown", "weak_sellers", "rejection"}

    def evaluate(
        self,
        game_theory: GameTheoryDecisionResult,
        multi_state: MultiTimeframeState,
        timeframe_results: dict[str, dict[str, Any]],
    ) -> TacticalEntryResult:
        reasons: list[str] = []
        blocked: list[str] = []
        warnings: list[str] = []

        macro_direction, macro_strong = self._macro_bias(timeframe_results)
        pullback_state, pullback_valid, pullback_quality = self._pullback_state(macro_direction, timeframe_results)
        micro_trigger, micro_quality = self._micro_trigger(macro_direction, timeframe_results)
        trap_penalty = self._trap_penalty(timeframe_results)

        if game_theory.market_regime == "CHAOS":
            blocked.append("chaos_regime")
        if game_theory.conflict_score >= 45:
            blocked.append("high_conflict")
        if trap_penalty >= 25:
            blocked.append("severe_trap_risk")

        tactical_score = round(
            game_theory.global_score * 0.40
            + pullback_quality * 0.20
            + micro_quality * 0.20
            + max(0, 100 - game_theory.conflict_score) * 0.10
            + max(0, 100 - trap_penalty) * 0.10
        )
        tactical_score = max(1, min(100, tactical_score))

        confidence = "HIGH" if tactical_score >= 75 else "MEDIUM" if tactical_score >= 55 else "LOW"
        side = "WAIT"
        if macro_direction == "LONG_BIAS" and pullback_valid and micro_trigger in self.MICRO_LONG:
            side = "LONG"
        elif macro_direction == "SHORT_BIAS" and pullback_valid and micro_trigger in self.MICRO_SHORT:
            side = "SHORT"

        if game_theory.decision == "WAIT":
            blocked.append("game_theory_wait")
        if not game_theory.execution_ready:
            blocked.append("execution_not_ready")
        if not macro_strong:
            blocked.append("macro_not_aligned")
        if not pullback_valid:
            blocked.append("pullback_not_confirmed")
        if micro_trigger == "none":
            blocked.append("no_micro_trigger")

        entry_window_open = (
            game_theory.decision != "WAIT"
            and game_theory.execution_ready
            and macro_strong
            and pullback_valid
            and micro_trigger != "none"
            and trap_penalty < 25
            and side in {"LONG", "SHORT"}
            and confidence in {"HIGH", "MEDIUM"}
            and not blocked
        )
        entry_allowed = entry_window_open

        if confidence == "HIGH":
            target_ticks, stop_ticks = 3, 2
        elif confidence == "MEDIUM" and side in {"LONG", "SHORT"}:
            target_ticks, stop_ticks = 2, 2
        else:
            target_ticks, stop_ticks = 0, 0

        if side == "WAIT":
            warnings.append("no_tactical_side")
        if trap_penalty > 0:
            warnings.append(f"trap_penalty={trap_penalty}")

        reasons.extend([
            f"macro={macro_direction}",
            f"pullback={pullback_state}",
            f"micro={micro_trigger}",
            f"gt_decision={game_theory.decision}",
        ])

        return TacticalEntryResult(
            entry_allowed=entry_allowed,
            side=side if entry_allowed else "WAIT",
            entry_type="MICRO_PULLBACK_CONTINUATION" if side in {"LONG", "SHORT"} else "NONE",
            confidence=confidence,
            macro_direction=macro_direction,
            pullback_state=pullback_state,
            micro_trigger=micro_trigger,
            target_ticks=target_ticks if entry_allowed else 0,
            stop_ticks=stop_ticks if entry_allowed else 0,
            expected_move_strength=confidence,
            entry_window_open=entry_window_open,
            tactical_score=tactical_score,
            reasons=reasons,
            blocked_reasons=sorted(set(blocked)),
            warnings=warnings,
        )

    @staticmethod
    def _macro_bias(tf: dict[str, dict[str, Any]]) -> tuple[str, bool]:
        dirs = [tf.get(k, {}).get("direction", "NO_DATA") for k in ("WEEK", "DAY", "HOUR")]
        if all(d == "UP" for d in dirs):
            return "LONG_BIAS", True
        if all(d == "DOWN" for d in dirs):
            return "SHORT_BIAS", True
        return "NEUTRAL_BIAS", False

    @staticmethod
    def _pullback_state(macro: str, tf: dict[str, dict[str, Any]]) -> tuple[str, bool, int]:
        ten = tf.get("10 MIN", {}).get("direction", "NO_DATA")
        score = int(tf.get("10 MIN", {}).get("score", 50))
        if macro == "LONG_BIAS" and ten == "DOWN":
            return ("deep_pullback" if score < 35 else "shallow_pullback", True, 70)
        if macro == "SHORT_BIAS" and ten == "UP":
            return ("deep_pullback" if score > 65 else "shallow_pullback", True, 70)
        if macro in {"LONG_BIAS", "SHORT_BIAS"} and ten in {"UP", "DOWN"}:
            return "pullback_finished", False, 40
        return "pullback_active", False, 30

    @staticmethod
    def _micro_trigger(macro: str, tf: dict[str, dict[str, Any]]) -> tuple[str, int]:
        ctx = tf.get("1 MIN", {}).get("microstructure_context", {}).get("context_state", "")
        if not ctx:
            return "none", 25
        if macro == "LONG_BIAS" and ctx in {"reclaim", "momentum_flip", "buyers_absorbed", "micro_breakout", "rejection"}:
            return ctx, 75
        if macro == "SHORT_BIAS" and ctx in {"weak_buyers", "sellers_absorbed", "micro_breakdown", "weak_sellers", "rejection"}:
            return ctx, 75
        return (ctx, 45)

    @staticmethod
    def _trap_penalty(tf: dict[str, dict[str, Any]]) -> int:
        trap_states = {"fake_breakout", "fake_breakdown", "weak_buyers", "weak_sellers"}
        count = 0
        for v in tf.values():
            if v.get("microstructure_context", {}).get("context_state") in trap_states:
                count += 1
        return min(40, count * 12)
