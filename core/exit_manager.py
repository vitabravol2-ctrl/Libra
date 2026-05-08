from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ExitDecision:
    action: str
    state: str
    reason: str


class ExitManager:
    def evaluate(self, position_side: str, ticks_in_profit: int, structure_break: bool, elapsed_sec: int, emergency: bool) -> ExitDecision:
        if emergency:
            return ExitDecision("EXIT", "DONE", "emergency_exit")
        if structure_break:
            return ExitDecision("EXIT", "DONE", "structure_break_sl")
        if ticks_in_profit >= 3:
            return ExitDecision("TAKE_PROFIT", "DONE", "tp_3_ticks")
        if ticks_in_profit >= 2:
            return ExitDecision("TAKE_PROFIT", "DONE", "tp_2_ticks")
        if ticks_in_profit >= 1:
            return ExitDecision("TAKE_PROFIT", "DONE", "tp_1_tick")
        if elapsed_sec >= 30:
            return ExitDecision("EXIT", "DONE", "timeout_exit")
        return ExitDecision("HOLD", "ACTIVE", f"holding_{position_side.lower()}")
