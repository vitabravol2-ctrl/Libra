from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StabilizedScore:
    final_score_raw: int
    final_score_stable: int
    direction: str
    warnings: list[str]


class ScoreStabilizer:
    def __init__(self) -> None:
        self._previous_score: dict[str, int] = {}
        self._previous_direction: dict[str, str] = {}

    def stabilize(self, timeframe: str, raw_score: int) -> StabilizedScore:
        prev = self._previous_score.get(timeframe, raw_score)
        jump = abs(raw_score - prev)
        stable = round(prev * 0.7 + raw_score * 0.3) if jump > 8 else raw_score
        warnings: list[str] = []
        if jump > 15:
            warnings.append("score_spike")

        prev_direction = self._previous_direction.get(timeframe, "NEUTRAL")
        if stable >= 53:
            direction = "UP"
        elif stable <= 47:
            direction = "DOWN"
        else:
            direction = prev_direction if prev_direction in {"UP", "DOWN"} else "NEUTRAL"

        self._previous_score[timeframe] = stable
        self._previous_direction[timeframe] = direction
        return StabilizedScore(final_score_raw=raw_score, final_score_stable=stable, direction=direction, warnings=warnings)
