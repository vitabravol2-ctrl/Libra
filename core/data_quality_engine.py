from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class DataQualityReport:
    quality_score: int
    status: str
    reasons: list[str]


class DataQualityEngine:
    def evaluate(self, pack: Any, klines: list[list[Any]], expected_candles: int, stale_threshold_sec: int, enabled: bool) -> DataQualityReport:
        if not enabled:
            if pack.timeframe == "1 SEC":
                return DataQualityReport(100, "WAITING_FOR_WS", ["timeframe_disabled", "waiting_for_ws"])
            return DataQualityReport(0, "DISABLED", ["timeframe_disabled"])

        reasons: list[str] = []
        if not klines:
            reasons.append("waiting_for_ws")
            return DataQualityReport(60, "WAITING_FOR_WS", reasons)
        score = 100
        if pack.price <= 0:
            score -= 50; reasons.append("price_zero_or_negative")
        if klines and len(klines) < max(3, expected_candles // 3):
            score -= 35; reasons.append("insufficient_candles")
        for k in klines:
            if float(k[2]) == 0 or float(k[3]) == 0 or float(k[4]) == 0:
                score -= 30; reasons.append("empty_candle_detected"); break
        try:
            ts = datetime.fromisoformat(pack.raw.get("close_time", pack.timestamp).replace("Z", "+00:00"))
            if ts.timestamp() <= 0:
                score -= 25; reasons.append("timestamp_broken")
        except Exception:  # noqa: BLE001
            score -= 25; reasons.append("timestamp_broken")

        if pack.stale_seconds > stale_threshold_sec:
            score -= 25; reasons.append("timeframe_stale")
        if pack.volatility.get("volatility_score", 50) >= 98:
            score -= 20; reasons.append("abnormal_volatility")

        score = max(1, min(100, score))
        status = "OK" if score >= 75 else "WARNING" if score >= 45 else "BAD"
        return DataQualityReport(score, status, reasons)
