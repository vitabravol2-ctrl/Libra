from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TimeframeConfig:
    label: str
    interval: str | None
    candle_limit: int
    stale_threshold_sec: int
    latency_threshold_ms: int
    weight: float
    enabled: bool = True
    experimental: bool = False
    context: str = ""


TIMEFRAME_REGISTRY: dict[str, TimeframeConfig] = {
    "WEEK": TimeframeConfig("WEEK", "1w", 52, 14 * 24 * 3600, 2500, 0.30, context="stable context"),
    "DAY": TimeframeConfig("DAY", "1d", 90, 2 * 24 * 3600, 2000, 0.25, context="macro context"),
    "HOUR": TimeframeConfig("HOUR", "1h", 168, 2 * 3600, 1500, 0.20, context="local trend"),
    "10 MIN": TimeframeConfig("10 MIN", "10m", 180, 20 * 60, 1500, 0.15, context="structure"),
    "1 MIN": TimeframeConfig("1 MIN", "1m", 240, 120, 1500, 0.10, context="entry preparation"),
    "1 SEC": TimeframeConfig("1 SEC", None, 0, 5, 1000, 0.0, enabled=False, experimental=True, context="execution timing / experimental"),
}
