"""Probability engine that transforms datapack into UP/DOWN probabilities."""

from __future__ import annotations

from typing import Any

from core.direction_model import DirectionModel


class ProbabilityEngine:
    """Runs score calculation for each timeframe."""

    def __init__(self, model: DirectionModel | None = None) -> None:
        self.model = model or DirectionModel()

    def evaluate(self, datapack: dict[str, Any]) -> dict[str, Any]:
        output: dict[str, Any] = {
            "symbol": datapack["symbol"],
            "current_price": datapack["current_price"],
            "timestamp": datapack["timestamp"],
            "timeframes": {},
        }

        for name, timeframe_data in datapack["timeframes"].items():
            score, factors = self.model.calculate_score(timeframe_data)
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
                "factors": factors,
                "candle_timestamp": timeframe_data.timestamp,
            }

        return output
