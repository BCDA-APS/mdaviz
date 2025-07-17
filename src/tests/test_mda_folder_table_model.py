"""Tests for MDAFolderTableModel."""

from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import pytest
from PyQt6.QtCore import QModelIndex, Qt

from mdaviz.mda_folder_table_model import MDAFolderTableModel

if TYPE_CHECKING:
    from _pytest.fixtures import FixtureRequest
    from pytest_mock.plugin import MockerFixture


class TestMDAFolderTableModel:
    """Test suite for MDAFolderTableModel class."""

    @pytest.fixture
    def mock_parent(self) -> Mock:
        """Create a mock parent (mda_mvc) for testing."""
        return Mock()

    @pytest.fixture
    def sample_file_info_list(self) -> list[dict[str, str]]:
        """Create sample file info list for testing."""
        return [
            {
                "File": "scan_001.mda",
                "Size": "1.2 KB",
                "Date": "2023-10-01",
                "Path": "/data/scan_001.mda"
            },
            {
                "File": "scan_002.mda",
                "Size": "2.1 KB", 
                "Date": "2023-10-02",
                "Path": "/data/scan_002.mda"
            },
            {
                "File": "scan_003.mda",
                "Size": "856 B",
                "Date": "2023-10-03", 
                "Path": "/data/scan_003.mda"
            }
        ]

    @pytest.fixture
    def mock_headers(self) -> list[str]:
        """Create mock headers for testing."""
        return ["File", "Size", "Date", "Path"]

    def test_init_with_data(self, mock_parent, sample_file_info_list, mock_headers) -> None:
        """Test initialization with data."""
        with patch('mdaviz.mda_folder_table_model.HEADERS', mock_headers):
            model = MDAFolderTableModel(sample_file_info_list, mock_parent)
            
            assert model.mda_mvc == mock_parent
            assert model.columnLabels == mock_headers
            assert model.fileInfoList() == sample_file_info_list

    def test_init_with_empty_data(self, mock_parent, mock_headers) -> None:
        """Test initialization with empty data."""
        with patch('mdaviz.mda_folder_table_model.HEADERS', mock_headers):
            model = MDAFolderTableModel([], mock_parent)
            
            assert model.mda_mvc == mock_parent
            assert model.columnLabels == mock_headers
            assert model.fileInfoList() == []

    def test_row_count_with_data(self, mock_parent, sample_file_info_list, mock_headers) -> None:
        """Test row count with data."""
        with patch('mdaviz.mda_folder_table_model.HEADERS', mock_headers):
            model = MDAFolderTableModel(sample_file_info_list, mock_parent)
            
            assert model.rowCount() == 3

    def test_row_count_empty_data(self, mock_parent, mock_headers) -> None:
        """Test row count with empty data."""
        with patch('mdaviz.mda_folder_table_model.HEADERS', mock_headers):
            model = MDAFolderTableModel([], mock_parent)
            
            assert model.rowCount() == 0

    def test_row_count_with_parent_index(self, mock_parent, sample_file_info_list, mock_headers) -> None:
        """Test row count with parent index parameter."""
        with patch('mdaviz.mda_folder_table_model.HEADERS', mock_headers):
            model = MDAFolderTableModel(sample_file_info_list, mock_parent)
            
            index = QModelIndex()
            assert model.rowCount(index) == 3

    def test_column_count(self, mock_parent, sample_file_info_list, mock_headers) -> None:
        """Test column count."""
        with patch('mdaviz.mda_folder_table_model.HEADERS', mock_headers):
            model = MDAFolderTableModel(sample_file_info_list, mock_parent)
            
            assert model.columnCount() == 4

    def test_column_count_with_parent_index(self, mock_parent, sample_file_info_list, mock_headers) -> None:
        """Test column count with parent index parameter."""
        with patch('mdaviz.mda_folder_table_model.HEADERS', mock_headers):
            model = MDAFolderTableModel(sample_file_info_list, mock_parent)
            
            index = QModelIndex()
            assert model.columnCount(index) == 4

    def test_data_valid_indices(self, mock_parent, sample_file_info_list, mock_headers) -> None:
        """Test data retrieval with valid indices."""
        with patch('mdaviz.mda_folder_table_model.HEADERS', mock_headers):
            model = MDAFolderTableModel(sample_file_info_list, mock_parent)
            
            # Test different cells
            index_00 = model.createIndex(0, 0)  # First file name
            assert model.data(index_00, Qt.ItemDataRole.DisplayRole) == "scan_001.mda"
            
            index_12 = model.createIndex(1, 2)  # Second file date
            assert model.data(index_12, Qt.ItemDataRole.DisplayRole) == "2023-10-02"
            
            index_23 = model.createIndex(2, 3)  # Third file path
            assert model.data(index_23, Qt.ItemDataRole.DisplayRole) == "/data/scan_003.mda"

    def test_data_display_role(self, mock_parent, sample_file_info_list, mock_headers) -> None:
        """Test data retrieval with display role (role=0)."""
        with patch('mdaviz.mda_folder_table_model.HEADERS', mock_headers):
            model = MDAFolderTableModel(sample_file_info_list, mock_parent)
            
            index = model.createIndex(0, 1)  # First file size
            assert model.data(index, 0) == "1.2 KB"

    def test_data_non_display_role(self, mock_parent, sample_file_info_list, mock_headers) -> None:
        """Test data retrieval with non-display role."""
        with patch('mdaviz.mda_folder_table_model.HEADERS', mock_headers):
            model = MDAFolderTableModel(sample_file_info_list, mock_parent)
            
            index = model.createIndex(0, 0)
            result = model.data(index, Qt.ItemDataRole.EditRole)
            
            # Should return None for non-display roles
            assert result is None

    def test_data_no_role_specified(self, mock_parent, sample_file_info_list, mock_headers) -> None:
        """Test data retrieval with no role specified (None)."""
        with patch('mdaviz.mda_folder_table_model.HEADERS', mock_headers):
            model = MDAFolderTableModel(sample_file_info_list, mock_parent)
            
            index = model.createIndex(0, 0)
            result = model.data(index, None)
            
            # Should return None when role is None
            assert result is None

    def test_header_data_horizontal_display_role(self, mock_parent, sample_file_info_list, mock_headers) -> None:
        """Test horizontal header data with display role."""
        with patch('mdaviz.mda_folder_table_model.HEADERS', mock_headers):
            model = MDAFolderTableModel(sample_file_info_list, mock_parent)
            
            # Test each column header
            for i, expected_header in enumerate(mock_headers):
                header = model.headerData(i, 1, 0)  # section, Horizontal, DisplayRole
                assert header == expected_header

    def test_header_data_vertical_display_role(self, mock_parent, sample_file_info_list, mock_headers) -> None:
        """Test vertical header data with display role (row numbers)."""
        with patch('mdaviz.mda_folder_table_model.HEADERS', mock_headers):
            model = MDAFolderTableModel(sample_file_info_list, mock_parent)
            
            # Should return row numbers starting from 1
            for i in range(3):
                header = model.headerData(i, 2, 0)  # section, Vertical, DisplayRole
                assert header == str(i + 1)

    def test_header_data_non_display_role(self, mock_parent, sample_file_info_list, mock_headers) -> None:
        """Test header data with non-display role."""
        with patch('mdaviz.mda_folder_table_model.HEADERS', mock_headers):
            model = MDAFolderTableModel(sample_file_info_list, mock_parent)
            
            header = model.headerData(0, 1, Qt.ItemDataRole.EditRole)
            assert header is None

    def test_file_info_list_getter_setter(self, mock_parent, sample_file_info_list, mock_headers) -> None:
        """Test fileInfoList getter and setFileInfoList setter."""
        with patch('mdaviz.mda_folder_table_model.HEADERS', mock_headers):
            model = MDAFolderTableModel([], mock_parent)
            
            # Initially empty
            assert model.fileInfoList() == []
            
            # Set new data
            model.setFileInfoList(sample_file_info_list)
            assert model.fileInfoList() == sample_file_info_list
            
            # Set different data
            new_data = [{"File": "new_scan.mda", "Size": "5 KB", "Date": "2023-10-04", "Path": "/data/new_scan.mda"}]
            model.setFileInfoList(new_data)
            assert model.fileInfoList() == new_data

    def test_inheritance(self, mock_parent, mock_headers) -> None:
        """Test that model inherits from QAbstractTableModel."""
        from PyQt6.QtCore import QAbstractTableModel
        
        with patch('mdaviz.mda_folder_table_model.HEADERS', mock_headers):
            model = MDAFolderTableModel([], mock_parent)
            
            assert isinstance(model, QAbstractTableModel)

    def test_data_with_missing_keys(self, mock_parent, mock_headers) -> None:
        """Test data handling when file info has missing keys."""
        # File info missing some expected headers
        incomplete_file_info = [
            {"File": "scan_001.mda", "Size": "1.2 KB"},  # Missing Date and Path
            {"File": "scan_002.mda", "Date": "2023-10-02"}  # Missing Size and Path
        ]
        
        with patch('mdaviz.mda_folder_table_model.HEADERS', mock_headers):
            model = MDAFolderTableModel(incomplete_file_info, mock_parent)
            
            # Should not crash, but might raise KeyError
            try:
                # Try to access missing data
                index = model.createIndex(0, 2)  # Date column for first file
                result = model.data(index, 0)
                # If it doesn't crash, result might be None or KeyError is raised
            except KeyError:
                # This is expected behavior when key is missing
                pass

    def test_out_of_bounds_access(self, mock_parent, sample_file_info_list, mock_headers) -> None:
        """Test data access with out of bounds indices."""
        with patch('mdaviz.mda_folder_table_model.HEADERS', mock_headers):
            model = MDAFolderTableModel(sample_file_info_list, mock_parent)
            
            # This may raise IndexError - let's see what the actual behavior is
            try:
                # Try to access row that doesn't exist
                index = model.createIndex(10, 0)  # Row 10 doesn't exist
                result = model.data(index, 0)
                # If no exception, result should be None or some default value
            except IndexError:
                # This is acceptable behavior
                pass
                
            try:
                # Try to access column that doesn't exist
                index = model.createIndex(0, 10)  # Column 10 doesn't exist
                result = model.data(index, 0)
            except IndexError:
                # This is acceptable behavior
                pass

    def test_empty_headers_list(self, mock_parent, sample_file_info_list) -> None:
        """Test with empty headers list."""
        with patch('mdaviz.mda_folder_table_model.HEADERS', []):
            model = MDAFolderTableModel(sample_file_info_list, mock_parent)
            
            assert model.columnCount() == 0
            assert model.rowCount() == 3  # Data is still there, just no columns

    def test_model_with_different_file_info_structures(self, mock_parent, mock_headers) -> None:
        """Test model with different file info structures."""
        # Test with different key names
        different_file_info = [
            {"File": "test1.mda", "Size": "100 B", "Date": "2023-01-01", "Path": "/test1.mda"},
            {"File": "test2.mda", "Size": "200 B", "Date": "2023-01-02", "Path": "/test2.mda"}
        ]
        
        with patch('mdaviz.mda_folder_table_model.HEADERS', mock_headers):
            model = MDAFolderTableModel(different_file_info, mock_parent)
            
            assert model.rowCount() == 2
            assert model.columnCount() == 4
            
            # Test data access
            index = model.createIndex(0, 0)
            assert model.data(index, 0) == "test1.mda"

    def test_complete_workflow(self, mock_parent, mock_headers) -> None:
        """Test complete workflow with the model."""
        with patch('mdaviz.mda_folder_table_model.HEADERS', mock_headers):
            # Start with empty model
            model = MDAFolderTableModel([], mock_parent)
            assert model.rowCount() == 0
            assert model.columnCount() == 4
            
            # Add some data
            file_data = [
                {"File": "workflow_test.mda", "Size": "3.2 KB", "Date": "2023-12-01", "Path": "/data/workflow_test.mda"}
            ]
            model.setFileInfoList(file_data)
            
            # Verify updated state
            assert model.rowCount() == 1
            assert model.fileInfoList() == file_data
            
            # Test data retrieval
            index = model.createIndex(0, 0)
            assert model.data(index, 0) == "workflow_test.mda"
            
            # Test headers
            assert model.headerData(0, 1, 0) == "File"
            assert model.headerData(0, 2, 0) == "1"  # Row number 