from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from core.confirmation_engine import ConfirmationResult, ConfirmationStatus
from core.liquidity_events import LiquidityEvent, LiquidityEventResult


class MicrostructureState(str, Enum):
    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    TRAP_RISK = "TRAP_RISK"
    EXHAUSTED = "EXHAUSTED"
    SPOOF_RISK = "SPOOF_RISK"
    ABSORBING = "ABSORBING"
    MOMENTUM_STRONG = "MOMENTUM_STRONG"
    MOMENTUM_DECAY = "MOMENTUM_DECAY"
    HIGH_QUALITY_SETUP = "HIGH_QUALITY_SETUP"


@dataclass
class MicrostructureResult:
    state: MicrostructureState
    spoof_score: int
    absorption_score: int
    exhaustion_score: int
    continuation_score: int
    vacuum_score: int
    decay_score: int
    pullback_quality: int
    final_quality: int
    reason: str
    metrics: dict[str, Any] = field(default_factory=dict)


class MicrostructureIntelligence:
    def analyze(self, snapshot: dict[str, Any], regime_result: Any, liquidity_result: LiquidityEventResult, confirmation_result: ConfirmationResult) -> MicrostructureResult:
        side = liquidity_result.setup_side
        spoof = self._spoof_score(snapshot)
        absorption = self._absorption_score(snapshot, side)
        exhaustion = self._exhaustion_score(snapshot, side)
        continuation = self._continuation_score(snapshot, liquidity_result)
        vacuum = self._vacuum_score(snapshot)
        decay = self._decay_score(snapshot, side)
        pullback = self._pullback_quality(snapshot, side)

        final_quality = int(max(0, min(100, 55 + continuation + pullback - spoof - exhaustion - decay - int(absorption * 0.4) + int(vacuum * 0.3))))
        state = self._state(final_quality, spoof, exhaustion, decay, absorption)

        reasons = []
        if spoof >= 70:
            reasons.append("spoof detected")
        if absorption >= 70:
            reasons.append("absorption detected")
        if continuation <= 25:
            reasons.append("continuation weak")
        if decay >= 60:
            reasons.append("momentum decay")
        if final_quality >= 86:
            reasons.append("high quality setup")
        if not reasons:
            reasons.append("balanced microstructure")

        if confirmation_result.status != ConfirmationStatus.READY:
            final_quality = min(final_quality, 50)
            state = MicrostructureState.WARNING
            reasons.append("confirmation not ready")

        return MicrostructureResult(
            state=state,
            spoof_score=spoof,
            absorption_score=absorption,
            exhaustion_score=exhaustion,
            continuation_score=continuation,
            vacuum_score=vacuum,
            decay_score=decay,
            pullback_quality=pullback,
            final_quality=final_quality,
            reason=", ".join(dict.fromkeys(reasons)),
            metrics={"side": side, "event": liquidity_result.event.value},
        )

    def _spoof_score(self, s: dict[str, Any]) -> int:
        wall = float(s.get("large_wall_ratio", 0.0))
        flash = float(s.get("flashing_liquidity", 0.0))
        vanished = 1.0 if bool(s.get("wall_disappeared", False)) else 0.0
        return int(min(100, round((wall * 35) + (flash * 35) + (vanished * 30))))

    def _absorption_score(self, s: dict[str, Any], side: str) -> int:
        buys = float(s.get("aggressive_buys", 0.0))
        sells = float(s.get("aggressive_sells", 0.0))
        delta = float(s.get("price_delta", 0.0))
        if side == "LONG":
            pressure = max(0.0, (buys - sells) / max(1.0, buys + sells))
            stuck = max(0.0, 1.0 - max(0.0, delta))
        else:
            pressure = max(0.0, (sells - buys) / max(1.0, buys + sells))
            stuck = max(0.0, 1.0 - max(0.0, -delta))
        return int(min(100, round(pressure * stuck * 100)))

    def _exhaustion_score(self, s: dict[str, Any], side: str) -> int:
        vel_now = float(s.get("micro_velocity", 0.0))
        vel_prev = float(s.get("prev_micro_velocity", vel_now))
        delta_now = float(s.get("delta_strength", 0.0))
        delta_prev = float(s.get("prev_delta_strength", delta_now))
        failed_pushes = int(s.get("failed_pushes", 0))
        vel_drop = max(0.0, (vel_prev - vel_now))
        delta_drop = max(0.0, (delta_prev - delta_now))
        return int(min(100, round((vel_drop * 35) + (delta_drop * 35) + min(30, failed_pushes * 10))))

    def _continuation_score(self, s: dict[str, Any], liq: LiquidityEventResult) -> int:
        if liq.event not in {LiquidityEvent.SWEEP_LOW_RECLAIM, LiquidityEvent.SWEEP_HIGH_REJECT}:
            return 50
        follow = float(s.get("follow_through", 0.0))
        cvel = float(s.get("continuation_velocity", 0.0))
        imb = float(s.get("continuation_imbalance", 0.0))
        return int(max(0, min(100, round((follow + cvel + imb) / 3 * 100))))

    def _vacuum_score(self, s: dict[str, Any]) -> int:
        up = float(s.get("liquidity_above", 1.0))
        dn = float(s.get("liquidity_below", 1.0))
        thin = max(0.0, 1.0 - min(up, dn))
        return int(min(100, round(thin * 100)))

    def _decay_score(self, s: dict[str, Any], side: str) -> int:
        vseq = float(s.get("velocity_trend", 0.0))
        aseq = float(s.get("aggressive_trend", 0.0))
        iseq = float(s.get("imbalance_trend", 0.0))
        decay = max(0.0, -vseq) + max(0.0, -aseq) + max(0.0, -iseq)
        return int(min(100, round(decay / 3 * 100)))

    def _pullback_quality(self, s: dict[str, Any], side: str) -> int:
        controlled = 1.0 if bool(s.get("pullback_controlled", False)) else 0.0
        structure_ok = 1.0 if not bool(s.get("pullback_structure_break", False)) else 0.0
        heavy_opp = float(s.get("heavy_opposite_aggression", 0.0))
        return int(max(0, min(100, round((controlled * 0.4 + structure_ok * 0.4 + (1 - heavy_opp) * 0.2) * 100))))

    def _state(self, q: int, spoof: int, exhaustion: int, decay: int, absorption: int) -> MicrostructureState:
        if spoof >= 75:
            return MicrostructureState.SPOOF_RISK
        if exhaustion >= 75:
            return MicrostructureState.EXHAUSTED
        if decay >= 70:
            return MicrostructureState.MOMENTUM_DECAY
        if absorption >= 75:
            return MicrostructureState.ABSORBING
        if q <= 30:
            return MicrostructureState.TRAP_RISK
        if q <= 50:
            return MicrostructureState.WARNING
        if q <= 70:
            return MicrostructureState.HEALTHY
        if q <= 85:
            return MicrostructureState.MOMENTUM_STRONG
        return MicrostructureState.HIGH_QUALITY_SETUP
