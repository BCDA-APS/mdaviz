"""
Tests for auto-load functionality.

This module tests the auto-load feature that automatically loads the first
valid folder from recent folders when the application starts.

.. autosummary::

    ~test_auto_load_setting_default
    ~test_auto_load_setting_toggle
    ~test_auto_load_first_folder_with_valid_folder
    ~test_auto_load_first_folder_with_invalid_folder
    ~test_auto_load_first_folder_with_no_recent_folders
"""

from pathlib import Path
from unittest.mock import Mock, patch

from mdaviz.mainwindow import MainWindow
from mdaviz.user_settings import settings


def test_auto_load_setting_default():
    """Test that auto-load setting defaults to True."""
    # Reset the setting to ensure clean state
    settings.setKey("auto_load_folder", None)

    # Create a mock main window to test the setting
    with patch("mdaviz.mainwindow.MainWindow.__init__", return_value=None):
        main_window = MainWindow()
        main_window.settings = settings

        # Test that the setting defaults to True
        assert main_window.get_auto_load_setting() is True


def test_auto_load_setting_toggle():
    """Test that auto-load setting can be toggled."""
    # Reset the setting to ensure clean state
    settings.setKey("auto_load_folder", True)

    # Create a mock main window to test the setting
    with patch("mdaviz.mainwindow.MainWindow.__init__", return_value=None):
        main_window = MainWindow()
        main_window.settings = settings
        main_window.setStatus = Mock()

        # Test toggling from True to False
        result = main_window.toggle_auto_load()
        assert result is False
        assert main_window.get_auto_load_setting() is False

        # Test toggling from False to True
        result = main_window.toggle_auto_load()
        assert result is True
        assert main_window.get_auto_load_setting() is True


def test_auto_load_first_folder_with_valid_folder():
    """Test auto-load with a valid folder in recent folders."""
    # Set up a valid folder path
    test_folder = Path.home()  # Use home directory as a valid folder

    # Mock the recent folders to include our test folder
    with patch(
        "mdaviz.mainwindow.MainWindow._getRecentFolders",
        return_value=[str(test_folder)],
    ):
        with patch("mdaviz.mainwindow.MainWindow.__init__", return_value=None):
            main_window = MainWindow()
            main_window.settings = settings
            main_window.setStatus = Mock()

            # Mock the lazy_scanner instance attribute
            mock_scanner = Mock()
            main_window.lazy_scanner = mock_scanner

            # Set auto-load to enabled
            settings.setKey("auto_load_folder", True)

            # Call the auto-load method
            main_window._auto_load_first_folder()

            # Verify that the scanner was called with the correct folder
            mock_scanner.scan_folder_async.assert_called_once_with(test_folder)


def test_auto_load_first_folder_with_invalid_folder():
    """Test auto-load with an invalid folder in recent folders."""
    # Set up an invalid folder path
    invalid_folder = "/path/that/does/not/exist"

    # Mock the recent folders to include our invalid folder
    with patch(
        "mdaviz.mainwindow.MainWindow._getRecentFolders", return_value=[invalid_folder]
    ):
        with patch("mdaviz.mainwindow.MainWindow.__init__", return_value=None):
            main_window = MainWindow()
            main_window.settings = settings
            main_window.setStatus = Mock()

            # Set auto-load to enabled
            settings.setKey("auto_load_folder", True)

            # Call the auto-load method
            main_window._auto_load_first_folder()

            # Verify that setStatus was called with the error message
            main_window.setStatus.assert_called_with(
                f"Auto-load failed: {invalid_folder} does not exist or is not a directory"
            )


def test_auto_load_first_folder_with_no_recent_folders():
    """Test auto-load when there are no recent folders."""
    # Mock the recent folders to be empty
    with patch("mdaviz.mainwindow.MainWindow._getRecentFolders", return_value=[]):
        with patch("mdaviz.mainwindow.MainWindow.__init__", return_value=None):
            main_window = MainWindow()
            main_window.settings = settings
            main_window.setStatus = Mock()

            # Set auto-load to enabled
            settings.setKey("auto_load_folder", True)

            # Call the auto-load method
            main_window._auto_load_first_folder()

            # Verify that setStatus was called with the appropriate message
            main_window.setStatus.assert_called_with(
                "No recent folders available for auto-loading"
            )


def test_auto_load_disabled():
    """Test that auto-load is skipped when disabled."""
    with patch(
        "mdaviz.mainwindow.MainWindow._getRecentFolders", return_value=["/some/folder"]
    ):
        with patch("mdaviz.mainwindow.MainWindow.__init__", return_value=None):
            main_window = MainWindow()
            main_window.settings = settings
            main_window.setStatus = Mock()

            # Set auto-load to disabled
            settings.setKey("auto_load_folder", False)

            # Call the auto-load method
            main_window._auto_load_first_folder()

            # Verify that setStatus was called with the disabled message
            main_window.setStatus.assert_called_with(
                "Auto-loading disabled by user preference"
            )
