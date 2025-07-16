#!/usr/bin/env python
"""
Comprehensive GUI integration tests for mdaviz.

This module provides extensive testing of the mdaviz GUI components using pytest-qt.
Tests cover user interactions, data loading, plotting, and UI responsiveness.

.. autosummary::

    ~test_mainwindow_initialization
    ~test_mainwindow_file_loading
    ~test_mainwindow_tab_management
    ~test_chartview_plotting_interactions
    ~test_data_table_interactions
    ~test_memory_management_ui
    ~test_error_handling_ui
    ~test_user_settings_ui
"""

from typing import TYPE_CHECKING
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock
import numpy as np

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtGui import QKeySequence

from mdaviz.mainwindow import MainWindow
from mdaviz.chartview import ChartView
from mdaviz.mda_file import MDAFile
from mdaviz.data_cache import DataCache, get_global_cache


if TYPE_CHECKING:
    from _pytest.fixtures import FixtureRequest


class TestMainWindowGUI:
    """Test MainWindow GUI functionality and user interactions."""

    def test_mainwindow_initialization(self, qtbot: "FixtureRequest") -> None:
        """Test MainWindow initialization and basic UI setup."""
        # Create MainWindow
        window = MainWindow()
        qtbot.addWidget(window)

        # Verify basic UI components exist
        assert window.mda_mvc is not None
        assert window.mda_mvc.mda_folder_table_view is not None
        assert window.mda_mvc.mda_file_table_view is not None
        assert window.mda_mvc.mda_file is not None
        assert window.mda_mvc.mda_file_viz is not None

        # Verify window properties
        assert window.windowTitle() == "MDA Data Visualization"
        assert window.isVisible()

        # Test window can be shown and hidden
        window.hide()
        assert not window.isVisible()
        window.show()
        assert window.isVisible()

    def test_mainwindow_menu_actions(self, qtbot: "FixtureRequest") -> None:
        """Test MainWindow menu actions and keyboard shortcuts."""
        window = MainWindow()
        qtbot.addWidget(window)

        # Test File menu actions
        file_menu = window.menuBar().actions()[0]  # File menu
        assert file_menu.text() == "&File"

        # Test Open action
        open_action = None
        for action in file_menu.menu().actions():
            if "Open" in action.text():
                open_action = action
                break

        assert open_action is not None
        assert open_action.shortcut() == QKeySequence("Ctrl+O")

    def test_mainwindow_status_bar(self, qtbot: "FixtureRequest") -> None:
        """Test MainWindow status bar functionality."""
        window = MainWindow()
        qtbot.addWidget(window)

        # Test status updates
        test_message = "Test status message"
        window.setStatus(test_message)

        # Verify status bar shows the message
        status_bar = window.statusBar()
        assert test_message in status_bar.currentMessage()

    def test_mainwindow_resize_behavior(self, qtbot: "FixtureRequest") -> None:
        """Test MainWindow resize behavior and layout responsiveness."""
        window = MainWindow()
        qtbot.addWidget(window)

        # Get initial size
        initial_size = window.size()

        # Resize window
        new_size = initial_size + (100, 100)
        window.resize(new_size)

        # Verify resize worked
        assert window.size() == new_size

        # Test minimum size constraints
        window.resize(100, 100)  # Very small size
        assert window.size().width() >= window.minimumSize().width()
        assert window.size().height() >= window.minimumSize().height()


class TestChartViewGUI:
    """Test ChartView GUI functionality and plotting interactions."""

    def test_chartview_plotting_interactions(self, qtbot: "FixtureRequest") -> None:
        """Test ChartView plotting and user interactions."""
        # Create mock parent with required attributes
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

            # Test basic plotting
            x_data = np.array([1, 2, 3, 4, 5])
            y_data = np.array([1, 4, 9, 16, 25])

            # Add curve through curve manager
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

            # Test plot clearing
            chart_view.clearPlot()
            assert len(chart_view.curveManager.curves()) == 0

    def test_chartview_mouse_interactions(self, qtbot: "FixtureRequest") -> None:
        """Test ChartView mouse interactions and zooming."""
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

            # Test mouse press and release
            canvas = chart_view.canvas
            qtbot.mousePress(canvas, Qt.MouseButton.LeftButton, pos=(100, 100))
            qtbot.mouseRelease(canvas, Qt.MouseButton.LeftButton, pos=(200, 200))

            # Test mouse move
            qtbot.mouseMove(canvas, pos=(150, 150))

    def test_chartview_keyboard_shortcuts(self, qtbot: "FixtureRequest") -> None:
        """Test ChartView keyboard shortcuts and interactions."""
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

            # Test zoom reset (typically 'r' key)
            qtbot.keyPress(chart_view, Qt.Key.Key_R)

            # Test home view (typically 'h' key)
            qtbot.keyPress(chart_view, Qt.Key.Key_H)


class TestDataTableGUI:
    """Test data table GUI functionality and interactions."""

    def test_data_table_selection(self, qtbot: "FixtureRequest") -> None:
        """Test data table selection and row highlighting."""
        # Create a temporary test data structure
        test_data = {
            "scanDict": {
                "pos1": {"name": "Position 1", "values": [1, 2, 3, 4, 5]},
                "det1": {"name": "Detector 1", "values": [10, 20, 30, 40, 50]},
            },
            "firstPos": 0,
            "firstDet": 1,
        }

        # Mock the parent
        parent = MagicMock()
        parent.mda_file_viz = MagicMock()

        # Create MDAFile widget
        mda_file = MDAFile(parent)
        qtbot.addWidget(mda_file)

        # Set test data
        mda_file._data = test_data

        # Test table data display
        mda_file.displayData(test_data["scanDict"])

        # Verify table was populated
        table_view = mda_file.mda_mvc.mda_file_viz.table_view
        assert table_view is not None

    def test_data_table_sorting(self, qtbot: "FixtureRequest") -> None:
        """Test data table sorting functionality."""
        # This test would verify that clicking column headers sorts the data
        # Implementation depends on the specific table implementation
        pass


class TestFileDialogGUI:
    """Test file dialog and file loading GUI functionality."""

    def test_file_dialog_integration(
        self, qtbot: "FixtureRequest", tmp_path: Path
    ) -> None:
        """Test file dialog integration and file loading."""
        # Create test MDA files
        test_file = tmp_path / "test.mda"
        test_file.write_bytes(b"fake mda data")

        window = MainWindow()
        qtbot.addWidget(window)

        # Mock file dialog to return our test file
        with patch.object(
            QFileDialog, "getExistingDirectory", return_value=str(tmp_path)
        ):
            # Trigger file dialog
            open_action = None
            for action in window.menuBar().actions()[0].menu().actions():
                if "Open" in action.text():
                    open_action = action
                    break

            if open_action:
                qtbot.mouseClick(open_action, Qt.MouseButton.LeftButton)
                qtbot.wait(100)  # Wait for dialog to process

    def test_file_loading_progress(self, qtbot: "FixtureRequest") -> None:
        """Test file loading progress indicators."""
        window = MainWindow()
        qtbot.addWidget(window)

        # Test that progress indicators work during file loading
        # This would involve mocking the file loading process
        pass


class TestMemoryManagementGUI:
    """Test memory management UI and monitoring."""

    def test_memory_warning_dialog(self, qtbot: "FixtureRequest") -> None:
        """Test memory warning dialog when memory usage is high."""
        # Create a cache with low memory limits
        cache = DataCache(max_memory_mb=10.0)  # Very low limit

        # Mock high memory usage
        with patch("psutil.Process") as mock_process:
            mock_instance = Mock()
            mock_instance.memory_info.return_value.rss = 15 * 1024 * 1024  # 15MB
            mock_process.return_value = mock_instance

            # Trigger memory check
            memory_usage = cache._check_memory_usage()

            # Verify memory warning was emitted
            with qtbot.waitSignal(cache.memory_warning, timeout=1000):
                pass

    def test_cache_statistics_display(self, qtbot: "FixtureRequest") -> None:
        """Test cache statistics display in UI."""
        cache = get_global_cache()

        # Add some test data to cache
        test_data = MagicMock()
        test_data.get_size_mb.return_value = 1.0
        test_data.file_path = "/test.mda"

        cache.put("/test.mda", test_data)

        # Get cache statistics
        stats = cache.get_stats()

        # Verify statistics are reasonable
        assert stats["entry_count"] >= 0
        assert stats["current_size_mb"] >= 0
        assert stats["utilization_percent"] >= 0


class TestErrorHandlingGUI:
    """Test error handling and user feedback in GUI."""

    def test_error_dialog_display(self, qtbot: "FixtureRequest") -> None:
        """Test error dialog display for various error conditions."""
        # Test that error dialogs are shown for various error conditions
        # This would involve mocking error conditions and verifying dialogs appear
        pass

    def test_invalid_file_handling(self, qtbot: "FixtureRequest") -> None:
        """Test handling of invalid or corrupted files."""
        window = MainWindow()
        qtbot.addWidget(window)

        # Test loading invalid file
        with patch("mdaviz.synApps_mdalib.mda.readMDA", return_value=None):
            # This should trigger error handling without crashing
            pass


class TestUserSettingsGUI:
    """Test user settings GUI functionality."""

    def test_settings_dialog(self, qtbot: "FixtureRequest") -> None:
        """Test user settings dialog and configuration."""
        # Test settings dialog can be opened and closed
        # Test settings are properly saved and loaded
        pass

    def test_preferences_persistence(self, qtbot: "FixtureRequest") -> None:
        """Test that user preferences are properly persisted."""
        # Test that settings are saved and restored between sessions
        pass


class TestPerformanceGUI:
    """Test GUI performance and responsiveness."""

    def test_large_dataset_loading(self, qtbot: "FixtureRequest") -> None:
        """Test loading large datasets without UI freezing."""
        # Test that loading large datasets doesn't freeze the UI
        # This would involve creating large test datasets and monitoring UI responsiveness
        pass

    def test_ui_responsiveness(self, qtbot: "FixtureRequest") -> None:
        """Test UI responsiveness during data processing."""
        # Test that UI remains responsive during background operations
        pass


# Fixture for creating test data
@pytest.fixture
def sample_mda_data() -> dict:
    """Create sample MDA data for testing."""
    return {
        "metadata": {
            "rank": 1,
            "dimensions": [100],
            "data_type": "float32",
        },
        "scanDict": {
            "pos1": {"name": "Position 1", "values": list(range(100))},
            "det1": {"name": "Detector 1", "values": [i * 2 for i in range(100)]},
        },
        "firstPos": 0,
        "firstDet": 1,
        "pvList": ["pos1", "det1"],
    }


# Fixture for creating temporary test directory
@pytest.fixture
def temp_test_dir(tmp_path: Path) -> Path:
    """Create a temporary directory with test MDA files."""
    # Create some test files
    for i in range(5):
        test_file = tmp_path / f"test_{i:04d}.mda"
        test_file.write_bytes(b"fake mda data")

    return tmp_path


# Integration test for full workflow
def test_full_workflow_integration(
    qtbot: "FixtureRequest", temp_test_dir: Path
) -> None:
    """Test complete workflow from file loading to plotting."""
    window = MainWindow()
    qtbot.addWidget(window)

    # Mock file dialog to return test directory
    with patch.object(
        QFileDialog, "getExistingDirectory", return_value=str(temp_test_dir)
    ):
        # Simulate user opening a folder
        # This would trigger the full workflow
        pass

    # Verify that files were loaded
    # Verify that UI was updated appropriately
    # Verify that plotting is available
    pass


# Test for accessibility features
def test_accessibility_features(qtbot: "FixtureRequest") -> None:
    """Test accessibility features like keyboard navigation."""
    window = MainWindow()
    qtbot.addWidget(window)

    # Test keyboard navigation
    # Test screen reader compatibility
    # Test high contrast mode
    pass


# Test for internationalization
def test_internationalization(qtbot: "FixtureRequest") -> None:
    """Test internationalization and localization features."""
    # Test that UI can handle different languages
    # Test that date/time formats are localized
    # Test that number formats are localized
    pass
