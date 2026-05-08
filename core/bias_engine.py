from __future__ import annotations


class BiasEngine:
    def calculate(self, klines: list[list[float]]) -> dict[str, float]:
        bullish = bearish = dominance = persistence = 0.0
        prev_dir = 0
        streak = 0
        for k in klines:
            open_price = float(k[1]); close_price = float(k[4]); high = float(k[2]); low = float(k[3])
            direction = 1 if close_price > open_price else -1 if close_price < open_price else 0
            body = abs(close_price - open_price)
            rng = max(high - low, 1e-8)
            dominance += body / rng
            if direction > 0:
                bullish += 1
            elif direction < 0:
                bearish += 1
            if direction != 0 and direction == prev_dir:
                streak += 1
            prev_dir = direction

        n = max(len(klines), 1)
        bullish_pressure = bullish / n
        bearish_pressure = bearish / n
        candle_dominance = dominance / n
        directional_persistence = streak / max(n - 1, 1)
        raw = (bullish_pressure - bearish_pressure) * 50 + (candle_dominance - 0.5) * 30 + directional_persistence * 20
        score = max(1, min(100, round(50 + raw)))
        return {
            "bullish_pressure": round(bullish_pressure, 4),
            "bearish_pressure": round(bearish_pressure, 4),
            "candle_dominance": round(candle_dominance, 4),
            "directional_persistence": round(directional_persistence, 4),
            "bias_score": float(score),
        }
