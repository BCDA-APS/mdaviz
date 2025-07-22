"""
Virtual table model for efficient data display.

This module provides a virtual table model that can handle large datasets
efficiently by loading data on-demand and caching frequently accessed items.

.. autosummary::

    ~VirtualTableModel
    ~VirtualDataProvider
    ~MDAVirtualDataProvider
"""

from typing import Any, Optional
from PyQt6.QtCore import QVariant
from PyQt6.QtCore import QAbstractTableModel


class VirtualDataProvider:
    """
    Abstract base class for data providers in virtual table models.

    This class defines the interface that data providers must implement
    to work with the VirtualTableModel.
    """

    def get_row_count(self) -> int:
        """
        Get the total number of rows in the dataset.

        Returns:
            int: Total number of rows
        """
        raise NotImplementedError

    def get_column_count(self) -> int:
        """
        Get the total number of columns in the dataset.

        Returns:
            int: Total number of columns
        """
        raise NotImplementedError

    def get_column_headers(self) -> list[str]:
        """
        Get the column headers.

        Returns:
            list[str]: List of column header strings
        """
        raise NotImplementedError

    def get_data(self, row: int, column: int) -> Any:
        """
        Get data for a specific cell.

        Parameters:
            row (int): Row index
            column (int): Column index

        Returns:
            Any: Data for the specified cell
        """
        raise NotImplementedError

    def load_data_range(self, start_row: int, end_row: int) -> None:
        """
        Load data for a specific range of rows.

        This method is called by the virtual table model when it needs
        to load data for a visible range of rows.

        Parameters:
            start_row (int): Starting row index (inclusive)
            end_row (int): Ending row index (exclusive)
        """
        raise NotImplementedError

    def is_data_loaded(self, row: int) -> bool:
        """
        Check if data for a specific row is loaded.

        Parameters:
            row (int): Row index

        Returns:
            bool: True if data is loaded, False otherwise
        """
        raise NotImplementedError

    def clear_cache(self) -> None:
        """
        Clear any cached data.

        This method should clear any internal caches maintained by the
        data provider to free up memory.
        """
        raise NotImplementedError


class VirtualTableModel(QAbstractTableModel):
    """
    Virtual table model for handling large datasets efficiently.

    This model implements virtual scrolling by loading data on-demand
    and only keeping a subset of the data in memory at any time.

    Attributes:
        data_provider (VirtualDataProvider): Provider for the actual data
        page_size (int): Number of rows to load per page
        preload_pages (int): Number of pages to preload
    """

    def __init__(
        self,
        data_provider: VirtualDataProvider,
        page_size: int = 100,
        preload_pages: int = 2,
        parent=None,
    ):
        """
        Initialize the virtual table model.

        Parameters:
            data_provider (VirtualDataProvider): Provider for the data
            page_size (int): Number of rows to load per page
            preload_pages (int): Number of pages to preload
            parent (QObject, optional): Parent object
        """
        super().__init__(parent)
        self.data_provider = data_provider
        self.page_size = page_size
        self.preload_pages = preload_pages

    def rowCount(self, parent=None):
        """Get the total number of rows."""
        return self.data_provider.get_row_count()

    def columnCount(self, parent=None):
        """Get the total number of columns."""
        return self.data_provider.get_column_count()

    def data(self, index, role=0):  # 0 = Qt.DisplayRole
        """Get data for a specific index and role."""
        if not index.isValid():
            return QVariant()

        if role == 0:  # Qt.DisplayRole
            row = index.row()
            column = index.column()

            # Ensure data is loaded for this row
            self._ensure_data_loaded(row)

            # Get data from provider
            return self.data_provider.get_data(row, column)

        return QVariant()

    def headerData(self, section, orientation, role=0):  # 0 = Qt.DisplayRole
        """Get header data for the table."""
        if role == 0:  # Qt.DisplayRole
            from PyQt6.QtCore import Qt

            if orientation == Qt.Orientation.Horizontal:
                headers = self.data_provider.get_column_headers()
                if 0 <= section < len(headers):
                    return headers[section]
            else:
                return str(section + 1)  # Row numbers

        return QVariant()

    def _ensure_data_loaded(self, row: int) -> None:
        """
        Ensure that data for a specific row is loaded.

        Parameters:
            row (int): Row index
        """
        if self.data_provider.is_data_loaded(row):
            return

        # Calculate the page for this row
        page = row // self.page_size
        start_row = page * self.page_size
        end_row = min(start_row + self.page_size, self.data_provider.get_row_count())

        # Load the page
        self.data_provider.load_data_range(start_row, end_row)

    def set_visible_range(self, start_row: int, end_row: int) -> None:
        """
        Set the currently visible range of rows.

        This method is called by the view to inform the model about
        which rows are currently visible, allowing for preloading.

        Parameters:
            start_row (int): Starting row index (inclusive)
            end_row (int): Ending row index (exclusive)
        """
        # Calculate pages to load
        start_page = start_row // self.page_size
        end_page = (end_row - 1) // self.page_size

        # Preload additional pages
        preload_start = max(0, start_page - self.preload_pages)
        preload_end = min(
            end_page + self.preload_pages + 1,
            (self.data_provider.get_row_count() - 1) // self.page_size + 1,
        )

        # Load all required pages
        for page in range(preload_start, preload_end):
            page_start = page * self.page_size
            page_end = min(
                page_start + self.page_size, self.data_provider.get_row_count()
            )
            self.data_provider.load_data_range(page_start, page_end)

    def clear_cache(self) -> None:
        """Clear the loaded data cache."""
        self.data_provider.clear_cache()


class MDAVirtualDataProvider(VirtualDataProvider):
    """
    Data provider for MDA file data in virtual table models.

    This provider handles loading and caching of MDA file data for
    display in virtual table models.
    """

    def __init__(self, scan_dict: dict[str, Any], cache_size: int = 1000):
        """
        Initialize the MDA data provider.

        Parameters:
            scan_dict (Dict[str, Any]): Scan dictionary from MDA file
            cache_size (int): Size of the data cache
        """
        self.scan_dict = scan_dict
        self.cache_size = cache_size
        self._data_cache: dict[int, list[Any]] = {}
        self._column_headers: Optional[list[str]] = None
        self._row_count: Optional[int] = None

    def get_row_count(self) -> int:
        """Get the total number of rows."""
        if self._row_count is None:
            if self.scan_dict:
                # Get the length of the first data array
                first_data = next(iter(self.scan_dict.values()))["data"]
                self._row_count = len(first_data) if first_data else 0
            else:
                self._row_count = 0
        return self._row_count

    def get_column_count(self) -> int:
        """Get the total number of columns."""
        return len(self.scan_dict) if self.scan_dict else 0

    def get_column_headers(self) -> list[str]:
        """Get the column headers."""
        if self._column_headers is None:
            self._column_headers = [v["name"] for v in self.scan_dict.values()]
        return self._column_headers

    def get_data(self, row: int, column: int) -> Any:
        """Get data for a specific cell."""
        if not self.scan_dict or row < 0 or column < 0:
            return None

        # Get the column key
        column_keys = list(self.scan_dict.keys())
        if column >= len(column_keys):
            return None

        column_key = column_keys[column]
        column_data = self.scan_dict[column_key]["data"]

        if row < len(column_data):
            return column_data[row]

        return None

    def load_data_range(self, start_row: int, end_row: int) -> None:
        """
        Load data for a specific range of rows.

        For MDA data, this is a no-op since all data is already loaded
        in the scan_dict. This method is provided for interface compatibility.

        Parameters:
            start_row (int): Starting row index (inclusive)
            end_row (int): Ending row index (exclusive)
        """
        # MDA data is already fully loaded, so no additional loading is needed
        pass

    def is_data_loaded(self, row: int) -> bool:
        """
        Check if data for a specific row is loaded.

        Parameters:
            row (int): Row index

        Returns:
            bool: True if data is loaded, False otherwise
        """
        return row < self.get_row_count()

    def clear_cache(self) -> None:
        """Clear the data cache."""
        self._data_cache.clear()

    def get_memory_usage_mb(self) -> float:
        """
        Get the approximate memory usage in megabytes.

        Returns:
            float: Memory usage in MB
        """
        total_size = 0
        for value in self.scan_dict.values():
            data = value.get("data", [])
            if data:
                # Rough estimate: assume 8 bytes per number
                total_size += len(data) * 8

        return total_size / (1024 * 1024)
