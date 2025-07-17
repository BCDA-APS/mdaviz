"""Tests for Virtual Table Model classes."""

from typing import TYPE_CHECKING, Any
from unittest.mock import Mock

import pytest
from PyQt6.QtCore import QModelIndex, Qt

from mdaviz.virtual_table_model import (
    MDAVirtualDataProvider,
    VirtualDataProvider,
    VirtualTableModel,
)

if TYPE_CHECKING:
    from _pytest.fixtures import FixtureRequest
    from pytest_mock.plugin import MockerFixture


class TestVirtualDataProvider:
    """Test suite for VirtualDataProvider abstract base class."""

    def test_abstract_methods_raise_not_implemented(self) -> None:
        """Test that all abstract methods raise NotImplementedError."""
        provider = VirtualDataProvider()
        
        with pytest.raises(NotImplementedError):
            provider.get_row_count()
        
        with pytest.raises(NotImplementedError):
            provider.get_column_count()
        
        with pytest.raises(NotImplementedError):
            provider.get_column_headers()
        
        with pytest.raises(NotImplementedError):
            provider.get_data(0, 0)
        
        with pytest.raises(NotImplementedError):
            provider.load_data_range(0, 10)
        
        with pytest.raises(NotImplementedError):
            provider.is_data_loaded(0)
        
        with pytest.raises(NotImplementedError):
            provider.clear_cache()


class MockDataProvider(VirtualDataProvider):
    """Mock implementation of VirtualDataProvider for testing."""

    def __init__(self, rows: int = 100, columns: int = 3) -> None:
        """Initialize mock provider with specified dimensions."""
        self.rows = rows
        self.columns = columns
        self.headers = [f"Column {i+1}" for i in range(columns)]
        self.loaded_ranges: list[tuple[int, int]] = []
        self.cache_cleared = False

    def get_row_count(self) -> int:
        """Get the total number of rows."""
        return self.rows

    def get_column_count(self) -> int:
        """Get the total number of columns."""
        return self.columns

    def get_column_headers(self) -> list[str]:
        """Get the column headers."""
        return self.headers

    def get_data(self, row: int, column: int) -> Any:
        """Get data for a specific cell."""
        if row < 0 or row >= self.rows or column < 0 or column >= self.columns:
            return None
        return f"Row{row}Col{column}"

    def load_data_range(self, start_row: int, end_row: int) -> None:
        """Load data for a specific range of rows."""
        self.loaded_ranges.append((start_row, end_row))

    def is_data_loaded(self, row: int) -> bool:
        """Check if data for a specific row is loaded."""
        for start, end in self.loaded_ranges:
            if start <= row < end:
                return True
        return False

    def clear_cache(self) -> None:
        """Clear any cached data."""
        self.cache_cleared = True
        self.loaded_ranges.clear()


class TestVirtualTableModel:
    """Test suite for VirtualTableModel class."""

    @pytest.fixture
    def mock_provider(self) -> MockDataProvider:
        """Create a mock data provider for testing."""
        return MockDataProvider(rows=50, columns=4)

    def test_init_with_default_values(self, mock_provider) -> None:
        """Test initialization with default values."""
        model = VirtualTableModel(mock_provider)
        
        assert model.data_provider == mock_provider
        assert model.page_size == 100
        assert model.preload_pages == 2

    def test_init_with_custom_values(self, mock_provider, qtbot) -> None:
        """Test initialization with custom values."""
        from PyQt6.QtWidgets import QWidget
        parent = QWidget()
        qtbot.addWidget(parent)
        
        model = VirtualTableModel(mock_provider, page_size=50, preload_pages=1, parent=parent)
        
        assert model.data_provider == mock_provider
        assert model.page_size == 50
        assert model.preload_pages == 1
        assert model.parent() == parent

    def test_row_count(self, mock_provider) -> None:
        """Test row count delegation to provider."""
        model = VirtualTableModel(mock_provider)
        assert model.rowCount() == 50

    def test_column_count(self, mock_provider) -> None:
        """Test column count delegation to provider."""
        model = VirtualTableModel(mock_provider)
        assert model.columnCount() == 4

    def test_data_valid_index(self, mock_provider) -> None:
        """Test data retrieval with valid index."""
        model = VirtualTableModel(mock_provider)
        
        # Initially no data is loaded
        mock_provider.loaded_ranges.clear()
        
        index = model.createIndex(5, 2)
        data = model.data(index, Qt.ItemDataRole.DisplayRole)
        
        # Should load data and return expected value
        assert data == "Row5Col2"
        assert len(mock_provider.loaded_ranges) > 0

    def test_data_invalid_index(self, mock_provider) -> None:
        """Test data retrieval with invalid index."""
        model = VirtualTableModel(mock_provider)
        
        invalid_index = QModelIndex()
        data = model.data(invalid_index, Qt.ItemDataRole.DisplayRole)
        
        assert data.isNull()

    def test_data_non_display_role(self, mock_provider) -> None:
        """Test data retrieval with non-display role."""
        model = VirtualTableModel(mock_provider)
        
        index = model.createIndex(0, 0)
        data = model.data(index, Qt.ItemDataRole.EditRole)
        
        assert data.isNull()

    def test_header_data_horizontal(self, mock_provider) -> None:
        """Test horizontal header data retrieval."""
        model = VirtualTableModel(mock_provider)
        
        for i in range(4):
            header = model.headerData(i, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
            assert header == f"Column {i+1}"

    def test_header_data_vertical(self, mock_provider) -> None:
        """Test vertical header data retrieval (row numbers)."""
        model = VirtualTableModel(mock_provider)
        
        # Should return row numbers starting from 1
        for i in range(5):
            header = model.headerData(i, Qt.Orientation.Vertical, Qt.ItemDataRole.DisplayRole)
            assert header == str(i + 1)

    def test_header_data_out_of_bounds(self, mock_provider) -> None:
        """Test header data with out of bounds section."""
        model = VirtualTableModel(mock_provider)
        
        header = model.headerData(10, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
        assert header.isNull()

    def test_header_data_non_display_role(self, mock_provider) -> None:
        """Test header data with non-display role."""
        model = VirtualTableModel(mock_provider)
        
        header = model.headerData(0, Qt.Orientation.Horizontal, Qt.ItemDataRole.EditRole)
        assert header.isNull()

    def test_ensure_data_loaded_when_not_loaded(self, mock_provider) -> None:
        """Test _ensure_data_loaded when data is not loaded."""
        model = VirtualTableModel(mock_provider, page_size=10)
        
        # Clear any previous loads
        mock_provider.loaded_ranges.clear()
        
        # Access row 25 (page 2)
        model._ensure_data_loaded(25)
        
        # Should load page 2 (rows 20-30)
        assert (20, 30) in mock_provider.loaded_ranges

    def test_ensure_data_loaded_when_already_loaded(self, mock_provider) -> None:
        """Test _ensure_data_loaded when data is already loaded."""
        model = VirtualTableModel(mock_provider, page_size=10)
        
        # Manually mark data as loaded
        mock_provider.loaded_ranges = [(20, 30)]
        
        # Access row 25 (should be already loaded)
        initial_loads = len(mock_provider.loaded_ranges)
        model._ensure_data_loaded(25)
        
        # Should not trigger additional loads
        assert len(mock_provider.loaded_ranges) == initial_loads

    def test_set_visible_range_single_page(self, mock_provider) -> None:
        """Test set_visible_range with single page."""
        model = VirtualTableModel(mock_provider, page_size=20, preload_pages=1)
        
        mock_provider.loaded_ranges.clear()
        model.set_visible_range(10, 15)
        
        # Should load pages 0 and 1 (with preloading)
        loaded_starts = [start for start, end in mock_provider.loaded_ranges]
        assert 0 in loaded_starts or 20 in loaded_starts

    def test_set_visible_range_multiple_pages(self, mock_provider) -> None:
        """Test set_visible_range spanning multiple pages."""
        model = VirtualTableModel(mock_provider, page_size=10, preload_pages=0)
        
        mock_provider.loaded_ranges.clear()
        model.set_visible_range(15, 25)
        
        # Should load pages 1 and 2
        assert len(mock_provider.loaded_ranges) >= 2

    def test_set_visible_range_with_preloading(self, mock_provider) -> None:
        """Test set_visible_range with preloading enabled."""
        model = VirtualTableModel(mock_provider, page_size=10, preload_pages=2)
        
        mock_provider.loaded_ranges.clear()
        model.set_visible_range(20, 25)
        
        # Should load more pages due to preloading
        assert len(mock_provider.loaded_ranges) > 1

    def test_clear_cache(self, mock_provider) -> None:
        """Test cache clearing delegation to provider."""
        model = VirtualTableModel(mock_provider)
        
        model.clear_cache()
        assert mock_provider.cache_cleared is True


class TestMDAVirtualDataProvider:
    """Test suite for MDAVirtualDataProvider class."""

    @pytest.fixture
    def sample_scan_dict(self) -> dict[str, Any]:
        """Create sample scan dictionary for testing."""
        return {
            "pos1": {
                "name": "X Position",
                "data": [1.0, 2.0, 3.0, 4.0, 5.0],
                "unit": "mm"
            },
            "det1": {
                "name": "Ion Chamber",
                "data": [100, 150, 200, 175, 120],
                "unit": "counts"
            },
            "det2": {
                "name": "Photodiode",
                "data": [50.5, 75.2, 100.8, 87.3, 60.1],
                "unit": "mV"
            }
        }

    def test_init_with_scan_dict(self, sample_scan_dict) -> None:
        """Test initialization with scan dictionary."""
        provider = MDAVirtualDataProvider(sample_scan_dict, cache_size=500)
        
        assert provider.scan_dict == sample_scan_dict
        assert provider.cache_size == 500
        assert provider._data_cache == {}
        assert provider._column_headers is None
        assert provider._row_count is None

    def test_init_with_empty_scan_dict(self) -> None:
        """Test initialization with empty scan dictionary."""
        provider = MDAVirtualDataProvider({})
        
        assert provider.scan_dict == {}
        assert provider.cache_size == 1000  # default

    def test_get_row_count_with_data(self, sample_scan_dict) -> None:
        """Test get_row_count with data."""
        provider = MDAVirtualDataProvider(sample_scan_dict)
        
        assert provider.get_row_count() == 5
        assert provider._row_count == 5  # Should be cached

    def test_get_row_count_empty_data(self) -> None:
        """Test get_row_count with empty data."""
        provider = MDAVirtualDataProvider({})
        
        assert provider.get_row_count() == 0

    def test_get_row_count_empty_data_arrays(self) -> None:
        """Test get_row_count with empty data arrays."""
        scan_dict = {
            "pos1": {"name": "Position", "data": []},
            "det1": {"name": "Detector", "data": []}
        }
        provider = MDAVirtualDataProvider(scan_dict)
        
        assert provider.get_row_count() == 0

    def test_get_column_count(self, sample_scan_dict) -> None:
        """Test get_column_count."""
        provider = MDAVirtualDataProvider(sample_scan_dict)
        
        assert provider.get_column_count() == 3

    def test_get_column_count_empty(self) -> None:
        """Test get_column_count with empty data."""
        provider = MDAVirtualDataProvider({})
        
        assert provider.get_column_count() == 0

    def test_get_column_headers(self, sample_scan_dict) -> None:
        """Test get_column_headers."""
        provider = MDAVirtualDataProvider(sample_scan_dict)
        
        headers = provider.get_column_headers()
        expected = ["X Position", "Ion Chamber", "Photodiode"]
        assert headers == expected
        assert provider._column_headers == expected  # Should be cached

    def test_get_column_headers_empty(self) -> None:
        """Test get_column_headers with empty data."""
        provider = MDAVirtualDataProvider({})
        
        assert provider.get_column_headers() == []

    def test_get_data_valid_indices(self, sample_scan_dict) -> None:
        """Test get_data with valid indices."""
        provider = MDAVirtualDataProvider(sample_scan_dict)
        
        # Test various valid cells
        assert provider.get_data(0, 0) == 1.0
        assert provider.get_data(2, 1) == 200
        assert provider.get_data(4, 2) == 60.1

    def test_get_data_invalid_indices(self, sample_scan_dict) -> None:
        """Test get_data with invalid indices."""
        provider = MDAVirtualDataProvider(sample_scan_dict)
        
        # Test out-of-bounds indices
        assert provider.get_data(-1, 0) is None  # Negative row
        assert provider.get_data(0, -1) is None  # Negative column
        assert provider.get_data(10, 0) is None  # Row out of bounds
        assert provider.get_data(0, 10) is None  # Column out of bounds

    def test_get_data_empty_scan_dict(self) -> None:
        """Test get_data with empty scan dictionary."""
        provider = MDAVirtualDataProvider({})
        
        assert provider.get_data(0, 0) is None

    def test_load_data_range_no_op(self, sample_scan_dict) -> None:
        """Test load_data_range (should be no-op)."""
        provider = MDAVirtualDataProvider(sample_scan_dict)
        
        # Should not raise exception
        provider.load_data_range(0, 5)
        provider.load_data_range(10, 20)

    def test_is_data_loaded(self, sample_scan_dict) -> None:
        """Test is_data_loaded."""
        provider = MDAVirtualDataProvider(sample_scan_dict)
        
        # Valid rows should be loaded
        assert provider.is_data_loaded(0) is True
        assert provider.is_data_loaded(4) is True
        
        # Invalid rows should not be loaded
        assert provider.is_data_loaded(5) is False
        assert provider.is_data_loaded(10) is False

    def test_is_data_loaded_empty(self) -> None:
        """Test is_data_loaded with empty data."""
        provider = MDAVirtualDataProvider({})
        
        assert provider.is_data_loaded(0) is False

    def test_clear_cache(self, sample_scan_dict) -> None:
        """Test clear_cache."""
        provider = MDAVirtualDataProvider(sample_scan_dict)
        
        # Add some data to cache
        provider._data_cache[0] = [1, 2, 3]
        provider._data_cache[1] = [4, 5, 6]
        
        provider.clear_cache()
        assert provider._data_cache == {}

    def test_get_memory_usage_mb(self, sample_scan_dict) -> None:
        """Test get_memory_usage_mb calculation."""
        provider = MDAVirtualDataProvider(sample_scan_dict)
        
        usage = provider.get_memory_usage_mb()
        
        # Should be a positive number
        assert usage > 0
        assert isinstance(usage, float)

    def test_get_memory_usage_mb_empty(self) -> None:
        """Test get_memory_usage_mb with empty data."""
        provider = MDAVirtualDataProvider({})
        
        usage = provider.get_memory_usage_mb()
        assert usage == 0.0

    def test_get_memory_usage_mb_no_data(self) -> None:
        """Test get_memory_usage_mb with scan dict but no data."""
        scan_dict = {
            "pos1": {"name": "Position", "data": []},
            "det1": {"name": "Detector"}  # No data key
        }
        provider = MDAVirtualDataProvider(scan_dict)
        
        usage = provider.get_memory_usage_mb()
        assert usage == 0.0

    def test_varying_data_lengths(self) -> None:
        """Test provider with varying data lengths across columns."""
        scan_dict = {
            "pos1": {"name": "Position", "data": [1, 2, 3]},
            "det1": {"name": "Detector", "data": [10, 20]}  # Shorter
        }
        provider = MDAVirtualDataProvider(scan_dict)
        
        # Row count should be based on first column
        assert provider.get_row_count() == 3
        
        # Accessing shorter column beyond its length should return None
        assert provider.get_data(0, 1) == 10  # Valid
        assert provider.get_data(2, 1) is None  # Beyond det1 data

    def test_integration_with_virtual_table_model(self, sample_scan_dict) -> None:
        """Test MDAVirtualDataProvider integration with VirtualTableModel."""
        provider = MDAVirtualDataProvider(sample_scan_dict)
        model = VirtualTableModel(provider, page_size=3)
        
        # Test basic functionality
        assert model.rowCount() == 5
        assert model.columnCount() == 3
        
        # Test data access
        index = model.createIndex(1, 2)
        data = model.data(index, Qt.ItemDataRole.DisplayRole)
        assert data == 75.2
        
        # Test headers
        header = model.headerData(0, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
        assert header == "X Position" 