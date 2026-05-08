from core.datapack import MultiTimeframeState
from core.game_theory_decision_engine import GameTheoryDecisionEngine


def make_tf(score, direction, context_state="directional_pressure", quality=80, health="HEALTHY"):
    return {
        "score": score,
        "direction": direction,
        "quality_score": quality,
        "health_status": health,
        "microstructure_context": {"context_state": context_state},
    }


def test_bullish_agreement_long():
    e = GameTheoryDecisionEngine()
    tfs = {"WEEK": make_tf(75, "UP"), "DAY": make_tf(70, "UP"), "HOUR": make_tf(68, "UP"), "10 MIN": make_tf(60, "UP"), "1 MIN": make_tf(62, "UP")}
    s = MultiTimeframeState(tfs, list(tfs), [], 90, 10, "UP", True)
    r = e.evaluate(s, tfs)
    assert r.decision == "LONG"
    assert r.long_allowed


def test_bearish_agreement_short():
    e = GameTheoryDecisionEngine()
    tfs = {"WEEK": make_tf(30, "DOWN"), "DAY": make_tf(28, "DOWN"), "HOUR": make_tf(34, "DOWN"), "10 MIN": make_tf(35, "DOWN"), "1 MIN": make_tf(38, "DOWN")}
    s = MultiTimeframeState(tfs, list(tfs), [], 88, 12, "DOWN", True)
    r = e.evaluate(s, tfs)
    assert r.decision == "SHORT"
    assert r.short_allowed


def test_mixed_conflict_wait():
    e = GameTheoryDecisionEngine()
    tfs = {"WEEK": make_tf(70, "UP"), "DAY": make_tf(68, "UP"), "HOUR": make_tf(32, "DOWN"), "10 MIN": make_tf(35, "DOWN"), "1 MIN": make_tf(50, "NEUTRAL")}
    s = MultiTimeframeState(tfs, list(tfs), [], 52, 48, "MIXED", True)
    r = e.evaluate(s, tfs)
    assert r.decision == "WAIT"


def test_chaos_blocks_execution():
    e = GameTheoryDecisionEngine()
    tfs = {"WEEK": make_tf(75, "UP"), "DAY": make_tf(20, "DOWN"), "HOUR": make_tf(80, "UP"), "10 MIN": make_tf(25, "DOWN"), "1 MIN": make_tf(65, "UP")}
    s = MultiTimeframeState(tfs, list(tfs), [], 35, 65, "MIXED", True)
    r = e.evaluate(s, tfs)
    assert r.market_regime == "CHAOS"
    assert not r.execution_ready


def test_trap_detection_lowers_confidence():
    e = GameTheoryDecisionEngine()
    clean = {"WEEK": make_tf(65, "UP"), "DAY": make_tf(64, "UP"), "HOUR": make_tf(66, "UP"), "10 MIN": make_tf(63, "UP"), "1 MIN": make_tf(62, "UP")}
    trap = dict(clean)
    trap["10 MIN"] = make_tf(63, "UP", context_state="fake_breakout")
    s = MultiTimeframeState(clean, list(clean), [], 80, 20, "UP", True)
    r1 = e.evaluate(s, clean)
    r2 = e.evaluate(s, trap)
    assert r2.confidence < r1.confidence


def test_timeframe_weighting_changes_by_regime():
    e = GameTheoryDecisionEngine()
    tfs = {"WEEK": make_tf(70, "UP"), "DAY": make_tf(70, "UP"), "HOUR": make_tf(70, "UP"), "10 MIN": make_tf(70, "UP"), "1 MIN": make_tf(70, "UP")}
    trend_state = MultiTimeframeState(tfs, list(tfs), [], 90, 10, "UP", True)
    chaos_state = MultiTimeframeState(tfs, list(tfs), [], 30, 70, "MIXED", True)
    trend = e.evaluate(trend_state, tfs)
    chaos = e.evaluate(chaos_state, tfs)
    assert trend.timeframe_weights["WEEK"] > chaos.timeframe_weights["WEEK"]
    assert trend.timeframe_weights["10 MIN"] < chaos.timeframe_weights["10 MIN"]
