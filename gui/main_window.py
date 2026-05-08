"""Main PySide6 GUI window for BTCUSDT probability engine."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime

from PySide6.QtCore import QThread, QTimer, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QProgressBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.data_collector import DataCollector
from core.log_deduplicator import LogDeduplicator
from core.probability_engine import ProbabilityEngine

TIMEFRAME_ORDER = ["WEEK", "DAY", "HOUR", "10 MIN", "1 MIN", "1 SEC"]


@dataclass
class TradingSettings:
    mode: str = "PAPER ONLY"
    long_threshold: int = 55
    short_threshold: int = 45
    tp_ticks: int = 80
    sl_ticks: int = 40
    grid_step: int = 15
    max_position: float = 0.02
    leverage_placeholder: int = 1
    risk_per_cycle: float = 0.5


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


def compact_timeframe_text(tf: str, data: dict) -> str:
    hs = data.get("health_status", "--")
    score = data.get("score")
    if tf == "1 SEC" and hs in {"DISABLED", "WAITING_FOR_WS"}:
        return f"{tf:<6} ● GREY WAITING_WS"
    if hs in {"ERROR", "STALE", "DELAYED"}:
        return f"{tf:<6} ● GREY {hs}"
    if score is None:
        return f"{tf:<6} ● GREY NO_DATA"
    score = int(score)
    side = "GREEN" if score >= 51 else "RED" if score <= 49 else "GREY"
    return f"{tf:<6} ● {side} {score}%"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("BTCUSDT Game Theory / Microtrend Probability Engine v0.3.3")
        self.resize(1100, 760)
        self.collector = DataCollector()
        self.engine = ProbabilityEngine()
        self.worker: Worker | None = None
        self.log_lines: deque[str] = deque(maxlen=20)
        self.last_log_message = ""
        self.last_scores: dict[str, int] = {}
        self.start_time = datetime.utcnow()
        self.log_dedup = LogDeduplicator()
        self.total_refreshes = 0
        self.failed_refreshes = 0
        self.avg_latency_ms = 0.0
        self.paper_mode_ready = False
        self.settings = TradingSettings()
        self.timer = QTimer(self)
        self.timer.setInterval(5000)
        self.timer.timeout.connect(self.fetch_update)

        central = QWidget()
        root = QVBoxLayout(central)

        top = self._build_top_panel()
        root.addWidget(top)

        middle = QHBoxLayout()
        middle.addWidget(self._build_tg_gauge(), 2)
        middle.addWidget(self._build_timeframes_panel(), 1)
        root.addLayout(middle)

        bottom = QHBoxLayout()
        bottom.addWidget(self._build_settings_panel(), 2)
        bottom.addWidget(self._build_trade_control_panel(), 1)
        root.addLayout(bottom)

        log_box = QGroupBox("COMPACT LOGS")
        log_layout = QVBoxLayout(log_box)
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        log_layout.addWidget(self.log)
        root.addWidget(log_box)

        self.setCentralWidget(central)
        self._refresh_settings_fields()

        self.timer.start()
        self.fetch_update()

    def _build_top_panel(self) -> QGroupBox:
        box = QGroupBox("TOP PANEL")
        grid = QGridLayout(box)
        self.price_label = QLabel("Current Price: --")
        self.api_status = QLabel("API status: --")
        self.update_status = QLabel("Update status: --")
        self.system_health = QLabel("System health: --")
        self.start_btn = QPushButton("Start")
        self.pause_btn = QPushButton("Pause")
        self.refresh_btn = QPushButton("Refresh")
        self.start_btn.clicked.connect(self.timer.start)
        self.pause_btn.clicked.connect(self.timer.stop)
        self.refresh_btn.clicked.connect(self.fetch_update)
        for i, w in enumerate([self.price_label, self.api_status, self.update_status, self.system_health]):
            grid.addWidget(w, 0, i)
        for i, w in enumerate([self.start_btn, self.pause_btn, self.refresh_btn]):
            grid.addWidget(w, 1, i)
        return box

    def _build_tg_gauge(self) -> QGroupBox:
        box = QGroupBox("CENTER PANEL — MAIN TG GAUGE")
        layout = QVBoxLayout(box)
        self.tg_state_label = QLabel("TG ENGINE: PREPARED / NOT ACTIVE")
        self.tg_gauge = QProgressBar()
        self.tg_gauge.setRange(1, 100)
        self.tg_gauge.setValue(50)
        self.tg_gauge.setFormat("TG SCORE %v")
        self.tg_decision_label = QLabel("TG Decision: WAIT")
        layout.addWidget(self.tg_state_label)
        layout.addWidget(self.tg_gauge)
        layout.addWidget(self.tg_decision_label)
        return box

    def _build_timeframes_panel(self) -> QGroupBox:
        box = QGroupBox("COMPACT TIMEFRAMES")
        layout = QVBoxLayout(box)
        self.tf_compact_labels = {}
        for tf in TIMEFRAME_ORDER:
            lbl = QLabel(f"{tf:<6} ● GREY NO_DATA")
            self.tf_compact_labels[tf] = lbl
            layout.addWidget(lbl)
        return box

    def _build_settings_panel(self) -> QGroupBox:
        box = QGroupBox("SCALPING / GRID SETTINGS")
        grid = QGridLayout(box)
        self.settings_inputs = {}
        fields = [
            ("mode", "Mode"), ("long_threshold", "Long threshold"), ("short_threshold", "Short threshold"),
            ("tp_ticks", "TP ticks"), ("sl_ticks", "SL ticks"), ("grid_step", "Grid step"),
            ("max_position", "Max position"), ("leverage_placeholder", "Leverage placeholder"), ("risk_per_cycle", "Risk per cycle"),
        ]
        for row, (key, text) in enumerate(fields):
            grid.addWidget(QLabel(text), row, 0)
            inp = QLineEdit()
            self.settings_inputs[key] = inp
            grid.addWidget(inp, row, 1)
        apply_btn = QPushButton("Apply Settings")
        reset_btn = QPushButton("Reset")
        save_btn = QPushButton("Save Profile")
        apply_btn.clicked.connect(self.apply_settings)
        reset_btn.clicked.connect(self.reset_settings)
        save_btn.clicked.connect(self.save_profile)
        grid.addWidget(apply_btn, len(fields), 0)
        grid.addWidget(reset_btn, len(fields), 1)
        grid.addWidget(save_btn, len(fields) + 1, 0)
        return box

    def _build_trade_control_panel(self) -> QGroupBox:
        box = QGroupBox("TRADE CONTROL")
        layout = QVBoxLayout(box)
        self.trade_decision = QLabel("TG Decision: WAIT")
        self.position_state = QLabel("Position State: FLAT")
        self.paper_mode = QLabel("Paper Mode: OFF")
        self.last_signal = QLabel("Last Signal: --")
        self.last_reason = QLabel("Last Reason: --")
        for w in [self.trade_decision, self.position_state, self.paper_mode, self.last_signal, self.last_reason]:
            layout.addWidget(w)
        arm = QPushButton("Arm Paper Mode")
        disarm = QPushButton("Disarm")
        estop = QPushButton("Emergency Stop")
        arm.clicked.connect(lambda: self._set_paper_mode(True))
        disarm.clicked.connect(lambda: self._set_paper_mode(False))
        estop.clicked.connect(self._emergency_stop)
        layout.addWidget(arm)
        layout.addWidget(disarm)
        layout.addWidget(estop)
        return box

    def _set_paper_mode(self, enabled: bool) -> None:
        self.paper_mode_ready = enabled
        self.paper_mode.setText(f"Paper Mode: {'READY' if enabled else 'OFF'}")

    def _emergency_stop(self) -> None:
        self._set_paper_mode(False)
        self.trade_decision.setText("TG Decision: WAIT")
        self.last_reason.setText("Last Reason: Emergency stop activated")

    def _refresh_settings_fields(self) -> None:
        for key, widget in self.settings_inputs.items():
            widget.setText(str(getattr(self.settings, key)))

    def apply_settings(self) -> None:
        self.settings = TradingSettings(
            mode=self.settings_inputs["mode"].text() or "PAPER ONLY",
            long_threshold=int(self.settings_inputs["long_threshold"].text() or 55),
            short_threshold=int(self.settings_inputs["short_threshold"].text() or 45),
            tp_ticks=int(self.settings_inputs["tp_ticks"].text() or 80),
            sl_ticks=int(self.settings_inputs["sl_ticks"].text() or 40),
            grid_step=int(self.settings_inputs["grid_step"].text() or 15),
            max_position=float(self.settings_inputs["max_position"].text() or 0.02),
            leverage_placeholder=int(self.settings_inputs["leverage_placeholder"].text() or 1),
            risk_per_cycle=float(self.settings_inputs["risk_per_cycle"].text() or 0.5),
        )
        self.log_message("INFO Settings applied locally (paper placeholder)")

    def reset_settings(self) -> None:
        self.settings = TradingSettings()
        self._refresh_settings_fields()
        self.log_message("INFO Settings reset to defaults")

    def save_profile(self) -> None:
        self.log_message("INFO Profile saved in-memory (placeholder)")

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
        self.api_status.setText("API status: OK")
        self.update_status.setText(f"Update status: refresh #{self.total_refreshes}")
        latency_acc = 0.0
        latency_count = 0
        tg_scores = []

        for tf in TIMEFRAME_ORDER:
            data = result["timeframes"].get(tf, {})
            self.tf_compact_labels[tf].setText(compact_timeframe_text(tf, data))
            score = data.get("score")
            if isinstance(score, (int, float)):
                tg_scores.append(int(score))
            lat = data.get("latency_ms")
            if lat is not None:
                latency_acc += float(lat)
                latency_count += 1

        if tg_scores:
            tg_score = max(1, min(100, int(sum(tg_scores) / len(tg_scores))))
            self.tg_state_label.setText("TG ENGINE: PREPARED")
            self.tg_gauge.setValue(tg_score)
            color = "#1f8b4c" if tg_score >= 51 else "#a32828" if tg_score <= 49 else "#7c7c7c"
            self.tg_gauge.setStyleSheet(f"QProgressBar::chunk {{ background-color: {color}; }}")
            decision = "LONG" if tg_score >= self.settings.long_threshold else "SHORT" if tg_score <= self.settings.short_threshold else "WAIT"
            self.tg_decision_label.setText(f"TG Decision: {decision}")
            self.trade_decision.setText(f"TG Decision: {decision}")
            self.last_signal.setText(f"Last Signal: TG {tg_score}")
            self.last_reason.setText("Last Reason: Global score placeholder from MTF state")
        else:
            self.tg_state_label.setText("TG ENGINE: PREPARED / NOT ACTIVE")

        avg_refresh_latency = (latency_acc / latency_count) if latency_count else 0.0
        self.avg_latency_ms = ((self.avg_latency_ms * (self.total_refreshes - 1)) + avg_refresh_latency) / self.total_refreshes
        uptime = datetime.utcnow() - self.start_time
        self.system_health.setText(f"System health: FAIL {self.failed_refreshes} | LAT {self.avg_latency_ms:.1f}ms | UPTIME {str(uptime).split('.')[0]}")

    def log_error(self, message: str) -> None:
        self.failed_refreshes += 1
        self.update_status.setText("Update status: ERROR")
        self.log_message(f"ERROR API/processing error: {message}")

    def log_message(self, message: str) -> None:
        if message == self.last_log_message:
            return
        self.last_log_message = message
        now = datetime.utcnow().isoformat(timespec="seconds")
        if message.startswith("WARN"):
            key = "WARN_GROUP"
            if self.log_dedup.should_emit(key, 15):
                self.log_lines.append(f"[{now}] WARN grouped warnings active")
        else:
            self.log_lines.append(f"[{now}] {message}")
        self.log.setPlainText("\n".join(self.log_lines))
        self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())
