from core.entry_gate import EntryGate


def test_entry_allowed_only_on_ready():
    d = EntryGate().evaluate("TREND_UP", "READY", "READY", 82, 1.0, 500, "LONG", 64000.0)
    assert d.allowed is True


def test_entry_blocked_on_chaos():
    d = EntryGate().evaluate("CHAOS", "READY", "READY", 85, 1.0, 500, "LONG", 64000.0)
    assert d.allowed is False


def test_entry_blocked_on_stale():
    d = EntryGate().evaluate("TREND_UP", "READY", "READY", 85, 1.0, 2500, "LONG", 64000.0)
    assert d.reason == "blocked_stale_data"


def test_entry_blocked_on_wide_spread():
    d = EntryGate().evaluate("TREND_UP", "READY", "READY", 85, 3.2, 500, "LONG", 64000.0)
    assert d.reason == "blocked_wide_spread"
