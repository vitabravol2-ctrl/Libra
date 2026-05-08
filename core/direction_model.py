"""Direction model with deterministic weighted formulas."""

from __future__ import annotations

from dataclasses import asdict

from core.data_collector import TimeframeData


class DirectionModel:
    """Simple non-ML model to calculate directional score in range 1..100."""

    def __init__(self) -> None:
        self.base_score = 50

    def calculate_score(self, timeframe_data: TimeframeData) -> tuple[int, dict[str, float]]:
        data = asdict(timeframe_data)
        score = float(self.base_score)
        factors: dict[str, float] = {}

        candle_body = 5.0 if data["close_price"] > data["open_price"] else -5.0 if data["close_price"] < data["open_price"] else 0.0
        score += candle_body
        factors["candle_body_direction"] = candle_body

        close_pos = data["close_position"]
        close_position_factor = 5.0 if close_pos >= 0.7 else -5.0 if close_pos <= 0.3 else 0.0
        score += close_position_factor
        factors["close_position_in_range"] = close_position_factor

        volume_strength = 5.0 if self._volume_strength(data) > 1.05 else -5.0 if self._volume_strength(data) < 0.95 else 0.0
        score += volume_strength
        factors["volume_strength"] = volume_strength

        momentum_factor = 5.0 if data["momentum"] > 0 else -5.0 if data["momentum"] < 0 else 0.0
        score += momentum_factor
        factors["momentum"] = momentum_factor

        volatility_factor = self._volatility_context(data["volatility"])
        score += volatility_factor
        factors["volatility_context"] = volatility_factor

        bias_factor = 5.0 if data["last_n_candles_bias"] > 0 else -5.0 if data["last_n_candles_bias"] < 0 else 0.0
        score += bias_factor
        factors["last_n_candles_bias"] = bias_factor

        normalized = max(1, min(100, round(score)))
        return normalized, factors

    @staticmethod
    def _volatility_context(volatility: float) -> float:
        if volatility < 0.003:
            return -2.0
        if volatility > 0.03:
            return 2.0
        return 0.0

    @staticmethod
    def _volume_strength(data: dict[str, float]) -> float:
        body = abs(data["price_change"])
        if body <= 1e-8:
            return 1.0
        return (data["quote_volume"] / max(data["close_price"], 1e-8)) / max(body, 1e-8)
