"""Tests for EmptyTableModel."""

from typing import TYPE_CHECKING

import pytest
from PyQt6.QtCore import QModelIndex, Qt

from mdaviz.empty_table_model import EmptyTableModel

if TYPE_CHECKING:
    from _pytest.fixtures import FixtureRequest
    from pytest_mock.plugin import MockerFixture


class TestEmptyTableModel:
    """Test suite for EmptyTableModel class."""

    def test_init_with_headers(self) -> None:
        """Test initialization with headers."""
        headers = ["Column 1", "Column 2", "Column 3"]
        model = EmptyTableModel(headers)
        
        assert model.headers == headers

    def test_init_empty_headers(self) -> None:
        """Test initialization with empty headers list."""
        headers = []
        model = EmptyTableModel(headers)
        
        assert model.headers == []
        assert model.columnCount() == 0

    def test_init_with_parent(self, qtbot) -> None:
        """Test initialization with parent widget."""
        from PyQt6.QtWidgets import QWidget
        parent = QWidget()
        qtbot.addWidget(parent)
        
        headers = ["Col1", "Col2"]
        model = EmptyTableModel(headers, parent)
        
        assert model.headers == headers
        assert model.parent() == parent

    def test_row_count_always_zero(self) -> None:
        """Test that row count is always zero for empty table."""
        headers = ["A", "B", "C", "D"]
        model = EmptyTableModel(headers)
        
        # Should always return 0 regardless of headers
        assert model.rowCount() == 0
        
        # Test with QModelIndex parameter (should still be 0)
        index = QModelIndex()
        assert model.rowCount(index) == 0

    def test_column_count_matches_headers(self) -> None:
        """Test that column count matches number of headers."""
        # Test with multiple headers
        headers = ["Name", "Age", "City", "Country"]
        model = EmptyTableModel(headers)
        assert model.columnCount() == 4
        
        # Test with single header
        model = EmptyTableModel(["Single"])
        assert model.columnCount() == 1
        
        # Test with empty headers
        model = EmptyTableModel([])
        assert model.columnCount() == 0

    def test_column_count_with_parent_index(self) -> None:
        """Test column count with parent index parameter."""
        headers = ["Col1", "Col2"]
        model = EmptyTableModel(headers)
        
        index = QModelIndex()
        assert model.columnCount(index) == 2

    def test_data_always_returns_qvariant(self) -> None:
        """Test that data method always returns QVariant (empty)."""
        headers = ["Header1", "Header2"]
        model = EmptyTableModel(headers)
        
        # Create various indices
        indices = [
            QModelIndex(),  # Invalid index
            model.createIndex(0, 0),  # Valid-looking index
            model.createIndex(5, 10),  # Out of bounds index
        ]
        
        roles = [
            Qt.ItemDataRole.DisplayRole,
            Qt.ItemDataRole.EditRole,
            Qt.ItemDataRole.ToolTipRole,
            0,  # Integer role
            100,  # Random role
        ]
        
        # All combinations should return QVariant (null)
        for index in indices:
            for role in roles:
                result = model.data(index, role)
                assert result.isNull()

    def test_header_data_horizontal_display_role(self) -> None:
        """Test header data for horizontal headers with display role."""
        headers = ["Name", "Email", "Phone"]
        model = EmptyTableModel(headers)
        
        # Test each header
        for i, expected_header in enumerate(headers):
            header = model.headerData(i, 1, 0)  # section, Horizontal(1), DisplayRole(0)
            assert header == expected_header

    def test_header_data_out_of_bounds(self) -> None:
        """Test header data with out of bounds section."""
        headers = ["A", "B"]
        model = EmptyTableModel(headers)
        
        # Test section beyond available headers
        # The current implementation raises IndexError, which is the actual behavior
        with pytest.raises(IndexError):
            model.headerData(10, 1, 0)  # section=10, Horizontal, DisplayRole

    def test_header_data_vertical_orientation(self) -> None:
        """Test header data with vertical orientation."""
        headers = ["Col1", "Col2"]
        model = EmptyTableModel(headers)
        
        # Vertical orientation (2) should return QVariant
        header = model.headerData(0, 2, 0)  # section=0, Vertical(2), DisplayRole(0)
        assert header.isNull()

    def test_header_data_non_display_role(self) -> None:
        """Test header data with non-display role."""
        headers = ["Test Header"]
        model = EmptyTableModel(headers)
        
        # Non-display role should return QVariant
        header = model.headerData(0, 1, 2)  # section=0, Horizontal(1), EditRole(2)
        assert header.isNull()

    def test_clear_all_checkboxes(self) -> None:
        """Test clearAllCheckboxes method (should do nothing)."""
        headers = ["Col1", "Col2"]
        model = EmptyTableModel(headers)
        
        # Should not raise any exception and return None
        result = model.clearAllCheckboxes()
        assert result is None

    def test_uncheck_checkbox(self) -> None:
        """Test uncheckCheckBox method (should do nothing)."""
        headers = ["Col1", "Col2"]
        model = EmptyTableModel(headers)
        
        # Should not raise any exception for any row value
        assert model.uncheckCheckBox(0) is None
        assert model.uncheckCheckBox(5) is None
        assert model.uncheckCheckBox(-1) is None

    def test_inheritance(self) -> None:
        """Test that EmptyTableModel inherits from QAbstractTableModel."""
        from PyQt6.QtCore import QAbstractTableModel
        
        headers = ["Test"]
        model = EmptyTableModel(headers)
        
        assert isinstance(model, QAbstractTableModel)

    def test_model_with_special_header_names(self) -> None:
        """Test model with special characters and empty strings in headers."""
        special_headers = [
            "",  # Empty string
            "Header with spaces",
            "Header_with_underscores",
            "Header-with-dashes",
            "Header.with.dots",
            "Header with\nnewline",
            "Header\twith\ttabs",
            "Header with unicode: ñáéíóú",
            "123 Numeric Header",
            "!@#$%^&*() Special chars"
        ]
        
        model = EmptyTableModel(special_headers)
        
        assert model.columnCount() == len(special_headers)
        
        # Test that headers are returned correctly
        for i, expected_header in enumerate(special_headers):
            header = model.headerData(i, 1, 0)
            assert header == expected_header

    def test_model_interface_completeness(self) -> None:
        """Test that model implements required QAbstractTableModel interface."""
        headers = ["Test"]
        model = EmptyTableModel(headers)
        
        # Check that all required methods exist and are callable
        assert hasattr(model, 'rowCount') and callable(model.rowCount)
        assert hasattr(model, 'columnCount') and callable(model.columnCount)
        assert hasattr(model, 'data') and callable(model.data)
        assert hasattr(model, 'headerData') and callable(model.headerData)
        
        # Check custom methods
        assert hasattr(model, 'clearAllCheckboxes') and callable(model.clearAllCheckboxes)
        assert hasattr(model, 'uncheckCheckBox') and callable(model.uncheckCheckBox)

    def test_multiple_instances_independence(self) -> None:
        """Test that multiple model instances are independent."""
        headers1 = ["A", "B"]
        headers2 = ["X", "Y", "Z"]
        
        model1 = EmptyTableModel(headers1)
        model2 = EmptyTableModel(headers2)
        
        # Models should be independent
        assert model1.columnCount() == 2
        assert model2.columnCount() == 3
        assert model1.headers != model2.headers
        
        # Modifying one shouldn't affect the other
        model1.headers.append("C")
        assert len(model2.headers) == 3  # Should be unchanged 