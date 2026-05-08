"""Main PySide6 GUI window for BTCUSDT probability engine."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime

from PySide6.QtCore import QThread, QTimer, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
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
        self.setWindowTitle("BTCUSDT Game Theory / Microtrend Probability Engine v0.4.2")
        self.resize(1280, 820)
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
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        root.addWidget(self._build_top_panel())

        cockpit = QGridLayout()
        cockpit.setHorizontalSpacing(10)
        cockpit.setVerticalSpacing(10)
        cockpit.addWidget(self._build_tg_gauge(), 0, 0)
        cockpit.addWidget(self._build_market_state_panel(), 0, 1)
        cockpit.addWidget(self._build_agreement_panel(), 0, 2)
        cockpit.addWidget(self._build_timeframes_panel(), 1, 0)
        cockpit.addWidget(self._build_reason_tape(), 1, 1)
        cockpit.addWidget(self._build_trade_control_panel(), 1, 2)
        cockpit.addWidget(self._build_settings_panel(), 0, 3, 2, 1)
        cockpit.setColumnStretch(0, 2)
        cockpit.setColumnStretch(1, 1)
        cockpit.setColumnStretch(2, 1)
        cockpit.setColumnStretch(3, 1)
        root.addLayout(cockpit)

        log_box = QGroupBox("COMPACT LOGS")
        log_box.setObjectName("Card")
        log_box.setMaximumHeight(140)
        log_layout = QVBoxLayout(log_box)
        self.log = QTextEdit()
        self.log.setObjectName("LogPane")
        self.log.setReadOnly(True)
        log_layout.addWidget(self.log)
        root.addWidget(log_box)

        self.setCentralWidget(central)
        self.setStyleSheet(self._cockpit_stylesheet())
        self._refresh_settings_fields()

        self.timer.start()
        self.fetch_update()

    def _cockpit_stylesheet(self) -> str:
        return """
        QMainWindow, QWidget { background-color: #0b0f14; color: #dbe6f2; font-size: 12px; }
        QGroupBox#Card { border: 1px solid #1f2d3c; border-radius: 8px; margin-top: 14px; background-color: #121922; }
        QGroupBox#Card::title { subcontrol-origin: margin; left: 8px; padding: 0 6px; color: #8da5bf; font-size: 12px; }
        QLabel[role='Heading'] { font-size: 14px; font-weight: 600; color: #b6c9dc; }
        QLabel#GaugeScore { font-size: 72px; font-weight: 700; qproperty-alignment: 'AlignCenter'; }
        QLabel#GaugeDecision { font-size: 28px; font-weight: 700; qproperty-alignment: 'AlignCenter'; }
        QLabel#GaugeMeta { font-size: 13px; color: #9fb2c4; qproperty-alignment: 'AlignCenter'; }
        QLabel[role='MetricLabel'] { color: #8da5bf; font-size: 11px; }
        QLabel[role='MetricValue'] { color: #dbe6f2; font-size: 12px; font-weight: 600; }
        QFrame#TimeframeCard { background: #172330; border: 1px solid #24384b; border-radius: 6px; }
        QLabel[role='TFName'] { font-weight: 700; font-size: 11px; color: #9fb2c4; }
        QLabel[role='TFValue'] { font-size: 16px; font-weight: 700; }
        QLabel[role='TFDir'] { font-size: 11px; color: #b6c9dc; }
        QLineEdit { background: #0f1720; border: 1px solid #26384d; border-radius: 4px; padding: 4px 6px; min-height: 22px; }
        QPushButton { background: #1f2f40; border: 1px solid #2a4258; border-radius: 4px; padding: 6px 8px; }
        QPushButton:hover { background: #28445d; }
        QTextEdit#LogPane { background: #0f1720; border: 1px solid #223447; }
        """

    def _build_top_panel(self) -> QGroupBox:
        box = QGroupBox("SYSTEM STATUS")
        box.setObjectName("Card")
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
        box = QGroupBox("GAME THEORY SCORE")
        box.setObjectName("Card")
        layout = QVBoxLayout(box)
        self.tg_state_label = QLabel("ENGINE READY")
        self.tg_state_label.setProperty("role", "Heading")

        self.tg_score_big = QLabel("50")
        self.tg_score_big.setObjectName("GaugeScore")
        self.tg_decision_big = QLabel("WAIT")
        self.tg_decision_big.setObjectName("GaugeDecision")
        self.tg_meta_line = QLabel("TREND_NEUTRAL · CONF 0% · EXEC NO")
        self.tg_meta_line.setObjectName("GaugeMeta")

        self.tg_decision_label = QLabel("GT Decision: WAIT")
        self.tg_decision_label.setProperty("role", "Heading")
        self.tg_regime = QLabel("REGIME: --")
        self.tg_dom = QLabel("DOMINANT: --")
        self.tg_conf = QLabel("CONF: 0%")
        self.tg_exec = QLabel("EXEC: NO")
        self.tg_risk = QLabel("RISK: --")
        self.tg_scenario = QLabel("SCENARIO: --")
        self.tg_agree = QLabel("AGREE: --")
        self.tg_conflict = QLabel("CONFLICT: --")
        for widget in [self.tg_regime, self.tg_dom, self.tg_conf, self.tg_exec, self.tg_risk, self.tg_scenario, self.tg_agree, self.tg_conflict]:
            widget.setObjectName("GaugeMeta")

        layout.addWidget(self.tg_state_label)
        layout.addStretch(1)
        layout.addWidget(self.tg_score_big)
        layout.addWidget(self.tg_decision_big)
        layout.addWidget(self.tg_meta_line)
        layout.addStretch(1)
        layout.addWidget(self.tg_decision_label)
        for widget in [self.tg_regime, self.tg_dom, self.tg_conf, self.tg_exec, self.tg_risk, self.tg_scenario, self.tg_agree, self.tg_conflict]:
            layout.addWidget(widget)
        return box

    def _build_market_state_panel(self) -> QGroupBox:
        box = QGroupBox("MARKET STATE")
        box.setObjectName("Card")
        layout = QVBoxLayout(box)
        self.market_mode = QLabel("Market Mode: --")
        self.strongest_reason = QLabel("Strongest: --")
        self.blocked_reason = QLabel("Blocked: --")
        self.trap_risk = QLabel("Trap Risk: --")
        self.pullback_state = QLabel("Pullback State: --")
        self.entry_window = QLabel("Entry Window: CLOSED")
        for w in [self.market_mode, self.strongest_reason, self.blocked_reason, self.trap_risk, self.pullback_state, self.entry_window]:
            layout.addWidget(w)
        return box

    def _build_agreement_panel(self) -> QGroupBox:
        box = QGroupBox("TIMEFRAME AGREEMENT")
        box.setObjectName("Card")
        layout = QVBoxLayout(box)
        self.agreement_score_label = QLabel("Agreement: --")
        self.conflict_score_label = QLabel("Conflict: --")
        self.active_tfs_label = QLabel("Active TFs: --")
        self.disabled_tfs_label = QLabel("Disabled TFs: --")
        for w in [self.agreement_score_label, self.conflict_score_label, self.active_tfs_label, self.disabled_tfs_label]:
            layout.addWidget(w)
        return box

    def _build_reason_tape(self) -> QGroupBox:
        box = QGroupBox("GT REASONS")
        box.setObjectName("Card")
        layout = QVBoxLayout(box)
        self.reason_tape = QLabel("--")
        self.reason_tape.setWordWrap(True)
        layout.addWidget(self.reason_tape)
        return box

    def _build_timeframes_panel(self) -> QGroupBox:
        box = QGroupBox("TIMEFRAMES")
        box.setObjectName("Card")
        grid = QGridLayout(box)
        self.tf_compact_labels = {}
        for idx, tf in enumerate(TIMEFRAME_ORDER):
            card = QFrame()
            card.setObjectName("TimeframeCard")
            card_layout = QVBoxLayout(card)
            name = QLabel(tf)
            name.setProperty("role", "TFName")
            val = QLabel("--")
            val.setProperty("role", "TFValue")
            direct = QLabel("NO_DATA")
            direct.setProperty("role", "TFDir")
            ctx = QLabel("Q-- / --")
            ctx.setProperty("role", "TFDir")
            card_layout.addWidget(name)
            card_layout.addWidget(val)
            card_layout.addWidget(direct)
            card_layout.addWidget(ctx)
            self.tf_compact_labels[tf] = {"value": val, "dir": direct, "ctx": ctx}
            grid.addWidget(card, idx // 2, idx % 2)
        return box

    def _build_settings_panel(self) -> QGroupBox:
        box = QGroupBox("TRADING SETTINGS")
        box.setObjectName("Card")
        grid = QGridLayout(box)
        self.settings_inputs = {}
        fields = [
            ("long_threshold", "Long threshold"), ("short_threshold", "Short threshold"),
            ("tp_ticks", "TP ticks"), ("sl_ticks", "SL ticks"), ("grid_step", "Grid step"),
            ("max_position", "Max position"), ("risk_per_cycle", "Risk"),
        ]
        for row, (key, text) in enumerate(fields):
            grid.addWidget(QLabel(text), row, 0)
            inp = QLineEdit()
            self.settings_inputs[key] = inp
            grid.addWidget(inp, row, 1)
        apply_btn = QPushButton("Apply")
        reset_btn = QPushButton("Reset")
        save_btn = QPushButton("Save")
        apply_btn.clicked.connect(self.apply_settings)
        reset_btn.clicked.connect(self.reset_settings)
        save_btn.clicked.connect(self.save_profile)
        grid.addWidget(apply_btn, len(fields), 0)
        grid.addWidget(reset_btn, len(fields), 1)
        grid.addWidget(save_btn, len(fields) + 1, 0, 1, 2)
        return box

    def _build_trade_control_panel(self) -> QGroupBox:
        box = QGroupBox("TRADE CONTROL")
        box.setObjectName("Card")
        layout = QVBoxLayout(box)
        self.trade_decision = QLabel("Decision: WAIT")
        self.position_state = QLabel("Position: FLAT")
        self.paper_mode = QLabel("Paper: OFF")
        self.last_signal = QLabel("Last signal: --")
        self.last_reason = QLabel("Last reason: --")
        self.tactical_head = QLabel("TACTICAL ENTRY: WAIT")
        self.tactical_window = QLabel("ENTRY WINDOW: CLOSED")
        self.tactical_meta = QLabel("MACRO -- | PULLBACK -- | MICRO --")
        self.tactical_score = QLabel("TACTICAL SCORE: -- | TP -- | SL --")
        self.paper_tape = QLabel("PAPER TRADE TAPE: --")
        for w in [
            self.trade_decision,
            self.position_state,
            self.paper_mode,
            self.last_signal,
            self.last_reason,
            self.tactical_head,
            self.tactical_window,
            self.tactical_meta,
            self.tactical_score,
            self.paper_tape,
        ]:
            layout.addWidget(w)
        buttons = QHBoxLayout()
        arm = QPushButton("Arm")
        disarm = QPushButton("Disarm")
        estop = QPushButton("Emergency Stop")
        arm.clicked.connect(lambda: self._set_paper_mode(True))
        disarm.clicked.connect(lambda: self._set_paper_mode(False))
        estop.clicked.connect(self._emergency_stop)
        buttons.addWidget(arm)
        buttons.addWidget(disarm)
        buttons.addWidget(estop)
        layout.addLayout(buttons)
        return box

    def _set_paper_mode(self, enabled: bool) -> None:
        self.paper_mode_ready = enabled
        self.paper_mode.setText(f"Paper: {'READY' if enabled else 'OFF'}")

    def _emergency_stop(self) -> None:
        self._set_paper_mode(False)
        self.trade_decision.setText("Decision: WAIT")
        self.last_reason.setText("Last reason: Emergency stop activated")

    def _refresh_settings_fields(self) -> None:
        for key, widget in self.settings_inputs.items():
            widget.setText(str(getattr(self.settings, key)))

    def apply_settings(self) -> None:
        self.settings = TradingSettings(
            mode=self.settings.mode,
            long_threshold=int(self.settings_inputs["long_threshold"].text() or 55),
            short_threshold=int(self.settings_inputs["short_threshold"].text() or 45),
            tp_ticks=int(self.settings_inputs["tp_ticks"].text() or 80),
            sl_ticks=int(self.settings_inputs["sl_ticks"].text() or 40),
            grid_step=int(self.settings_inputs["grid_step"].text() or 15),
            max_position=float(self.settings_inputs["max_position"].text() or 0.02),
            leverage_placeholder=self.settings.leverage_placeholder,
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
            hs = data.get("health_status", "NO_DATA")
            score = data.get("score")
            if tf == "1 SEC" and hs in {"DISABLED", "WAITING_FOR_WS"}:
                value, direction, color = "--", "WAITING_WS", "#7c8796"
            elif hs in {"ERROR", "STALE", "DELAYED"}:
                value, direction, color = "--", hs, "#7c8796"
            elif score is None:
                value, direction, color = "--", "NO_DATA", "#7c8796"
            else:
                score = int(score)
                value = f"{score}%"
                direction = "LONG" if score >= 51 else "SHORT" if score <= 49 else "WAIT"
                color = "#1f8b4c" if direction == "LONG" else "#a32828" if direction == "SHORT" else "#7c8796"
                tg_scores.append(score)
            self.tf_compact_labels[tf]["value"].setText(value)
            self.tf_compact_labels[tf]["value"].setStyleSheet(f"color: {color};")
            self.tf_compact_labels[tf]["dir"].setText(direction)
            quality = data.get("quality_status", "Q--")
            context = data.get("context_label", data.get("market_context", "--"))
            self.tf_compact_labels[tf]["ctx"].setText(f"{quality} / {context}")
            lat = data.get("latency_ms")
            if lat is not None:
                latency_acc += float(lat)
                latency_count += 1

        gt = result.get("game_theory", {})
        gt_score = int(gt.get("global_score", max(1, min(100, int(sum(tg_scores) / len(tg_scores))) if tg_scores else 50)))
        decision = gt.get("decision", "WAIT")
        regime = gt.get("market_regime", "UNKNOWN")
        confidence = int(gt.get("confidence", 0))
        execution_ready = bool(gt.get("execution_ready", False))
        dominant_side = gt.get("dominant_side", "MIXED")
        risk_level = gt.get("risk_level", "UNKNOWN")
        scenario = gt.get("scenario_type", "--")
        agreement = int(gt.get("agreement_score", 0))
        conflict = int(gt.get("conflict_score", 0))
        blocked_reasons = gt.get("blocked_reasons", [])
        explanations = gt.get("explanations", [])
        reasons = ", ".join(gt.get("strongest_reasons", [])[:2]) or "--"
        entry_open = execution_ready and decision in {"LONG", "SHORT"} and confidence >= 60

        self.tg_state_label.setText("GAME THEORY ENGINE LIVE")
        self.tg_score_big.setText(str(gt_score))
        self.tg_decision_big.setText(decision)
        color = "#1f8b4c" if decision == "LONG" else "#a32828" if decision == "SHORT" else "#7c8796"
        self.tg_score_big.setStyleSheet(f"color: {color};")
        self.tg_decision_big.setStyleSheet(f"color: {color};")
        self.tg_meta_line.setText(f"{regime} · CONF {confidence}% · EXEC {'YES' if execution_ready else 'NO'}")
        self.tg_decision_label.setText(f"GT Decision: {decision}")
        self.tg_regime.setText(f"REGIME: {regime}")
        self.tg_dom.setText(f"DOMINANT: {dominant_side}")
        self.tg_conf.setText(f"CONF: {confidence}%")
        self.tg_exec.setText(f"EXEC: {'READY' if execution_ready else 'BLOCKED'}")
        self.tg_exec.setStyleSheet(f"color: {'#1f8b4c' if execution_ready else '#c2672a'};")
        self.tg_risk.setText(f"RISK: {risk_level}")
        risk_color = "#1f8b4c" if risk_level == "LOW" else "#c2672a" if risk_level in {"HIGH", "EXTREME"} else "#dbe6f2"
        self.tg_risk.setStyleSheet(f"color: {risk_color};")
        self.tg_scenario.setText(f"SCENARIO: {scenario}")
        self.tg_agree.setText(f"AGREE: {agreement}")
        self.tg_conflict.setText(f"CONFLICT: {conflict}")
        self.market_mode.setText(f"Market Mode: {regime}")
        strongest = gt.get("strongest_reasons", [])
        self.strongest_reason.setText(f"Strongest: {(strongest[0] if strongest else '--')}")
        self.blocked_reason.setText(f"Blocked: {(blocked_reasons[0] if blocked_reasons else '--')}")
        self.trap_risk.setText(f"Trap Risk: {gt.get('trap_risk', risk_level)}")
        self.pullback_state.setText(f"Pullback State: {gt.get('pullback_state', '--')}")
        self.entry_window.setText(f"Entry Window: {'OPEN' if entry_open else 'CLOSED'}")
        self.entry_window.setStyleSheet(f"color: {'#1f8b4c' if entry_open else '#7c8796'};")
        self.agreement_score_label.setText(f"Agreement: {agreement}")
        self.conflict_score_label.setText(f"Conflict: {conflict}")
        self.active_tfs_label.setText(f"Active TFs: {', '.join(gt.get('active_timeframes', [])) or '--'}")
        self.disabled_tfs_label.setText(f"Disabled TFs: {', '.join(gt.get('disabled_timeframes', [])) or '--'}")
        tape_items = [*gt.get("strongest_reasons", [])[:3], *[f"BLOCK:{b}" for b in blocked_reasons[:2]], *explanations[:2]]
        self.reason_tape.setText(" | ".join(tape_items[:5]) or "--")
        self.trade_decision.setText(f"Decision: {decision}")
        self.last_signal.setText(f"Last signal: GT {gt_score} ({dominant_side})")
        self.last_reason.setText(f"Last reason: {reasons}")
        tactical = result.get("tactical_entry", {})
        t_side = tactical.get("side", "WAIT")
        t_window = "OPEN" if tactical.get("entry_window_open") else "CLOSED"
        self.tactical_head.setText(f"TACTICAL ENTRY: {t_side}")
        self.tactical_window.setText(f"ENTRY WINDOW: {t_window}")
        self.tactical_meta.setText(
            f"MACRO {tactical.get('macro_direction', '--')} | PULLBACK {tactical.get('pullback_state', '--')} | MICRO {tactical.get('micro_trigger', '--')}"
        )
        self.tactical_score.setText(
            f"TACTICAL SCORE: {tactical.get('tactical_score', '--')} | TP +{tactical.get('target_ticks', 0)} | SL -{tactical.get('stop_ticks', 0)}"
        )
        self.paper_tape.setText(
            f"PAPER TRADE TAPE: side={t_side} ts={result.get('timestamp', '--')} tp={tactical.get('target_ticks', 0)} conf={tactical.get('confidence', '--')}"
        )

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
