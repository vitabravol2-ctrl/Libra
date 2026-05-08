"""Main PySide6 GUI window for BTCUSDT probability engine."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QThread, QTimer, Signal
from PySide6.QtWidgets import QGridLayout, QLabel, QMainWindow, QProgressBar, QTextEdit, QVBoxLayout, QWidget

from core.data_collector import DataCollector
from core.probability_engine import ProbabilityEngine


class Worker(QThread):
    data_ready = Signal(dict)
    error = Signal(str)

    def __init__(self, collector: DataCollector, engine: ProbabilityEngine) -> None:
        super().__init__()
        self.collector = collector
        self.engine = engine

    def run(self) -> None:
        try:
            self.data_ready.emit(self.engine.evaluate(self.collector.collect()))
        except Exception as exc:  # noqa: BLE001
            self.error.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("BTCUSDT Game Theory / Microtrend Probability Engine v0.2.0")
        self.resize(980, 700)
        self.collector = DataCollector(); self.engine = ProbabilityEngine(); self.worker: Worker | None = None
        self.bars: dict[str, QProgressBar] = {}
        self.labels: dict[str, QLabel] = {}
        self.health_labels: dict[str, QLabel] = {}
        self.last_log_message = ""
        self.start_time = datetime.utcnow()
        self.total_refreshes = 0
        self.failed_refreshes = 0
        self.avg_latency_ms = 0.0

        central = QWidget(); layout = QVBoxLayout(central)
        self.price_label = QLabel("Current Price: --"); layout.addWidget(self.price_label)

        grid = QGridLayout(); layout.addLayout(grid)
        for row, tf in enumerate(["DAY", "HOUR", "10 MIN", "1 MIN"]):
            grid.addWidget(QLabel(tf), row, 0)
            bar = QProgressBar(); bar.setRange(1, 100); bar.setValue(50); bar.setFormat("%v"); self.bars[tf] = bar; grid.addWidget(bar, row, 1)
            label = QLabel("UP: -- | DOWN: -- | DIR: -- | CONF: -- | TS: --"); self.labels[tf] = label; grid.addWidget(label, row, 2)
            health = QLabel("HEALTH: -- | LAT: -- | STALE: --"); self.health_labels[tf] = health; grid.addWidget(health, row, 3)

        self.telemetry = QLabel("SYSTEM TELEMETRY | API: -- | FREQ: -- | REFRESH: 0 | FAIL: 0 | AVG LAT: -- | UPTIME: -- | SYMBOL: -- | SOURCE: --")
        layout.addWidget(self.telemetry)
        self.log = QTextEdit(); self.log.setReadOnly(True); layout.addWidget(self.log)
        self.setCentralWidget(central)

        self.timer = QTimer(self); self.timer.setInterval(5000); self.timer.timeout.connect(self.fetch_update); self.timer.start(); self.fetch_update()

    def fetch_update(self) -> None:
        if self.worker is not None and self.worker.isRunning():
            return
        self.worker = Worker(self.collector, self.engine)
        self.worker.data_ready.connect(self.apply_result)
        self.worker.error.connect(self.log_error)
        self.worker.start()

    def apply_result(self, result: dict) -> None:
        self.total_refreshes += 1
        self.price_label.setText(f"Current Price: {result['current_price']:.2f}")
        latency_acc = 0.0
        for tf, data in result["timeframes"].items():
            score = int(data["score"]); self.bars[tf].setValue(score)
            self.bars[tf].setStyleSheet(f"QProgressBar::chunk {{ background-color: {'#1f8b4c' if score >= 51 else '#a32828'}; }}")
            self.labels[tf].setText(f"UP: {data['up']}% | DOWN: {data['down']}% | DIR: {data['direction']} | CONF: {data['confidence']}% | TS: {data['candle_timestamp']}")
            hs = data["health_status"]; latency_acc += float(data["latency_ms"])
            color = {"HEALTHY": "#1f8b4c", "DELAYED": "#e0a100", "STALE": "#d17b00", "ERROR": "#a32828"}.get(hs, "#808080")
            self.health_labels[tf].setStyleSheet(f"color: {color};")
            self.health_labels[tf].setText(f"HEALTH: {hs} | LAT: {data['latency_ms']}ms | STALE: {data['stale_seconds']}s")

        self.avg_latency_ms = ((self.avg_latency_ms * (self.total_refreshes - 1)) + (latency_acc / 4)) / self.total_refreshes
        uptime = datetime.utcnow() - self.start_time
        self.telemetry.setText(
            f"SYSTEM TELEMETRY | API: OK | FREQ: 5s | REFRESH: {self.total_refreshes} | FAIL: {self.failed_refreshes} | AVG LAT: {self.avg_latency_ms:.2f}ms | UPTIME: {str(uptime).split('.')[0]} | SYMBOL: {result['symbol']} | SOURCE: {result.get('source', '--')}"
        )
        self.log_message("INFO Updated successfully")

    def log_error(self, message: str) -> None:
        self.failed_refreshes += 1
        self.log_message(f"ERROR API/processing error: {message}")

    def log_message(self, message: str) -> None:
        if message == self.last_log_message:
            return
        self.last_log_message = message
        now = datetime.utcnow().isoformat(timespec="seconds")
        self.log.append(f"[{now}] {message}")
