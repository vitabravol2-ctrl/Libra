"""Probability engine that transforms datapack into UP/DOWN probabilities."""

from __future__ import annotations

from typing import Any


class ProbabilityEngine:
    """Runs score calculation for each timeframe using normalized MarketDataPack."""

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
            score = self._score_from_pack(pack)
            up = score
            down = 100 - up
            direction = "UP" if score > 50 else "DOWN" if score < 50 else "NEUTRAL"
            confidence = abs(score - 50) * 2

            output["timeframes"][name] = {
                "score": score,
                "up": up,
                "down": down,
                "direction": direction,
                "confidence": confidence,
                "candle_timestamp": pack.raw.get("close_time", pack.timestamp),
                "health_status": pack.health_status.value,
                "latency_ms": pack.latency_ms,
                "stale_seconds": pack.stale_seconds,
                "errors": pack.errors,
                "warnings": pack.warnings,
            }

        return output

    @staticmethod
    def _score_from_pack(pack: Any) -> int:
        score = 50.0
        score += 10 if pack.candle_stats.direction > 0 else -10 if pack.candle_stats.direction < 0 else 0
        score += (pack.candle_stats.close_position - 0.5) * 20
        score += (pack.direction_bias.get("bias_score", 50) - 50) * 0.4
        score += (pack.volatility.get("volatility_score", 50) - 50) * 0.2
        score += 5 if pack.momentum > 0 else -5 if pack.momentum < 0 else 0
        return max(1, min(100, round(score)))
