from core.datapack import MultiTimeframeState
from core.game_theory_decision_engine import GameTheoryDecisionResult, PaperTradeIntent
from core.tactical_entry_engine import TacticalEntryEngine


def make_gt(decision="LONG", regime="TREND_UP", execution=True, conflict=20, score=74):
    return GameTheoryDecisionResult(
        global_score=score,
        decision=decision,
        confidence=80,
        market_regime=regime,
        dominant_side="UP" if decision != "SHORT" else "DOWN",
        agreement_score=80,
        conflict_score=conflict,
        risk_level="LOW",
        execution_ready=execution,
        scenario_type=regime,
        paper_trade_intent=PaperTradeIntent(True, decision, 80, "test", "LOW"),
    )


def make_tf(week, day, hour, ten, one, one_ctx="reclaim"):
    return {
        "WEEK": {"direction": week, "score": 70, "microstructure_context": {"context_state": "directional_pressure"}},
        "DAY": {"direction": day, "score": 70, "microstructure_context": {"context_state": "directional_pressure"}},
        "HOUR": {"direction": hour, "score": 70, "microstructure_context": {"context_state": "directional_pressure"}},
        "10 MIN": {"direction": ten, "score": 40 if ten == "DOWN" else 60, "microstructure_context": {"context_state": "directional_pressure"}},
        "1 MIN": {"direction": one, "score": 60 if one == "UP" else 40, "microstructure_context": {"context_state": one_ctx}},
    }


def make_state(tfs, dominant="UP", agreement=80, conflict=20):
    return MultiTimeframeState(tfs, list(tfs), [], agreement, conflict, dominant, True)


def test_bullish_pullback_gives_long():
    e = TacticalEntryEngine()
    tfs = make_tf("UP", "UP", "UP", "DOWN", "UP", "reclaim")
    r = e.evaluate(make_gt("LONG"), make_state(tfs), tfs)
    assert r.entry_allowed
    assert r.side == "LONG"


def test_bearish_pullback_gives_short():
    e = TacticalEntryEngine()
    tfs = make_tf("DOWN", "DOWN", "DOWN", "UP", "DOWN", "weak_buyers")
    r = e.evaluate(make_gt("SHORT", regime="TREND_DOWN"), make_state(tfs, dominant="DOWN"), tfs)
    assert r.entry_allowed
    assert r.side == "SHORT"


def test_mixed_macro_blocks_entry():
    e = TacticalEntryEngine()
    tfs = make_tf("UP", "DOWN", "UP", "DOWN", "UP", "reclaim")
    r = e.evaluate(make_gt("LONG"), make_state(tfs, dominant="MIXED", agreement=55, conflict=45), tfs)
    assert not r.entry_allowed
    assert "macro_not_aligned" in r.blocked_reasons


def test_chaos_blocks_entry():
    e = TacticalEntryEngine()
    tfs = make_tf("UP", "UP", "UP", "DOWN", "UP", "reclaim")
    r = e.evaluate(make_gt("LONG", regime="CHAOS", conflict=70), make_state(tfs, conflict=70), tfs)
    assert not r.entry_allowed
    assert "chaos_regime" in r.blocked_reasons


def test_trap_lowers_tactical_score():
    e = TacticalEntryEngine()
    clean = make_tf("UP", "UP", "UP", "DOWN", "UP", "reclaim")
    trap = make_tf("UP", "UP", "UP", "DOWN", "UP", "weak_buyers")
    r1 = e.evaluate(make_gt("LONG"), make_state(clean), clean)
    r2 = e.evaluate(make_gt("LONG"), make_state(trap), trap)
    assert r2.tactical_score < r1.tactical_score


def test_no_micro_trigger_wait():
    e = TacticalEntryEngine()
    tfs = make_tf("UP", "UP", "UP", "DOWN", "UP", "")
    r = e.evaluate(make_gt("LONG"), make_state(tfs), tfs)
    assert not r.entry_allowed
    assert "no_micro_trigger" in r.blocked_reasons


def test_target_ticks_assigned_correctly():
    e = TacticalEntryEngine()
    high = make_tf("UP", "UP", "UP", "DOWN", "UP", "reclaim")
    high_r = e.evaluate(make_gt("LONG", score=80), make_state(high), high)
    med_r = e.evaluate(make_gt("LONG", score=58), make_state(high), high)
    assert high_r.target_ticks == 3 and high_r.stop_ticks == 2
    assert med_r.target_ticks == 2 and med_r.stop_ticks == 2
