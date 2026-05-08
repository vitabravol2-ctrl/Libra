# BTCUSDT Game Theory / Microtrend Probability Engine v0.1.0

Desktop-приложение на PySide6 для оценки вероятности направления BTCUSDT на таймфреймах:
- 1D
- 1H
- 10M
- 1M

## Что делает
- Сбор публичных данных Binance (без ключей).
- Нормализация свечных признаков.
- Расчёт score (1..100), UP %, DOWN %, direction и confidence.
- GUI с 4 шкалами и логом обновлений.

## Запуск
```bash
python main.py
```

## Тесты
```bash
pytest -q
```
