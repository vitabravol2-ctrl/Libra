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
        self.setWindowTitle("BTCUSDT Tree Console v0.6.2")
        self.resize(1100, 760)
        self.pipeline = DecisionPipeline()
        self.settings = EntrySettings()
        self.log_dedup: deque[str] = deque(maxlen=40)
        self._last_state_key: str | None = None

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
        for node in ["MARKET REGIME", "LIQUIDITY EVENT", "CONFIRMATION", "ENTRY BLOCKED"]:
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
            "touch_lower_boundary": second % 4 == 2,
            "touch_upper_boundary": False,
            "bid_volume": 180.0,
            "ask_volume": 120.0,
            "aggressive_buys": 140.0,
            "aggressive_sells": 80.0,
            "micro_velocity": 0.75,
            "velocity_stability": 0.9,
            "spread": 1.0,
            "freshness_ms": 500,
            "ticks_in_profit": second % 4,
            "elapsed_sec": 12,
            "emergency": False,
            "structure_break": False,
        }
        result = self.pipeline.run(snapshot)
        regime = result.market_regime
        liq = result.liquidity_event

        self.regime_label.setText(f"{regime['regime'].value}")
        self.conf_label.setText(f"CONFIDENCE {regime['confidence']}%")
        self.direction_label.setText(f"SETUP SIDE {liq['setup_side']}")
        conf = result.confirmation
        self.state_label.setText(
            f"CONFIRMATION {conf['status'].value} {conf['score']}% | "
            f"IMB {conf['imbalance_score']} AGG {conf['aggressive_score']} "
            f"VEL {conf['velocity_score']} SPR {conf['spread_score']} FR {conf['freshness_score']}"
        )

        self._set_node("MARKET REGIME", regime["regime"].value)
        self._set_node("LIQUIDITY EVENT", self._liquidity_display(liq))
        self._set_node("CONFIRMATION", f"{conf['status'].value} {conf['score']}%")
        self._set_node("ENTRY BLOCKED", "BLOCKED / NOT_IMPLEMENTED")

        state_key = f"conf={conf['status'].value}|score={conf['score']}"
        if state_key != self._last_state_key:
            if conf["status"].value == "BLOCKED":
                self._add_log(f"confirmation blocked: {conf['reason']}")
            elif conf["status"].value == "READY":
                self._add_log(f"confirmation READY {conf['score']}%")
            else:
                self._add_log(f"confirmation -> {conf['status'].value} {conf['score']}%")
            self._last_state_key = state_key

    def _liquidity_display(self, liq: dict) -> str:
        if liq["status"] == "BLOCKED":
            return "BLOCKED"
        return liq["metrics"].get("wait", liq["event"].value)

    def _setup_display(self, liq: dict) -> str:
        if liq["status"] == "BLOCKED":
            return "NONE"
        return liq["metrics"].get("setup", "WAIT")

    def _set_node(self, node: str, state: str):
        color = "red" if "BLOCKED" in state else "green" if "SETUP" in state or "READY" in state else "gray"
        self.tree_nodes[node].setText(f"{node}: {state}")
        self.tree_nodes[node].setStyleSheet(f"color:{color};")

    def _add_log(self, line: str):
        if self.log_dedup and self.log_dedup[-1] == line:
            return
        self.log_dedup.append(line)
        self.log.setPlainText("\n".join(self.log_dedup))
