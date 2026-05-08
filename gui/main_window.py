"""Main PySide6 GUI window for BTCUSDT probability engine."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QThread, QTimer, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QLabel,
    QMainWindow,
    QProgressBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

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
            datapack = self.collector.collect()
            result = self.engine.evaluate(datapack)
            self.data_ready.emit(result)
        except Exception as exc:  # noqa: BLE001
            self.error.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("BTCUSDT Game Theory / Microtrend Probability Engine v0.1.0")
        self.resize(900, 650)

        self.collector = DataCollector()
        self.engine = ProbabilityEngine()
        self.worker: Worker | None = None

        self.bars: dict[str, QProgressBar] = {}
        self.labels: dict[str, QLabel] = {}

        central = QWidget()
        layout = QVBoxLayout(central)

        self.price_label = QLabel("Current Price: --")
        layout.addWidget(self.price_label)

        grid = QGridLayout()
        layout.addLayout(grid)

        for row, tf in enumerate(["DAY", "HOUR", "10 MIN", "1 MIN"]):
            grid.addWidget(QLabel(tf), row, 0)

            bar = QProgressBar()
            bar.setRange(1, 100)
            bar.setValue(50)
            bar.setFormat("%v")
            self.bars[tf] = bar
            grid.addWidget(bar, row, 1)

            label = QLabel("UP: -- | DOWN: -- | DIR: -- | CONF: -- | TS: --")
            self.labels[tf] = label
            grid.addWidget(label, row, 2)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)

        self.setCentralWidget(central)

        self.timer = QTimer(self)
        self.timer.setInterval(5000)
        self.timer.timeout.connect(self.fetch_update)
        self.timer.start()

        self.fetch_update()

    def fetch_update(self) -> None:
        if self.worker is not None and self.worker.isRunning():
            return
        self.worker = Worker(self.collector, self.engine)
        self.worker.data_ready.connect(self.apply_result)
        self.worker.error.connect(self.log_error)
        self.worker.start()

    def apply_result(self, result: dict) -> None:
        self.price_label.setText(f"Current Price: {result['current_price']:.2f}")
        for tf, data in result["timeframes"].items():
            score = int(data["score"])
            self.bars[tf].setValue(score)
            color = "#1f8b4c" if score >= 51 else "#a32828"
            self.bars[tf].setStyleSheet(
                f"QProgressBar::chunk {{ background-color: {color}; }}"
            )
            self.labels[tf].setText(
                f"UP: {data['up']}% | DOWN: {data['down']}% | DIR: {data['direction']} "
                f"| CONF: {data['confidence']}% | TS: {data['candle_timestamp']}"
            )

        self.log_message("Updated successfully")

    def log_error(self, message: str) -> None:
        self.log_message(f"API/processing error: {message}")

    def log_message(self, message: str) -> None:
        now = datetime.utcnow().isoformat(timespec="seconds")
        self.log.append(f"[{now}] {message}")
