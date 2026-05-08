# BTCUSDT Game Theory / Microtrend Probability Engine v0.2.0

Desktop-приложение на PySide6 для оценки вероятности направления BTCUSDT на таймфреймах: 1D / 1H / 10M / 1M.

## Pipeline v0.2.0
Collector → DataPack v2 → Probability Engine → GUI.

## Что добавлено
- Единый `MarketDataPack` для каждого timeframe.
- Health system: `HEALTHY`, `DELAYED`, `STALE`, `ERROR`.
- GUI health panel с latency/stale метриками.
- SYSTEM TELEMETRY блок.
- Volatility engine и bias engine для нормализованных признаков.
- Дедупликация логов (без спама одинаковыми сообщениями).

## Запуск
```bash
python main.py
```

## Тесты
```bash
pytest -q
```

## v0.3.0 Direction Factors + Microstructure Context
- Added Direction Factors v2 (15 candle-based factors) with transparent contributions.
- Added Microstructure Context Engine (candle-only, no order book/WebSocket yet).
- Final score now combines: base + bias + volatility + factors + microstructure.
- Still NOT a trading bot: no live trading, no keys, no margin/futures execution.
- Order book and WebSocket context layer planned for future versions.


## v0.3.1 Timeframe Expansion + Data Stability
- Added multi-timeframe ladder: WEEK, DAY, HOUR, 10 MIN, 1 MIN, 1 SEC (experimental).
- 1W provides global context for cleaner directional map.
- 1S is intentionally experimental with safe fallback state `DISABLED / WAITING_FOR_WS`.
- Added Timeframe Registry and Data Quality Layer to control freshness, candle sufficiency, timestamp and anomaly checks.
- ProbabilityEngine now blocks scoring on bad data and emits `NO_DATA` with neutral score (50/50).
- Added `MultiTimeframeState` for future Game Theory Layer input without adding TG logic yet.
