"""Tests for DataTableModel."""

from typing import TYPE_CHECKING

import pytest
from PyQt6.QtCore import QModelIndex, Qt

from mdaviz.data_table_model import DataTableModel

if TYPE_CHECKING:
    from _pytest.fixtures import FixtureRequest
    from pytest_mock.plugin import MockerFixture


class TestDataTableModel:
    """Test suite for DataTableModel class."""

    def test_init_with_valid_data(self) -> None:
        """Test initialization with valid scan data."""
        scan_dict = {
            "pos1": {
                "object": None,
                "data": [1.0, 2.0, 3.0],
                "unit": "mm",
                "name": "Position 1",
                "type": "positioner"
            },
            "det1": {
                "object": None,
                "data": [10.5, 20.5, 30.5],
                "unit": "counts",
                "name": "Detector 1",
                "type": "detector"
            }
        }
        
        model = DataTableModel(scan_dict)
        
        assert model.columnCount() == 2
        assert model.rowCount() == 3
        assert "Position 1" in model.columnLabels()
        assert "Detector 1" in model.columnLabels()

    def test_init_with_empty_data(self) -> None:
        """Test initialization with empty scan data."""
        model = DataTableModel({})
        
        assert model.columnCount() == 0
        assert model.rowCount() == 0
        assert model.columnLabels() == []

    def test_init_with_none_data(self) -> None:
        """Test initialization with None data."""
        model = DataTableModel(None)
        
        assert model.columnCount() == 0
        assert model.rowCount() == 0
        assert model.columnLabels() == []

    def test_row_count_with_varying_data_lengths(self) -> None:
        """Test row count returns maximum length across all columns."""
        scan_dict = {
            "pos1": {
                "object": None,
                "data": [1.0, 2.0],  # 2 items
                "unit": "mm",
                "name": "Position 1",
                "type": "positioner"
            },
            "det1": {
                "object": None,
                "data": [10.5, 20.5, 30.5, 40.5],  # 4 items
                "unit": "counts",
                "name": "Detector 1",
                "type": "detector"
            }
        }
        
        model = DataTableModel(scan_dict)
        
        # Should return the maximum length (4)
        assert model.rowCount() == 4

    def test_column_count(self) -> None:
        """Test column count method."""
        scan_dict = {
            "pos1": {"name": "Position 1", "data": [1, 2, 3]},
            "pos2": {"name": "Position 2", "data": [4, 5, 6]},
            "det1": {"name": "Detector 1", "data": [7, 8, 9]}
        }
        
        model = DataTableModel(scan_dict)
        assert model.columnCount() == 3

    def test_data_valid_index(self) -> None:
        """Test data retrieval with valid index."""
        scan_dict = {
            "pos1": {
                "name": "Position 1",
                "data": [1.5, 2.5, 3.5]
            }
        }
        
        model = DataTableModel(scan_dict)
        
        # Test valid data retrieval
        index = model.createIndex(1, 0)  # Row 1, Column 0
        data = model.data(index, Qt.ItemDataRole.DisplayRole)
        assert data == 2.5  # Implementation returns actual values, not strings

    def test_data_invalid_index(self) -> None:
        """Test data retrieval with invalid index."""
        scan_dict = {
            "pos1": {
                "name": "Position 1", 
                "data": [1.5, 2.5, 3.5]
            }
        }
        
        model = DataTableModel(scan_dict)
        
        # Test invalid index
        invalid_index = QModelIndex()
        data = model.data(invalid_index, Qt.ItemDataRole.DisplayRole)
        assert data.isNull()

    def test_data_out_of_bounds_row(self) -> None:
        """Test data retrieval with row index out of bounds."""
        scan_dict = {
            "pos1": {
                "name": "Position 1",
                "data": [1.5, 2.5]
            }
        }
        
        model = DataTableModel(scan_dict)
        
        # Test row out of bounds
        index = model.createIndex(5, 0)  # Row 5 doesn't exist
        data = model.data(index, Qt.ItemDataRole.DisplayRole)
        assert data.isNull()

    def test_data_out_of_bounds_column(self) -> None:
        """Test data retrieval with column index out of bounds."""
        scan_dict = {
            "pos1": {
                "name": "Position 1",
                "data": [1.5, 2.5]
            }
        }
        
        model = DataTableModel(scan_dict)
        
        # Test column out of bounds
        index = model.createIndex(0, 5)  # Column 5 doesn't exist
        data = model.data(index, Qt.ItemDataRole.DisplayRole)
        assert data.isNull()

    def test_data_non_display_role(self) -> None:
        """Test data retrieval with non-display role."""
        scan_dict = {
            "pos1": {
                "name": "Position 1",
                "data": [1.5, 2.5]
            }
        }
        
        model = DataTableModel(scan_dict)
        
        index = model.createIndex(0, 0)
        data = model.data(index, Qt.ItemDataRole.EditRole)  # EditRole (non-DisplayRole)
        assert data.isNull()

    def test_header_data_horizontal(self) -> None:
        """Test horizontal header data retrieval."""
        scan_dict = {
            "pos1": {"name": "Position 1", "data": [1, 2, 3]},
            "det1": {"name": "Detector 1", "data": [4, 5, 6]}
        }
        
        model = DataTableModel(scan_dict)
        
        # Use proper Qt enums
        header0 = model.headerData(0, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
        header1 = model.headerData(1, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
        
        assert header0 == "Position 1"
        assert header1 == "Detector 1"

    def test_header_data_vertical(self) -> None:
        """Test vertical header data retrieval returns row numbers."""
        scan_dict = {
            "pos1": {"name": "Position 1", "data": [1, 2, 3]}
        }
        
        model = DataTableModel(scan_dict)
        
        header = model.headerData(0, Qt.Orientation.Vertical, Qt.ItemDataRole.DisplayRole)
        assert header == "1"  # Row numbers start from 1

    def test_header_data_non_display_role(self) -> None:
        """Test header data with non-display role returns null."""
        scan_dict = {
            "pos1": {"name": "Position 1", "data": [1, 2, 3]}
        }
        
        model = DataTableModel(scan_dict)
        
        header = model.headerData(0, Qt.Orientation.Horizontal, Qt.ItemDataRole.EditRole)
        assert header.isNull()

    def test_column_labels_getter_setter(self) -> None:
        """Test column labels getter and setter methods."""
        scan_dict = {
            "pos1": {"name": "Position 1", "data": [1, 2, 3]},
            "det1": {"name": "Detector 1", "data": [4, 5, 6]}
        }
        
        model = DataTableModel(scan_dict)
        
        # Test getter
        labels = model.columnLabels()
        assert "Position 1" in labels
        assert "Detector 1" in labels
        assert len(labels) == 2
        
        # Test setter updates the labels
        model.setColumnLabels()  # setColumnLabels returns None
        new_labels = model.columnLabels()  # Get updated labels
        assert new_labels == labels

    def test_all_data_getter_setter(self) -> None:
        """Test allData getter and setAllData setter methods."""
        scan_dict = {
            "pos1": {"name": "Position 1", "data": [1, 2, 3]},
            "det1": {"name": "Detector 1", "data": [4, 5, 6]}
        }
        
        model = DataTableModel({})  # Start with empty
        
        # Test setter (setAllData returns None)
        model.setAllData(scan_dict)
        
        # Test getter - data is stored as-is, not transformed
        data = model.allData()
        expected = scan_dict  # Data is stored as-is
        assert data == expected

    def test_set_all_data_with_empty_dict(self) -> None:
        """Test setAllData with empty dictionary."""
        model = DataTableModel({})
        
        model.setAllData({})  # setAllData returns None
        assert model.allData() == {}

    def test_set_all_data_with_none(self) -> None:
        """Test setAllData with None."""
        model = DataTableModel({})
        
        model.setAllData(None)  # setAllData returns None
        assert model.allData() == {}

    def test_row_count_with_non_list_data(self) -> None:
        """Test row count when data contains non-list values."""
        scan_dict = {
            "pos1": {"name": "Position 1", "data": "not a list"},
            "det1": {"name": "Detector 1", "data": [1, 2, 3]}
        }
        
        model = DataTableModel(scan_dict)
        
        # Should still work and return the max length of actual lists
        assert model.rowCount() == 3

    def test_complete_workflow(self) -> None:
        """Test a complete workflow with the model."""
        # Create initial data
        scan_dict = {
            "pos1": {
                "name": "X Position",
                "data": [0.0, 1.0, 2.0, 3.0],
                "unit": "mm",
                "type": "positioner"
            },
            "det1": {
                "name": "Ion Chamber",
                "data": [100, 150, 200, 175],
                "unit": "counts",
                "type": "detector"
            }
        }
        
        model = DataTableModel(scan_dict)
        
        # Verify basic properties
        assert model.rowCount() == 4
        assert model.columnCount() == 2
        
        # Verify headers
        header0 = model.headerData(0, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
        header1 = model.headerData(1, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
        assert header0 == "X Position"
        assert header1 == "Ion Chamber"
        
        # Verify data access
        assert model.data(model.createIndex(0, 0), Qt.ItemDataRole.DisplayRole) == 0.0
        assert model.data(model.createIndex(1, 1), Qt.ItemDataRole.DisplayRole) == 150
        assert model.data(model.createIndex(3, 0), Qt.ItemDataRole.DisplayRole) == 3.0
        
        # Update data
        new_scan_dict = {
            "pos2": {"name": "Y Position", "data": [5.0, 6.0]},
        }
        
        model.setAllData(new_scan_dict)
        model.setColumnLabels()
        
        # Verify updated state
        assert model.rowCount() == 2
        assert model.columnCount() == 1
        header = model.headerData(0, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
        assert header == "Y Position" 