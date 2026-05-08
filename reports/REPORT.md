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

## v0.3.0 Update
Direction Factors v2 and Microstructure Context Engine are integrated into ProbabilityEngine.
Final score formula is explicit and explainable (base/bias/volatility/factors/microstructure components).
Current factors are candle-derived only; order book + websocket microstructure is scheduled for later releases.


## v0.3.1
- Expanded ladder to WEEK/DAY/HOUR/10MIN/1MIN/1SEC.
- Introduced `core/timeframe_registry.py` and `core/data_quality_engine.py`.
- 1SEC remains experimental and does not break runtime when exchange 1s candles are unavailable.
- Added anti-chaos gate in probability evaluation (`NO_DATA`, score=50, confidence=0 on bad inputs).
- Added MultiTimeframeState aggregation for next Game Theory integration phase.


## v0.3.2 Stability Prep
- Added Log anti-spam v2 with centralized deduplication for repeated WARN/INFO messages and calmer 1 SEC disabled output.
- Added score stabilizer with hysteresis (UP >= 53, DOWN <= 47, 48-52 hold previous) and raw/stable score split.
- Added 10 MIN fallback aggregation from 1m candles to reduce NO_DATA conditions.
- Refined data quality statuses to include WAITING_FOR_WS/NO_DATA behaviors for safer pre-Game-Theory inputs.
