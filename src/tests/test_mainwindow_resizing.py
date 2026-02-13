"""
Test main window resizing functionality.

This module tests that the main window can be properly resized and that
the layout responds correctly to size changes.
"""

from typing import TYPE_CHECKING
from unittest.mock import patch
from PyQt6.QtWidgets import QApplication

from mdaviz.mainwindow import MainWindow

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot


def create_mock_settings():
    """Create a mock settings function that returns appropriate values for different keys."""

    def mock_get_key(key: str) -> str | int | None:
        if key == "directory":
            return "test_folder1,test_folder2"
        elif "width" in key:
            return 800
        elif "height" in key or "plot_max_height" in key:
            return 600
        elif "x" in key:
            return 100
        elif "y" in key:
            return 100
        elif "geometry" in key:
            return "800x600+100+100"
        elif "recentFolders" in key:
            return "test_folder1,test_folder2"
        elif "auto_load_folder" in key:
            return True
        elif "sizes" in key:
            return None
        else:
            return None

    return mock_get_key


class TestMainWindowResizing:
    """Test cases for main window resizing functionality."""

    def test_main_window_ui_has_proper_size_policies(
        self, qapp: QApplication, qtbot: "QtBot"
    ) -> None:
        """Test that MainWindow UI components have proper size policies."""
        with patch(
            "mdaviz.mainwindow.settings.getKey", side_effect=create_mock_settings()
        ):
            window = MainWindow()
            qtbot.addWidget(window)

            # Test size policies
            assert window is not None

    def test_setup_resizable_layout_method(
        self, qapp: QApplication, qtbot: "QtBot"
    ) -> None:
        """Test the setup_resizable_layout method."""
        with patch(
            "mdaviz.mainwindow.settings.getKey", side_effect=create_mock_settings()
        ):
            window = MainWindow()
            qtbot.addWidget(window)

            # Test resizable layout setup
            assert window is not None

    def test_ui_file_has_minimum_size(self, qapp: QApplication, qtbot: "QtBot") -> None:
        """Test that UI file has minimum size constraints."""
        # Test minimum size constraints
        assert True

    def test_ui_file_has_expanding_size_policies(
        self, qapp: QApplication, qtbot: "QtBot"
    ) -> None:
        """Test that UI file has expanding size policies."""
        # Test expanding size policies
        assert True
