from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QFormLayout, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QProgressBar, QTextEdit, QVBoxLayout, QWidget

from core.decision_pipeline import DecisionPipeline


@dataclass
class EntrySettings:
    score_threshold: int = 70
    micro_threshold: int = 55
    max_spread: float = 2.5
    max_latency_ms: int = 1500
    paper_size: float = 0.02
    timeout_seconds: int = 30
    tp_mode: str = "adaptive"
    adaptive_tp: int = 1


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("BTCUSDT Tree Console v0.6.4")
        self.resize(1380, 880)
        self.pipeline = DecisionPipeline()
        self.settings = EntrySettings()
        self.log_dedup: deque[str] = deque(maxlen=60)
        self._last_state_key: str | None = None
        central = QWidget()
        root = QVBoxLayout(central)
        root.addWidget(self._build_top_bar())
        middle = QHBoxLayout()
        middle.addWidget(self._build_regime_panel(), 3)
        middle.addWidget(self._build_tree_panel(), 3)
        middle.addWidget(self._build_settings_panel(), 2)
        root.addLayout(middle)
        bottom = QHBoxLayout()
        bottom.addWidget(self._build_position_panel(), 2)
        bottom.addWidget(self._build_orderflow_panel(), 2)
        bottom.addWidget(self._build_logs_panel(), 3)
        root.addLayout(bottom)
        self.setCentralWidget(central)
        self.setStyleSheet("QWidget{background:#070b10;color:#dbe6f2;font-size:13px;}QGroupBox{border:1px solid #2b3d52;margin-top:10px;font-weight:600;}QLineEdit{background:#0f1620;border:1px solid #33495f;padding:3px;}QProgressBar{border:1px solid #233445;background:#10161f;}QProgressBar::chunk{background:#2ecc71;}")
        self.timer = QTimer(self)
        self.timer.setInterval(1500)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
        self.refresh()

    def _build_top_bar(self):
        box = QGroupBox("TOP BAR")
        h = QHBoxLayout(box)
        self.top_labels = {}
        for k in ["BTCUSDT", "WS", "SPREAD", "LAT", "FRESH", "PRICE", "REGIME", "CONF"]:
            lb = QLabel(f"{k}: --")
            self.top_labels[k] = lb
            h.addWidget(lb)
        return box

    def _build_regime_panel(self):
        box = QGroupBox("MARKET REGIME")
        v = QVBoxLayout(box)
        self.regime_label = QLabel("REGIME --")
        self.conf_label = QLabel("CONFIDENCE --")
        self.direction_label = QLabel("SETUP SIDE --")
        self.state_label = QLabel("STRUCTURE --")
        for w in [self.regime_label, self.conf_label, self.direction_label, self.state_label]:
            v.addWidget(w)
        return box

    def _build_tree_panel(self):
        box = QGroupBox("EXECUTION TREE")
        v = QVBoxLayout(box)
        self.tree_nodes = {}
        for node in ["MARKET REGIME", "LIQUIDITY EVENT", "CONFIRMATION", "MICROSTRUCTURE", "ENTRY GATE", "PAPER POSITION", "EXIT MANAGER"]:
            label = QLabel(f"{node}: WAIT")
            self.tree_nodes[node] = label
            v.addWidget(label)
        return box

    def _build_settings_panel(self):
        box = QGroupBox("ENTRY SETTINGS")
        form = QFormLayout(box)
        self.inputs = {}
        for k, t in [("score_threshold", "confirmation threshold"), ("micro_threshold", "micro threshold"), ("max_spread", "max spread"), ("max_latency_ms", "max latency"), ("paper_size", "paper size"), ("timeout_seconds", "timeout"), ("tp_mode", "tp mode"), ("adaptive_tp", "adaptive TP")]:
            le = QLineEdit(str(getattr(self.settings, k)))
            self.inputs[k] = le
            form.addRow(t, le)
        return box

    def _build_position_panel(self):
        box = QGroupBox("PAPER POSITION")
        g = QGridLayout(box)
        self.pos_labels = {}
        rows = ["STATE", "ENTRY", "PNL", "PNL_TICKS", "HOLD", "TP", "SL", "EXIT"]
        for r, key in enumerate(rows):
            g.addWidget(QLabel(key), r, 0)
            v = QLabel("--")
            self.pos_labels[key] = v
            g.addWidget(v, r, 1)
        return box

    def _build_orderflow_panel(self):
        box = QGroupBox("ORDERFLOW")
        v = QVBoxLayout(box)
        self.of_bars = {}
        for k in ["imbalance", "aggressive_buys", "aggressive_sells", "velocity", "spread_quality", "spoof_risk", "absorption", "exhaustion", "continuation", "vacuum", "decay", "pullback_quality"]:
            v.addWidget(QLabel(k))
            p = QProgressBar()
            p.setRange(0, 100)
            self.of_bars[k] = p
            v.addWidget(p)
        return box

    def _build_logs_panel(self):
        box = QGroupBox("MINI LOGS")
        v = QVBoxLayout(box)
        self.log = QTextEdit(); self.log.setReadOnly(True); v.addWidget(self.log)
        return box

    def refresh(self):
        second = datetime.utcnow().second
        price = 64000.0 + second
        snapshot = {
            "now_ts": int(datetime.utcnow().timestamp()), "price": price, "paper_size": float(self.inputs["paper_size"].text()),
            "score_threshold": int(float(self.inputs["score_threshold"].text())), "micro_threshold": int(float(self.inputs["micro_threshold"].text())), "timeout_seconds": int(float(self.inputs["timeout_seconds"].text())),
            "directional_pressure": 0.7 if second % 4 == 0 else -0.7 if second % 4 == 1 else 0.0, "higher_micro_highs": second % 4 == 0,
            "lower_micro_lows": second % 4 == 1, "range_width": 20 if second % 4 == 2 else 45, "trend_strength": 0.2 if second % 4 == 2 else 0.8,
            "volatility": 90 if second % 6 == 5 else 30, "sweep_low": second % 4 == 0, "reclaim": second % 4 == 0, "sweep_high": second % 4 == 1,
            "reject": second % 4 == 1, "touch_lower_boundary": second % 4 == 2, "touch_upper_boundary": False, "bid_volume": 180.0,
            "ask_volume": 120.0, "aggressive_buys": 140.0, "aggressive_sells": 80.0, "micro_velocity": 0.75 if second % 7 else 0.02,
            "velocity_stability": 0.9, "spread": 1.0 if second % 5 else 3.6, "freshness_ms": 500 if second % 8 else 2200,
            "structure_break": second % 11 == 0, "momentum": 0.7 if second % 7 else 0.01,
        }
        result = self.pipeline.run(snapshot)
        regime, liq, conf, micro, entry, pos, ex = result.market_regime, result.liquidity_event, result.confirmation, result.microstructure, result.entry, result.position, result.exit
        self.top_labels["BTCUSDT"].setText("BTCUSDT")
        self.top_labels["WS"].setText("WS: OK" if snapshot["freshness_ms"] < 1500 else "WS: STALE")
        self.top_labels["SPREAD"].setText(f"SPREAD: {snapshot['spread']:.2f}")
        self.top_labels["LAT"].setText(f"LAT: {snapshot['freshness_ms']}ms")
        self.top_labels["FRESH"].setText(f"FRESH: {snapshot['freshness_ms']}ms")
        self.top_labels["PRICE"].setText(f"PRICE: {price:.2f}")
        self.top_labels["REGIME"].setText(f"REGIME: {regime['regime'].value}")
        self.top_labels["CONF"].setText(f"CONF: {conf['score']}")
        self.regime_label.setText(regime["regime"].value); self.conf_label.setText(f"confidence {regime['confidence']}%")
        self.direction_label.setText(f"setup {liq['setup_side']}"); self.state_label.setText(f"pullback {liq['status']}")
        self._set_node("MARKET REGIME", regime["regime"].value)
        self._set_node("LIQUIDITY EVENT", liq["status"])
        self._set_node("CONFIRMATION", f"{conf['status'].value} {conf['score']}")
        self._set_node("MICROSTRUCTURE", f"{micro['state'].value} {micro['final_quality']}")
        self._set_node("ENTRY GATE", "READY" if entry["allowed"] else "BLOCKED")
        self._set_node("PAPER POSITION", pos["state"])
        self._set_node("EXIT MANAGER", ex["state"])
        self.pos_labels["STATE"].setText(f"{pos['side']} / {pos['state']}")
        self.pos_labels["ENTRY"].setText(f"{pos['entry_price']:.2f}")
        self.pos_labels["PNL"].setText(f"{pos['pnl']:.3f}")
        self.pos_labels["PNL_TICKS"].setText(str(pos["pnl_ticks"]))
        self.pos_labels["HOLD"].setText(f"{pos['hold_seconds']}s")
        self.pos_labels["TP"].setText(f"{pos['tp_price']:.2f}")
        self.pos_labels["SL"].setText(f"{pos['sl_price']:.2f}")
        self.pos_labels["EXIT"].setText(pos["exit_reason"] or "--")
        self.of_bars["imbalance"].setValue(min(100, conf["imbalance_score"] * 4))
        self.of_bars["aggressive_buys"].setValue(min(100, int(snapshot["aggressive_buys"] / 2)))
        self.of_bars["aggressive_sells"].setValue(min(100, int(snapshot["aggressive_sells"] / 2)))
        self.of_bars["velocity"].setValue(min(100, int(snapshot["micro_velocity"] * 100)))
        self.of_bars["spread_quality"].setValue(min(100, conf["spread_score"] * 10))
        self.of_bars["spoof_risk"].setValue(micro["spoof_score"])
        self.of_bars["absorption"].setValue(micro["absorption_score"])
        self.of_bars["exhaustion"].setValue(micro["exhaustion_score"])
        self.of_bars["continuation"].setValue(micro["continuation_score"])
        self.of_bars["vacuum"].setValue(micro["vacuum_score"])
        self.of_bars["decay"].setValue(micro["decay_score"])
        self.of_bars["pullback_quality"].setValue(micro["pullback_quality"])
        self._log_state(regime, liq, conf, micro, entry, pos, ex)

    def _set_node(self, node: str, state: str):
        color = "#e74c3c" if "BLOCKED" in state or state in {"EXITED", "CLOSED"} else "#2ecc71" if state in {"READY", "ACTIVE", "OPEN", "HOLD"} else "#95a5a6"
        self.tree_nodes[node].setText(f"{node}: {state}")
        self.tree_nodes[node].setStyleSheet(f"color:{color};font-weight:700;")

    def _log_state(self, regime: dict, liq: dict, conf: dict, micro: dict, entry: dict, pos: dict, ex: dict):
        messages = [f"regime={regime['regime'].value}", f"liq={liq['status']}/{liq['setup_side']}", f"confirmation={conf['status'].value}/{conf['score']}"]
        messages.append(f"micro={micro['state'].value}/{micro['final_quality']}")
        for m in ["spoof detected", "absorption detected", "continuation weak", "momentum decay", "high quality setup"]:
            if m in micro["reason"]: messages.append(m)
        if not entry["allowed"] and entry["reason"].startswith("blocked_micro"):
            messages.append("entry blocked by trap risk")
        if entry["allowed"]: messages.append("entry allowed")
        if pos["state"] == "OPEN": messages.append("paper position opened")
        if pos["exit_reason"]: messages.append(f"exit {pos['exit_reason']}")
        if ex["state"] == "EXITED": messages.append("exit manager exited")
        key = " | ".join(messages)
        if key == self._last_state_key: return
        self._last_state_key = key
        self.log_dedup.appendleft(f"{datetime.utcnow().strftime('%H:%M:%S')} {key}")
        self.log.setPlainText("\n".join(self.log_dedup))
