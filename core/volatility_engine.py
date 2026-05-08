from __future__ import annotations


class VolatilityEngine:
    def calculate(self, klines: list[list[float]]) -> dict[str, float]:
        ranges = []
        for k in klines:
            high = float(k[2]); low = float(k[3]); open_price = float(k[1])
            candle_range = max(high - low, 1e-8)
            ranges.append(candle_range / max(open_price, 1e-8))

        avg_range = sum(ranges) / max(len(ranges), 1)
        latest = ranges[-1] if ranges else 0.0
        expansion = latest / max(avg_range, 1e-8)
        compression = max(0.0, 1.0 - min(latest / max(avg_range, 1e-8), 1.0))
        score = max(1, min(100, round(50 + (expansion - 1.0) * 25)))
        return {
            "candle_expansion": round(expansion, 4),
            "candle_compression": round(compression, 4),
            "avg_range": round(avg_range, 6),
            "volatility_score": float(score),
            "latest_range": round(latest, 6),
        }
