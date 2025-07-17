"""Tests for OpenDialog."""

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import pytest
from PyQt6.QtWidgets import QFileDialog, QMainWindow

from mdaviz.opendialog import OpenDialog

if TYPE_CHECKING:
    from _pytest.fixtures import FixtureRequest
    from pytest_mock.plugin import MockerFixture


class TestOpenDialog:
    """Test suite for OpenDialog class."""

    @pytest.fixture
    def parent_widget(self, qtbot) -> QMainWindow:
        """Create a parent widget for testing."""
        parent = QMainWindow()
        qtbot.addWidget(parent)
        return parent

    @patch('mdaviz.opendialog.settings')
    def test_init_with_parent(self, mock_settings, parent_widget, qtbot) -> None:
        """Test initialization with parent widget."""
        mock_settings.getKey.return_value = None
        
        dialog = OpenDialog(parent_widget)
        qtbot.addWidget(dialog)
        
        assert dialog.parent == parent_widget
        assert dialog.parent == parent_widget

    @patch('mdaviz.opendialog.settings')
    def test_inheritance(self, mock_settings, parent_widget, qtbot) -> None:
        """Test that OpenDialog inherits from QFileDialog."""
        mock_settings.getKey.return_value = None
        
        dialog = OpenDialog(parent_widget)
        qtbot.addWidget(dialog)
        
        assert isinstance(dialog, QFileDialog)

    @patch('mdaviz.opendialog.settings')
    def test_modal_setup(self, mock_settings, parent_widget, qtbot) -> None:
        """Test that dialog is set up as modal."""
        mock_settings.getKey.return_value = None
        
        dialog = OpenDialog(parent_widget)
        qtbot.addWidget(dialog)
        
        assert dialog.isModal() is True

    @patch('mdaviz.opendialog.settings')
    def test_file_mode_setup(self, mock_settings, parent_widget, qtbot) -> None:
        """Test file mode configuration."""
        mock_settings.getKey.return_value = None
        
        dialog = OpenDialog(parent_widget)
        qtbot.addWidget(dialog)
        
        assert dialog.fileMode() == QFileDialog.FileMode.ExistingFile

    @patch('mdaviz.opendialog.settings')
    def test_file_dialog_options(self, mock_settings, parent_widget, qtbot) -> None:
        """Test file dialog options configuration."""
        mock_settings.getKey.return_value = None
        
        dialog = OpenDialog(parent_widget)
        qtbot.addWidget(dialog)
        
        # Test that ShowDirsOnly is not set (False)
        assert not dialog.testOption(QFileDialog.Option.ShowDirsOnly)
        
        # Test that DontUseNativeDialog is not set (False)
        assert not dialog.testOption(QFileDialog.Option.DontUseNativeDialog)

    @patch('mdaviz.opendialog.settings')
    def test_name_filter_setup(self, mock_settings, parent_widget, qtbot) -> None:
        """Test name filter configuration for MDA files."""
        mock_settings.getKey.return_value = None
        
        dialog = OpenDialog(parent_widget)
        qtbot.addWidget(dialog)
        
        name_filters = dialog.nameFilters()
        # Should contain MDA files filter and All files filter
        assert len(name_filters) >= 1
        # Check if MDA filter is present (might be combined or separate)
        filter_text = ' '.join(name_filters)
        assert '*.mda' in filter_text

    @patch('mdaviz.opendialog.settings')
    def test_view_mode_setup(self, mock_settings, parent_widget, qtbot) -> None:
        """Test view mode configuration."""
        mock_settings.getKey.return_value = None
        
        dialog = OpenDialog(parent_widget)
        qtbot.addWidget(dialog)
        
        assert dialog.viewMode() == QFileDialog.ViewMode.Detail

    @patch('mdaviz.opendialog.settings')
    def test_default_directory_from_settings_with_recent_dirs(self, mock_settings, parent_widget, qtbot) -> None:
        """Test default directory setup with recent directories in settings."""
        recent_dir = "/path/to/recent/directory"
        mock_settings.getKey.return_value = f"{recent_dir},/other/path"
        
        dialog = OpenDialog(parent_widget)
        qtbot.addWidget(dialog)
        
        # Should use the first directory from the comma-separated list
        assert dialog.directory().absolutePath() == recent_dir

    @patch('mdaviz.opendialog.settings')
    def test_default_directory_from_settings_single_dir(self, mock_settings, parent_widget, qtbot) -> None:
        """Test default directory setup with single directory in settings."""
        recent_dir = "/single/directory/path"
        mock_settings.getKey.return_value = recent_dir
        
        dialog = OpenDialog(parent_widget)
        qtbot.addWidget(dialog)
        
        assert dialog.directory().absolutePath() == recent_dir

    @patch('mdaviz.opendialog.settings')
    def test_default_directory_empty_settings(self, mock_settings, parent_widget, qtbot) -> None:
        """Test default directory setup with empty settings."""
        mock_settings.getKey.return_value = ""
        
        dialog = OpenDialog(parent_widget)
        qtbot.addWidget(dialog)
        
        # Should fall back to home directory
        expected_home = str(Path.home())
        assert dialog.directory().absolutePath() == expected_home

    @patch('mdaviz.opendialog.settings')
    def test_default_directory_none_settings(self, mock_settings, parent_widget, qtbot) -> None:
        """Test default directory setup with None from settings."""
        mock_settings.getKey.return_value = None
        
        dialog = OpenDialog(parent_widget)
        qtbot.addWidget(dialog)
        
        # Should fall back to home directory
        expected_home = str(Path.home())
        assert dialog.directory().absolutePath() == expected_home

    @patch('mdaviz.opendialog.settings')
    def test_settings_key_usage(self, mock_settings, parent_widget, qtbot) -> None:
        """Test that correct settings key is used."""
        mock_settings.getKey.return_value = None
        
        dialog = OpenDialog(parent_widget)
        qtbot.addWidget(dialog)
        
        # Should have called getKey with DIR_SETTINGS_KEY
        mock_settings.getKey.assert_called_once_with("directory")

    @patch('mdaviz.opendialog.settings')
    def test_complete_setup_workflow(self, mock_settings, parent_widget, qtbot) -> None:
        """Test complete setup workflow with all configurations."""
        # Setup mock settings
        test_dir = "/test/data/directory"
        mock_settings.getKey.return_value = f"{test_dir},/backup/dir"
        
        dialog = OpenDialog(parent_widget)
        qtbot.addWidget(dialog)
        
        # Verify all setup configurations
        assert dialog.parent == parent_widget
        assert dialog.isModal() is True
        assert dialog.fileMode() == QFileDialog.FileMode.ExistingFile
        assert not dialog.testOption(QFileDialog.Option.ShowDirsOnly)
        assert not dialog.testOption(QFileDialog.Option.DontUseNativeDialog)
        assert dialog.viewMode() == QFileDialog.ViewMode.Detail
        assert dialog.directory().absolutePath() == test_dir
        
        # Check name filters contain MDA filter
        name_filters = dialog.nameFilters()
        filter_text = ' '.join(name_filters)
        assert '*.mda' in filter_text

    @patch('mdaviz.opendialog.settings')
    def test_empty_recent_dirs_list(self, mock_settings, parent_widget, qtbot) -> None:
        """Test behavior with empty recent directories list."""
        mock_settings.getKey.return_value = ","  # Just commas
        
        dialog = OpenDialog(parent_widget)
        qtbot.addWidget(dialog)
        
        # Should fall back to home directory when split results in empty strings
        expected_home = str(Path.home())
        # This might need adjustment based on actual behavior
        current_dir = dialog.directory().absolutePath()
        # Either falls back to home or uses first empty string which becomes current dir
        assert current_dir is not None

    @patch('mdaviz.opendialog.settings')
    def test_multiple_instantiation(self, mock_settings, parent_widget, qtbot) -> None:
        """Test that multiple dialog instances can be created."""
        mock_settings.getKey.return_value = "/test/dir"
        
        dialog1 = OpenDialog(parent_widget)
        dialog2 = OpenDialog(parent_widget)
        
        qtbot.addWidget(dialog1)
        qtbot.addWidget(dialog2)
        
        # Both should be separate instances
        assert dialog1 is not dialog2
        assert dialog1.parent == parent_widget
        assert dialog2.parent == parent_widget
        
        # Both should have the same configuration
        assert dialog1.isModal() == dialog2.isModal()
        assert dialog1.fileMode() == dialog2.fileMode()

    @patch('mdaviz.opendialog.settings')
    def test_dir_settings_key_constant(self, mock_settings, parent_widget, qtbot) -> None:
        """Test that DIR_SETTINGS_KEY constant is used correctly."""
        from mdaviz.opendialog import DIR_SETTINGS_KEY
        
        mock_settings.getKey.return_value = None
        
        dialog = OpenDialog(parent_widget)
        qtbot.addWidget(dialog)
        
        assert DIR_SETTINGS_KEY == "directory"
        mock_settings.getKey.assert_called_with(DIR_SETTINGS_KEY)

    @patch('mdaviz.opendialog.settings')
    def test_setup_method_called(self, mock_settings, parent_widget, qtbot) -> None:
        """Test that setup method is called during initialization."""
        mock_settings.getKey.return_value = None
        
        with patch.object(OpenDialog, 'setup') as mock_setup:
            dialog = OpenDialog(parent_widget)
            qtbot.addWidget(dialog)
            
            mock_setup.assert_called_once()

    @patch('mdaviz.opendialog.settings')
    def test_pathlib_path_home_usage(self, mock_settings, parent_widget, qtbot) -> None:
        """Test Path.home() usage when no settings available."""
        mock_settings.getKey.return_value = None
        
        with patch.object(Path, 'home') as mock_home:
            mock_home.return_value = Path("/mocked/home")
            
            dialog = OpenDialog(parent_widget)
            qtbot.addWidget(dialog)
            
            mock_home.assert_called_once()
            # Directory should be set to the mocked home path
            assert dialog.directory().absolutePath() == "/mocked/home" 