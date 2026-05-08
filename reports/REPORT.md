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

 codex/create-tactical-entry-engine
## Tactical Entry Engine v0.5.0

Integrated TacticalEntryEngine for paper intent generation:
- Decision -> Tactical Entry -> Paper Intent.
- Macro/Pullback/Micro architecture implemented.
- Entry window gating and anti-chaos/trap blocking added.
- Tactical score and micro TP/SL tick assignment included.
- Cockpit now shows tactical entry status and paper trade tape placeholder.

Paper-only status remains enforced (no real order execution).
## v0.4.2 Live Game Theory Cockpit
- Центральный блок Game Theory обновлен до live-cockpit формата:
  - TG score + decision
  - regime/dominant side/confidence/execution readiness
  - risk/scenario/agreement/conflict
- Добавлен отдельный Market State panel:
  - Market Mode
  - Strongest / Blocked reason
  - Trap Risk
  - Pullback State
  - Entry Window placeholder (`OPEN` only when execution_ready=true, decision in LONG/SHORT, confidence>=60)
- Добавлен Timeframe Agreement mini-radar:
  - agreement score
  - conflict score
  - active/disabled timeframes
- Добавлен GT Reason Tape (короткая лента последних reasons без GUI-spam).
- Compact timeframe cards расширены краткими quality/context labels.
- Архитектурный контракт pipeline сохранен:
  - DataCollector unchanged
  - ProbabilityEngine contract unchanged
  - GameTheoryDecisionEngine contract unchanged
- По-прежнему no real trading: без Binance keys, без futures/margin исполнения, только анализ и подготовка к paper trading.

## v0.5.0 MARKET REGIME RESET
- Старый decision слой отключён.
- Новый фундамент начинается с Market Regime.
- Пока нет входов (entry disabled).
- Система определяет только режим и ожидаемое следующее событие.
- Следующая версия: v0.5.1 Liquidity Event Layer.

## v0.6.0 TREE ARCHITECTURE RESET
- Удалены перегруженные панели и лишняя телеметрия из GUI.
- Введён строгий pipeline: `market_regime -> liquidity_event -> confirmation -> entry_gate -> exit_manager`.
- Реализованы новые core-модули:
  - `core/market_regime.py`
  - `core/liquidity_events.py`
  - `core/confirmation_engine.py`
  - `core/entry_gate.py`
  - `core/exit_manager.py`
  - `core/decision_pipeline.py`
- Entry разрешается только при подтверждении score>70, fresh data и normal spread.
- Exit ограничен TP(+1/+2/+3), structure break SL, timeout, emergency.

## v0.6.1 LIQUIDITY EVENT LAYER
- второй слой дерева добавлен
- система теперь после Market Regime ищет liquidity setup
- entry всё ещё отключён
- цель следующей версии v0.6.2: Confirmation Layer

## v0.6.2 CONFIRMATION LAYER
- Добавлен третий слой дерева между liquidity и entry.
- Введён `ConfirmationEngine` с проверками orderbook imbalance, aggressive trades, micro velocity, spread quality и data freshness.
- Реализован `confirmation_score` 0..100 и статусы: WEAK, BUILDING, STRONG, READY, BLOCKED.
- Блокировки подтверждения активируются при CHAOS/UNKNOWN, blocked liquidity, stale data и abnormal spread.
- Entry по-прежнему принудительно отключён (NOT_IMPLEMENTED).
- Следующий этап: v0.6.3 ENTRY GATE.

## v0.6.5 EXECUTION QUALITY ENGINE
- added deterministic execution intelligence
- queue positioning
- maker quality analysis
- spread harvesting
- slippage risk
- fill probability
- adaptive timeout
- partial fill support
- cancel/reprice engine
