from core.paper_position import PaperPositionEngine


def _open():
    e = PaperPositionEngine()
    e.open("LONG", 0.02, 64000.0, 64002.0, 63998.5, 100)
    return e


def test_timeout_exit():
    e = _open()
    p = e.update(64000.2, 150, 1.0, 500, "TREND_UP", False, 0.1, 30)
    assert p.exit_reason == "timeout_exit"


def test_emergency_exit():
    e = _open()
    p = e.update(64000.2, 105, 5.0, 500, "TREND_UP", False, 0.8, 30)
    assert p.exit_reason == "emergency_exit"


def test_tp_exit():
    e = _open()
    p = e.update(64002.2, 110, 1.0, 500, "TREND_UP", False, 0.8, 30)
    assert p.exit_reason == "tp_exit"


def test_structure_break_exit():
    e = _open()
    p = e.update(63999.8, 110, 1.0, 500, "TREND_UP", True, 0.8, 30)
    assert p.exit_reason == "structure_break_exit"
