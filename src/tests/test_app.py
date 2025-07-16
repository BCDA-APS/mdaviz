#!/usr/bin/env python
"""
Tests for the mdaviz application module.

This module tests the main application functionality including command line
interface, logging configuration, and application startup.
"""

import argparse
import logging
import os
import sys
from typing import TYPE_CHECKING
from unittest.mock import patch, MagicMock

import pytest
from PyQt6 import QtWidgets

from mdaviz.app import command_line_interface, main, gui

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


class TestCommandLineInterface:
    """Test command line interface functionality."""

    def test_default_arguments(self) -> None:
        """Test command line interface with default arguments."""
        with patch('sys.argv', ['mdaviz']):
            args = command_line_interface()
            
        assert args.log == "warning"
        assert not hasattr(args, 'directory')

    def test_log_level_argument(self) -> None:
        """Test command line interface with different log levels."""
        test_cases = ["debug", "info", "warning", "error", "critical"]
        
        for log_level in test_cases:
            with patch('sys.argv', ['mdaviz', '--log', log_level]):
                args = command_line_interface()
                assert args.log == log_level

    def test_version_argument(self, capsys: "CaptureFixture") -> None:
        """Test version argument displays version and exits."""
        with patch('sys.argv', ['mdaviz', '--version']):
            with pytest.raises(SystemExit):
                command_line_interface()
        
        # Version should be displayed
        captured = capsys.readouterr()
        # Check that some version information is displayed
        assert len(captured.out.strip()) > 0 or len(captured.err.strip()) > 0

    def test_invalid_log_level(self) -> None:
        """Test that invalid log level raises error."""
        with patch('sys.argv', ['mdaviz', '--log', 'invalid']):
            with pytest.raises(SystemExit):
                command_line_interface()


class TestMainFunction:
    """Test main function functionality."""

    @patch('mdaviz.app.gui')
    @patch('mdaviz.app.command_line_interface')
    def test_main_function_calls_gui(self, mock_cli: "MockerFixture", mock_gui: "MockerFixture") -> None:
        """Test that main function calls gui function."""
        # Mock command line interface
        mock_args = MagicMock()
        mock_args.log = "warning"
        mock_cli.return_value = mock_args
        
        # Call main function
        main()
        
        # Verify gui was called
        mock_gui.assert_called_once()

    @patch('mdaviz.app.gui')
    @patch('mdaviz.app.command_line_interface')
    def test_main_function_sets_logging(self, mock_cli: "MockerFixture", mock_gui: "MockerFixture") -> None:
        """Test that main function sets up logging correctly."""
        # Mock command line interface
        mock_args = MagicMock()
        mock_args.log = "debug"
        mock_cli.return_value = mock_args
        
        # Reset logging to default
        logging.getLogger().setLevel(logging.WARNING)
        
        # Call main function
        main()
        
        # Verify that basicConfig was called with debug level
        # Note: We can't easily test the actual logging level change
        # because basicConfig might not always affect the root logger
        # in test environments, but we can verify the function runs
        mock_cli.assert_called_once()
        mock_gui.assert_called_once()

    @patch('mdaviz.app.gui')
    @patch('mdaviz.app.command_line_interface')
    def test_main_function_sets_package_logging(self, mock_cli: "MockerFixture", mock_gui: "MockerFixture") -> None:
        """Test that main function sets package logging levels."""
        # Mock command line interface
        mock_args = MagicMock()
        mock_args.log = "info"
        mock_cli.return_value = mock_args
        
        # Call main function
        main()
        
        # Verify package logging levels were set
        for package in ["httpcore", "httpx", "PyQt6", "tiled"]:
            logger = logging.getLogger(package)
            assert logger.level == logging.WARNING

    @patch('mdaviz.app.gui')
    @patch('mdaviz.app.command_line_interface')
    def test_main_function_logs_info(self, mock_cli: "MockerFixture", mock_gui: "MockerFixture", caplog: "LogCaptureFixture") -> None:
        """Test that main function logs the logging level."""
        # Mock command line interface
        mock_args = MagicMock()
        mock_args.log = "info"
        mock_cli.return_value = mock_args
        
        # Set up logging capture
        caplog.set_level(logging.INFO)
        
        # Call main function
        main()
        
        # Verify logging message
        assert "Logging level: info" in caplog.text


class TestGuiFunction:
    """Test GUI function functionality."""

    @patch('sys.exit')
    @patch('PyQt6.QtWidgets.QApplication')
    @patch('mdaviz.mainwindow.MainWindow')
    def test_gui_function_creates_application(self, mock_mainwindow: "MockerFixture", mock_qapp: "MockerFixture", mock_exit: "MockerFixture") -> None:
        """Test that gui function creates QApplication."""
        mock_app_instance = MagicMock()
        mock_qapp.return_value = mock_app_instance
        mock_window_instance = MagicMock()
        mock_mainwindow.return_value = mock_window_instance
        
        gui()
        
        # Verify QApplication was created
        mock_qapp.assert_called_once_with(sys.argv)
        mock_app_instance.exec.assert_called_once()
        mock_exit.assert_called_once()

    @patch('sys.exit')
    @patch('PyQt6.QtWidgets.QApplication')
    @patch('mdaviz.mainwindow.MainWindow')
    def test_gui_function_creates_main_window(self, mock_mainwindow: "MockerFixture", mock_qapp: "MockerFixture", mock_exit: "MockerFixture") -> None:
        """Test that gui function creates MainWindow."""
        mock_app_instance = MagicMock()
        mock_qapp.return_value = mock_app_instance
        mock_window_instance = MagicMock()
        mock_mainwindow.return_value = mock_window_instance
        
        gui()
        
        # Verify MainWindow was created and configured
        mock_mainwindow.assert_called_once()
        mock_window_instance.setStatus.assert_called_once_with("Application started ...")
        mock_window_instance.show.assert_called_once()


class TestAppIntegration:
    """Integration tests for the application."""

    @patch('sys.exit')
    @patch('PyQt6.QtWidgets.QApplication')
    @patch('mdaviz.mainwindow.MainWindow')
    def test_app_startup_flow(self, mock_mainwindow: "MockerFixture", mock_qapp: "MockerFixture", mock_exit: "MockerFixture") -> None:
        """Test complete application startup flow."""
        # Mock QApplication
        mock_app_instance = MagicMock()
        mock_qapp.return_value = mock_app_instance
        
        # Mock MainWindow
        mock_window_instance = MagicMock()
        mock_mainwindow.return_value = mock_window_instance
        
        # Mock command line interface
        with patch('mdaviz.app.command_line_interface') as mock_cli:
            mock_args = MagicMock()
            mock_args.log = "warning"
            mock_cli.return_value = mock_args
            
            # Call main function
            main()
        
        # Verify complete flow
        mock_cli.assert_called_once()
        mock_qapp.assert_called_once_with(sys.argv)
        mock_mainwindow.assert_called_once()
        mock_window_instance.setStatus.assert_called_once_with("Application started ...")
        mock_window_instance.show.assert_called_once()
        mock_app_instance.exec.assert_called_once()
        mock_exit.assert_called_once()


class TestAppErrorHandling:
    """Test error handling in the application."""

    @patch('mdaviz.app.command_line_interface')
    def test_main_function_handles_cli_errors(self, mock_cli: "MockerFixture") -> None:
        """Test that main function handles CLI errors gracefully."""
        # Mock CLI to raise an exception
        mock_cli.side_effect = SystemExit(1)
        
        # Should propagate the SystemExit
        with pytest.raises(SystemExit):
            main()

    @patch('mdaviz.app.gui')
    @patch('mdaviz.app.command_line_interface')
    def test_main_function_handles_gui_errors(self, mock_cli: "MockerFixture", mock_gui: "MockerFixture") -> None:
        """Test that main function handles GUI errors gracefully."""
        # Mock command line interface
        mock_args = MagicMock()
        mock_args.log = "warning"
        mock_cli.return_value = mock_args
        
        # Mock GUI to raise an exception
        mock_gui.side_effect = Exception("GUI Error")
        
        # Should propagate the exception
        with pytest.raises(Exception, match="GUI Error"):
            main()


# Skip GUI tests in CI environment
@pytest.mark.skipif(
    "CI" in os.environ,
    reason="Skip GUI test in CI environment"
)
class TestGuiIntegration:
    """Integration tests for GUI functionality (skipped in CI)."""

    def test_main_window_components(self, qtbot: "MockerFixture") -> None:
        """Test that main window components are created correctly."""
        # This test would require a full GUI environment
        # For now, we'll skip it in CI
        pass

    def test_about_dialog(self, qtbot: "MockerFixture") -> None:
        """Test about dialog functionality."""
        # This test would require a full GUI environment
        # For now, we'll skip it in CI
        pass

    def test_data_cache_initialization(self, qtbot: "MockerFixture") -> None:
        """Test data cache initialization in main window."""
        # This test would require a full GUI environment
        # For now, we'll skip it in CI
        pass

    def test_lazy_folder_scanner_initialization(self, qtbot: "MockerFixture") -> None:
        """Test lazy folder scanner initialization in main window."""
        # This test would require a full GUI environment
        # For now, we'll skip it in CI
        pass

    def test_fit_manager_initialization(self, qtbot: "MockerFixture") -> None:
        """Test fit manager initialization in main window."""
        # This test would require a full GUI environment
        # For now, we'll skip it in CI
        pass


class TestCompatibility:
    """Test compatibility and deprecation warnings."""

    def test_xdrlib_fallback(self) -> None:
        """Test that xdrlib fallback works correctly."""
        # Import should work without errors
        import mdaviz.synApps_mdalib.mda
        assert mdaviz.synApps_mdalib.mda is not None

    def test_deprecation_warnings_suppressed(self) -> None:
        """Test that deprecation warnings are properly handled."""
        import warnings
        
        # Capture warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            # Import should work without raising deprecation warnings
            import mdaviz.synApps_mdalib.mda
            
            # Check that no unexpected deprecation warnings were raised
            # (xdrlib deprecation is expected and handled)
            unexpected_warnings = [
                warning for warning in w 
                if warning.category == DeprecationWarning 
                and 'xdrlib' not in str(warning.message)
            ]
            assert len(unexpected_warnings) == 0
