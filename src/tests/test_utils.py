"""Tests for mdaviz.utils."""

from PyQt6.QtWidgets import QVBoxLayout, QWidget, QSpacerItem, QSizePolicy

from mdaviz import utils


def test_removeAllLayoutWidgets_skips_spacer(qtbot):
    """removeAllLayoutWidgets does not crash when layout contains a spacer (itemAt(i).widget() is None)."""
    parent = QWidget()
    qtbot.addWidget(parent)
    layout = QVBoxLayout(parent)
    widget = QWidget()
    layout.addWidget(widget)
    layout.addSpacerItem(
        QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
    )
    assert layout.count() == 2
    assert layout.itemAt(0).widget() is widget
    assert layout.itemAt(1).widget() is None  # spacer has no widget

    utils.removeAllLayoutWidgets(layout)
    # No crash; widget should have been removed (setParent(None))
    assert widget.parent() is None
    assert layout.count() == 1  # spacer item remains (we only remove widgets)
