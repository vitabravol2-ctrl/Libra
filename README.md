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

