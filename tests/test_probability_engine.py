from core.data_collector import TimeframeData
from core.probability_engine import ProbabilityEngine


def make_tf(close_price: float, open_price: float, momentum: float, bias: float) -> TimeframeData:
    return TimeframeData(
        timeframe="TEST",
        open_price=open_price,
        high_price=max(open_price, close_price) + 10,
        low_price=min(open_price, close_price) - 10,
        close_price=close_price,
        volume=1000,
        quote_volume=100000,
        candle_count=50,
        price_change=close_price - open_price,
        candle_direction=1 if close_price > open_price else -1 if close_price < open_price else 0,
        volatility=0.01,
        high_low_range=20,
        close_position=0.8 if close_price >= open_price else 0.2,
        momentum=momentum,
        simple_delta=momentum,
        last_n_candles_bias=bias,
        timestamp="2026-01-01T00:00:00+00:00",
    )


def test_probability_engine_up_bias():
    engine = ProbabilityEngine()
    datapack = {
        "symbol": "BTCUSDT",
        "current_price": 100000.0,
        "timestamp": "2026-01-01T00:00:00+00:00",
        "timeframes": {
            "DAY": make_tf(101000, 100000, 200, 0.4),
        },
    }

    result = engine.evaluate(datapack)
    assert result["timeframes"]["DAY"]["score"] > 50
    assert result["timeframes"]["DAY"]["direction"] == "UP"


def test_probability_engine_down_bias():
    engine = ProbabilityEngine()
    datapack = {
        "symbol": "BTCUSDT",
        "current_price": 100000.0,
        "timestamp": "2026-01-01T00:00:00+00:00",
        "timeframes": {
            "DAY": make_tf(99000, 100000, -200, -0.4),
        },
    }

    result = engine.evaluate(datapack)
    assert result["timeframes"]["DAY"]["score"] < 50
    assert result["timeframes"]["DAY"]["direction"] == "DOWN"
