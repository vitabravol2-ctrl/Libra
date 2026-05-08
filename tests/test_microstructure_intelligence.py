from core.confirmation_engine import ConfirmationResult, ConfirmationStatus
from core.entry_gate import EntryGate
from core.liquidity_events import LiquidityEventResult, LiquidityEvent
from core.microstructure_intelligence import MicrostructureIntelligence


def _conf_ready():
    return ConfirmationResult(ConfirmationStatus.READY, 80, 20, 20, 20, 10, 10, "ok", {})


def _liq_long():
    return LiquidityEventResult(LiquidityEvent.SWEEP_LOW_RECLAIM, "LONG", "READY", 80, "ok", {})


def test_spoof_detection():
    m = MicrostructureIntelligence().analyze({"large_wall_ratio": 1, "flashing_liquidity": 1, "wall_disappeared": True}, None, _liq_long(), _conf_ready())
    assert m.spoof_score >= 90


def test_absorption_detection():
    m = MicrostructureIntelligence().analyze({"aggressive_buys": 200, "aggressive_sells": 50, "price_delta": 0.0}, None, _liq_long(), _conf_ready())
    assert m.absorption_score >= 50


def test_exhaustion_detection():
    m = MicrostructureIntelligence().analyze({"micro_velocity": 0.1, "prev_micro_velocity": 0.9, "delta_strength": 0.1, "prev_delta_strength": 0.8, "failed_pushes": 3}, None, _liq_long(), _conf_ready())
    assert m.exhaustion_score >= 70


def test_continuation_strong_weak():
    engine = MicrostructureIntelligence()
    strong = engine.analyze({"follow_through": 1, "continuation_velocity": 0.9, "continuation_imbalance": 0.8}, None, _liq_long(), _conf_ready())
    weak = engine.analyze({"follow_through": 0.1, "continuation_velocity": 0.1, "continuation_imbalance": 0.1}, None, _liq_long(), _conf_ready())
    assert strong.continuation_score > weak.continuation_score


def test_vacuum_and_decay_detection():
    m = MicrostructureIntelligence().analyze({"liquidity_above": 0.1, "liquidity_below": 0.2, "velocity_trend": -1, "aggressive_trend": -0.8, "imbalance_trend": -0.7}, None, _liq_long(), _conf_ready())
    assert m.vacuum_score >= 80
    assert m.decay_score >= 70


def test_entry_blocked_by_spoof():
    d = EntryGate().evaluate("TREND_UP", "READY", "READY", 80, 1.0, 100, "LONG", 64000, microstructure={"final_quality": 70, "spoof_score": 80, "exhaustion_score": 10, "decay_score": 10, "continuation_score": 50})
    assert d.reason == "blocked_micro_spoof"


def test_entry_blocked_by_exhaustion():
    d = EntryGate().evaluate("TREND_UP", "READY", "READY", 80, 1.0, 100, "LONG", 64000, microstructure={"final_quality": 70, "spoof_score": 10, "exhaustion_score": 80, "decay_score": 10, "continuation_score": 50})
    assert d.reason == "blocked_micro_exhaustion"


def test_entry_allowed_on_healthy_momentum():
    d = EntryGate().evaluate("TREND_UP", "READY", "READY", 85, 1.0, 100, "LONG", 64000, microstructure={"final_quality": 82, "spoof_score": 10, "exhaustion_score": 20, "decay_score": 20, "continuation_score": 70})
    assert d.allowed is True
