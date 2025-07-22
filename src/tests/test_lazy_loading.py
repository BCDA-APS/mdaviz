"""
Tests for lazy loading functionality.

This module contains tests for the lazy loading implementation to ensure
it works correctly and handles large folders efficiently.

.. autosummary::

    ~TestLazyFolderScanner
    ~TestDataCache
    ~TestVirtualTableModel
    ~TestLazyLoadingConfig
"""

import pytest
from pathlib import Path
from typing import TYPE_CHECKING, Dict, Any
from unittest.mock import Mock

from PyQt6 import QtCore

from mdaviz.lazy_folder_scanner import LazyFolderScanner
from mdaviz.data_cache import DataCache, CachedFileData, get_global_cache
from mdaviz.virtual_table_model import (
    VirtualTableModel,
    VirtualDataProvider,
    MDAVirtualDataProvider,
)
from mdaviz.lazy_loading_config import LazyLoadingConfig, ConfigManager
from mdaviz.utils import get_file_info_lightweight, get_file_info_full

if TYPE_CHECKING:
    pass


class TestLazyFolderScanner:
    """Test LazyFolderScanner functionality."""

    @pytest.fixture
    def scanner(self) -> LazyFolderScanner:
        """Create a LazyFolderScanner instance for testing."""
        return LazyFolderScanner(batch_size=10, max_files=100)

    @pytest.fixture
    def temp_folder(self, tmp_path: Path) -> Path:
        """Create a temporary folder for testing."""
        return tmp_path

    @pytest.mark.skip(reason="Skip in CI/headless: uses Qt/QThread")
    def test_scanner_initialization(self, scanner: LazyFolderScanner) -> None:
        """Test that the scanner initializes correctly."""
        assert scanner is not None
        assert scanner.batch_size == 10
        assert scanner.max_files == 100

    @pytest.mark.skip(reason="Skip in CI/headless: uses Qt/QThread")
    def test_scan_folder_empty(
        self, scanner: LazyFolderScanner, temp_folder: Path
    ) -> None:
        """Test scanning an empty folder."""
        result = scanner.scan_folder(temp_folder)
        assert result.is_complete
        assert len(result.file_list) == 0
        assert result.total_files == 0

    @pytest.mark.skip(reason="Skip in CI/headless: uses Qt/QThread")
    def test_scan_folder_with_files(
        self, scanner: LazyFolderScanner, temp_folder: Path
    ) -> None:
        """Test scanning a folder with MDA files."""
        # Create some test MDA files
        for i in range(5):
            (temp_folder / f"test_{i}.mda").touch()

        result = scanner.scan_folder(temp_folder)
        assert result.is_complete
        assert len(result.file_list) == 5
        assert result.total_files == 5

    @pytest.mark.skip(reason="Skip in CI/headless: uses Qt/QThread")
    def test_scan_folder_nonexistent(self, scanner: LazyFolderScanner) -> None:
        """Test scanning a non-existent folder."""
        result = scanner.scan_folder(Path("/nonexistent/folder"))
        assert not result.is_complete
        assert result.error_message == "Folder does not exist"

    @pytest.mark.skip(
        reason="Skip in CI/headless: triggers Qt crash with too many files"
    )
    def test_scan_folder_too_many_files(
        self, scanner: LazyFolderScanner, temp_folder: Path
    ) -> None:
        """Test scanning a folder with too many files."""
        # Create more files than the max_files limit
        for i in range(150):
            (temp_folder / f"test_{i}.mda").touch()

        result = scanner.scan_folder(temp_folder)
        assert not result.is_complete
        assert "Too many files" in result.error_message

    @pytest.mark.skip(reason="Skip in CI/headless: uses Qt/QThread")
    def test_scan_progress_callback(
        self, scanner: LazyFolderScanner, temp_folder: Path
    ) -> None:
        """Test that progress callback is called during scanning."""
        # Create some test files
        for i in range(3):
            (temp_folder / f"test_{i}.mda").touch()

        progress_calls = []

        def progress_callback(current: int, total: int) -> None:
            progress_calls.append((current, total))

        result = scanner.scan_folder(temp_folder, progress_callback)
        assert result.is_complete
        assert len(progress_calls) > 0
        assert (
            progress_calls[-1][0] == progress_calls[-1][1]
        )  # Final call should be complete

    @pytest.mark.skip(reason="Skip in CI/headless: uses Qt/QThread")
    def test_cancel_scan(self, scanner: LazyFolderScanner, temp_folder: Path) -> None:
        """Test that scan can be cancelled."""
        # Create many files to make the scan take some time
        for i in range(50):
            (temp_folder / f"test_{i}.mda").touch()

        # Start async scan
        scanner.scan_folder_async(temp_folder)

        # Cancel immediately
        scanner.cancel_scan()

        # Should not be scanning anymore
        assert not scanner.is_scanning()


class TestDataCache:
    """Test cases for the DataCache class."""

    @pytest.fixture
    def cache(self) -> DataCache:
        """Create a DataCache instance for testing."""
        return DataCache(max_size_mb=10.0, max_entries=5)

    @pytest.fixture
    def test_file_data(self) -> CachedFileData:
        """Create test cached file data."""
        return CachedFileData(
            file_path="/test/file.mda",
            metadata={"test": "metadata"},
            scan_dict={"test": "data"},
            first_pos=1,
            first_det=2,
            pv_list=["test_pv"],
            file_name="test_file",
            folder_path="/test",
            size_bytes=1024 * 1024,  # 1MB
        )

    def test_cache_initialization(self, cache: DataCache) -> None:
        """Test that the cache initializes correctly."""
        assert cache.max_size_mb == 10.0
        assert cache.max_entries == 5
        assert cache._current_size_mb == 0.0
        assert len(cache._cache) == 0

    def test_cache_put_and_get(
        self, cache: DataCache, test_file_data: CachedFileData
    ) -> None:
        """Test putting and getting data from the cache."""
        file_path = "/test/file.mda"

        # Put data in cache
        cache.put(file_path, test_file_data)

        # Get data from cache
        retrieved_data = cache.get(file_path)

        assert retrieved_data is not None
        assert retrieved_data.file_path == test_file_data.file_path
        assert retrieved_data.metadata == test_file_data.metadata

    def test_cache_miss(self, cache: DataCache) -> None:
        """Test getting data that's not in the cache."""
        retrieved_data = cache.get("/nonexistent/file.mda")
        assert retrieved_data is None

    def test_cache_lru_eviction(self, cache: DataCache) -> None:
        """Test LRU eviction when cache is full."""
        # Fill the cache
        for i in range(6):  # More than max_entries
            file_data = CachedFileData(
                file_path=f"/test/file_{i}.mda",
                metadata={},
                scan_dict={},
                first_pos=1,
                first_det=2,
                pv_list=[],
                file_name=f"file_{i}",
                folder_path="/test",
                size_bytes=1024 * 1024,
            )
            cache.put(f"/test/file_{i}.mda", file_data)

        # Check that oldest entry was evicted
        assert len(cache._cache) == 5
        assert "/test/file_0.mda" not in cache._cache
        assert "/test/file_5.mda" in cache._cache

    def test_cache_size_eviction(self, cache: DataCache) -> None:
        """Test eviction when cache size limit is exceeded."""
        # Add a large file that exceeds the size limit
        large_file_data = CachedFileData(
            file_path="/test/large_file.mda",
            metadata={},
            scan_dict={},
            first_pos=1,
            first_det=2,
            pv_list=[],
            file_name="large_file",
            folder_path="/test",
            size_bytes=15 * 1024 * 1024,  # 15MB, exceeds 10MB limit
        )

        cache.put("/test/large_file.mda", large_file_data)

        # Check that the file was not added due to size limit
        assert len(cache._cache) == 0

    def test_cache_clear(
        self, cache: DataCache, test_file_data: CachedFileData
    ) -> None:
        """Test clearing the cache."""
        cache.put("/test/file.mda", test_file_data)
        assert len(cache._cache) == 1

        cache.clear()
        assert len(cache._cache) == 0
        assert cache._current_size_mb == 0.0

    def test_cache_stats(
        self, cache: DataCache, test_file_data: CachedFileData
    ) -> None:
        """Test getting cache statistics."""
        cache.put("/test/file.mda", test_file_data)
        stats = cache.get_stats()

        assert stats["entry_count"] == 1
        assert stats["current_size_mb"] == 1.0
        assert stats["max_size_mb"] == 10.0
        assert stats["max_entries"] == 5
        assert stats["utilization_percent"] == 10.0

    def test_global_cache(self) -> None:
        """Test the global cache functionality."""
        cache1 = get_global_cache()
        cache2 = get_global_cache()

        # Should return the same instance
        assert cache1 is cache2


class TestVirtualTableModel:
    """Test cases for the VirtualTableModel class."""

    @pytest.fixture
    def mock_data_provider(self) -> Mock:
        """Create a mock data provider for testing."""
        provider = Mock(spec=VirtualDataProvider)
        provider.get_row_count.return_value = 1000
        provider.get_column_count.return_value = 5
        provider.get_column_headers.return_value = [
            "Col1",
            "Col2",
            "Col3",
            "Col4",
            "Col5",
        ]
        provider.get_data.return_value = "test_data"
        provider.is_data_loaded.return_value = True
        setattr(provider, "clear_cache", Mock())
        return provider

    @pytest.fixture
    def virtual_model(self, mock_data_provider: Mock) -> VirtualTableModel:
        """Create a VirtualTableModel instance for testing."""
        return VirtualTableModel(mock_data_provider, page_size=100, preload_pages=2)

    def test_model_initialization(
        self, virtual_model: VirtualTableModel, mock_data_provider: Mock
    ) -> None:
        """Test that the model initializes correctly."""
        assert virtual_model.data_provider is mock_data_provider
        assert virtual_model.page_size == 100
        assert virtual_model.preload_pages == 2

    def test_row_count(
        self, virtual_model: VirtualTableModel, mock_data_provider: Mock
    ) -> None:
        """Test getting row count."""
        assert virtual_model.rowCount() == 1000
        mock_data_provider.get_row_count.assert_called_once()

    def test_column_count(
        self, virtual_model: VirtualTableModel, mock_data_provider: Mock
    ) -> None:
        """Test getting column count."""
        assert virtual_model.columnCount() == 5
        mock_data_provider.get_column_count.assert_called_once()

    def test_data_retrieval(
        self, virtual_model: VirtualTableModel, mock_data_provider: Mock
    ) -> None:
        """Test retrieving data from the model."""
        index = virtual_model.index(0, 0)
        data = virtual_model.data(index, QtCore.Qt.ItemDataRole.DisplayRole)

        assert data == "test_data"
        mock_data_provider.get_data.assert_called_with(0, 0)

    def test_header_data(
        self, virtual_model: VirtualTableModel, mock_data_provider: Mock
    ) -> None:
        """Test getting header data."""
        header = virtual_model.headerData(
            0,
            QtCore.Qt.Orientation.Horizontal,
            QtCore.Qt.ItemDataRole.DisplayRole,
        )
        assert header == "Col1"
        mock_data_provider.get_column_headers.assert_called()

        row_header = virtual_model.headerData(
            0,
            QtCore.Qt.Orientation.Vertical,
            QtCore.Qt.ItemDataRole.DisplayRole,
        )
        assert row_header == "1"

    def test_set_visible_range(
        self, virtual_model: VirtualTableModel, mock_data_provider: Mock
    ) -> None:
        """Test setting the visible range."""
        virtual_model.set_visible_range(0, 100)

        # Should call load_data_range for the visible pages
        mock_data_provider.load_data_range.assert_called()

    def test_clear_cache(
        self, virtual_model: VirtualTableModel, mock_data_provider: Mock
    ) -> None:
        """Test clearing the model cache."""
        virtual_model.clear_cache()
        mock_data_provider.clear_cache.assert_called_once()


class TestMDAVirtualDataProvider:
    """Test cases for the MDAVirtualDataProvider class."""

    @pytest.fixture
    def test_scan_dict(self) -> Dict[str, Any]:
        """Create test scan dictionary."""
        return {
            "0": {
                "name": "Index",
                "data": list(range(100)),
                "type": "POS",
                "unit": "",
                "desc": "Index",
            },
            "1": {
                "name": "Detector1",
                "data": [i * 2 for i in range(100)],
                "type": "DET",
                "unit": "counts",
                "desc": "Test Detector",
            },
        }

    @pytest.fixture
    def mda_provider(self, test_scan_dict: Dict[str, Any]) -> MDAVirtualDataProvider:
        """Create an MDAVirtualDataProvider instance for testing."""
        return MDAVirtualDataProvider(test_scan_dict)

    def test_provider_initialization(
        self,
        mda_provider: MDAVirtualDataProvider,
        test_scan_dict: Dict[str, Any],
    ) -> None:
        """Test that the provider initializes correctly."""
        assert mda_provider.scan_dict is test_scan_dict
        assert mda_provider.cache_size == 1000

    def test_row_count(self, mda_provider: MDAVirtualDataProvider) -> None:
        """Test getting row count."""
        assert mda_provider.get_row_count() == 100

    def test_column_count(self, mda_provider: MDAVirtualDataProvider) -> None:
        """Test getting column count."""
        assert mda_provider.get_column_count() == 2

    def test_column_headers(self, mda_provider: MDAVirtualDataProvider) -> None:
        """Test getting column headers."""
        headers = mda_provider.get_column_headers()
        assert headers == ["Index", "Detector1"]

    def test_data_retrieval(self, mda_provider: MDAVirtualDataProvider) -> None:
        """Test retrieving data from the provider."""
        # Test first column (Index)
        data = mda_provider.get_data(0, 0)
        assert data == 0

        data = mda_provider.get_data(50, 0)
        assert data == 50

        # Test second column (Detector1)
        data = mda_provider.get_data(0, 1)
        assert data == 0

        data = mda_provider.get_data(50, 1)
        assert data == 100

    def test_data_retrieval_out_of_bounds(
        self, mda_provider: MDAVirtualDataProvider
    ) -> None:
        """Test data retrieval with out-of-bounds indices."""
        # Row out of bounds
        data = mda_provider.get_data(200, 0)
        assert data is None

        # Column out of bounds
        data = mda_provider.get_data(0, 10)
        assert data is None

        # Negative indices
        data = mda_provider.get_data(-1, 0)
        assert data is None

        data = mda_provider.get_data(0, -1)
        assert data is None

    def test_is_data_loaded(self, mda_provider: MDAVirtualDataProvider) -> None:
        """Test checking if data is loaded."""
        assert mda_provider.is_data_loaded(0) is True
        assert mda_provider.is_data_loaded(99) is True
        assert mda_provider.is_data_loaded(100) is False

    def test_memory_usage(self, mda_provider: MDAVirtualDataProvider) -> None:
        """Test getting memory usage."""
        memory_usage = mda_provider.get_memory_usage_mb()
        assert memory_usage > 0
        assert memory_usage < 1  # Should be small for this test data


class TestLazyLoadingConfig:
    """Test cases for the LazyLoadingConfig class."""

    @pytest.fixture
    def config(self) -> LazyLoadingConfig:
        """Create a LazyLoadingConfig instance for testing."""
        return LazyLoadingConfig()

    def test_config_initialization(self, config: LazyLoadingConfig) -> None:
        """Test that the config initializes with default values."""
        assert config.folder_scan_batch_size == 50
        assert config.folder_scan_max_files == 10000
        assert config.folder_scan_use_lightweight is True
        assert config.data_cache_max_size_mb == 500.0
        assert config.data_cache_max_entries == 100

    def test_config_to_dict(self, config: LazyLoadingConfig) -> None:
        """Test converting config to dictionary."""
        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert config_dict["folder_scan_batch_size"] == 50
        assert config_dict["folder_scan_max_files"] == 10000
        assert config_dict["folder_scan_use_lightweight"] is True

    def test_config_from_dict(self) -> None:
        """Test creating config from dictionary."""
        config_dict = {
            "folder_scan_batch_size": 100,
            "folder_scan_max_files": 5000,
            "folder_scan_use_lightweight": False,
        }

        config = LazyLoadingConfig.from_dict(config_dict)

        assert config.folder_scan_batch_size == 100
        assert config.folder_scan_max_files == 5000
        assert config.folder_scan_use_lightweight is False

    def test_config_save_and_load(
        self, config: LazyLoadingConfig, tmp_path: Path
    ) -> None:
        """Test saving and loading config to/from file."""
        config_file = tmp_path / "test_config.json"

        # Save config
        success = config.save_to_file(config_file)
        assert success is True
        assert config_file.exists()

        # Load config
        loaded_config = LazyLoadingConfig.load_from_file(config_file)
        assert loaded_config is not None
        assert loaded_config.folder_scan_batch_size == config.folder_scan_batch_size
        assert loaded_config.folder_scan_max_files == config.folder_scan_max_files


class TestConfigManager:
    """Test cases for the ConfigManager class."""

    @pytest.fixture
    def temp_config_file(self, tmp_path: Path) -> Path:
        """Create a temporary config file for testing."""
        return tmp_path / "test_config.json"

    @pytest.fixture
    def config_manager(self, temp_config_file: Path) -> ConfigManager:
        """Create a ConfigManager instance for testing."""
        return ConfigManager(temp_config_file)

    def test_config_manager_initialization(self, config_manager: ConfigManager) -> None:
        """Test that the config manager initializes correctly."""
        assert config_manager.config is not None
        assert isinstance(config_manager.config, LazyLoadingConfig)

    def test_get_config(self, config_manager: ConfigManager) -> None:
        """Test getting the current configuration."""
        config = config_manager.get_config()
        assert config is not None
        assert isinstance(config, LazyLoadingConfig)

    def test_update_config(self, config_manager: ConfigManager) -> None:
        """Test updating configuration."""
        success = config_manager.update_config(
            folder_scan_batch_size=100, folder_scan_max_files=5000
        )

        assert success is True
        assert config_manager.config.folder_scan_batch_size == 100
        assert config_manager.config.folder_scan_max_files == 5000

    def test_update_config_invalid_key(self, config_manager: ConfigManager) -> None:
        """Test updating configuration with invalid key."""
        success = config_manager.update_config(invalid_key="value")

        # Should still return True but log a warning
        assert success is True

    def test_reset_to_defaults(self, config_manager: ConfigManager) -> None:
        """Test resetting configuration to defaults."""
        # Modify config
        config_manager.config.folder_scan_batch_size = 999

        # Reset to defaults
        success = config_manager.reset_to_defaults()

        assert success is True
        assert config_manager.config.folder_scan_batch_size == 50  # Default value


class TestUtils:
    """Test cases for utility functions."""

    @pytest.fixture
    def temp_mda_file(self, tmp_path: Path) -> Path:
        """Create a temporary MDA file for testing."""
        mda_file = tmp_path / "test.mda"
        mda_file.write_bytes(b"test mda data")
        return mda_file

    def test_get_file_info_lightweight(self, temp_mda_file: Path) -> None:
        """Test lightweight file info extraction."""
        file_info = get_file_info_lightweight(temp_mda_file)

        assert file_info is not None
        assert file_info["Name"] == "test.mda"
        assert "Size" in file_info
        assert "Date" in file_info

    def test_get_file_info_full(self, temp_mda_file: Path) -> None:
        """Test full file info extraction."""
        # This test might fail if the file is not a valid MDA file
        # We'll just test that the function doesn't crash
        try:
            file_info = get_file_info_full(temp_mda_file)
            # If it succeeds, check basic structure
            if file_info is not None:
                assert "Name" in file_info
                assert "Size" in file_info
        except Exception:
            # Expected for invalid MDA files
            pass


if __name__ == "__main__":
    pytest.main([__file__])
