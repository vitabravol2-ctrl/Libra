# REPORT v0.1.0

## Что реализовано
- Базовый сбор данных BTCUSDT из Binance public API.
- Нормализация candle-параметров по 4 таймфреймам.
- Probability Engine с детерминированной формулой score (1..100).
- GUI на PySide6 с обновлением через QTimer и неблокирующей загрузкой в QThread.
- Логирование ошибок API без падения приложения.
- Базовые unit-тесты для сценариев UP и DOWN.

## Собираемые данные
Для каждой свечи (последняя + история):
- current price
- OHLC
- volume / quote volume
- price change
- candle direction
- volatility
- high/low range
- close position in range
- momentum
- simple delta
- last N candles bias

## Формулы v0.1.0
Базовая точка: `score = 50`.

Факторы:
1. `candle_body_direction`: close > open (+5), close < open (-5)
2. `close_position_in_range`: near high (+5), near low (-5)
3. `volume_strength`: условный индикатор активности (+5/-5/0)
4. `momentum`: positive (+5), negative (-5)
5. `volatility_context`: low volatility (-2), high volatility (+2)
6. `last_n_candles_bias`: bullish bias (+5), bearish bias (-5)

Ограничения:
- `score` clamp в диапазон `1..100`
- `UP = score`
- `DOWN = 100 - UP`
- `direction = UP/DOWN/NEUTRAL` относительно порога 50
- `confidence = abs(score - 50) * 2`

## Что дальше
- Добавить более устойчивые статистические признаки.
- Ввести калибровку весов и бэктест.
- Добавить сохранение истории сигналов.
- Добавить графики и drill-down по факторам в GUI.
