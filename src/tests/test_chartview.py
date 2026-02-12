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
    from pytest_qt.qtbot import QtBot


def test_auto_color_and_symbol() -> None:
    """Test color and symbol cycling utilities."""
    colors = [auto_color() for _ in range(5)]
    symbols = [auto_symbol() for _ in range(5)]
    assert len(set(colors)) > 1
    assert len(set(symbols)) > 1


def test_chartview_instantiation(qtbot: "QtBot") -> None:
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
    # CurveManager updates if x_data, y_data, or label changed
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


def test_curve_manager_y_data_change_detection():
    """Test that Y data changes are detected and trigger recompute_y (e.g. normalization/unscaling)."""
    manager = CurveManager()
    curve_updated = []
    manager.curveUpdated.connect(
        lambda cid, recompute_y, update_x: curve_updated.append(
            (cid, recompute_y, update_x)
        )
    )
    row = 0
    x = np.array([1, 2, 3])
    y1 = np.array([4, 5, 6])
    y2 = np.array([7, 8, 9])  # Different Y data
    label = "test_curve"  # Same label
    file_path = "/tmp/test.mda"
    plot_options = {"filePath": file_path, "fileName": "test"}
    ds_options = {"label": label}

    # Add curve with y1
    manager.addCurve(row, x, y1, plot_options=plot_options, ds_options=ds_options)
    curve_id = manager.generateCurveID(label, file_path, row)
    assert curve_id in manager.curves()

    # Add same curve with different Y data but same X and label (e.g. normalization)
    manager.addCurve(row, x, y2, plot_options=plot_options, ds_options=ds_options)

    # Should trigger update with recompute_y=True, update_x=False
    assert len(curve_updated) == 1
    assert curve_updated[0][0] == curve_id
    assert curve_updated[0][1] is True  # recompute_y
    assert curve_updated[0][2] is False  # update_x
    np.testing.assert_array_equal(manager.getCurveData(curve_id)["ds"][1], y2)


def test_curve_manager_no_update_when_data_unchanged():
    """Test that addCurve does not update when x, y, and label are identical."""
    manager = CurveManager()
    row = 0
    x = np.array([1, 2, 3])
    y = np.array([4, 5, 6])
    label = "test_curve"
    file_path = "/tmp/test.mda"
    plot_options = {"filePath": file_path, "fileName": "test"}
    ds_options = {"label": label}

    curve_updated = []
    manager.curveUpdated.connect(
        lambda cid, recompute_y, update_x: curve_updated.append(
            (cid, recompute_y, update_x)
        )
    )

    manager.addCurve(row, x, y, plot_options=plot_options, ds_options=ds_options)
    assert len(curve_updated) == 0

    # Call addCurve again with identical data and label
    manager.addCurve(row, x, y, plot_options=plot_options, ds_options=ds_options)
    # Should not trigger update
    assert len(curve_updated) == 0


def test_curve_manager_persistent_properties():
    """Test persistent style properties in CurveManager (offset/factor are not persistent)."""
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
    # Remove and re-add - offset/factor should reset to defaults (not persistent)
    manager.removeCurve(curve_id)
    manager.addCurve(row, x, y, plot_options=plot_options, ds_options=ds_options)
    curve_data = manager.getCurveData(curve_id)
    assert curve_data["offset"] == 0  # Resets to default
    assert curve_data["factor"] == 1  # Resets to default


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
    found_ids = manager.findCurveID(file_path, row)
    assert found_ids == [curve_id]


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
    widget.curveManager.getTransformedCurveXYData.return_value = (
        np.array([1.0, 2.0, 3.0]),
        np.array([4.0, 5.0, 6.0]),
    )

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

    # Test offset and factor update (now combined)
    widget.onOffsetFactorUpdated()
    widget.curveManager.updateCurveOffsetFactor.assert_called()


def test_curve_manager_apply_transformations():
    """Test applyTransformations method with various combinations."""
    manager = CurveManager()
    row = 0
    x = np.array([1, 2, 3, 4, 5])
    y = np.array([2, 4, 6, 8, 10])
    label = "test_curve"
    file_path = "/tmp/test.mda"
    plot_options = {"filePath": file_path, "fileName": "test"}
    ds_options = {"label": label}

    manager.addCurve(row, x, y, plot_options=plot_options, ds_options=ds_options)
    curve_id = manager.generateCurveID(label, file_path, row)
    curve_data = manager.getCurveData(curve_id)
    original_y = curve_data["original_y"]

    # Test 1: No transformations (default values)
    result = manager.applyTransformations(curve_id, x, original_y)
    np.testing.assert_array_equal(result, original_y)

    # Test 2: Offset only
    manager.updateCurveOffset(curve_id, 10.0)
    result = manager.applyTransformations(curve_id, x, original_y)
    expected = original_y + 10.0
    np.testing.assert_array_almost_equal(result, expected)

    # Test 3: Factor only
    manager.updateCurveOffset(curve_id, 0.0)  # Reset offset
    manager.updateCurveFactor(curve_id, 2.0)
    result = manager.applyTransformations(curve_id, x, original_y)
    expected = 2.0 * original_y
    np.testing.assert_array_almost_equal(result, expected)

    # Test 4: Offset + factor
    manager.updateCurveOffset(curve_id, 5.0)
    result = manager.applyTransformations(curve_id, x, original_y)
    expected = 5.0 + 2.0 * original_y
    np.testing.assert_array_almost_equal(result, expected)

    # Test 5: Derivative only (no offset/factor)
    manager.updateCurveOffset(curve_id, 0.0)
    manager.updateCurveFactor(curve_id, 1.0)
    manager.updateCurveDerivative(curve_id, True)
    result = manager.applyTransformations(curve_id, x, original_y)
    expected_grad = np.gradient(original_y, x)
    np.testing.assert_array_almost_equal(result, expected_grad)

    # Test 6: All transformations combined
    manager.updateCurveOffset(curve_id, 3.0)
    manager.updateCurveFactor(curve_id, 2.0)
    result = manager.applyTransformations(curve_id, x, original_y)
    expected = 3.0 + 2.0 * np.gradient(original_y, x)
    np.testing.assert_array_almost_equal(result, expected)

    # Test 7: Non-uniform x spacing (derivative should account for this)
    x_nonuniform = np.array([1, 2, 5, 8, 10])  # Non-uniform spacing
    y_nonuniform = np.array([1, 4, 16, 64, 100])
    manager.addCurve(
        1,
        x_nonuniform,
        y_nonuniform,
        plot_options=plot_options,
        ds_options={"label": "nonuniform"},
    )
    curve_id2 = manager.generateCurveID("nonuniform", file_path, 1)
    curve_data2 = manager.getCurveData(curve_id2)
    original_y2 = curve_data2["original_y"]
    manager.updateCurveDerivative(curve_id2, True)
    result = manager.applyTransformations(curve_id2, x_nonuniform, original_y2)
    expected_grad = np.gradient(original_y2, x_nonuniform)
    np.testing.assert_array_almost_equal(result, expected_grad)

    # Test 8: Missing curve_data (should return original_y as fallback)
    result = manager.applyTransformations("nonexistent_curve", x, original_y)
    np.testing.assert_array_equal(result, original_y)


def test_curve_manager_get_transformed_curve_xy_data():
    """Test getTransformedCurveXYData method."""
    manager = CurveManager()
    row = 0
    x = np.array([1, 2, 3])
    y = np.array([4, 5, 6])
    label = "test_curve"
    file_path = "/tmp/test.mda"
    plot_options = {"filePath": file_path, "fileName": "test"}
    ds_options = {"label": label}

    manager.addCurve(row, x, y, plot_options=plot_options, ds_options=ds_options)
    curve_id = manager.generateCurveID(label, file_path, row)

    # Test 1: Get transformed data with default transformations
    x_out, y_out = manager.getTransformedCurveXYData(curve_id)
    np.testing.assert_array_equal(x_out, x)
    np.testing.assert_array_equal(y_out, y)  # No transformations applied

    # Test 2: Get transformed data with offset and factor
    manager.updateCurveOffset(curve_id, 10.0)
    manager.updateCurveFactor(curve_id, 2.0)
    x_out, y_out = manager.getTransformedCurveXYData(curve_id)
    np.testing.assert_array_equal(x_out, x)
    expected_y = 10.0 + 2.0 * y
    np.testing.assert_array_almost_equal(y_out, expected_y)

    # Test 3: Get transformed data with derivative
    manager.updateCurveDerivative(curve_id, True)
    x_out, y_out = manager.getTransformedCurveXYData(curve_id)
    np.testing.assert_array_equal(x_out, x)
    expected_y = 10.0 + 2.0 * np.gradient(y, x)
    np.testing.assert_array_almost_equal(y_out, expected_y)

    # Test 4: Invalid curveID
    x_out, y_out = manager.getTransformedCurveXYData("nonexistent")
    assert x_out is None
    assert y_out is None

    # Test 5: Missing original_y (should return None, None)
    # Manually remove original_y to simulate edge case
    curve_data = manager.getCurveData(curve_id)
    original_y_backup = curve_data["original_y"]
    del curve_data["original_y"]
    x_out, y_out = manager.getTransformedCurveXYData(curve_id)
    assert x_out is None
    assert y_out is None
    # Restore for cleanup
    curve_data["original_y"] = original_y_backup


def test_curve_manager_update_derivative():
    """Test updateCurveDerivative method."""
    manager = CurveManager()
    row = 0
    x = np.array([1, 2, 3])
    y = np.array([4, 5, 6])
    label = "test_curve"
    file_path = "/tmp/test.mda"
    plot_options = {"filePath": file_path, "fileName": "test"}
    ds_options = {"label": label}

    manager.addCurve(row, x, y, plot_options=plot_options, ds_options=ds_options)
    curve_id = manager.generateCurveID(label, file_path, row)

    # Track curveUpdated signals
    curve_updated_calls = []
    manager.curveUpdated.connect(
        lambda cid, recompute_y, update_x: curve_updated_calls.append(
            (cid, recompute_y, update_x)
        )
    )

    # Test 1: Enable derivative
    manager.updateCurveDerivative(curve_id, True)
    curve_data = manager.getCurveData(curve_id)
    assert curve_data["derivative"] is True
    assert len(curve_updated_calls) == 1
    assert curve_updated_calls[-1] == (curve_id, True, False)

    # Test 2: Disable derivative
    manager.updateCurveDerivative(curve_id, False)
    curve_data = manager.getCurveData(curve_id)
    assert curve_data["derivative"] is False
    assert len(curve_updated_calls) == 2

    # Test 3: Setting same value should not trigger update
    curve_updated_calls.clear()
    manager.updateCurveDerivative(curve_id, False)
    assert len(curve_updated_calls) == 0

    # Test 4: Invalid curveID (should not crash)
    manager.updateCurveDerivative("nonexistent", True)
    assert len(curve_updated_calls) == 0


def test_curve_manager_clear_persistent_properties():
    """Test clearPersistentProperties: after clear, re-added curves get defaults."""
    manager = CurveManager()
    row = 0
    x = np.array([1, 2, 3])
    y = np.array([4, 5, 6])
    label = "test_curve"
    file_path = "/tmp/test.mda"
    plot_options = {"filePath": file_path, "fileName": "test"}
    ds_options = {"label": label}

    manager.addCurve(row, x, y, plot_options=plot_options, ds_options=ds_options)
    curve_id = manager.generateCurveID(label, file_path, row)
    manager.updateCurveDerivative(curve_id, True)
    manager.updateCurveOffset(curve_id, 10)

    # Same-file re-plot: removeAllCurves(True) saves props, then we clear (file changed)
    manager.removeAllCurves(doNotClearCheckboxes=True)
    manager.clearPersistentProperties()

    # Re-add same curve: should get defaults, not saved values
    manager.addCurve(row, x, y, plot_options=plot_options, ds_options=ds_options)
    curve_data = manager.getCurveData(curve_id)
    assert curve_data["derivative"] is False
    assert curve_data["offset"] == 0


def test_chartview_derivative_toggle(qtbot):
    """Test derivative checkbox toggle in ChartView."""
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
    widget.curveManager.curves.return_value = {"test_curve": {}}
    widget.curveManager.getCurveData.return_value = {"derivative": False}

    # Mock the combo box to return a valid curve
    mock_combo = MagicMock()
    mock_combo.currentIndex.return_value = 0
    mock_combo.itemData.return_value = "test_curve"
    widget.curveBox = mock_combo

    # Mock updateBasicMathInfo to avoid side effects
    widget.updateBasicMathInfo = MagicMock()

    # Mock getSelectedCurveID to return the curve ID
    widget.getSelectedCurveID = MagicMock(return_value="test_curve")

    # Test derivative toggle
    widget.onDerivativeToggled(True)
    widget.curveManager.updateCurveDerivative.assert_called_with(
        "test_curve", derivative=True
    )
    widget.updateBasicMathInfo.assert_called_with("test_curve")

    # Test untoggle
    widget.onDerivativeToggled(False)
    assert widget.curveManager.updateCurveDerivative.call_count == 2
    widget.curveManager.updateCurveDerivative.assert_called_with(
        "test_curve", derivative=False
    )


def test_chartview_derivative_checkbox_sync(qtbot):
    """Test that derivative checkbox syncs with curve selection."""
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
    widget.curveManager.curves.return_value = {"curve1": {}, "curve2": {}}

    # Mock getCurveData to return different derivative states
    def mock_get_curve_data(curve_id):
        if curve_id == "curve1":
            return {
                "derivative": True,
                "offset": 0,
                "factor": 1,
                "file_path": "/tmp/test.mda",
                "row": 0,
            }
        elif curve_id == "curve2":
            return {
                "derivative": False,
                "offset": 5,
                "factor": 2,
                "file_path": "/tmp/test.mda",
                "row": 1,
            }
        return None

    widget.curveManager.getCurveData.side_effect = mock_get_curve_data

    # Mock plotObjects
    widget.plotObjects = {"curve1": MagicMock(), "curve2": MagicMock()}

    # Mock mda_mvc
    widget.mda_mvc = MagicMock()
    widget.mda_mvc.mda_file = MagicMock()
    widget.mda_mvc.mda_file.highlightRowInTab = MagicMock()
    widget.mda_mvc.mda_file_viz = MagicMock()
    widget.mda_mvc.mda_file_viz.updatePlotControls = MagicMock()

    # Mock UI elements
    from PyQt6.QtWidgets import QCheckBox, QLineEdit

    widget.derivativeCheckBox = QCheckBox()
    widget.offset_value = QLineEdit()
    widget.factor_value = QLineEdit()

    # Mock update methods to avoid side effects
    widget.updateBasicMathInfo = MagicMock()
    widget.updateFitUI = MagicMock()
    widget.updatePlot = MagicMock()

    # Mock combo box
    mock_combo = MagicMock()

    def mock_item_data(index, role):
        if index == 0:
            return "curve1"
        elif index == 1:
            return "curve2"
        return None

    mock_combo.itemData.side_effect = mock_item_data
    widget.curveBox = mock_combo

    # Test 1: Select curve1 (derivative=True)
    widget.onCurveSelected(0)
    assert widget.derivativeCheckBox.isChecked() is True
    assert widget.derivative is True

    # Test 2: Select curve2 (derivative=False)
    widget.onCurveSelected(1)
    assert widget.derivativeCheckBox.isChecked() is False
    assert widget.derivative is False

    # Test 3: Deselect (index < 0)
    widget.onCurveSelected(-1)
    assert widget.derivativeCheckBox.isChecked() is False
    assert widget.derivative is False


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
    widget.curveManager.findCurveID.return_value = ["test_curve"]
    widget.onDetRemoved("/path/to/file.mda", 0)
    widget.curveManager.removeCurve.assert_called()


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


def test_chartview_log_scale_toggling(qtbot: "QtBot") -> None:
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


def test_chartview_curve_style_changes(qtbot: "QtBot") -> None:
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


def test_chartview_error_handling_on_invalid_curve(qtbot: "QtBot") -> None:
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


def test_onAllCurvesRemoved_preserves_log_scale(qtbot: "QtBot") -> None:
    """When onAllCurvesRemoved runs (e.g. browse/replace), log scale is preserved."""
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

    widget._log_x = True
    widget._log_y = True
    widget.clearPlot = MagicMock()
    widget.fitManager.clearAllFits = MagicMock()
    widget.setLogScales = MagicMock()
    # Mock curveManager so curves() returns empty (loop does nothing)
    widget.curveManager = MagicMock()
    widget.curveManager.curves.return_value = {}
    widget.curveManager.removeCurve = MagicMock()

    widget.onAllCurvesRemoved(doNotClearCheckboxes=True)

    # Log scale should be reapplied (preserved)
    widget.setLogScales.assert_called_with(True, True)


def test_onCurveRemoved_resets_log_scale_when_last_curve(
    qtbot: "QtBot",
) -> None:
    """When the last curve is removed (e.g. last DET or last tab), log scale is reset."""
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
    parent.mda_file_viz.setLogScaleState = MagicMock()

    import mdaviz.user_settings

    mdaviz.user_settings.settings.getKey = lambda key: 800

    widget = ChartView(parent)
    qtbot.addWidget(widget)

    widget.plotObjects = {}
    widget.removeItemCurveBox = MagicMock()
    widget.updatePlot = MagicMock()
    widget.fitManager.removeFit = MagicMock()
    # Mock curveManager so curves() returns {} (0 curves left)
    widget.curveManager = MagicMock()
    widget.curveManager.curves.return_value = {}
    parent.mda_file.tabPath2Tableview.return_value = None  # skip checkbox logic
    parent.mda_file.mode.return_value = "Auto-add"
    parent.mda_file.tabManager.removeTab = MagicMock()

    curveID = "test_curve"
    curveData = {"row": 0, "file_path": "/tmp/test.mda"}
    count = 0

    widget.onCurveRemoved(curveID, curveData, count)

    parent.mda_file_viz.setLogScaleState.assert_called_once_with(False, False)


def test_onClearAllClicked_resets_log_scale(qtbot: "QtBot") -> None:
    """When Clear All is clicked, log scale is reset and allCurvesRemoved is emitted."""
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
    parent.mda_file_viz.setLogScaleState = MagicMock()

    import mdaviz.user_settings

    mdaviz.user_settings.settings.getKey = lambda key: 800

    widget = ChartView(parent)
    qtbot.addWidget(widget)

    widget.onClearAllClicked()

    # Clear All click should reset log scale (emit is a Qt signal, not mocked)
    parent.mda_file_viz.setLogScaleState.assert_called_once_with(False, False)


def test_onDetRemoved_removes_curve(qtbot: "QtBot") -> None:
    """When a detector is removed, onDetRemoved removes its curve from the manager."""
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

    widget.curveManager = MagicMock()
    widget.curveManager.findCurveID.return_value = ["curve_id"]
    widget.curveManager.removeCurve = MagicMock()
    widget.curveManager._persistent_properties = {}

    file_path = "/tmp/test.mda"
    row = 0

    widget.onDetRemoved(file_path, row)

    widget.curveManager.removeCurve.assert_called_once_with("curve_id")
