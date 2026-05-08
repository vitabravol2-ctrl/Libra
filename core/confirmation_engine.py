from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from core.liquidity_events import LiquidityEventResult
from core.market_regime import MarketRegime, MarketRegimeResult


class ConfirmationStatus(str, Enum):
    WEAK = "WEAK"
    BUILDING = "BUILDING"
    STRONG = "STRONG"
    READY = "READY"
    BLOCKED = "BLOCKED"


@dataclass
class ConfirmationResult:
    status: ConfirmationStatus
    score: int
    imbalance_score: int
    aggressive_score: int
    velocity_score: int
    spread_score: int
    freshness_score: int
    reason: str
    metrics: dict[str, Any] = field(default_factory=dict)


class ConfirmationEngine:
    max_spread: float = 2.5
    max_freshness_ms: int = 1500

    def analyze(
        self,
        snapshot: dict[str, Any],
        regime_result: MarketRegimeResult,
        liquidity_result: LiquidityEventResult,
    ) -> ConfirmationResult:
        spread = float(snapshot.get("spread", 99.0))
        freshness_ms = int(snapshot.get("freshness_ms", 999999))
        ws_stale = bool(snapshot.get("ws_stale", False))

        if regime_result.regime in {MarketRegime.CHAOS, MarketRegime.UNKNOWN}:
            return self._blocked("blocked_by_regime", spread, freshness_ms, ws_stale)
        if liquidity_result.status == "BLOCKED":
            return self._blocked("blocked_by_liquidity", spread, freshness_ms, ws_stale)
        if ws_stale or freshness_ms > self.max_freshness_ms:
            return self._blocked("stale_data", spread, freshness_ms, ws_stale)
        if spread > self.max_spread:
            return self._blocked("abnormal_spread", spread, freshness_ms, ws_stale)

        side = liquidity_result.setup_side
        imbalance = self._imbalance_score(snapshot, side)
        aggressive = self._aggressive_score(snapshot, side)
        velocity = self._velocity_score(snapshot, side)
        spread_score = int(round(max(0.0, min(1.0, (self.max_spread - spread) / self.max_spread)) * 10))
        freshness_score = int(round(max(0.0, min(1.0, (self.max_freshness_ms - freshness_ms) / self.max_freshness_ms)) * 10))

        total = min(100, imbalance + aggressive + velocity + spread_score + freshness_score)
        status = self._status_from_score(total)
        return ConfirmationResult(
            status=status,
            score=total,
            imbalance_score=imbalance,
            aggressive_score=aggressive,
            velocity_score=velocity,
            spread_score=spread_score,
            freshness_score=freshness_score,
            reason="ok",
            metrics={"side": side, "spread": spread, "freshness_ms": freshness_ms, "ws_stale": ws_stale},
        )

    def _blocked(self, reason: str, spread: float, freshness_ms: int, ws_stale: bool) -> ConfirmationResult:
        return ConfirmationResult(
            status=ConfirmationStatus.BLOCKED,
            score=0,
            imbalance_score=0,
            aggressive_score=0,
            velocity_score=0,
            spread_score=0,
            freshness_score=0,
            reason=reason,
            metrics={"spread": spread, "freshness_ms": freshness_ms, "ws_stale": ws_stale},
        )

    def _imbalance_score(self, snapshot: dict[str, Any], side: str) -> int:
        bid = float(snapshot.get("bid_volume", snapshot.get("orderbook_bid_volume", 0.0)))
        ask = float(snapshot.get("ask_volume", snapshot.get("orderbook_ask_volume", 0.0)))
        total = bid + ask
        if total <= 0:
            return 0
        dominance = bid / total if side == "LONG" else ask / total if side == "SHORT" else 0.5
        return int(round(max(0.0, min(1.0, (dominance - 0.5) / 0.5)) * 25))

    def _aggressive_score(self, snapshot: dict[str, Any], side: str) -> int:
        buys = float(snapshot.get("aggressive_buys", 0.0))
        sells = float(snapshot.get("aggressive_sells", 0.0))
        total = buys + sells
        if total <= 0:
            return 0
        dominance = buys / total if side == "LONG" else sells / total if side == "SHORT" else 0.5
        return int(round(max(0.0, min(1.0, (dominance - 0.5) / 0.5)) * 20))

    def _velocity_score(self, snapshot: dict[str, Any], side: str) -> int:
        velocity = float(snapshot.get("micro_velocity", snapshot.get("velocity", 0.0)))
        stability = float(snapshot.get("velocity_stability", 1.0))
        signed = velocity if side == "LONG" else -velocity if side == "SHORT" else 0.0
        base = max(0.0, min(1.0, signed))
        stable = max(0.0, min(1.0, stability))
        return int(round(base * stable * 35))

    def _status_from_score(self, total: int) -> ConfirmationStatus:
        if total <= 30:
            return ConfirmationStatus.WEAK
        if total <= 55:
            return ConfirmationStatus.BUILDING
        if total <= 75:
            return ConfirmationStatus.STRONG
        return ConfirmationStatus.READY
