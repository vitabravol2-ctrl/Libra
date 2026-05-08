from __future__ import annotations

from dataclasses import dataclass

from core.confirmation_engine import ConfirmationEngine
from core.entry_gate import EntryGate
from core.exit_manager import ExitManager
from core.microstructure_intelligence import MicrostructureIntelligence
from core.liquidity_events import LiquidityEventDetector
from core.market_regime import MarketRegimeDetector
from core.paper_position import PaperPositionEngine


@dataclass
class PipelineResult:
    market_regime: dict
    liquidity_event: dict
    confirmation: dict
    microstructure: dict
    entry: dict
    position: dict
    exit: dict


class DecisionPipeline:
    def __init__(self) -> None:
        self.regime = MarketRegimeDetector()
        self.liquidity = LiquidityEventDetector()
        self.confirmation = ConfirmationEngine()
        self.microstructure = MicrostructureIntelligence()
        self.entry = EntryGate()
        self.paper = PaperPositionEngine()
        self.exit = ExitManager()

    def run(self, snapshot: dict) -> PipelineResult:
        regime = self.regime.analyze(snapshot)
        liq = self.liquidity.analyze(snapshot, regime)
        conf = self.confirmation.analyze(snapshot, regime, liq)

        micro = self.microstructure.analyze(snapshot, regime, liq, conf)

        price = float(snapshot.get("price", 0.0))
        entry = self.entry.evaluate(
            regime=regime.regime.value,
            liquidity_status=liq.status,
            confirmation_status=conf.status.value,
            confirmation_score=conf.score,
            spread=float(snapshot.get("spread", 99.0)),
            freshness_ms=int(snapshot.get("freshness_ms", 999999)),
            side=liq.setup_side,
            price=price,
            threshold=int(snapshot.get("score_threshold", 70)),
            timeout_seconds=int(snapshot.get("timeout_seconds", 30)),
            microstructure={**micro.__dict__, "absorption_against": bool(snapshot.get("absorption_against_setup", False))},
            micro_threshold=int(snapshot.get("micro_threshold", 55)),
        )

        now_ts = int(snapshot.get("now_ts", 0))
        if entry.allowed and self.paper.position.state == "CLOSED":
            self.paper.open(entry.side, float(snapshot.get("paper_size", 0.02)), entry.entry_price, entry.tp_price, entry.sl_price, now_ts)
        pos = self.paper.update(
            price=price,
            now_ts=now_ts,
            spread=float(snapshot.get("spread", 99.0)),
            freshness_ms=int(snapshot.get("freshness_ms", 999999)),
            regime=regime.regime.value,
            structure_break=bool(snapshot.get("structure_break", False)),
            momentum=float(snapshot.get("momentum", 0.2)),
            timeout_seconds=int(snapshot.get("timeout_seconds", 30)),
        )
        exit_decision = self.exit.evaluate(pos)
        return PipelineResult(regime.__dict__, liq.__dict__, conf.__dict__, micro.__dict__, entry.__dict__, pos.__dict__, exit_decision.__dict__)
