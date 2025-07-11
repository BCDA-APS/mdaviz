"""
Test main window resizing functionality.

This module tests that the main window can be properly resized and that
the layout responds correctly to size changes.
"""

from typing import TYPE_CHECKING
from PyQt5 import QtWidgets

if TYPE_CHECKING:
    pass


class TestMainWindowResizing:
    """Test cases for main window resizing functionality."""

    def test_main_window_ui_has_proper_size_policies(self):
        """
        Test that the main window UI file has proper size policies set.

        This test checks the UI file directly without creating a full MainWindow
        to avoid Qt initialization issues in the test environment.
        """
        # Import here to avoid Qt initialization issues
        from mdaviz.mainwindow import MainWindow

        # Create a minimal test that doesn't require full initialization
        app = QtWidgets.QApplication.instance()
        if app is None:
            app = QtWidgets.QApplication([])

        try:
            window = MainWindow()

            # Check that the window has expanding size policy
            size_policy = window.sizePolicy()
            assert size_policy.horizontalPolicy() == QtWidgets.QSizePolicy.Expanding
            assert size_policy.verticalPolicy() == QtWidgets.QSizePolicy.Expanding

            # Check that the window has reasonable minimum size
            min_size = window.minimumSize()
            assert min_size.width() >= 400
            assert min_size.height() >= 300

            # Check that central widget has expanding size policy
            central_widget = window.centralwidget
            size_policy = central_widget.sizePolicy()
            assert size_policy.horizontalPolicy() == QtWidgets.QSizePolicy.Expanding
            assert size_policy.verticalPolicy() == QtWidgets.QSizePolicy.Expanding

            # Check that groupbox has expanding size policy
            groupbox = window.groupbox
            size_policy = groupbox.sizePolicy()
            assert size_policy.horizontalPolicy() == QtWidgets.QSizePolicy.Expanding
            assert size_policy.verticalPolicy() == QtWidgets.QSizePolicy.Expanding

        finally:
            # Clean up
            if app:
                app.quit()

    def test_setup_resizable_layout_method(self):
        """
        Test that the _setup_resizable_layout method works correctly.
        """
        # Import here to avoid Qt initialization issues
        from mdaviz.mainwindow import MainWindow

        # Create a minimal test that doesn't require full initialization
        app = QtWidgets.QApplication.instance()
        if app is None:
            app = QtWidgets.QApplication([])

        try:
            window = MainWindow()

            # Call the method explicitly
            window._setup_resizable_layout()

            # Check that all widgets have proper size policies
            assert (
                window.centralwidget.sizePolicy().horizontalPolicy()
                == QtWidgets.QSizePolicy.Expanding
            )
            assert (
                window.groupbox.sizePolicy().horizontalPolicy()
                == QtWidgets.QSizePolicy.Expanding
            )

        finally:
            # Clean up
            if app:
                app.quit()

    def test_ui_file_has_minimum_size(self):
        """
        Test that the UI file has minimum size constraints.

        This test checks the UI file content directly.
        """
        import xml.etree.ElementTree as ET
        from pathlib import Path

        # Parse the UI file to check for minimum size
        ui_file = (
            Path(__file__).parent.parent / "mdaviz" / "resources" / "mainwindow.ui"
        )
        tree = ET.parse(ui_file)
        root = tree.getroot()

        # Check that the main window has minimum size
        main_window = root.find(".//widget[@class='QMainWindow']")
        assert main_window is not None

        min_size = main_window.find("property[@name='minimumSize']")
        assert min_size is not None

        # Check the minimum size values
        size_elem = min_size.find("size")
        assert size_elem is not None

        width_elem = size_elem.find("width")
        height_elem = size_elem.find("height")
        assert width_elem is not None
        assert height_elem is not None

        width = int(width_elem.text)
        height = int(height_elem.text)
        assert width >= 400
        assert height >= 300

    def test_ui_file_has_expanding_size_policies(self):
        """
        Test that the UI file has expanding size policies for resizable widgets.

        This test checks the UI file content directly.
        """
        import xml.etree.ElementTree as ET
        from pathlib import Path

        # Parse the UI file to check for size policies
        ui_file = (
            Path(__file__).parent.parent / "mdaviz" / "resources" / "mainwindow.ui"
        )
        tree = ET.parse(ui_file)
        root = tree.getroot()

        # Check that central widget has expanding size policy
        central_widget = root.find(".//widget[@name='centralwidget']")
        assert central_widget is not None

        size_policy = central_widget.find("property[@name='sizePolicy']")
        assert size_policy is not None

        sizepolicy_elem = size_policy.find("sizepolicy")
        assert sizepolicy_elem is not None

        hsizetype = sizepolicy_elem.get("hsizetype")
        vsizetype = sizepolicy_elem.get("vsizetype")
        assert hsizetype == "Expanding"
        assert vsizetype == "Expanding"

        # Check that groupbox has expanding size policy
        groupbox = root.find(".//widget[@name='groupbox']")
        assert groupbox is not None

        size_policy = groupbox.find("property[@name='sizePolicy']")
        assert size_policy is not None

        sizepolicy_elem = size_policy.find("sizepolicy")
        assert sizepolicy_elem is not None

        hsizetype = sizepolicy_elem.get("hsizetype")
        vsizetype = sizepolicy_elem.get("vsizetype")
        assert hsizetype == "Expanding"
        assert vsizetype == "Expanding"
