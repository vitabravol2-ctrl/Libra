from __future__ import annotations

from dataclasses import dataclass, field

from core.datapack import MarketDataPack


@dataclass
class MicrostructureContext:
    timeframe: str
    context_state: str
    pressure_side: str
    confidence: int
    warnings: list[str] = field(default_factory=list)
    explanation: str = ""


class MicrostructureContextEngine:
    def evaluate(self, pack: MarketDataPack) -> MicrostructureContext:
        c = pack.candle_stats
        v = pack.volatility
        b = pack.direction_bias
        warnings: list[str] = []

        expansion = v.get("candle_expansion", 1.0)
        compression = v.get("candle_compression", 0.0)
        wick_rejection = c.upper_wick >= c.body_size * 1.0 or c.lower_wick >= c.body_size * 1.0

        if expansion > 1.25 and c.direction > 0:
            state = "impulse_up"
        elif expansion > 1.25 and c.direction < 0:
            state = "impulse_down"
        elif compression > 0.35:
            state = "compression"
        elif expansion > 1.1:
            state = "expansion"
        elif c.direction < 0 and b.get("bias_score", 50) > 55:
            state = "pullback"
        elif c.close_position > 0.65 and c.lower_wick > c.upper_wick:
            state = "reclaim"
        elif wick_rejection:
            state = "rejection"
        elif c.upper_wick > c.body_size * 1.5 and c.close_position < 0.45:
            state = "fake_breakout"
        elif c.lower_wick > c.body_size * 1.5 and c.close_position > 0.55:
            state = "fake_breakdown"
        elif b.get("bullish_pressure", 0.5) > 0.65 and c.direction <= 0:
            state = "buyers_absorbed"
        elif b.get("bearish_pressure", 0.5) > 0.65 and c.direction >= 0:
            state = "sellers_absorbed"
        elif b.get("bullish_pressure", 0.5) > 0.6 and c.body_size < c.range * 0.25:
            state = "weak_buyers"
        elif b.get("bearish_pressure", 0.5) > 0.6 and c.body_size < c.range * 0.25:
            state = "weak_sellers"
        else:
            state = "directional_pressure"

        pressure_delta = b.get("bullish_pressure", 0.5) - b.get("bearish_pressure", 0.5)
        side = "BUYERS" if pressure_delta > 0.08 else "SELLERS" if pressure_delta < -0.08 else "BALANCED"
        confidence = max(1, min(100, round(50 + pressure_delta * 120 + (expansion - 1.0) * 25)))

        if pack.health_status.value != "HEALTHY":
            warnings.append(f"health={pack.health_status.value}")
        if pack.stale_seconds > 120:
            warnings.append("stale_data")
        if wick_rejection:
            warnings.append("wick_rejection")

        return MicrostructureContext(
            timeframe=pack.timeframe,
            context_state=state,
            pressure_side=side,
            confidence=confidence,
            warnings=warnings,
            explanation=f"state={state}, pressure={pressure_delta:.3f}, expansion={expansion:.3f}, compression={compression:.3f}",
        )
