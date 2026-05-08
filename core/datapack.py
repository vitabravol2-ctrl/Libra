from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class HealthStatus(str, Enum):
    HEALTHY = "HEALTHY"
    DELAYED = "DELAYED"
    STALE = "STALE"
    ERROR = "ERROR"


@dataclass
class CandleStats:
    open: float
    high: float
    low: float
    close: float
    volume: float
    range: float
    body_size: float
    upper_wick: float
    lower_wick: float
    direction: int
    close_position: float


@dataclass
class MarketDataPack:
    symbol: str
    timestamp: str
    server_time: str
    source: str
    health_status: HealthStatus
    price: float
    spread_placeholder: float
    volatility: dict[str, float]
    momentum: float
    volume: float
    direction_bias: dict[str, float]
    candle_stats: CandleStats
    timeframe: str
    latency_ms: float
    stale_seconds: float
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)
