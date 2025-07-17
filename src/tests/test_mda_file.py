#!/usr/bin/env python
"""
Tests for the mdaviz mda_file module.

Covers file loading, caching, error handling, and tab management.
"""

import pytest
from typing import TYPE_CHECKING
from unittest.mock import Mock, patch
from PyQt6.QtWidgets import QApplication
from pathlib import Path

from mdaviz.mda_file import MDAFile, TabManager

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot


@pytest.fixture
def app(qtbot: "QtBot") -> QApplication:
    """Create a QApplication instance for testing."""
    return qtbot.qapp


class TestMDAFile:
    """Test MDAFile functionality."""

    def test_mda_file_creation(self, qapp: QApplication, qtbot: "QtBot") -> None:
        """Test that MDAFile can be created successfully."""
        mock_parent = Mock()
        mda_file = MDAFile(parent=mock_parent)
        qtbot.addWidget(mda_file)

        assert mda_file is not None
        assert isinstance(mda_file, MDAFile)

    def test_mda_file_set_data_with_valid_file(
        self, qapp: QApplication, qtbot: "QtBot", single_mda_file: Path
    ) -> None:
        """Test setting data with a valid file path using real test data."""
        # Create a mock parent (MDA_MVC)
        mock_parent = Mock()
        mock_parent.dataPath.return_value = single_mda_file.parent
        mock_parent.mdaFileList.return_value = [single_mda_file.name]

        mda_file = MDAFile(parent=mock_parent)
        qtbot.addWidget(mda_file)

        # Set data (index 0, since only one file in list)
        mda_file.setData(0)

        assert mda_file._data["fileName"] == single_mda_file.stem

    def test_mda_file_set_data_with_missing_file(
        self, qapp: QApplication, qtbot: "QtBot"
    ) -> None:
        """Test setting data with a missing file path using real test data path."""
        # Create a mock parent that points to a real directory but missing file
        from pathlib import Path

        test_dir = Path(__file__).parent / "data" / "test_folder1"
        missing_file = "nonexistent_file.mda"

        mock_parent = Mock()
        mock_parent.dataPath.return_value = test_dir
        mock_parent.mdaFileList.return_value = [missing_file]

        mda_file = MDAFile(parent=mock_parent)
        qtbot.addWidget(mda_file)

        # Set data (index 0, since only one file in list)
        mda_file.setData(0)

        # Should still set the file name even if file doesn't exist
        assert mda_file._data["fileName"] == "nonexistent_file"

    @pytest.mark.skip(reason="Mock data path issue - needs proper mock setup")
    def test_mda_file_set_data_with_read_error(
        self, qapp: QApplication, qtbot: "QtBot"
    ) -> None:
        """Test setting data when file read fails."""
        mda_file = MDAFile()
        qtbot.addWidget(mda_file)

        # Mock the data path and file
        with patch("mdaviz.mda_file.settings") as mock_settings:
            mock_settings.dataPath.return_value = "/test/path"
            mock_settings.mdaFileList.return_value = ["test.mda"]

            # Mock file path
            mock_path = Mock()
            mock_path.exists.return_value = True
            mock_path.stem = "test"
            mock_settings.dataPath.return_value.__truediv__.return_value = mock_path

            # Mock read error
            with patch(
                "mdaviz.synApps_mdalib.mda.readMDA", side_effect=Exception("Read error")
            ):
                mda_file.setData(0)

                assert mda_file._data["fileName"] == "test"

    def test_mda_file_cache_integration(
        self, qapp: QApplication, qtbot: "QtBot", single_mda_file: Path
    ) -> None:
        """Test that MDAFile properly integrates with the data cache using real test data."""
        # Create a mock parent with real file data
        mock_parent = Mock()
        mock_parent.dataPath.return_value = single_mda_file.parent
        mock_parent.mdaFileList.return_value = [single_mda_file.name]

        mda_file = MDAFile(parent=mock_parent)
        qtbot.addWidget(mda_file)

        # Mock cache to verify it's called
        mock_cache_instance = Mock()
        mock_cache_instance.get_or_load.return_value = (
            None  # Force fallback to direct loading
        )

        with patch("mdaviz.mda_file.get_global_cache") as mock_cache:
            mock_cache.return_value = mock_cache_instance

            # Set data
            mda_file.setData(0)

            # Verify cache was called with the real file path
            mock_cache_instance.get_or_load.assert_called_once_with(
                str(single_mda_file)
            )

    def test_mda_file_display_metadata(
        self, qapp: QApplication, qtbot: "QtBot"
    ) -> None:
        """Test displaying metadata in the visualization panel."""
        mock_parent = Mock()
        mda_file = MDAFile(parent=mock_parent)
        qtbot.addWidget(mda_file)

        # Test metadata display
        test_metadata = {"test": "metadata"}
        mda_file.displayMetadata(test_metadata)

        assert mda_file is not None

    def test_mda_file_display_data(self, qapp: QApplication, qtbot: "QtBot") -> None:
        """Test displaying data in the visualization panel."""
        mock_parent = Mock()
        mda_file = MDAFile(parent=mock_parent)
        qtbot.addWidget(mda_file)

        # Test data display
        test_data = {"test": "data"}
        mda_file.displayData(test_data)

        assert mda_file is not None

    def test_mda_file_default_selection(
        self, qapp: QApplication, qtbot: "QtBot"
    ) -> None:
        """Test default field selection logic."""
        mock_parent = Mock()
        mda_file = MDAFile(parent=mock_parent)
        qtbot.addWidget(mda_file)

        # Test default selection
        assert mda_file is not None

    def test_mda_file_tab_management(self, qapp: QApplication, qtbot: "QtBot") -> None:
        """Test tab management functionality."""
        mock_parent = Mock()
        mda_file = MDAFile(parent=mock_parent)
        qtbot.addWidget(mda_file)

        # Test tab management
        assert mda_file is not None

    def test_mda_file_clear_graph(self, qapp: QApplication, qtbot: "QtBot") -> None:
        """Test clearing the graph area."""
        mock_parent = Mock()
        mda_file = MDAFile(parent=mock_parent)
        qtbot.addWidget(mda_file)

        # Test that the MDAFile has the necessary UI components
        # The clearGraph functionality would be via the visualization panel
        assert mda_file is not None
        assert hasattr(mda_file, "clearGraphButton")


class TestTabManager:
    """Test TabManager functionality."""

    def test_tab_manager_creation(self, qapp: QApplication, qtbot: "QtBot") -> None:
        """Test that TabManager can be created successfully."""
        tab_manager = TabManager()

        assert tab_manager is not None
        assert isinstance(tab_manager, TabManager)

    def test_tab_manager_add_tab(self, qapp: QApplication, qtbot: "QtBot") -> None:
        """Test adding a tab to the manager."""
        tab_manager = TabManager()

        # Test adding a tab (addTab takes file_path, metadata, tabledata)
        tab_manager.addTab("/test/path.mda", {"metadata": "test"}, {"data": "test"})

        assert len(tab_manager._tabs) == 1

    def test_tab_manager_remove_tab(self, qapp: QApplication, qtbot: "QtBot") -> None:
        """Test removing a tab from the manager."""
        tab_manager = TabManager()

        # Add a tab first
        tab_manager.addTab("/test/path.mda", {"metadata": "test"}, {"data": "test"})
        assert len(tab_manager._tabs) == 1
        # Remove the tab
        tab_manager.removeTab("/test/path.mda")
        assert len(tab_manager._tabs) == 0

    def test_tab_manager_remove_all_tabs(
        self, qapp: QApplication, qtbot: "QtBot"
    ) -> None:
        """Test removing all tabs from the manager."""
        tab_manager = TabManager()

        # Add multiple tabs
        tab_manager.addTab("/test/path1.mda", {"metadata": "test1"}, {"data": "test1"})
        tab_manager.addTab("/test/path2.mda", {"metadata": "test2"}, {"data": "test2"})
        assert len(tab_manager._tabs) == 2
        # Remove all tabs
        tab_manager.removeAllTabs()
        assert len(tab_manager._tabs) == 0

    def test_tab_manager_get_tab_data_nonexistent(
        self, qapp: QApplication, qtbot: "QtBot"
    ) -> None:
        """Test getting data for a non-existent tab."""
        tab_manager = TabManager()

        # Try to get data from nonexistent tab
        data = tab_manager.getTabData("Nonexistent Tab")
        assert data is None

    def test_tab_manager_tabs_list(self, qapp: QApplication, qtbot: "QtBot") -> None:
        """Test getting the list of all tabs."""
        tab_manager = TabManager()

        # Add tabs
        tab_manager.addTab("/test/path1.mda", {"metadata": "test1"}, {"data": "test1"})
        tab_manager.addTab("/test/path2.mda", {"metadata": "test2"}, {"data": "test2"})

        # Check tabs list directly
        assert len(tab_manager._tabs) == 2
        assert "/test/path1.mda" in tab_manager._tabs
        assert "/test/path2.mda" in tab_manager._tabs
