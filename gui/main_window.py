from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QTextEdit, QVBoxLayout, QWidget

from core.decision_pipeline import DecisionPipeline


@dataclass
class EntrySettings:
    tp_ticks: int = 3
    sl_ticks: int = 2
    score_threshold: int = 70
    max_position: float = 0.02


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("BTCUSDT Tree Console v0.6.0")
        self.resize(1100, 760)
        self.pipeline = DecisionPipeline()
        self.settings = EntrySettings()
        self.log_dedup: deque[str] = deque(maxlen=40)

        central = QWidget()
        root = QVBoxLayout(central)

        top = QHBoxLayout()
        top.addWidget(self._build_regime_panel(), 2)
        top.addWidget(self._build_tree_panel(), 3)
        top.addWidget(self._build_settings_panel(), 2)
        root.addLayout(top)

        logs = QGroupBox("MINI LOGS")
        l = QVBoxLayout(logs)
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        l.addWidget(self.log)
        root.addWidget(logs)

        self.setCentralWidget(central)
        self.setStyleSheet("QWidget{background:#0b0f14;color:#dbe6f2;}QGroupBox{border:1px solid #233445;margin-top:10px;}QLineEdit{background:#111922;border:1px solid #33495f;}")

        self.timer = QTimer(self)
        self.timer.setInterval(2000)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
        self.refresh()

    def _build_regime_panel(self):
        box = QGroupBox("MARKET REGIME")
        v = QVBoxLayout(box)
        self.regime_label = QLabel("REGIME --")
        self.conf_label = QLabel("CONFIDENCE --")
        self.direction_label = QLabel("DIRECTION --")
        self.state_label = QLabel("STATE --")
        for w in [self.regime_label, self.conf_label, self.direction_label, self.state_label]:
            v.addWidget(w)
        return box

    def _build_tree_panel(self):
        box = QGroupBox("DECISION TREE")
        v = QVBoxLayout(box)
        self.tree_nodes = {}
        for node in ["MARKET REGIME", "LIQUIDITY EVENT", "CONFIRMATION", "ENTRY", "EXIT"]:
            label = QLabel(f"{node}: WAIT")
            self.tree_nodes[node] = label
            v.addWidget(label)
        return box

    def _build_settings_panel(self):
        box = QGroupBox("ENTRY SETTINGS")
        g = QGridLayout(box)
        self.inputs = {}
        for row, (k, t) in enumerate([("tp_ticks", "TP ticks"), ("sl_ticks", "SL ticks"), ("score_threshold", "Score threshold"), ("max_position", "Max position")]):
            g.addWidget(QLabel(t), row, 0)
            le = QLineEdit(str(getattr(self.settings, k)))
            self.inputs[k] = le
            g.addWidget(le, row, 1)
        return box

    def refresh(self):
        second = datetime.utcnow().second
        snapshot = {
            "directional_pressure": 0.7 if second % 4 == 0 else -0.7 if second % 4 == 1 else 0.0,
            "higher_micro_highs": second % 4 == 0,
            "lower_micro_lows": second % 4 == 1,
            "range_width": 20 if second % 4 == 2 else 45,
            "trend_strength": 0.2 if second % 4 == 2 else 0.8,
            "volatility": 90 if second % 4 == 3 else 30,
            "sweep_low": second % 4 == 0,
            "reclaim": second % 4 == 0,
            "sweep_high": second % 4 == 1,
            "reject": second % 4 == 1,
            "orderbook_imbalance": 0.9,
            "aggressive_trades": 0.8,
            "velocity": 0.7,
            "spread": 1.0,
            "freshness_ms": 500,
            "ticks_in_profit": second % 4,
            "elapsed_sec": 12,
            "emergency": False,
            "structure_break": False,
        }
        result = self.pipeline.run(snapshot)
        regime = result.market_regime
        self.regime_label.setText(f"{regime['regime'].value}")
        self.conf_label.setText(f"CONFIDENCE {regime['confidence']}%")
        direction = "LOOKING FOR LONG PULLBACK" if regime['regime'].value == 'TREND_UP' else "LOOKING FOR SHORT PULLBACK" if regime['regime'].value == 'TREND_DOWN' else "WAIT RANGE EDGE" if regime['regime'].value == 'RANGE' else "NO TRADE"
        self.direction_label.setText(direction)
        self.state_label.setText(f"STATE {result.entry['state']}")

        self._set_node("MARKET REGIME", "READY")
        self._set_node("LIQUIDITY EVENT", result.liquidity_event["state"])
        self._set_node("CONFIRMATION", result.confirmation["state"])
        self._set_node("ENTRY", result.entry["state"])
        self._set_node("EXIT", result.exit["state"])

        self._add_log(f"regime={regime['regime'].value} liq={result.liquidity_event['event'].value} entry={result.entry['state']} exit={result.exit['reason']}")

    def _set_node(self, node: str, state: str):
        color = {"ACTIVE": "yellow", "WAIT": "gray", "READY": "green", "BLOCKED": "red", "DONE": "green"}.get(state, "gray")
        self.tree_nodes[node].setText(f"{node}: {state}")
        self.tree_nodes[node].setStyleSheet(f"color:{color};")

    def _add_log(self, line: str):
        if self.log_dedup and self.log_dedup[-1] == line:
            return
        self.log_dedup.append(line)
        self.log.setPlainText("\n".join(self.log_dedup))
