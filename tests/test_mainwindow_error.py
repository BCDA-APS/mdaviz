"""
Test to verify that the main window can be created without errors.

This test specifically addresses the AttributeError that was occurring when
trying to access mainTabWidget, fitDataTab, and fitDataText attributes that
didn't exist in the UI file.
"""

from typing import TYPE_CHECKING

import pytest
from PyQt5 import QtWidgets

from src.mdaviz.mainwindow import MainWindow
from src.mdaviz.user_settings import settings

if TYPE_CHECKING:
    from _pytest.fixtures import FixtureRequest


class TestMainWindowError:
    """Test class for main window error handling."""

    def test_main_window_creation_no_errors(self, qtbot):
        """
        Test that MainWindow can be created without AttributeError.
        
        This test verifies that the fix for the missing mainTabWidget,
        fitDataTab, and fitDataText attributes works correctly.
        """
        # Disable auto-loading to avoid folder scanning issues
        settings.setKey("auto_load_folder", False)
        
        # Create the main window - this should not raise an AttributeError
        main_window = MainWindow()
        
        # Verify the window was created successfully
        assert main_window is not None
        assert isinstance(main_window, MainWindow)
        
        # Verify that the tab widget and fit data components were created
        assert hasattr(main_window, 'mainTabWidget')
        assert hasattr(main_window, 'fitDataTab')
        assert hasattr(main_window, 'fitDataText')
        assert hasattr(main_window, 'fitDataLabel')
        
        # Verify the components are the correct types
        assert isinstance(main_window.mainTabWidget, QtWidgets.QTabWidget)
        assert isinstance(main_window.fitDataTab, QtWidgets.QWidget)
        assert isinstance(main_window.fitDataText, QtWidgets.QTextEdit)
        assert isinstance(main_window.fitDataLabel, QtWidgets.QLabel)
        
        # Verify the fit data tab is initially hidden
        assert not main_window.mainTabWidget.isTabVisible(0)
        
        # Clean up
        main_window.close()

    def test_fit_data_tab_functionality(self, qtbot):
        """
        Test that the fit data tab functionality works correctly.
        
        This test verifies that the fit data tab can be shown and
        updated with data.
        """
        # Disable auto-loading to avoid folder scanning issues
        settings.setKey("auto_load_folder", False)
        
        main_window = MainWindow()
        
        # Test showing the fit data tab
        main_window.showFitDataTab()
        assert main_window.mainTabWidget.isTabVisible(0)
        assert main_window.mainTabWidget.currentIndex() == 0
        
        # Test updating fit data
        test_data = "Test fit data\nParameter 1: 1.234\nParameter 2: 5.678"
        main_window.updateFitData(test_data)
        
        # Verify the data was set correctly
        assert main_window.fitDataText.toPlainText() == test_data
        assert main_window.fitDataLabel.text() == "Fit Data Available"
        
        # Clean up
        main_window.close()

    def test_main_window_resizable_layout(self, qtbot):
        """
        Test that the resizable layout setup works without errors.
        
        This test verifies that the _setup_resizable_layout method
        handles missing components gracefully.
        """
        # Disable auto-loading to avoid folder scanning issues
        settings.setKey("auto_load_folder", False)
        
        main_window = MainWindow()
        
        # Call the resizable layout setup - should not raise errors
        main_window._setup_resizable_layout()
        
        # Verify the window has proper size policies
        assert main_window.sizePolicy().horizontalPolicy() == QtWidgets.QSizePolicy.Expanding
        assert main_window.sizePolicy().verticalPolicy() == QtWidgets.QSizePolicy.Expanding
        
        # Clean up
        main_window.close() 