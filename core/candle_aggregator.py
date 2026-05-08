from __future__ import annotations

from typing import Any


def aggregate_1m_to_10m(candles: list[list[Any]]) -> list[list[Any]]:
    if len(candles) < 10:
        return []
    out: list[list[Any]] = []
    for i in range(0, len(candles) // 10):
        chunk = candles[i * 10 : (i + 1) * 10]
        first, last = chunk[0], chunk[-1]
        high = max(float(c[2]) for c in chunk)
        low = min(float(c[3]) for c in chunk)
        volume = sum(float(c[5]) for c in chunk)
        out.append([first[0], first[1], str(high), str(low), last[4], str(volume), last[6]])
    return out
