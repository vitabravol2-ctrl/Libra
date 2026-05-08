# REPORT v0.2.0

## DataPack Architecture
Введен нормализованный `MarketDataPack` как единый объект состояния рынка на timeframe.
Содержит:
- метаданные источника и времени,
- candle stats,
- volatility layer,
- direction bias layer,
- health/errors/warnings/latency/stale.

## Health System
Статусы:
- HEALTHY
- DELAYED
- STALE
- ERROR

Логика:
- STALE при превышении stale-threshold по интервалу.
- DELAYED при высокой транспортной задержке.
- ERROR при исключении API.
- HEALTHY во всех остальных случаях.

## Telemetry
GUI показывает:
- API status
- update frequency
- total refreshes
- failed refreshes
- average latency
- uptime
- symbol/source

## Volatility Layer
`core/volatility_engine.py` рассчитывает:
- candle expansion
- candle compression
- avg range
- volatility score

## Bias Layer
`core/bias_engine.py` рассчитывает:
- bullish pressure
- bearish pressure
- candle dominance
- directional persistence
- bias score (1..100)

## Thread stability notes
- Обновление выполняется в `QThread`.
- Повторный refresh не стартует пока идет предыдущий.
- Ошибки API переходят в `ERROR` state и лог, без падения GUI/event loop.
