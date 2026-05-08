from core.paper_position import PaperPositionEngine
from core.reprice_engine import RepriceEngine


def test_reprice_triggered_on_queue_deterioration():
    d = RepriceEngine().evaluate(64000.0, 63999.5, 64000.5, 63999.8, 64000.4, 20, 1.0, 0)
    assert d.should_reprice is True


def test_reprice_stops_on_max_retries():
    d = RepriceEngine().evaluate(64000.0, 63999.5, 64000.5, 63999.8, 64000.4, 20, 1.0, 3)
    assert d.reason == "max_retries_reached"


def test_partial_fill_fields_present():
    e = PaperPositionEngine()
    e.open("LONG", 0.02, 64000.0, 64003.0, 63998.0, 100)
    p = e.update(64000.5, 110, 1.0, 100, "TREND_UP", False, 0.7, 60, {"fill_probability": 62, "final_execution_score": 71, "spread_capture_score": 58})
    assert p.partial_fill_pct == 62
    assert p.remaining_qty > 0
