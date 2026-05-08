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

## v0.3.3 Cockpit Architecture Update
- Replaced overloaded control-center style UI with cockpit-style composition based on `QGroupBox` + `QGridLayout`.
- TG/Game Theory is now represented as the main central gauge (`1..100`) and currently uses placeholder aggregation from MultiTimeframe score outputs.
- Timeframes are rendered as compact assistant indicators (short text + colored bullet semantics).
- Added placeholders for future strategy execution flow:
  - Scalping/Grid settings model (local state only).
  - Trade control state panel with paper-mode arming/disarming.
- Logging panel is compact (20 latest events), auto-scrolling, and warning-group aware.
- Runtime remains analysis-only: **no live order placement** in this release.

## v0.4.0 Game Theory Decision Engine Foundation
- Introduced `core/game_theory_decision_engine.py` as deterministic explainable decision layer.
- Input sources: `MultiTimeframeState` + per-timeframe probability/factors/microstructure outputs + quality/health states.
- Output model: `GameTheoryDecisionResult` + `PaperTradeIntent` placeholder.
- Decision model:
  - `global_score >= 65` => LONG candidate.
  - `global_score <= 35` => SHORT candidate.
  - `36..64` => WAIT.
  - Additional gates: conflict, regime chaos, trap risk, quality and health.
- Regime-aware weighting:
  - Trend profile: WEEK/DAY/HOUR emphasized.
  - Micro profile: 10MIN/1MIN emphasized.
- Execution readiness is true only when quality/health/conflict/regime/trap gates are acceptable.
- Added explanation traces for regime/decision transitions and block reasons for anti-chaos behavior.
- Integration point in GUI now consumes `game_theory` payload for central decision telemetry.
