#!/usr/bin/env python
"""
Tests for the mdaviz mda_file module.

Covers file loading, caching, error handling, and tab management.
"""

from typing import TYPE_CHECKING
from pathlib import Path
from unittest.mock import MagicMock, patch

from mdaviz.mda_file import MDAFile, TabManager

if TYPE_CHECKING:
    from _pytest.fixtures import FixtureRequest


class TestMDAFile:
    """Test MDAFile functionality."""

    def test_mda_file_creation(self, qtbot: "FixtureRequest") -> None:
        """Test that MDAFile can be created with proper setup."""
        parent = MagicMock()
        parent.mda_file_viz = MagicMock()
        mda_file = MDAFile(parent)
        qtbot.addWidget(mda_file)

        assert mda_file is not None
        assert hasattr(mda_file, "tabWidget")
        assert hasattr(mda_file, "mda_mvc")
        assert hasattr(mda_file, "tabManager")

    def test_mda_file_set_data_with_valid_file(
        self, qtbot: "FixtureRequest", tmp_path: Path
    ) -> None:
        """Test setting data with a valid file path."""
        parent = MagicMock()
        parent.mda_file_viz = MagicMock()
        mda_file = MDAFile(parent)
        qtbot.addWidget(mda_file)

        # Create a temporary test file
        test_file = tmp_path / "test.mda"
        test_file.write_bytes(b"fake mda data")

        # Mock the readMDA function to return valid data
        mock_metadata = {
            "rank": 1,
            "dimensions": [100],
            "data_type": "float32",
        }
        mock_data = {
            "pos1": {"name": "Position 1", "values": [1, 2, 3, 4, 5]},
            "det1": {"name": "Detector 1", "values": [10, 20, 30, 40, 50]},
        }

        with patch("mdaviz.synApps_mdalib.mda.readMDA") as mock_read:
            mock_read.return_value = (mock_metadata, mock_data, None, None)
            with patch("mdaviz.utils.get_scan") as mock_get_scan:
                mock_get_scan.return_value = (mock_data, 0, 1)

                mda_file.setData(0)

                # Verify data was set
                assert mda_file._data is not None
                assert mda_file._data["fileName"] == "test"
                assert mda_file._data["filePath"] == str(test_file)

    def test_mda_file_set_data_with_missing_file(self, qtbot: "FixtureRequest") -> None:
        """Test setting data with a missing file path."""
        parent = MagicMock()
        parent.mda_file_viz = MagicMock()
        mda_file = MDAFile(parent)
        qtbot.addWidget(mda_file)

        # Mock file list to return a non-existent file
        mda_file.mdaFileList = MagicMock()
        mda_file.mdaFileList.return_value = ["/non/existent/file.mda"]

        with patch("pathlib.Path.exists", return_value=False):
            mda_file.setData(0)

            # Should handle missing file gracefully
            assert mda_file._data is not None
            assert mda_file._data["fileName"] == "file"

    def test_mda_file_set_data_with_read_error(
        self, qtbot: "FixtureRequest", tmp_path: Path
    ) -> None:
        """Test setting data when file read fails."""
        parent = MagicMock()
        parent.mda_file_viz = MagicMock()
        mda_file = MDAFile(parent)
        qtbot.addWidget(mda_file)

        # Create a temporary test file
        test_file = tmp_path / "test.mda"
        test_file.write_bytes(b"fake mda data")

        # Mock the readMDA function to return None (read error)
        with patch("mdaviz.synApps_mdalib.mda.readMDA", return_value=None):
            mda_file.setData(0)

            # Should handle read error gracefully
            assert mda_file._data is not None
            assert mda_file._data["fileName"] == "test"

    def test_mda_file_cache_integration(
        self, qtbot: "FixtureRequest", tmp_path: Path
    ) -> None:
        """Test that MDAFile properly integrates with the data cache."""
        parent = MagicMock()
        parent.mda_file_viz = MagicMock()
        mda_file = MDAFile(parent)
        qtbot.addWidget(mda_file)

        # Create a temporary test file
        test_file = tmp_path / "test.mda"
        test_file.write_bytes(b"fake mda data")

        # Mock cache to return cached data
        mock_cached_data = MagicMock()
        mock_cached_data.file_name = "test"
        mock_cached_data.file_path = str(test_file)
        mock_cached_data.folder_path = str(tmp_path)
        mock_cached_data.metadata = {"rank": 1}
        mock_cached_data.scan_dict = {
            "pos1": {"name": "Position 1", "values": [1, 2, 3]}
        }
        mock_cached_data.first_pos = 0
        mock_cached_data.first_det = 1
        mock_cached_data.pv_list = ["pos1"]

        with patch("mdaviz.data_cache.get_global_cache") as mock_cache:
            mock_cache_instance = MagicMock()
            mock_cache_instance.get_or_load.return_value = mock_cached_data
            mock_cache.return_value = mock_cache_instance

            mda_file.setData(0)

            # Verify cache was used
            mock_cache_instance.get_or_load.assert_called_once()

    def test_mda_file_display_metadata(self, qtbot: "FixtureRequest") -> None:
        """Test displaying metadata in the visualization panel."""
        parent = MagicMock()
        parent.mda_file_viz = MagicMock()
        mda_file = MDAFile(parent)
        qtbot.addWidget(mda_file)

        test_metadata = {"rank": 1, "dimensions": [100]}
        mda_file.displayMetadata(test_metadata)

        # Verify metadata was passed to visualization
        parent.mda_file_viz.setMetadata.assert_called_once()

    def test_mda_file_display_data(self, qtbot: "FixtureRequest") -> None:
        """Test displaying data in the visualization panel."""
        parent = MagicMock()
        parent.mda_file_viz = MagicMock()
        mda_file = MDAFile(parent)
        qtbot.addWidget(mda_file)

        # Set some test data
        mda_file._data = {
            "scanDict": {"pos1": {"name": "Position 1", "values": [1, 2, 3]}}
        }

        test_data = {"pos1": {"name": "Position 1", "values": [1, 2, 3]}}
        mda_file.displayData(test_data)

        # Verify data was passed to visualization
        parent.mda_file_viz.setTableData.assert_called_once()

    def test_mda_file_default_selection(self, qtbot: "FixtureRequest") -> None:
        """Test default field selection logic."""
        parent = MagicMock()
        parent.mda_file_viz = MagicMock()
        mda_file = MDAFile(parent)
        qtbot.addWidget(mda_file)

        # Test with no existing selection
        result = mda_file.defaultSelection(0, 1, None)
        assert result == {"X": 0, "Y": [1]}

        # Test with existing selection
        existing_selection = {"X": 2, "Y": [3]}
        result = mda_file.defaultSelection(0, 1, existing_selection)
        assert result == existing_selection

    def test_mda_file_tab_management(self, qtbot: "FixtureRequest") -> None:
        """Test tab management functionality."""
        parent = MagicMock()
        parent.mda_file_viz = MagicMock()
        mda_file = MDAFile(parent)
        qtbot.addWidget(mda_file)

        # Mock tab widget
        mock_tab_widget = MagicMock()
        mock_tab_widget.count.return_value = 2
        mda_file.tabWidget = mock_tab_widget

        # Test tab path to index conversion
        mock_tab = MagicMock()
        mock_tab.filePath.text.return_value = "/test/file.mda"
        mock_tab_widget.widget.return_value = mock_tab

        index = mda_file.tabPath2Index("/test/file.mda")
        assert index == 0  # First tab

        # Test tab index to path conversion
        path = mda_file.tabIndex2Path(0)
        assert path == "/test/file.mda"

    def test_mda_file_clear_graph(self, qtbot: "FixtureRequest") -> None:
        """Test clearing the graph area."""
        parent = MagicMock()
        parent.mda_file_viz = MagicMock()
        mda_file = MDAFile(parent)
        qtbot.addWidget(mda_file)

        # Mock the plot widget and curve manager
        mock_plot_widget = MagicMock()
        mock_curve_manager = MagicMock()
        mock_plot_widget.curveManager = mock_curve_manager

        mock_layout = MagicMock()
        mock_layout.count.return_value = 1
        mock_layout.itemAt.return_value.widget.return_value = mock_plot_widget

        with patch.object(
            mda_file.mda_mvc.mda_file_viz, "plotPageMpl"
        ) as mock_plot_page:
            mock_plot_page.layout.return_value = mock_layout

            mda_file.onClearGraphRequested()

            # Verify curve manager was called to remove all curves
            mock_curve_manager.removeAllCurves.assert_called_once_with(
                doNotClearCheckboxes=False
            )


class TestTabManager:
    """Test TabManager functionality."""

    def test_tab_manager_creation(self) -> None:
        """Test that TabManager can be created."""
        tab_manager = TabManager()
        assert tab_manager is not None
        assert hasattr(tab_manager, "addTab")
        assert hasattr(tab_manager, "removeTab")

    def test_tab_manager_add_tab(self) -> None:
        """Test adding a tab to the manager."""
        tab_manager = TabManager()

        file_path = "/test/file.mda"
        metadata = {"rank": 1}
        tabledata = {"pos1": {"name": "Position 1", "values": [1, 2, 3]}}

        tab_manager.addTab(file_path, metadata, tabledata)

        # Verify tab was added
        tab_data = tab_manager.getTabData(file_path)
        assert tab_data is not None
        assert tab_data["metadata"] == metadata
        assert tab_data["tabledata"] == tabledata

    def test_tab_manager_remove_tab(self) -> None:
        """Test removing a tab from the manager."""
        tab_manager = TabManager()

        file_path = "/test/file.mda"
        metadata = {"rank": 1}
        tabledata = {"pos1": {"name": "Position 1", "values": [1, 2, 3]}}

        # Add tab
        tab_manager.addTab(file_path, metadata, tabledata)
        assert tab_manager.getTabData(file_path) is not None

        # Remove tab
        tab_manager.removeTab(file_path)
        assert tab_manager.getTabData(file_path) is None

    def test_tab_manager_remove_all_tabs(self) -> None:
        """Test removing all tabs from the manager."""
        tab_manager = TabManager()

        # Add multiple tabs
        for i in range(3):
            file_path = f"/test/file{i}.mda"
            metadata = {"rank": 1}
            tabledata = {"pos1": {"name": "Position 1", "values": [1, 2, 3]}}
            tab_manager.addTab(file_path, metadata, tabledata)

        # Verify tabs were added
        assert len(tab_manager.tabs()) == 3

        # Remove all tabs
        tab_manager.removeAllTabs()
        assert len(tab_manager.tabs()) == 0

    def test_tab_manager_get_tab_data_nonexistent(self) -> None:
        """Test getting data for a non-existent tab."""
        tab_manager = TabManager()

        # Try to get data for non-existent tab
        tab_data = tab_manager.getTabData("/non/existent/file.mda")
        assert tab_data is None

    def test_tab_manager_tabs_list(self) -> None:
        """Test getting the list of all tabs."""
        tab_manager = TabManager()

        # Add some tabs
        for i in range(2):
            file_path = f"/test/file{i}.mda"
            metadata = {"rank": 1}
            tabledata = {"pos1": {"name": "Position 1", "values": [1, 2, 3]}}
            tab_manager.addTab(file_path, metadata, tabledata)

        # Get tabs list
        tabs = tab_manager.tabs()
        assert len(tabs) == 2
        assert "/test/file0.mda" in tabs
        assert "/test/file1.mda" in tabs
