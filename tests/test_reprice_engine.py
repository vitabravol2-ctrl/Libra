from core.reprice_engine import RepriceEngine


def test_reprice_triggered_when_bid_moves_away():
    d = RepriceEngine().evaluate(order_price=100.0, best_bid=100.2, best_ask=100.4, previous_spread=0.4, current_spread=0.4, queue_score=70, retries=0, side="LONG")
    assert d.should_reprice is True


def test_reprice_triggered_on_queue_deterioration():
    d = RepriceEngine().evaluate(order_price=100.0, best_bid=100.0, best_ask=100.2, previous_spread=0.2, current_spread=0.2, queue_score=20, retries=1, side="LONG")
    assert d.should_reprice is True


def test_keep_order_when_conditions_stable():
    d = RepriceEngine().evaluate(order_price=100.0, best_bid=100.0, best_ask=100.2, previous_spread=0.2, current_spread=0.22, queue_score=80, retries=1, side="LONG")
    assert d.should_reprice is False
