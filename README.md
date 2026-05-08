# BTCUSDT Game Theory / Microtrend Probability Engine v0.3.1.1

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
