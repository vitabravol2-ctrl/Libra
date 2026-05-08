from __future__ import annotations

from dataclasses import dataclass

from core.paper_position import PaperPositionState


@dataclass
class ExitDecision:
    action: str
    state: str
    reason: str


class ExitManager:
    def evaluate(self, position: PaperPositionState) -> ExitDecision:
        if position.state == "CLOSED" and position.exit_reason:
            return ExitDecision("EXIT", "EXITED", position.exit_reason)
        if position.state == "CLOSED":
            return ExitDecision("WAIT", "FLAT", "no_position")
        return ExitDecision("HOLD", "ACTIVE", "holding")
