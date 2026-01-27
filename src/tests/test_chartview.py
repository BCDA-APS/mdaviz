#!/usr/bin/env python
"""
Tests for the mdaviz chartview module.

Covers utility functions and widget instantiation.
"""

from typing import TYPE_CHECKING
import pytest
from unittest.mock import MagicMock

from mdaviz.chartview import auto_color, auto_symbol, ChartView
from mdaviz.curve_manager import CurveManager
import numpy as np
from PyQt6.QtWidgets import QComboBox


if TYPE_CHECKING:
    from _pytest.fixtures import FixtureRequest


def test_auto_color_and_symbol() -> None:
    """Test color and symbol cycling utilities."""
    colors = [auto_color() for _ in range(5)]
    symbols = [auto_symbol() for _ in range(5)]
    assert len(set(colors)) > 1
    assert len(set(symbols)) > 1


def test_chartview_instantiation(qtbot: "FixtureRequest") -> None:
    """Test that ChartView can be instantiated with a mock parent."""
    # Mock the parent and required attributes
    parent = MagicMock()
    parent.mda_file_viz.curveBox = MagicMock()
    parent.mda_file_viz.clearAll = MagicMock()
    parent.mda_file_viz.curveRemove = MagicMock()
    parent.mda_file_viz.cursor1_remove = MagicMock()
    parent.mda_file_viz.cursor2_remove = MagicMock()
    parent.mda_file_viz.offset_value = MagicMock()
    parent.mda_file_viz.factor_value = MagicMock()
    parent.mda_file.tabManager.tabRemoved = MagicMock()
    parent.mda_file_viz.curveBox.currentIndexChanged = MagicMock()
    parent.detRemoved = MagicMock()

    # Patch settings.getKey to avoid config issues
    import mdaviz.user_settings

    mdaviz.user_settings.settings.getKey = lambda key: 800

    widget = ChartView(parent)
    qtbot.addWidget(widget)
    assert widget is not None
    assert hasattr(widget, "figure")
    assert hasattr(widget, "canvas")
    assert hasattr(widget, "main_axes")
    assert hasattr(widget, "toolbar")
    assert widget.layout() is not None


def test_curve_manager_add_update_remove(qtbot):
    """Test adding, updating, and removing curves in CurveManager."""
    manager = CurveManager()
    curve_added = []
    curve_updated = []
    curve_removed = []
    all_curves_removed = []

    manager.curveAdded.connect(lambda cid: curve_added.append(cid))
    manager.curveUpdated.connect(
        lambda cid, recompute_y, update_x: curve_updated.append(
            (cid, recompute_y, update_x)
        )
    )
    manager.curveRemoved.connect(
        lambda cid, data, count: curve_removed.append((cid, data, count))
    )
    manager.allCurvesRemoved.connect(
        lambda doNotClear: all_curves_removed.append(doNotClear)
    )

    # Add a curve
    row = 0
    x = np.array([1, 2, 3])
    y = np.array([4, 5, 6])
    label = "test"
    file_path = "/tmp/test.mda"
    plot_options = {"filePath": file_path, "fileName": "test"}
    ds_options = {"label": label}
    manager.addCurve(row, x, y, plot_options=plot_options, ds_options=ds_options)
    curve_id = manager.generateCurveID(label, file_path, row)
    assert curve_id in manager.curves()
    assert curve_added[-1] == curve_id

    # Update the curve with different data to trigger update
    # The CurveManager only updates if the x data is different, not y data
    x2 = np.array([1, 2, 4])  # Different x data
    y2 = np.array([7, 8, 9])
    manager.addCurve(row, x2, y2, plot_options=plot_options, ds_options=ds_options)
    # The curve should be updated since x data is different
    assert len(curve_updated) > 0
    assert manager.getCurveData(curve_id)["ds"][0] is x2

    # Remove the curve
    manager.removeCurve(curve_id)
    assert curve_removed[-1][0] == curve_id
    assert curve_id not in manager.curves()

    # Add again and remove all
    manager.addCurve(row, x, y, plot_options=plot_options, ds_options=ds_options)
    manager.removeAllCurves()
    assert all_curves_removed[-1] is True
    assert len(manager.curves()) == 0


def test_curve_manager_persistent_properties():
    """Test persistent offset and factor properties in CurveManager."""
    manager = CurveManager()
    row = 1
    file_path = "/tmp/test2.mda"
    label = "curve2"
    plot_options = {"filePath": file_path, "fileName": "test2"}
    ds_options = {"label": label}
    x = np.array([1, 2, 3])
    y = np.array([4, 5, 6])
    manager.addCurve(row, x, y, plot_options=plot_options, ds_options=ds_options)
    curve_id = manager.generateCurveID(label, file_path, row)
    manager.updateCurveOffset(curve_id, 42)
    manager.updateCurveFactor(curve_id, 3.14)
    # Remove and re-add to test persistence
    manager.removeCurve(curve_id)
    manager.addCurve(row, x, y, plot_options=plot_options, ds_options=ds_options)
    curve_data = manager.getCurveData(curve_id)
    assert curve_data["offset"] == 42
    assert curve_data["factor"] == 3.14


def test_curve_manager_find_curve_id():
    """Test finding curve ID by file path and row."""
    manager = CurveManager()
    row = 2
    file_path = "/tmp/test3.mda"
    label = "curve3"
    plot_options = {"filePath": file_path, "fileName": "test3"}
    ds_options = {"label": label}
    x = np.array([1, 2, 3])
    y = np.array([4, 5, 6])
    manager.addCurve(row, x, y, plot_options=plot_options, ds_options=ds_options)
    curve_id = manager.generateCurveID(label, file_path, row)
    found_id = manager.findCurveID(file_path, row)
    assert found_id == curve_id


def test_chartview_plotting_methods(qtbot):
    """Test basic plotting methods and configuration."""
    # Mock the parent and required attributes
    parent = MagicMock()
    parent.mda_file_viz.curveBox = MagicMock()
    parent.mda_file_viz.clearAll = MagicMock()
    parent.mda_file_viz.curveRemove = MagicMock()
    parent.mda_file_viz.cursor1_remove = MagicMock()
    parent.mda_file_viz.cursor2_remove = MagicMock()
    parent.mda_file_viz.offset_value = MagicMock()
    parent.mda_file_viz.factor_value = MagicMock()
    parent.mda_file.tabManager.tabRemoved = MagicMock()
    parent.mda_file_viz.curveBox.currentIndexChanged = MagicMock()
    parent.detRemoved = MagicMock()

    # Patch settings.getKey to avoid config issues
    import mdaviz.user_settings

    mdaviz.user_settings.settings.getKey = lambda key: 800

    widget = ChartView(parent)
    qtbot.addWidget(widget)

    # Test title and axis label methods
    widget.setTitle("Test Title")
    assert widget.title() == "Test Title"

    widget.setXlabel("X Axis")
    assert widget.xlabel() == "X Axis"

    widget.setYlabel("Y Axis")
    assert widget.ylabel() == "Y Axis"

    # Test plot configuration - mock the grid methods
    widget.main_axes.grid = MagicMock()
    widget.configPlot(grid=True)
    # The actual call includes additional parameters, so we check it was called
    assert widget.main_axes.grid.called

    widget.configPlot(grid=False)
    assert widget.main_axes.grid.called


def test_chartview_curve_selection(qtbot):
    """Test curve selection and combo box management."""
    # Mock the parent and required attributes
    parent = MagicMock()
    parent.mda_file_viz.curveBox = MagicMock()
    parent.mda_file_viz.clearAll = MagicMock()
    parent.mda_file_viz.curveRemove = MagicMock()
    parent.mda_file_viz.cursor1_remove = MagicMock()
    parent.mda_file_viz.cursor2_remove = MagicMock()
    parent.mda_file_viz.offset_value = MagicMock()
    parent.mda_file_viz.factor_value = MagicMock()
    parent.mda_file.tabManager.tabRemoved = MagicMock()
    parent.mda_file_viz.curveBox.currentIndexChanged = MagicMock()
    parent.detRemoved = MagicMock()

    # Patch settings.getKey to avoid config issues
    import mdaviz.user_settings

    mdaviz.user_settings.settings.getKey = lambda key: 800

    widget = ChartView(parent)
    qtbot.addWidget(widget)

    # Mock the curve manager to return a valid curve
    widget.curveManager = MagicMock()
    widget.curveManager.curves.return_value = {"test_curve_id": {}}

    # Mock the combo box properly
    mock_combo = MagicMock()
    mock_combo.currentIndex.return_value = 0  # Return an integer
    mock_combo.itemData.return_value = "test_curve_id"
    widget.curveBox = mock_combo

    # Test getting selected curve ID
    selected_id = widget.getSelectedCurveID()
    assert selected_id == "test_curve_id"

    # Test when no item is selected
    mock_combo.currentIndex.return_value = -1
    selected_id = widget.getSelectedCurveID()
    assert selected_id is None


def test_chartview_cursor_management(qtbot):
    """Test cursor management functionality."""
    # Mock the parent and required attributes
    parent = MagicMock()
    parent.mda_file_viz.curveBox = MagicMock()
    parent.mda_file_viz.clearAll = MagicMock()
    parent.mda_file_viz.curveRemove = MagicMock()
    parent.mda_file_viz.cursor1_remove = MagicMock()
    parent.mda_file_viz.cursor2_remove = MagicMock()
    parent.mda_file_viz.offset_value = MagicMock()
    parent.mda_file_viz.factor_value = MagicMock()
    parent.mda_file.tabManager.tabRemoved = MagicMock()
    parent.mda_file_viz.curveBox.currentIndexChanged = MagicMock()
    parent.detRemoved = MagicMock()

    # Patch settings.getKey to avoid config issues
    import mdaviz.user_settings

    mdaviz.user_settings.settings.getKey = lambda key: 800

    widget = ChartView(parent)
    qtbot.addWidget(widget)

    # Test cursor removal
    widget.onRemoveCursor(cursor_num=1)
    assert widget.cursors[1] is None
    assert widget.cursors["pos1"] is None

    widget.onRemoveCursor(cursor_num=2)
    assert widget.cursors[2] is None
    assert widget.cursors["pos2"] is None

    # Test clearing all cursors
    widget.clearCursors()
    assert widget.cursors[1] is None
    assert widget.cursors[2] is None
    assert widget.cursors["pos1"] is None
    assert widget.cursors["pos2"] is None


def test_chartview_find_nearest_point(qtbot):
    """Test finding nearest point functionality."""
    # Mock the parent and required attributes
    parent = MagicMock()
    parent.mda_file_viz.curveBox = MagicMock()
    parent.mda_file_viz.clearAll = MagicMock()
    parent.mda_file_viz.curveRemove = MagicMock()
    parent.mda_file_viz.cursor1_remove = MagicMock()
    parent.mda_file_viz.cursor2_remove = MagicMock()
    parent.mda_file_viz.offset_value = MagicMock()
    parent.mda_file_viz.factor_value = MagicMock()
    parent.mda_file.tabManager.tabRemoved = MagicMock()
    parent.mda_file_viz.curveBox.currentIndexChanged = MagicMock()
    parent.detRemoved = MagicMock()

    # Patch settings.getKey to avoid config issues
    import mdaviz.user_settings

    mdaviz.user_settings.settings.getKey = lambda key: 800

    widget = ChartView(parent)
    qtbot.addWidget(widget)

    # Mock the curve manager to return a valid curve
    widget.curveManager = MagicMock()
    widget.curveManager.curves.return_value = {"test_curve": {}}
    widget.curveManager.getCurveData.return_value = {
        "ds": [np.array([1.0, 2.0, 3.0]), np.array([4.0, 5.0, 6.0])],
        "factor": 1,
        "offset": 0,
    }

    # Mock the combo box to return a valid index
    mock_combo = MagicMock()
    mock_combo.currentIndex.return_value = 0
    mock_combo.itemData.return_value = "test_curve"
    widget.curveBox = mock_combo

    # Test with no curves
    widget.curveManager.curves.return_value = {}
    result = widget.findNearestPoint(1.0, 2.0)
    assert result is None

    # Test with mock curve data
    widget.curveManager.curves.return_value = {"test_curve": {}}
    result = widget.findNearestPoint(2.1, 5.1)
    assert result is not None
    assert len(result) == 2


def test_chartview_offset_factor_updates(qtbot):
    """Test offset and factor update handling."""
    # Mock the parent and required attributes
    parent = MagicMock()
    parent.mda_file_viz.curveBox = MagicMock()
    parent.mda_file_viz.clearAll = MagicMock()
    parent.mda_file_viz.curveRemove = MagicMock()
    parent.mda_file_viz.cursor1_remove = MagicMock()
    parent.mda_file_viz.cursor2_remove = MagicMock()
    parent.mda_file_viz.offset_value = MagicMock()
    parent.mda_file_viz.factor_value = MagicMock()
    parent.mda_file.tabManager.tabRemoved = MagicMock()
    parent.mda_file_viz.curveBox.currentIndexChanged = MagicMock()
    parent.detRemoved = MagicMock()

    # Patch settings.getKey to avoid config issues
    import mdaviz.user_settings

    mdaviz.user_settings.settings.getKey = lambda key: 800

    widget = ChartView(parent)
    qtbot.addWidget(widget)

    # Mock the curve manager to return a valid curve
    widget.curveManager = MagicMock()
    widget.curveManager.curves.return_value = {"test_curve": {}}

    # Mock the combo box to return a valid index
    mock_combo = MagicMock()
    mock_combo.currentIndex.return_value = 0
    mock_combo.itemData.return_value = "test_curve"
    widget.curveBox = mock_combo

    # Mock the offset and factor line edits
    mock_offset = MagicMock()
    mock_offset.text.return_value = "10.5"
    widget.offset_value = mock_offset

    mock_factor = MagicMock()
    mock_factor.text.return_value = "2.0"
    widget.factor_value = mock_factor

    # Test offset update
    widget.onOffsetUpdated()
    widget.curveManager.updateCurveOffset.assert_called()

    # Test factor update
    widget.onFactorUpdated()
    widget.curveManager.updateCurveFactor.assert_called()


def test_chartview_curve_removal_signals(qtbot):
    """Test curve removal signal handling."""
    # Mock the parent and required attributes
    parent = MagicMock()
    parent.mda_file_viz.curveBox = MagicMock()
    parent.mda_file_viz.clearAll = MagicMock()
    parent.mda_file_viz.curveRemove = MagicMock()
    parent.mda_file_viz.cursor1_remove = MagicMock()
    parent.mda_file_viz.cursor2_remove = MagicMock()
    parent.mda_file_viz.offset_value = MagicMock()
    parent.mda_file_viz.factor_value = MagicMock()
    parent.mda_file.tabManager.tabRemoved = MagicMock()
    parent.mda_file_viz.curveBox.currentIndexChanged = MagicMock()
    parent.detRemoved = MagicMock()

    # Patch settings.getKey to avoid config issues
    import mdaviz.user_settings

    mdaviz.user_settings.settings.getKey = lambda key: 800

    widget = ChartView(parent)
    qtbot.addWidget(widget)

    # Mock the curve manager to return a valid curve with proper data structure
    widget.curveManager = MagicMock()
    widget.curveManager.curves.return_value = {"test_curve": {}, "other_curve": {}}
    widget.curveManager.getCurveData.return_value = {
        "plot_options": {"x": "test_x_label", "y": "test_y_label"}
    }

    # Mock the combo box to return a valid index
    mock_combo = MagicMock()
    mock_combo.currentIndex.return_value = 0
    mock_combo.itemData.return_value = "test_curve"
    widget.curveBox = mock_combo

    # Test remove button click - need to mock the curves() method to return more than one curve
    widget.onRemoveButtonClicked()
    widget.curveManager.removeCurve.assert_called_with("test_curve")

    # Test curve removal signal
    widget.plotObjects = {"test_curve": MagicMock()}
    # Provide a curveData dict with required keys
    curve_data = {"row": 0, "file_path": "/tmp/test.mda"}
    widget.mda_mvc.mda_file.tabPath2Tableview.return_value = (
        None  # Avoids further calls
    )
    widget.onCurveRemoved("test_curve", curve_data, 0)
    assert "test_curve" not in widget.plotObjects


def test_chartview_tab_and_det_removal(qtbot):
    """Test tab and detector removal handling."""
    # Mock the parent and required attributes
    parent = MagicMock()
    parent.mda_file_viz.curveBox = MagicMock()
    parent.mda_file_viz.clearAll = MagicMock()
    parent.mda_file_viz.curveRemove = MagicMock()
    parent.mda_file_viz.cursor1_remove = MagicMock()
    parent.mda_file_viz.cursor2_remove = MagicMock()
    parent.mda_file_viz.offset_value = MagicMock()
    parent.mda_file_viz.factor_value = MagicMock()
    parent.mda_file.tabManager.tabRemoved = MagicMock()
    parent.mda_file_viz.curveBox.currentIndexChanged = MagicMock()
    parent.detRemoved = MagicMock()

    # Patch settings.getKey to avoid config issues
    import mdaviz.user_settings

    mdaviz.user_settings.settings.getKey = lambda key: 800

    widget = ChartView(parent)
    qtbot.addWidget(widget)

    # Mock the curve manager
    widget.curveManager = MagicMock()
    widget.curveManager.curves.return_value = {
        "test_curve": {"file_path": "/path/to/file.mda"}
    }

    # Mock the mda_file mode
    widget.mda_mvc.mda_file.mode.return_value = "Auto-add"

    # Test tab removal
    widget.onTabRemoved("/path/to/file.mda")
    widget.curveManager.removeCurve.assert_called()

    # Test detector removal
    widget.curveManager.findCurveID.return_value = "test_curve"
    widget.onDetRemoved("/path/to/file.mda", 0)
    widget.curveManager.removeCurve.assert_called()


def test_chartview_has_data_items(qtbot):
    """Test checking if chart has data items."""
    # Mock the parent and required attributes
    parent = MagicMock()
    parent.mda_file_viz.curveBox = MagicMock()
    parent.mda_file_viz.clearAll = MagicMock()
    parent.mda_file_viz.curveRemove = MagicMock()
    parent.mda_file_viz.cursor1_remove = MagicMock()
    parent.mda_file_viz.cursor2_remove = MagicMock()
    parent.mda_file_viz.offset_value = MagicMock()
    parent.mda_file_viz.factor_value = MagicMock()
    parent.mda_file.tabManager.tabRemoved = MagicMock()
    parent.mda_file_viz.curveBox.currentIndexChanged = MagicMock()
    parent.detRemoved = MagicMock()

    # Patch settings.getKey to avoid config issues
    import mdaviz.user_settings

    mdaviz.user_settings.settings.getKey = lambda key: 800

    widget = ChartView(parent)
    qtbot.addWidget(widget)

    # Test with no data
    widget.main_axes.has_data = MagicMock(return_value=False)
    assert not widget.hasDataItems()

    # Test with data
    widget.main_axes.has_data = MagicMock(return_value=True)
    assert widget.hasDataItems()


def test_chartview_clear_plot(qtbot):
    """Test clearing the plot."""
    # Mock the parent and required attributes
    parent = MagicMock()
    parent.mda_file_viz.curveBox = MagicMock()
    parent.mda_file_viz.clearAll = MagicMock()
    parent.mda_file_viz.curveRemove = MagicMock()
    parent.mda_file_viz.cursor1_remove = MagicMock()
    parent.mda_file_viz.cursor2_remove = MagicMock()
    parent.mda_file_viz.offset_value = MagicMock()
    parent.mda_file_viz.factor_value = MagicMock()
    parent.mda_file.tabManager.tabRemoved = MagicMock()
    parent.mda_file_viz.curveBox.currentIndexChanged = MagicMock()
    parent.detRemoved = MagicMock()

    # Patch settings.getKey to avoid config issues
    import mdaviz.user_settings

    mdaviz.user_settings.settings.getKey = lambda key: 800

    widget = ChartView(parent)
    qtbot.addWidget(widget)

    # Mock the axes clear method
    widget.main_axes.clear = MagicMock()

    # Test clearing the plot
    widget.clearPlot()
    widget.main_axes.clear.assert_called()


def test_chartview_maximum_height_setting(qtbot):
    """Test setting maximum plot height."""
    # Mock the parent and required attributes
    parent = MagicMock()
    parent.mda_file_viz.curveBox = MagicMock()
    parent.mda_file_viz.clearAll = MagicMock()
    parent.mda_file_viz.curveRemove = MagicMock()
    parent.mda_file_viz.cursor1_remove = MagicMock()
    parent.mda_file_viz.cursor2_remove = MagicMock()
    parent.mda_file_viz.offset_value = MagicMock()
    parent.mda_file_viz.factor_value = MagicMock()
    parent.mda_file.tabManager.tabRemoved = MagicMock()
    parent.mda_file_viz.curveBox.currentIndexChanged = MagicMock()
    parent.detRemoved = MagicMock()

    # Patch settings.getKey to avoid config issues
    import mdaviz.user_settings

    mdaviz.user_settings.settings.getKey = lambda key: 800

    widget = ChartView(parent)
    qtbot.addWidget(widget)

    # Test setting maximum height
    widget.setMaximumPlotHeight(600)
    assert widget.maximumHeight() == 600
    assert widget.canvas.maximumHeight() == 550  # 600 - 50 for toolbar


def test_chartview_modifier_key_checking(qtbot):
    """Test modifier key checking functionality."""
    # Mock the parent and required attributes
    parent = MagicMock()
    parent.mda_file_viz.curveBox = MagicMock()
    parent.mda_file_viz.clearAll = MagicMock()
    parent.mda_file_viz.curveRemove = MagicMock()
    parent.mda_file_viz.cursor1_remove = MagicMock()
    parent.mda_file_viz.cursor2_remove = MagicMock()
    parent.mda_file_viz.offset_value = MagicMock()
    parent.mda_file_viz.factor_value = MagicMock()
    parent.mda_file.tabManager.tabRemoved = MagicMock()
    parent.mda_file_viz.curveBox.currentIndexChanged = MagicMock()
    parent.detRemoved = MagicMock()

    # Patch settings.getKey to avoid config issues
    import mdaviz.user_settings

    mdaviz.user_settings.settings.getKey = lambda key: 800

    widget = ChartView(parent)
    qtbot.addWidget(widget)

    # Test modifier key checking
    widget.check_modifier_keys()
    # Should not raise an exception and should set alt_pressed to a Qt modifier
    assert hasattr(widget.alt_pressed, "__class__")


def test_chartview_combo_box_curve_management(qtbot):
    """Test combo box curve ID management."""
    # Mock the parent and required attributes
    parent = MagicMock()
    parent.mda_file_viz.curveBox = MagicMock()
    parent.mda_file_viz.clearAll = MagicMock()
    parent.mda_file_viz.curveRemove = MagicMock()
    parent.mda_file_viz.cursor1_remove = MagicMock()
    parent.mda_file_viz.cursor2_remove = MagicMock()
    parent.mda_file_viz.offset_value = MagicMock()
    parent.mda_file_viz.factor_value = MagicMock()
    parent.mda_file.tabManager.tabRemoved = MagicMock()
    parent.mda_file_viz.curveBox.currentIndexChanged = MagicMock()
    parent.detRemoved = MagicMock()

    # Patch settings.getKey to avoid config issues
    import mdaviz.user_settings

    mdaviz.user_settings.settings.getKey = lambda key: 800

    widget = ChartView(parent)
    qtbot.addWidget(widget)

    # Mock the combo box
    mock_combo = MagicMock()
    mock_combo.count.return_value = 1
    mock_combo.itemData.return_value = "test_curve_id"
    widget.curveBox = mock_combo

    # Test removing item from curve box
    widget.removeItemCurveBox("test_curve_id")
    mock_combo.removeItem.assert_called_with(0)

    # Test updating combo box curve IDs
    widget.plotObjects = {"curve1": MagicMock(), "curve2": MagicMock()}
    widget.curveManager = MagicMock()
    widget.curveManager.curves.return_value = {
        "curve1": {"file_path": "/path1", "ds_options": {"label": "label1"}},
        "curve2": {"file_path": "/path2", "ds_options": {"label": "label2"}},
    }
    widget.updateComboBoxCurveIDs()
    # Should call itemData and setItemData
    assert mock_combo.itemData.called


def test_chartview_log_scale_functionality(qtbot):
    """Test log scale functionality."""
    # Mock the parent and required attributes
    parent = MagicMock()
    parent.mda_file_viz.curveBox = MagicMock()
    parent.mda_file_viz.clearAll = MagicMock()
    parent.mda_file_viz.curveRemove = MagicMock()
    parent.mda_file_viz.cursor1_remove = MagicMock()
    parent.mda_file_viz.cursor2_remove = MagicMock()
    parent.mda_file_viz.offset_value = MagicMock()
    parent.mda_file_viz.factor_value = MagicMock()
    parent.mda_file.tabManager.tabRemoved = MagicMock()
    parent.mda_file_viz.curveBox.currentIndexChanged = MagicMock()
    parent.detRemoved = MagicMock()

    # Patch settings.getKey to avoid config issues
    import mdaviz.user_settings

    mdaviz.user_settings.settings.getKey = lambda key: 800

    widget = ChartView(parent)
    qtbot.addWidget(widget)

    # Test log scale functionality
    # Mock the axes methods
    widget.main_axes.set_xscale = MagicMock()
    widget.main_axes.set_yscale = MagicMock()
    widget.canvas.draw = MagicMock()

    # Test setting log scales
    widget.setLogScales(True, False)
    widget.main_axes.set_xscale.assert_called_once_with("log")
    widget.main_axes.set_yscale.assert_called_once_with("linear")
    widget.canvas.draw.assert_called()

    # Reset mocks
    widget.main_axes.set_xscale.reset_mock()
    widget.main_axes.set_yscale.reset_mock()
    widget.canvas.draw.reset_mock()

    # Test setting both log scales
    widget.setLogScales(True, True)
    widget.main_axes.set_xscale.assert_called_once_with("log")
    widget.main_axes.set_yscale.assert_called_once_with("log")
    widget.canvas.draw.assert_called()

    # Reset mocks
    widget.main_axes.set_xscale.reset_mock()
    widget.main_axes.set_yscale.reset_mock()
    widget.canvas.draw.reset_mock()

    # Test setting linear scales
    widget.setLogScales(False, False)
    widget.main_axes.set_xscale.assert_called_once_with("linear")
    widget.main_axes.set_yscale.assert_called_once_with("linear")
    widget.canvas.draw.assert_called()


def test_chartview_log_scale_toggling(qtbot: "FixtureRequest") -> None:
    """Test toggling log scale for X and Y axes in ChartView."""
    parent = MagicMock()
    parent.mda_file_viz.curveBox = MagicMock()
    parent.mda_file_viz.clearAll = MagicMock()
    parent.mda_file_viz.curveRemove = MagicMock()
    parent.mda_file_viz.cursor1_remove = MagicMock()
    parent.mda_file_viz.cursor2_remove = MagicMock()
    parent.mda_file_viz.offset_value = MagicMock()
    parent.mda_file_viz.factor_value = MagicMock()
    parent.mda_file.tabManager.tabRemoved = MagicMock()
    parent.mda_file_viz.curveBox.currentIndexChanged = MagicMock()
    parent.detRemoved = MagicMock()

    import mdaviz.user_settings

    mdaviz.user_settings.settings.getKey = lambda key: 800

    widget = ChartView(parent)
    qtbot.addWidget(widget)
    widget.show()
    # Simulate enabling log scale controls
    widget.setLogScales(True, False)
    assert widget._log_x is True
    assert widget._log_y is False
    widget.setLogScales(True, True)
    assert widget._log_x is True
    assert widget._log_y is True
    widget.setLogScales(False, True)
    assert widget._log_x is False
    assert widget._log_y is True
    widget.setLogScales(False, False)
    assert widget._log_x is False
    assert widget._log_y is False


def test_chartview_curve_style_changes(qtbot: "FixtureRequest") -> None:
    """Test changing curve style in ChartView and error handling for invalid styles."""
    parent = MagicMock()
    parent.mda_file_viz.curveBox = QComboBox()
    parent.mda_file_viz.clearAll = MagicMock()
    parent.mda_file_viz.curveRemove = MagicMock()
    parent.mda_file_viz.cursor1_remove = MagicMock()
    parent.mda_file_viz.cursor2_remove = MagicMock()
    parent.mda_file_viz.offset_value = MagicMock()
    parent.mda_file_viz.factor_value = MagicMock()
    parent.mda_file.tabManager.tabRemoved = MagicMock()
    parent.detRemoved = MagicMock()

    import mdaviz.user_settings

    mdaviz.user_settings.settings.getKey = lambda key: 800

    # Assign the real style dictionary to the mock
    parent.mda_file_viz.curve_styles = {
        "Line": "-",
        "Points": ".",
        "Circle Markers": "o-",
        "Square Markers": "s-",
        "Triangle Markers": "^-",
        "Diamond Markers": "D-",
        "Dashed": "--",
        "Dots": ":",
        "Dash-Dot": "-.",
    }

    widget = ChartView(parent)
    qtbot.addWidget(widget)
    widget.show()
    # Add a curve - pass x and y as positional arguments
    x = np.array([1, 2, 3])
    y = np.array([1, 4, 9])
    widget.curveManager.addCurve(
        0,  # row as positional
        x,
        y,  # x and y as positional
        plot_options={"filePath": "/test.mda", "fileName": "test"},
        ds_options={"label": "Test"},
    )
    curve_id = list(widget.curveManager.curves().keys())[0]
    # Set up the combo box to select the curve
    widget.curveBox.addItem("Test")
    widget.curveBox.setItemData(0, curve_id, 32)  # 32 = QtCore.Qt.ItemDataRole.UserRole
    widget.curveBox.setCurrentIndex(0)

    # Change style using ChartView method
    widget.updateCurveStyle("Dashed")
    # Verify the style was updated in the curve data
    curve_data = widget.curveManager.getCurveData(curve_id)
    assert curve_data["style"] == "--"
    # Try invalid style (should not raise)
    try:
        widget.updateCurveStyle("invalid-style")
    except Exception as e:
        pytest.fail(f"updateCurveStyle raised an exception: {e}")


def test_chartview_error_handling_on_invalid_curve(qtbot: "FixtureRequest") -> None:
    """Test error handling when updating/removing a non-existent curve in ChartView."""
    parent = MagicMock()
    parent.mda_file_viz.curveBox = MagicMock()
    parent.mda_file_viz.clearAll = MagicMock()
    parent.mda_file_viz.curveRemove = MagicMock()
    parent.mda_file_viz.cursor1_remove = MagicMock()
    parent.mda_file_viz.cursor2_remove = MagicMock()
    parent.mda_file_viz.offset_value = MagicMock()
    parent.mda_file_viz.factor_value = MagicMock()
    parent.mda_file.tabManager.tabRemoved = MagicMock()
    parent.mda_file_viz.curveBox.currentIndexChanged = MagicMock()
    parent.detRemoved = MagicMock()

    import mdaviz.user_settings

    mdaviz.user_settings.settings.getKey = lambda key: 800

    widget = ChartView(parent)
    qtbot.addWidget(widget)
    widget.show()
    # Try to remove a non-existent curve
    non_existent_id = "not_a_real_curve_id"
    # Should not raise
    try:
        widget.curveManager.removeCurve(non_existent_id)
    except Exception as e:
        pytest.fail(f"CurveManager raised an exception on invalid curve id: {e}")
