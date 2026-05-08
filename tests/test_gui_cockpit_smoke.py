import pytest

pytest.importorskip("PySide6")

from gui.main_window import MainWindow, TradingSettings, compact_timeframe_text


def test_gui_imports_and_window_builds(qapp):
    window = MainWindow()
    assert window.windowTitle().endswith("v0.4.1")


def test_settings_model_works():
    s = TradingSettings(long_threshold=60, short_threshold=40)
    assert s.long_threshold == 60
    assert s.short_threshold == 40


def test_tg_placeholder_score_renders(qapp):
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
        "game_theory": {"global_score": 46, "decision": "WAIT", "market_regime": "TREND_DOWN", "confidence": 92, "execution_ready": True},
    }
    window.apply_result(result)
    assert window.tg_score_big.text() == "46"
    assert window.tg_decision_big.text() == "WAIT"
    assert "CONF 92%" in window.tg_meta_line.text()


def test_cockpit_widgets_and_dark_theme_stylesheet(qapp):
    window = MainWindow()
    assert "background-color: #0b0f14" in window.styleSheet()
    assert window.findChild(type(window.tg_score_big), "GaugeScore") is not None
    assert window.log.maximumHeight() <= 16777215


def test_timeframe_compact_formatter_works():
    assert "GREEN" in compact_timeframe_text("DAY", {"score": 66, "health_status": "HEALTHY"})
    assert "RED" in compact_timeframe_text("HOUR", {"score": 43, "health_status": "HEALTHY"})
    assert "WAITING_WS" in compact_timeframe_text("1 SEC", {"health_status": "DISABLED"})
