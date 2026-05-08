"""Probability engine that transforms datapack into UP/DOWN probabilities."""

from __future__ import annotations

from typing import Any

from core.direction_factors_engine import DirectionFactorsEngine
from core.microstructure_context_engine import MicrostructureContextEngine


class ProbabilityEngine:
    def __init__(self) -> None:
        self.factors_engine = DirectionFactorsEngine()
        self.micro_engine = MicrostructureContextEngine()

    def evaluate(self, datapack: dict[str, Any]) -> dict[str, Any]:
        output: dict[str, Any] = {
            "symbol": datapack["symbol"],
            "current_price": datapack["current_price"],
            "timestamp": datapack["timestamp"],
            "server_time": datapack.get("server_time"),
            "source": datapack.get("source"),
            "timeframes": {},
            "telemetry": datapack.get("telemetry", {}),
        }

        for name, pack in datapack["timeframes"].items():
            factors = self.factors_engine.evaluate(pack)
            micro = self.micro_engine.evaluate(pack)
            base_score = self._base_score(pack)
            bias_score = int(pack.direction_bias.get("bias_score", 50))
            volatility_score = int(pack.volatility.get("volatility_score", 50))
            factors_score = factors.final_factor_score
            micro_score = micro.confidence if micro.pressure_side == "BUYERS" else 100 - micro.confidence if micro.pressure_side == "SELLERS" else 50

            final_score = round(base_score * 0.30 + bias_score * 0.20 + volatility_score * 0.10 + factors_score * 0.25 + micro_score * 0.15)
            final_score = max(1, min(100, final_score))
            up = final_score
            down = 100 - up
            direction = "UP" if final_score > 50 else "DOWN" if final_score < 50 else "NEUTRAL"
            confidence = abs(final_score - 50) * 2

            output["timeframes"][name] = {
                "score": final_score,
                "up": up,
                "down": down,
                "direction": direction,
                "confidence": confidence,
                "base_score": base_score,
                "bias_score": bias_score,
                "volatility_score": volatility_score,
                "factors_score": factors_score,
                "microstructure_score": micro_score,
                "final_score": final_score,
                "factors": [f.__dict__ for f in factors.factors],
                "factors_summary": factors.summary,
                "microstructure_context": micro.__dict__,
                "explanation": f"final={final_score} from base={base_score}, bias={bias_score}, vol={volatility_score}, factors={factors_score}, micro={micro_score}",
                "candle_timestamp": pack.raw.get("close_time", pack.timestamp),
                "health_status": pack.health_status.value,
                "latency_ms": pack.latency_ms,
                "stale_seconds": pack.stale_seconds,
                "errors": pack.errors,
                "warnings": pack.warnings,
            }

        return output

    @staticmethod
    def _base_score(pack: Any) -> int:
        score = 50.0
        score += 10 if pack.candle_stats.direction > 0 else -10 if pack.candle_stats.direction < 0 else 0
        score += (pack.candle_stats.close_position - 0.5) * 20
        score += 5 if pack.momentum > 0 else -5 if pack.momentum < 0 else 0
        return max(1, min(100, round(score)))
