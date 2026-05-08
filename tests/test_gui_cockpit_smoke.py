import pytest

pytest.importorskip("PySide6")

try:
    from gui.main_window import MainWindow, TradingSettings, compact_timeframe_text
except ImportError as exc:
    pytest.skip(f"GUI runtime deps unavailable: {exc}", allow_module_level=True)


def test_gui_imports_and_window_builds(qapp):
    window = MainWindow()
    assert window.windowTitle().endswith("v0.4.2")


def test_settings_model_works():
    s = TradingSettings(long_threshold=60, short_threshold=40)
    assert s.long_threshold == 60
    assert s.short_threshold == 40


def test_tg_cockpit_panels_render(qapp):
    window = MainWindow()
    result = {
        "symbol": "BTCUSDT",
        "current_price": 100000.0,
        "timeframes": {
            "WEEK": {"score": 60, "health_status": "HEALTHY", "latency_ms": 50},
            "DAY": {"score": 65, "health_status": "HEALTHY", "latency_ms": 40},
            "HOUR": {"score": 55, "health_status": "HEALTHY", "latency_ms": 30},
            "10 MIN": {"score": 45, "health_status": "HEALTHY", "latency_ms": 30},
            "1 MIN": {"score": 50, "health_status": "HEALTHY", "latency_ms": 25},
            "1 SEC": {"health_status": "WAITING_FOR_WS"},
        },
        "game_theory": {
            "global_score": 68, "decision": "LONG", "market_regime": "PULLBACK", "confidence": 74, "execution_ready": True,
            "dominant_side": "BUYERS", "risk_level": "MEDIUM", "scenario_type": "pullback_inside_bullish_structure",
            "agreement_score": 80, "conflict_score": 20, "strongest_reasons": ["pullback_inside_bullish_structure"],
            "blocked_reasons": [], "active_timeframes": ["WEEK", "DAY"], "disabled_timeframes": ["1 SEC"]
        },
    }
    window.apply_result(result)
    assert window.tg_score_big.text() == "68"
    assert window.tg_decision_big.text() == "LONG"
    assert "CONF 74%" in window.tg_meta_line.text()
    assert "Market Mode: PULLBACK" == window.market_mode.text()
    assert "Agreement: 80" == window.agreement_score_label.text()
    assert "pullback_inside_bullish_structure" in window.reason_tape.text()


def test_cockpit_widgets_and_dark_theme_stylesheet(qapp):
    window = MainWindow()
    assert "background-color: #0b0f14" in window.styleSheet()
    assert window.findChild(type(window.tg_score_big), "GaugeScore") is not None
    assert window.findChild(type(window.reason_tape)) is not None
    assert window.log.maximumHeight() <= 16777215


def test_timeframe_compact_formatter_works():
    assert "GREEN" in compact_timeframe_text("DAY", {"score": 66, "health_status": "HEALTHY"})
    assert "RED" in compact_timeframe_text("HOUR", {"score": 43, "health_status": "HEALTHY"})
    assert "WAITING_WS" in compact_timeframe_text("1 SEC", {"health_status": "DISABLED"})
