import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture(scope="session")
def qapp():
    qtwidgets = pytest.importorskip("PySide6.QtWidgets")
    QApplication = qtwidgets.QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app
