from __future__ import annotations

from dataclasses import dataclass

from core.confirmation_engine import ConfirmationEngine
from core.entry_gate import EntryGate
from core.exit_manager import ExitManager
from core.liquidity_events import LiquidityEventDetector
from core.market_regime import MarketRegimeDetector


@dataclass
class PipelineResult:
    market_regime: dict
    liquidity_event: dict
    confirmation: dict
    entry: dict
    exit: dict


class DecisionPipeline:
    def __init__(self) -> None:
        self.regime = MarketRegimeDetector()
        self.liquidity = LiquidityEventDetector()
        self.confirmation = ConfirmationEngine()
        self.entry = EntryGate()
        self.exit = ExitManager()

    def run(self, snapshot: dict) -> PipelineResult:
        regime = self.regime.analyze(snapshot)
        liq = self.liquidity.detect(snapshot)
        conf = self.confirmation.evaluate(snapshot)
        entry = self.entry.evaluate(regime.regime.value, liq.event.value, conf.score, conf.data_fresh, conf.spread_normal)
        exit_decision = self.exit.evaluate(entry.side, int(snapshot.get("ticks_in_profit", 0)), bool(snapshot.get("structure_break", False)), int(snapshot.get("elapsed_sec", 0)), bool(snapshot.get("emergency", False)))
        return PipelineResult(regime.__dict__, liq.__dict__, conf.__dict__, entry.__dict__, exit_decision.__dict__)
