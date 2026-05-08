"""Main PySide6 GUI window for BTCUSDT probability engine."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QThread, QTimer, Signal
from PySide6.QtWidgets import QGridLayout, QLabel, QMainWindow, QProgressBar, QTextEdit, QVBoxLayout, QWidget, QGroupBox

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
        self.setWindowTitle("BTCUSDT Game Theory / Microtrend Probability Engine v0.3.1")
        self.resize(980, 700)
        self.collector = DataCollector(); self.engine = ProbabilityEngine(); self.worker: Worker | None = None
        self.bars: dict[str, QProgressBar] = {}
        self.labels: dict[str, QLabel] = {}
        self.health_labels: dict[str, QLabel] = {}
        self.factor_labels: dict[str, QLabel] = {}
        self.last_log_message = ""
        self.last_scores: dict[str, int] = {}
        self.last_context: dict[str, str] = {}
        self.last_strongest: dict[str, str] = {}
        self.start_time = datetime.utcnow()
        self.total_refreshes = 0
        self.failed_refreshes = 0
        self.avg_latency_ms = 0.0

        central = QWidget(); layout = QVBoxLayout(central)
        self.price_label = QLabel("Current Price: --"); layout.addWidget(self.price_label)

        grid = QGridLayout(); layout.addLayout(grid)
        for row, tf in enumerate(["WEEK", "DAY", "HOUR", "10 MIN", "1 MIN", "1 SEC"]):
            grid.addWidget(QLabel(tf), row, 0)
            bar = QProgressBar(); bar.setRange(1, 100); bar.setValue(50); bar.setFormat("%v"); self.bars[tf] = bar; grid.addWidget(bar, row, 1)
            label = QLabel("UP: -- | DOWN: -- | DIR: -- | CONF: -- | Q: -- | CTX: --"); self.labels[tf] = label; grid.addWidget(label, row, 2)
            health = QLabel("HEALTH: -- | LAT: -- | STALE: --"); self.health_labels[tf] = health; grid.addWidget(health, row, 3)


        factor_box = QGroupBox("DIRECTION FACTORS")
        factor_layout = QGridLayout(factor_box)
        for row, tf in enumerate(["WEEK", "DAY", "HOUR", "10 MIN", "1 MIN", "1 SEC"]):
            factor_layout.addWidget(QLabel(tf), row, 0)
            factor_label = QLabel("UP: -- | DOWN: -- | SCORE: -- | CTX: -- | PRESSURE: --")
            self.factor_labels[tf] = factor_label
            factor_layout.addWidget(factor_label, row, 1)
        layout.addWidget(factor_box)

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
            self.labels[tf].setText(f"UP: {data.get('up','--')}% | DOWN: {data.get('down','--')}% | DIR: {data.get('direction','--')} | CONF: {data.get('confidence','--')}% | Q: {data.get('quality_score','--')} | CTX: {data.get('context','--')}")
            hs = data["health_status"]; latency_acc += float(data["latency_ms"])
            color = {"HEALTHY": "#1f8b4c", "DELAYED": "#e0a100", "STALE": "#d17b00", "ERROR": "#a32828"}.get(hs, "#808080")
            self.health_labels[tf].setStyleSheet(f"color: {color};")
            self.health_labels[tf].setText('1 SEC: WAITING FOR WS / EXPERIMENTAL' if hs=='DISABLED' and tf=='1 SEC' else f"HEALTH: {hs} | LAT: {data.get('latency_ms','--')}ms | STALE: {data.get('stale_seconds','--')}s")
            factors = data.get("factors", [])
            up_factors = [f for f in factors if f["direction"] == "UP"]
            down_factors = [f for f in factors if f["direction"] == "DOWN"]
            strongest_up = max(up_factors, key=lambda x: x["contribution"], default={"name": "--", "contribution": 0})
            strongest_down = min(down_factors, key=lambda x: x["contribution"], default={"name": "--", "contribution": 0})
            micro = data.get("microstructure_context", {})
            self.factor_labels[tf].setText(f"UP: {strongest_up['name']} | DOWN: {strongest_down['name']} | SCORE: {data.get('factors_score','--')} | CTX: {micro.get('context_state','--')} | PRESSURE: {micro.get('pressure_side','--')}")
            sig = abs(self.last_scores.get(tf, score) - score) >= 7
            if sig:
                self.log_message(f"INFO score changed significantly {tf}: {self.last_scores.get(tf, score)} -> {score}")
            self.last_scores[tf] = score
            ctx = micro.get("context_state", "--")
            if self.last_context.get(tf) != ctx:
                self.log_message(f"INFO context change {tf}: {self.last_context.get(tf, '--')} -> {ctx}")
            self.last_context[tf] = ctx
            strongest = strongest_up['name'] if abs(strongest_up.get('contribution',0)) >= abs(strongest_down.get('contribution',0)) else strongest_down['name']
            if self.last_strongest.get(tf) != strongest:
                self.log_message(f"INFO strongest factor change {tf}: {self.last_strongest.get(tf, '--')} -> {strongest}")
            self.last_strongest[tf] = strongest
            for w in micro.get('warnings', []):
                self.log_message(f"WARN {tf} {w}")

        self.avg_latency_ms = ((self.avg_latency_ms * (self.total_refreshes - 1)) + (latency_acc / 6)) / self.total_refreshes
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
