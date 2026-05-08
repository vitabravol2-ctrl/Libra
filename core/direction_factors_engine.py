from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from core.datapack import MarketDataPack

Direction = Literal["UP", "DOWN", "NEUTRAL"]


@dataclass
class DirectionFactor:
    name: str
    value: float
    direction: Direction
    weight: float
    contribution: float
    explanation: str


@dataclass
class DirectionFactorsResult:
    timeframe: str
    total_up_points: float
    total_down_points: float
    neutral_points: float
    final_factor_score: int
    factors: list[DirectionFactor]
    summary: str


class DirectionFactorsEngine:
    WEIGHTS = {
        "candle_body_strength": 1.2,
        "close_position_strength": 1.0,
        "wick_pressure": 0.8,
        "upper_wick_pressure": 0.7,
        "lower_wick_pressure": 0.7,
        "last_n_candles_bias": 1.0,
        "momentum_strength": 1.1,
        "volume_anomaly": 0.6,
        "volatility_expansion": 0.7,
        "volatility_compression": 0.5,
        "trend_slope": 1.0,
        "micro_pullback": 0.6,
        "reclaim_attempt": 0.9,
        "failed_breakdown": 0.9,
        "failed_breakout": 0.9,
    }

    def evaluate(self, pack: MarketDataPack) -> DirectionFactorsResult:
        c = pack.candle_stats
        v = pack.volatility
        b = pack.direction_bias
        last_bias = (b.get("bullish_pressure", 0.5) - b.get("bearish_pressure", 0.5)) * 2
        momentum_n = max(-1.0, min(1.0, pack.momentum / max(c.range, 1e-8)))
        body_ratio = c.body_size / max(c.range, 1e-8)
        wick_diff = (c.lower_wick - c.upper_wick) / max(c.range, 1e-8)
        vol_exp = min(2.0, max(0.0, v.get("candle_expansion", 1.0)))
        vol_cmp = min(1.0, max(0.0, v.get("candle_compression", 0.0)))

        raw = {
            "candle_body_strength": body_ratio * c.direction,
            "close_position_strength": (c.close_position - 0.5) * 2,
            "wick_pressure": wick_diff,
            "upper_wick_pressure": -(c.upper_wick / max(c.range, 1e-8)),
            "lower_wick_pressure": c.lower_wick / max(c.range, 1e-8),
            "last_n_candles_bias": last_bias,
            "momentum_strength": momentum_n,
            "volume_anomaly": 1.0 if c.volume > pack.volume * 0.9 else -0.3,
            "volatility_expansion": (vol_exp - 1.0),
            "volatility_compression": -vol_cmp,
            "trend_slope": (b.get("bias_score", 50) - 50) / 50,
            "micro_pullback": -0.6 if c.direction < 0 and last_bias > 0 else 0.6 if c.direction > 0 and last_bias < 0 else 0.0,
            "reclaim_attempt": 0.7 if c.close_position > 0.65 and c.lower_wick > c.upper_wick else -0.2,
            "failed_breakdown": 0.8 if c.lower_wick > c.body_size and c.close_position > 0.55 else 0.0,
            "failed_breakout": -0.8 if c.upper_wick > c.body_size and c.close_position < 0.45 else 0.0,
        }

        factors: list[DirectionFactor] = []
        up = down = neutral = 0.0
        for name, value in raw.items():
            weight = self.WEIGHTS[name]
            contribution = value * weight
            direction: Direction = "UP" if contribution > 0.05 else "DOWN" if contribution < -0.05 else "NEUTRAL"
            if direction == "UP":
                up += contribution
            elif direction == "DOWN":
                down += abs(contribution)
            else:
                neutral += weight
            factors.append(DirectionFactor(name, round(value, 4), direction, weight, round(contribution, 4), f"{name}={value:.3f} * w={weight:.2f}"))

        net = up - down
        score = max(1, min(100, round(50 + net * 10)))
        summary = f"UP points={up:.2f}, DOWN points={down:.2f}, net={net:.2f}"
        return DirectionFactorsResult(pack.timeframe, round(up, 3), round(down, 3), round(neutral, 3), score, factors, summary)
