# BTCUSDT Game Theory / Microtrend Probability Engine v0.4.2

Desktop-приложение на PySide6 для оценки вероятности направления BTCUSDT на таймфреймах: 1D / 1H / 10M / 1M.

## Pipeline
Collector → DataPack v2 → Probability Engine → GUI.

## Что добавлено
- Единый `MarketDataPack` для каждого timeframe.
- Health system: `HEALTHY`, `DELAYED`, `STALE`, `ERROR`.
- GUI health panel с latency/stale метриками.
- SYSTEM TELEMETRY блок.
- Volatility engine и bias engine для нормализованных признаков.
- Дедупликация логов (без спама одинаковыми сообщениями).
- Direction Factors v2 (15 candle-based factors) с прозрачным вкладом факторов.
- Microstructure Context Engine (candle-only, без order book/WebSocket на текущем этапе).
- Multi-timeframe ladder: WEEK, DAY, HOUR, 10 MIN, 1 MIN, 1 SEC (experimental).

## Требования
Файл `requirements.txt` теперь обязателен для стандартного сценария установки зависимостей.

Содержимое:
- `PySide6>=6.7`
- `requests>=2.31`
- `pytest>=8.0`

## Запуск проекта

### Вариант 1: напрямую через Python
```bash
python main.py
```

### Вариант 2: Windows script (рекомендуется)
- `RUN_APP.bat`
- `RUN_APP.ps1`

Эти скрипты:
1. переходят в директорию проекта,
2. создают `.venv` при отсутствии,
3. активируют окружение,
4. обновляют `pip`,
5. проверяют `requirements.txt`:
   - `[INFO] requirements.txt found` → выполняется `pip install -r requirements.txt`,
   - `[WARNING] requirements.txt not found` → установка пропускается, запуск продолжается,
6. запускают GUI: `python main.py`.

## Обновление и запуск
- `UPDATE_AND_RUN.bat`
- `UPDATE_AND_RUN.ps1`

Эти скрипты:
1. выполняют `git pull`,
2. подготавливают/активируют `.venv`,
3. обновляют `pip`,
4. условно устанавливают зависимости из `requirements.txt` (или показывают warning и продолжают),
5. запускают тесты `pytest -q`,
6. при успешных тестах запускают GUI.

## Тесты
```bash
pytest -q
```

## Примечания по отказоустойчивости скриптов
- Скрипты больше не падают при отсутствии `requirements.txt`.
- В сценариях ошибок предусмотрен явный вывод в консоль.
- В PowerShell и BAT сценариях есть ожидание ввода (`pause` / `Read-Host`), поэтому окно не закрывается мгновенно.
- Проект не является торговым ботом: нет live-trading, API-ключей и исполнения ордеров.


## v0.3.2 Stability Prep
- Added Log anti-spam v2 with centralized deduplication for repeated WARN/INFO messages and calmer 1 SEC disabled output.
- Added score stabilizer with hysteresis (UP >= 53, DOWN <= 47, 48-52 hold previous) and raw/stable score split.
- Added 10 MIN fallback aggregation from 1m candles to reduce NO_DATA conditions.
- Refined data quality statuses to include WAITING_FOR_WS/NO_DATA behaviors for safer pre-Game-Theory inputs.

## v0.3.3 Cockpit GUI Refactor
- GUI reorganized into a compact **trading cockpit** layout with three zones:
  - **Top panel**: Current Price, API status, update status, system health, Start/Pause/Refresh.
  - **Center panel**: large **TG main gauge** (`TG SCORE 1..100`) with LONG/SHORT/NEUTRAL color signaling.
  - **Side panel**: compact timeframe indicators (WEEK/DAY/HOUR/10M/1M/1S) with color-dot status text.
- Added **Scalping/Grid Settings** block as a local placeholder (in-memory only): Apply/Reset/Save Profile.
- Added **Trade Control** block placeholder: TG Decision, Position State, Paper Mode, Last Signal/Reason, plus Arm/Disarm/Emergency Stop.
- Compact logs now keep only the latest 20 lines, auto-scroll, and group warnings to reduce spam.
- **No real trading added**: no order execution, no broker/exchange trading API actions.

## v0.4.0 Game Theory Decision Engine Foundation
- Added deterministic `GameTheoryDecisionEngine` as the central decision brain (not AI).
- Added `GameTheoryDecisionResult` with explainable fields: `global_score`, `decision`, `market_regime`, `confidence`, agreement/conflict, risk, execution readiness, reasons, and per-timeframe weights.
- Added market regime detection: `TREND_UP`, `TREND_DOWN`, `RANGE`, `EXPANSION`, `PULLBACK`, `REVERSAL_RISK`, `CHAOS`, plus trap-oriented scenario routing.
- Added dynamic timeframe weighting profiles (trend vs micro mode).
- Added trap/fake-move interpretation (`fake_breakout`, `fake_breakdown`, `liquidity_grab`, weak/trapped participants, exhaustion).
- Added `PaperTradeIntent` placeholder for future paper trading integration (no real orders).
- GUI main gauge now displays **Game Theory Engine** state with regime/confidence/execution-readiness and explainable reasons.
- Still **analysis-only**: no Binance keys, no futures/margin/autotrading execution.

 codex/create-tactical-entry-engine
## Tactical Entry Engine (v0.5.0)

Paper/simulation-only tactical layer added after Game Theory decision.

- Macro layer: WEEK/DAY/HOUR alignment -> LONG_BIAS / SHORT_BIAS / NEUTRAL_BIAS.
- Pullback layer: 10 MIN validates local pullback vs macro trend.
- Micro trigger layer: 1 MIN context (reclaim, momentum flip, weak buyers/sellers, breakout/breakdown).
- Entry window opens only when: GT != WAIT, execution_ready, macro aligned, pullback valid, micro trigger present, low trap risk.
- Tactical score (1..100) combines GT score, pullback/micro quality, conflict, trap risk.
- Tick model (micro scalp): HIGH=TP3/SL2, MEDIUM=TP2/SL2, LOW=no entry.

 Safety: paper intent only. No exchange execution, no API keys, no auto-trading.
## v0.4.2 Live Game Theory Cockpit + Market State Panel
- Reworked central Game Theory widget into a **live cockpit panel** with TG score, decision, regime, dominant side, confidence, execution readiness, risk, scenario, agreement and conflict indicators.
- Added dedicated **Market State** block: market mode, strongest reason, blocked reason, trap risk, pullback state and Entry Window status.
- Added **Timeframe Agreement mini-radar** with agreement/conflict score plus active/disabled timeframes.
- Extended compact timeframe cards with score, direction, and short quality/context labels.
- Added **GT Reason Tape** for concise strongest/blocked reasons and short explanations (last 3-5 items).
- Entry Window is a placeholder signal (`OPEN` when execution_ready=true, decision is LONG/SHORT, confidence>=60).
- Runtime remains strictly **analysis-only / paper-prep**: no real trading execution, no Binance API keys.

## v0.5.0 MARKET REGIME RESET
- Старый decision-слой отключён и изолирован через новый pipeline.
- Новый фундамент начинается с определения Market Regime.
- В v0.5.0 входы в сделки отключены (no-entry mode).
- Система определяет режим, разрешённое направление и ожидаемое следующее событие.
- Следующая версия v0.5.1: Liquidity Event Layer.

## v0.6.0 TREE ARCHITECTURE RESET
- Старые системы удалены/изолированы из активного UI-контура.
- GUI полностью упрощён до дерева принятия решений.
- Decision pipeline теперь deterministic: `regime -> liquidity -> confirmation -> entry -> exit`.
- Архитектура основана только на 5 узлах: MARKET REGIME, LIQUIDITY EVENT, CONFIRMATION, ENTRY, EXIT.
- Цель системы: microstructure tick scalping (+1/+2/+3 ticks) без AI/предикторов.

## v0.6.1 LIQUIDITY EVENT LAYER
- второй слой дерева добавлен
- система теперь после Market Regime ищет liquidity setup
- entry всё ещё отключён
- цель следующей версии v0.6.2: Confirmation Layer
