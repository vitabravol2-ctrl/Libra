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
