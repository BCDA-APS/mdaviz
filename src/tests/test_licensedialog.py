"""Tests for LicenseDialog."""

import pathlib
from typing import TYPE_CHECKING
from unittest.mock import mock_open, patch

import pytest
from PyQt6.QtWidgets import QApplication, QMainWindow

from mdaviz.licensedialog import LicenseDialog

if TYPE_CHECKING:
    from _pytest.fixtures import FixtureRequest
    from pytest_mock.plugin import MockerFixture


class TestLicenseDialog:
    """Test suite for LicenseDialog class."""

    @pytest.fixture
    def parent_widget(self, qtbot) -> QMainWindow:
        """Create a parent widget for testing."""
        parent = QMainWindow()
        qtbot.addWidget(parent)
        return parent

    @patch('mdaviz.utils.myLoadUi')
    @patch('builtins.open', new_callable=mock_open, read_data="Test License Content")
    def test_init_and_setup(self, mock_file_open, mock_load_ui, parent_widget, qtbot, mocker) -> None:
        """Test initialization and setup of LicenseDialog."""
        # Mock the license widget that gets created by the UI file
        mock_license_widget = mocker.Mock()
        
        def mock_load_ui_side_effect(ui_file, baseinstance=None):
            # Simulate what myLoadUi does - adds UI elements to the instance
            baseinstance.license = mock_license_widget
            
        mock_load_ui.side_effect = mock_load_ui_side_effect
        
        dialog = LicenseDialog(parent_widget)
        qtbot.addWidget(dialog)
        
        # Verify parent is set correctly
        assert dialog.parent == parent_widget
        
        # Verify UI loading was called
        mock_load_ui.assert_called_once()
        
        # Verify modal state
        assert dialog.isModal() is True
        
        # Verify file was opened and content was set
        mock_file_open.assert_called_once()
        
        # Verify the LICENSE.txt path construction
        current_file = pathlib.Path(__file__)
        project_root = current_file.parent.parent.parent
        expected_license_path = project_root / "LICENSE.txt"
        
        # Check that open was called with correct path
        mock_file_open.assert_called_with(expected_license_path, "r")
        
        # Verify license text was set
        mock_license_widget.setText.assert_called_with("Test License Content")

    @patch('mdaviz.utils.myLoadUi')
    def test_license_file_path_construction(self, mock_load_ui, parent_widget, qtbot, mocker) -> None:
        """Test that license file path is constructed correctly."""
        mock_license_widget = mocker.Mock()
        
        def mock_load_ui_side_effect(ui_file, baseinstance=None):
            baseinstance.license = mock_license_widget
            
        mock_load_ui.side_effect = mock_load_ui_side_effect
        
        with patch('builtins.open', mock_open(read_data="License Content")) as mock_file:
            dialog = LicenseDialog(parent_widget)
            qtbot.addWidget(dialog)
            
            # Verify the correct LICENSE.txt path is used
            current_file = pathlib.Path(__file__)
            project_root = current_file.parent.parent.parent
            expected_path = project_root / "LICENSE.txt"
            
            mock_file.assert_called_with(expected_path, "r")

    @patch('mdaviz.utils.myLoadUi')
    @patch('mdaviz.utils.getUiFileName')
    def test_ui_file_resolution(self, mock_get_ui_filename, mock_load_ui, parent_widget, qtbot) -> None:
        """Test that UI file name is resolved correctly."""
        mock_get_ui_filename.return_value = "test_ui_file.ui"
        
        with patch('builtins.open', mock_open(read_data="License Content")):
            dialog = LicenseDialog(parent_widget)
            qtbot.addWidget(dialog)
            
            # Verify getUiFileName was called with the module file
            mock_get_ui_filename.assert_called_once()
            
            # Verify myLoadUi was called with the resolved UI file
            mock_load_ui.assert_called_once_with("test_ui_file.ui", baseinstance=dialog)

    @patch('mdaviz.utils.myLoadUi')
    def test_license_text_setting(self, mock_load_ui, parent_widget, qtbot, mocker) -> None:
        """Test that license text is set correctly."""
        # Mock the license widget
        mock_license_widget = mocker.Mock()
        
        with patch('builtins.open', mock_open(read_data="Sample License Text")):
            dialog = LicenseDialog(parent_widget)
            qtbot.addWidget(dialog)
            
            # Set up the mock license widget after initialization
            dialog.license = mock_license_widget
            
            # Call setup again to test the license text setting
            dialog.setup()
            
            # Verify setText was called with the license content
            mock_license_widget.setText.assert_called_with("Sample License Text")

    @patch('mdaviz.utils.myLoadUi')
    def test_file_read_error_handling(self, mock_load_ui, parent_widget, qtbot, mocker) -> None:
        """Test handling of file read errors."""
        # Mock open to raise an exception
        with patch('builtins.open', side_effect=FileNotFoundError("License file not found")):
            with pytest.raises(FileNotFoundError):
                dialog = LicenseDialog(parent_widget)

    @patch('mdaviz.utils.myLoadUi')
    def test_inheritance_and_modal_setup(self, mock_load_ui, parent_widget, qtbot, mocker) -> None:
        """Test that dialog inherits correctly and sets up modal behavior."""
        mock_license_widget = mocker.Mock()
        
        def mock_load_ui_side_effect(ui_file, baseinstance=None):
            baseinstance.license = mock_license_widget
            
        mock_load_ui.side_effect = mock_load_ui_side_effect
        
        with patch('builtins.open', mock_open(read_data="License Content")):
            dialog = LicenseDialog(parent_widget)
            qtbot.addWidget(dialog)
            
            # Verify it's a QDialog
            from PyQt6.QtWidgets import QDialog
            assert isinstance(dialog, QDialog)
            
            # Verify modal setup
            assert dialog.isModal() is True
            
            # Verify parent relationship
            assert dialog.parent() == parent_widget

    @patch('mdaviz.utils.myLoadUi')
    def test_multiple_instantiation(self, mock_load_ui, parent_widget, qtbot) -> None:
        """Test that multiple instances can be created."""
        with patch('builtins.open', mock_open(read_data="License Content")):
            dialog1 = LicenseDialog(parent_widget)
            dialog2 = LicenseDialog(parent_widget)
            
            qtbot.addWidget(dialog1)
            qtbot.addWidget(dialog2)
            
            # Both should be separate instances
            assert dialog1 is not dialog2
            assert dialog1.parent == parent_widget
            assert dialog2.parent == parent_widget

    @patch('mdaviz.utils.myLoadUi')
    def test_ui_file_attribute(self, mock_load_ui, parent_widget, qtbot) -> None:
        """Test that ui_file class attribute is set correctly."""
        with patch('mdaviz.utils.myLoadUi'):
            with patch('mdaviz.utils.getUiFileName', return_value="licensedialog.ui"):
                with patch('builtins.open', mock_open(read_data="License Content")):
                    dialog = LicenseDialog(parent_widget)
                    qtbot.addWidget(dialog)
                    
                    # Check that ui_file attribute exists and is properly set
                    assert hasattr(LicenseDialog, 'ui_file') 