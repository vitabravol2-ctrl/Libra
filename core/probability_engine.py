from __future__ import annotations

from typing import Any

from core.data_quality_engine import DataQualityEngine
from core.datapack import HealthStatus, MultiTimeframeState
from core.direction_factors_engine import DirectionFactorsEngine
from core.microstructure_context_engine import MicrostructureContextEngine
from core.game_theory_decision_engine import GameTheoryDecisionEngine
from core.score_stabilizer import ScoreStabilizer
from core.timeframe_registry import TIMEFRAME_REGISTRY


class ProbabilityEngine:
    def __init__(self) -> None:
        self.factors_engine = DirectionFactorsEngine()
        self.micro_engine = MicrostructureContextEngine()
        self.quality_engine = DataQualityEngine()
        self.score_stabilizer = ScoreStabilizer()
        self.game_theory_engine = GameTheoryDecisionEngine()

    def evaluate(self, datapack: dict[str, Any]) -> dict[str, Any]:
        output = {"symbol": datapack["symbol"], "current_price": datapack["current_price"], "timestamp": datapack["timestamp"], "timeframes": {}, "telemetry": datapack.get("telemetry", {})}
        directions = []
        for name, pack in datapack["timeframes"].items():
            cfg = TIMEFRAME_REGISTRY[name]
            klines = pack.raw.get("klines", [])
            q = self.quality_engine.evaluate(pack, klines, cfg.candle_limit, cfg.stale_threshold_sec, cfg.enabled)
            blocked = pack.health_status in {HealthStatus.ERROR, HealthStatus.DISABLED} or q.quality_score < 45 or "insufficient_candles" in q.reasons
            if blocked:
                res = {"score": 50, "final_score": 50, "up": 50, "down": 50, "direction": "NO_DATA", "confidence": 0, "quality_score": q.quality_score, "quality_status": q.status, "quality_reasons": q.reasons, "health_status": pack.health_status.value, "context": cfg.context, "strongest_factor": "--", "microstructure_context": {"context_state": "NO_DATA", "pressure_side": "NONE", "warnings": q.reasons}}
            else:
                factors = self.factors_engine.evaluate(pack); micro = self.micro_engine.evaluate(pack)
                base = self._base_score(pack); bias = int(pack.direction_bias.get("bias_score", 50)); vol = int(pack.volatility.get("volatility_score", 50)); fac = factors.final_factor_score
                micro_score = micro.confidence if micro.pressure_side == "BUYERS" else 100 - micro.confidence if micro.pressure_side == "SELLERS" else 50
                score = max(1, min(100, round(base*0.3 + bias*0.2 + vol*0.1 + fac*0.25 + micro_score*0.15)))
                stabilized = self.score_stabilizer.stabilize(name, score)
                strongest = max(factors.factors, key=lambda x: abs(x.contribution)).name if factors.factors else "--"
                res = {"score": stabilized.final_score_stable, "final_score": stabilized.final_score_stable, "final_score_raw": stabilized.final_score_raw, "final_score_stable": stabilized.final_score_stable, "up": stabilized.final_score_stable, "down": 100-stabilized.final_score_stable, "direction": stabilized.direction, "confidence": abs(stabilized.final_score_stable-50)*2, "quality_score": q.quality_score, "quality_status": q.status, "quality_reasons": q.reasons + stabilized.warnings, "health_status": pack.health_status.value, "context": cfg.context, "strongest_factor": strongest, "factors": [f.__dict__ for f in factors.factors], "factors_score": fac, "microstructure_context": micro.__dict__}
            output["timeframes"][name] = res
            if res["direction"] in {"UP", "DOWN"}: directions.append(res["direction"])

        output["multi_timeframe_state"] = self._build_state(output["timeframes"], directions)
        gt = self.game_theory_engine.evaluate(output["multi_timeframe_state"], output["timeframes"])
        output["game_theory"] = {**gt.__dict__, "paper_trade_intent": gt.paper_trade_intent.__dict__ if gt.paper_trade_intent else None}
        return output

    def _build_state(self, tf_results: dict[str, dict[str, Any]], directions: list[str]) -> MultiTimeframeState:
        active = [k for k, v in tf_results.items() if v["direction"] != "NO_DATA"]
        disabled = [k for k, v in tf_results.items() if v["health_status"] == "DISABLED"]
        up = directions.count("UP"); down = directions.count("DOWN"); total = max(1, up + down)
        agreement = round(max(up, down) / total * 100)
        conflict = 100 - agreement
        dominant = "UP" if up > down else "DOWN" if down > up else "MIXED"
        clean = all(v["quality_score"] >= 45 or v["health_status"] == "DISABLED" for v in tf_results.values())
        warnings = [f"{k}:{','.join(v['quality_reasons'])}" for k, v in tf_results.items() if v["quality_reasons"]]
        return MultiTimeframeState(tf_results, active, disabled, agreement, conflict, dominant, clean, warnings)

    @staticmethod
    def _base_score(pack: Any) -> int:
        score = 50 + (10 if pack.candle_stats.direction > 0 else -10 if pack.candle_stats.direction < 0 else 0) + (pack.candle_stats.close_position - 0.5) * 20 + (5 if pack.momentum > 0 else -5 if pack.momentum < 0 else 0)
        return max(1, min(100, round(score)))
