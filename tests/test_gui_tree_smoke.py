import pytest

pytest.importorskip("PySide6")

try:
    from gui.main_window import MainWindow
except ImportError as exc:
    pytest.skip(f"GUI runtime deps unavailable: {exc}", allow_module_level=True)


def test_gui_window_builds(qapp):
    w = MainWindow()
    assert "v0.6.1" in w.windowTitle()
    assert "MARKET REGIME" in w.tree_nodes
