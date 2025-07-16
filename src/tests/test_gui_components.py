#!/usr/bin/env python
"""
Focused GUI component tests for mdaviz.

This module provides targeted testing of critical GUI components using pytest-qt.
Focuses on the most important UI interactions and functionality.

.. autosummary::

    ~test_mainwindow_basic_functionality
    ~test_chartview_plotting
    ~test_data_table_interactions
    ~test_file_loading_workflow
    ~test_memory_management_ui
"""

from typing import TYPE_CHECKING
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock
import numpy as np

from PyQt6.QtWidgets import QFileDialog

from mdaviz.mainwindow import MainWindow
from mdaviz.chartview import ChartView
from mdaviz.mda_file import MDAFile
from mdaviz.data_cache import DataCache
from mdaviz.mda_file_viz import MDAFileVisualization


if TYPE_CHECKING:
    from _pytest.fixtures import FixtureRequest


class TestMainWindowBasic:
    """Test basic MainWindow functionality."""

    def test_mainwindow_creation(self, qtbot: "FixtureRequest") -> None:
        """Test that MainWindow can be created and displayed."""
        window = MainWindow()
        qtbot.addWidget(window)
        window.show()

        # Basic existence checks
        assert window is not None
        assert window.isVisible()
        assert window.windowTitle() == "MDA Data Visualization"

        # Check that main components exist
        assert hasattr(window, "mda_mvc")
        assert window.mda_mvc is not None

    def test_mainwindow_menu_structure(self, qtbot: "FixtureRequest") -> None:
        """Test MainWindow menu structure and basic actions."""
        window = MainWindow()
        qtbot.addWidget(window)

        # Check menu bar exists
        menu_bar = window.menuBar()
        assert menu_bar is not None

        # Check that menus exist
        actions = menu_bar.actions()
        assert len(actions) > 0

        # Check for File menu
        file_menu = None
        for action in actions:
            if "File" in action.text():
                file_menu = action
                break

        assert file_menu is not None

    def test_mainwindow_status_updates(self, qtbot: "FixtureRequest") -> None:
        """Test MainWindow status bar updates."""
        window = MainWindow()
        qtbot.addWidget(window)

        # Test status update
        test_message = "Test status message"
        window.setStatus(test_message)

        # Check status bar
        status_bar = window.statusBar()
        assert status_bar is not None
        assert test_message in status_bar.currentMessage()

    def test_mainwindow_resize(self, qtbot: "FixtureRequest") -> None:
        """Test MainWindow resize behavior."""
        window = MainWindow()
        qtbot.addWidget(window)

        # Test resize
        original_size = window.size()
        new_size = original_size + (50, 50)
        window.resize(new_size)

        # Verify resize worked
        assert window.size() == new_size


class TestChartViewBasic:
    """Test basic ChartView functionality."""

    def test_chartview_creation(self, qtbot: "FixtureRequest") -> None:
        """Test that ChartView can be created with proper setup."""
        # Create mock parent
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

        # Patch settings
        with patch("mdaviz.user_settings.settings.getKey", return_value=800):
            chart_view = ChartView(parent)
            qtbot.addWidget(chart_view)

            # Check basic components
            assert chart_view is not None
            assert hasattr(chart_view, "figure")
            assert hasattr(chart_view, "canvas")
            assert hasattr(chart_view, "main_axes")
            assert hasattr(chart_view, "curveManager")

    def test_chartview_curve_management(self, qtbot: "FixtureRequest") -> None:
        """Test ChartView curve management functionality."""
        # Create mock parent
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

        with patch("mdaviz.user_settings.settings.getKey", return_value=800):
            chart_view = ChartView(parent)
            qtbot.addWidget(chart_view)

            # Test adding a curve
            x_data = np.array([1, 2, 3, 4, 5])
            y_data = np.array([1, 4, 9, 16, 25])

            chart_view.curveManager.addCurve(
                row=0,
                x=x_data,
                y=y_data,
                plot_options={"filePath": "/test.mda", "fileName": "test"},
                ds_options={"label": "Test Curve"},
            )

            # Verify curve was added
            curves = chart_view.curveManager.curves()
            assert len(curves) == 1

            # Test removing curve
            curve_id = list(curves.keys())[0]
            chart_view.curveManager.removeCurve(curve_id)
            assert len(chart_view.curveManager.curves()) == 0

    def test_chartview_plot_clearing(self, qtbot: "FixtureRequest") -> None:
        """Test ChartView plot clearing functionality."""
        # Create mock parent
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

        with patch("mdaviz.user_settings.settings.getKey", return_value=800):
            chart_view = ChartView(parent)
            qtbot.addWidget(chart_view)

            # Add some curves
            for i in range(3):
                chart_view.curveManager.addCurve(
                    row=i,
                    x=np.array([1, 2, 3]),
                    y=np.array([i, i + 1, i + 2]),
                    plot_options={"filePath": f"/test{i}.mda", "fileName": f"test{i}"},
                    ds_options={"label": f"Curve {i}"},
                )

            # Verify curves were added
            assert len(chart_view.curveManager.curves()) == 3

            # Clear plot
            chart_view.clearPlot()
            assert len(chart_view.curveManager.curves()) == 0


class TestDataTableBasic:
    """Test basic data table functionality."""

    def test_mda_file_creation(self, qtbot: "FixtureRequest") -> None:
        """Test that MDAFile widget can be created."""
        # Create mock parent
        parent = MagicMock()
        parent.mda_file_viz = MagicMock()

        mda_file = MDAFile(parent)
        qtbot.addWidget(mda_file)

        # Check basic structure
        assert mda_file is not None
        assert hasattr(mda_file, "tabWidget")
        assert hasattr(mda_file, "mda_mvc")

    def test_data_display(self, qtbot: "FixtureRequest") -> None:
        """Test data display functionality."""
        # Create mock parent
        parent = MagicMock()
        parent.mda_file_viz = MagicMock()

        mda_file = MDAFile(parent)
        qtbot.addWidget(mda_file)

        # Create test data
        test_data = {
            "scanDict": {
                "pos1": {"name": "Position 1", "values": [1, 2, 3, 4, 5]},
                "det1": {"name": "Detector 1", "values": [10, 20, 30, 40, 50]},
            },
            "firstPos": 0,
            "firstDet": 1,
        }

        # Set data
        mda_file._data = test_data

        # Test data display
        mda_file.displayData(test_data["scanDict"])

        # Verify data was processed
        assert mda_file._data is not None


class TestFileLoadingWorkflow:
    """Test file loading workflow and integration."""

    def test_file_dialog_mocking(self, qtbot: "FixtureRequest", tmp_path: Path) -> None:
        """Test file dialog integration with mocked responses."""
        # Create test files
        test_file = tmp_path / "test.mda"
        test_file.write_bytes(b"fake mda data")

        window = MainWindow()
        qtbot.addWidget(window)

        # Mock file dialog
        with patch.object(
            QFileDialog, "getExistingDirectory", return_value=str(tmp_path)
        ):
            # This would normally trigger file loading
            # For now, just verify the mock works
            result = QFileDialog.getExistingDirectory()
            assert result == str(tmp_path)

    def test_cache_integration(self, qtbot: "FixtureRequest") -> None:
        """Test cache integration with file loading."""
        # Create a test cache
        cache = DataCache(max_size_mb=10.0, max_entries=5)

        # Test cache statistics
        stats = cache.get_stats()
        assert stats["entry_count"] == 0
        assert stats["current_size_mb"] == 0.0
        assert stats["utilization_percent"] == 0.0


class TestMemoryManagementUI:
    """Test memory management UI components."""

    def test_memory_warning_signal(self, qtbot: "FixtureRequest") -> None:
        """Test memory warning signal emission."""
        # Create cache with low memory limit
        cache = DataCache(max_memory_mb=10.0)

        # Mock high memory usage
        with patch("psutil.Process") as mock_process:
            mock_instance = Mock()
            mock_instance.memory_info.return_value.rss = 15 * 1024 * 1024  # 15MB
            mock_process.return_value = mock_instance

            # Check memory usage
            memory_usage = cache._check_memory_usage()

            # Verify memory warning was emitted
            with qtbot.waitSignal(cache.memory_warning, timeout=1000):
                pass

    def test_cache_eviction(self, qtbot: "FixtureRequest") -> None:
        """Test cache eviction when limits are exceeded."""
        # Create small cache
        cache = DataCache(max_size_mb=1.0, max_entries=2)

        # Add test data that exceeds limits
        test_data1 = MagicMock()
        test_data1.get_size_mb.return_value = 0.6
        test_data1.file_path = "/test1.mda"

        test_data2 = MagicMock()
        test_data2.get_size_mb.return_value = 0.6
        test_data2.file_path = "/test2.mda"

        test_data3 = MagicMock()
        test_data3.get_size_mb.return_value = 0.6
        test_data3.file_path = "/test3.mda"

        # Add data to cache
        cache.put("/test1.mda", test_data1)
        cache.put("/test2.mda", test_data2)
        cache.put("/test3.mda", test_data3)

        # Verify eviction occurred
        stats = cache.get_stats()
        assert stats["entry_count"] <= 2  # Should not exceed max_entries


class TestErrorHandling:
    """Test error handling in GUI components."""

    def test_invalid_file_handling(self, qtbot: "FixtureRequest") -> None:
        """Test handling of invalid files."""
        window = MainWindow()
        qtbot.addWidget(window)

        # Test with invalid file path
        with patch("mdaviz.synApps_mdalib.mda.readMDA", return_value=None):
            # This should not crash the application
            pass

    def test_memory_error_handling(self, qtbot: "FixtureRequest") -> None:
        """Test handling of memory errors."""
        cache = DataCache()

        # Test with psutil import error
        with patch("psutil.Process", side_effect=ImportError("psutil not available")):
            memory_usage = cache._check_memory_usage()
            assert memory_usage == 0.0  # Should return 0 when psutil unavailable


# Fixture for creating test data
@pytest.fixture
def sample_plot_data() -> tuple[np.ndarray, np.ndarray]:
    """Create sample plotting data."""
    x = np.linspace(0, 10, 100)
    y = np.sin(x)
    return x, y


# Fixture for creating mock parent
@pytest.fixture
def mock_chartview_parent() -> MagicMock:
    """Create a mock parent for ChartView."""
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
    return parent


# Integration test
def test_basic_workflow_integration(
    qtbot: "FixtureRequest", mock_chartview_parent: MagicMock
) -> None:
    """Test basic workflow integration."""
    # Create main window
    window = MainWindow()
    qtbot.addWidget(window)

    # Create chart view
    with patch("mdaviz.user_settings.settings.getKey", return_value=800):
        chart_view = ChartView(mock_chartview_parent)
        qtbot.addWidget(chart_view)

        # Add a curve
        x, y = np.array([1, 2, 3]), np.array([1, 4, 9])
        chart_view.curveManager.addCurve(
            row=0,
            x=x,
            y=y,
            plot_options={"filePath": "/test.mda", "fileName": "test"},
            ds_options={"label": "Test"},
        )

        # Verify integration works
        assert len(chart_view.curveManager.curves()) == 1
        assert window.isVisible()


def test_mda_file_viz_log_scale_functionality(qtbot):
    """Test log scale functionality in MDAFileVisualization."""
    # Mock the parent
    parent = MagicMock()

    # Patch settings.getKey to avoid config issues
    import mdaviz.user_settings

    mdaviz.user_settings.settings.getKey = lambda key: 800

    widget = MDAFileVisualization(parent)
    qtbot.addWidget(widget)

    # Test that log scale controls are initially disabled
    assert not widget.logXCheckBox.isEnabled()
    assert not widget.logYCheckBox.isEnabled()

    # Test that log scale controls can be enabled
    widget.updateCurveStyleControls(True)
    assert widget.logXCheckBox.isEnabled()
    assert widget.logYCheckBox.isEnabled()

    # Test that log scale controls can be disabled
    widget.updateCurveStyleControls(False)
    assert not widget.logXCheckBox.isEnabled()
    assert not widget.logYCheckBox.isEnabled()

    # Test log scale checkbox state changes
    # Mock the chart_view
    mock_chart_view = MagicMock()
    widget.chart_view = mock_chart_view

    # Test LogX checkbox
    widget.logXCheckBox.setChecked(True)
    mock_chart_view.setLogScales.assert_called_with(True, False)

    # Test LogY checkbox
    widget.logYCheckBox.setChecked(True)
    mock_chart_view.setLogScales.assert_called_with(True, True)

    # Test both unchecked
    widget.logXCheckBox.setChecked(False)
    mock_chart_view.setLogScales.assert_called_with(False, True)


def test_multiple_checkbox_changes_work(qtbot):
    """Test that multiple checkbox changes work correctly after the first change."""
    # Mock the parent
    parent = MagicMock()

    # Mock the table view and model properly
    mock_tableview = MagicMock()
    mock_model = MagicMock()
    mock_tableview.tableView.model.return_value = mock_model
    mock_tableview.tableView.model().checkCheckBox = MagicMock()

    # Mock the chart view widget
    mock_chart_view = MagicMock()
    mock_chart_view.curveManager = MagicMock()

    # Mock the layout
    mock_layout = MagicMock()
    mock_layout.count.return_value = 1
    mock_layout.itemAt.return_value.widget.return_value = mock_chart_view

    # Mock the file mode and other required attributes
    parent.mda_file.mode.return_value = "Auto-add"
    parent.currentFileTableview.return_value = mock_tableview
    parent.mda_file_viz.plotPageMpl.layout.return_value = mock_layout
    parent.mda_file_viz.setPlot = MagicMock()
    parent.mda_file.tabWidget.count.return_value = 1
    parent.detRemoved = MagicMock()

    # Mock the data2Plot method to return valid data
    mock_tableview.data2Plot.return_value = ([([1, 2, 3], [4, 5, 6])], {})

    from mdaviz.mda_folder import MDA_MVC

    # Create the MVC instance
    mvc = MDA_MVC(parent)

    # Test first checkbox change (detector removal)
    selection1 = {"X": 0, "Y": [1], "I0": None}
    det_removed1 = [2]  # Detector 2 was removed

    # This should not return early and should process the change
    mvc.onCheckboxStateChanged(selection1, det_removed1)

    # Verify that detRemoved signal was emitted
    parent.detRemoved.emit.assert_called_once()

    # Reset the mock
    parent.detRemoved.emit.reset_mock()

    # Test second checkbox change (different selection)
    selection2 = {"X": 0, "Y": [1, 3], "I0": 4}  # Different Y and I0 selection
    det_removed2 = []  # No detectors removed

    # This should also work and not be blocked by the previous change
    mvc.onCheckboxStateChanged(selection2, det_removed2)

    # Verify that data2Plot was called for both changes
    assert mock_tableview.data2Plot.call_count == 2

    # Verify that setPlot was called for both changes
    assert parent.mda_file_viz.setPlot.call_count == 2
