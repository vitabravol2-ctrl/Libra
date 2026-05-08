from __future__ import annotations

from datetime import datetime, timedelta


class LogDeduplicator:
    def __init__(self) -> None:
        self._last_emit: dict[str, datetime] = {}
        self._last_context_value: dict[str, str] = {}
        self._last_wick_state: dict[str, int] = {}

    def should_emit(self, key: str, cooldown_sec: int, now: datetime | None = None) -> bool:
        now = now or datetime.utcnow()
        last = self._last_emit.get(key)
        if last and now - last < timedelta(seconds=cooldown_sec):
            return False
        self._last_emit[key] = now
        return True

    def should_emit_context_change(self, timeframe: str, context_value: str) -> bool:
        key = f"context:{timeframe}"
        previous = self._last_context_value.get(key)
        if previous == context_value:
            return False
        self._last_context_value[key] = context_value
        return True

    def should_emit_wick_rejection(self, timeframe: str, warning_text: str) -> bool:
        key = f"wick:{timeframe}"
        level = 2 if "strong" in warning_text else 1
        previous = self._last_wick_state.get(key, 0)
        if level > previous:
            self._last_wick_state[key] = level
            return True
        if previous == 0:
            self._last_wick_state[key] = level
            return True
        return False
