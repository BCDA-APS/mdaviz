"""
Enhanced MDA file management with optimized loading and caching.

This module provides advanced MDA file handling with performance optimizations,
asynchronous loading capabilities, and comprehensive error handling.

.. autosummary::

    ~MDAFile
    ~TabManager
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtWidgets import QAbstractItemView, QWidget

from mdaviz.synApps_mdalib.mda import readMDA
from mdaviz.data_cache import get_global_cache, CachedFileData
from mdaviz.mda_file_table_view import MDAFileTableView
from mdaviz.utils import OptimizedFileReader
from mdaviz import utils


class MDAFile(QWidget):
    """
    Enhanced MDA file manager with optimized loading and caching.

    This widget provides advanced MDA file handling with performance optimizations,
    asynchronous loading capabilities, memory management, and comprehensive error handling.

    Attributes:
        enable_async_loading (bool): Whether to use asynchronous file loading
        preload_enabled (bool): Whether to preload adjacent files for faster navigation
        max_preload_files (int): Maximum number of files to preload
        memory_limit_mb (float): Memory limit for file operations
    """

    # Signals for async operations
    file_loading_started = pyqtSignal(str)  # file path
    file_loading_completed = pyqtSignal(str, bool)  # file path, success
    file_loading_progress = pyqtSignal(int, int)  # current, total
    memory_warning = pyqtSignal(float)  # memory usage in MB

    # UI file name matches this module, different extension
    ui_file = utils.getUiFileName(__file__)

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        enable_async_loading: bool = True,
        preload_enabled: bool = True,
        max_preload_files: int = 3,
        memory_limit_mb: float = 200.0,
    ) -> None:
        """
        Initialize the enhanced MDA file manager.

        Parameters:
            parent (Optional[QWidget]): Parent widget
            enable_async_loading (bool): Whether to use asynchronous file loading
            preload_enabled (bool): Whether to preload adjacent files
            max_preload_files (int): Maximum number of files to preload
            memory_limit_mb (float): Memory limit for file operations
        """
        super().__init__(parent)

        self.enable_async_loading = enable_async_loading
        self.preload_enabled = preload_enabled
        self.max_preload_files = max_preload_files
        self.memory_limit_mb = memory_limit_mb

        # Initialize optimized file reader
        self._file_reader = OptimizedFileReader(
            max_memory_mb=memory_limit_mb,
            enable_parallel=enable_async_loading,
            max_workers=4,
        )

        # Performance tracking
        self._load_times: Dict[str, float] = {}
        self._preloaded_files: Dict[str, CachedFileData] = {}
        self._loading_futures: Dict[str, asyncio.Future] = {}

        # Async loading support
        self._executor = (
            ThreadPoolExecutor(max_workers=2) if enable_async_loading else None
        )
        self._preload_timer = QTimer()
        self._preload_timer.setSingleShot(True)
        self._preload_timer.timeout.connect(self._perform_preload)

        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()

    def setup(self) -> None:
        """
        Set up the MDA file manager with enhanced features.

        This method initializes the UI components, connects signals,
        and sets up performance monitoring.
        """
        try:
            # Initialize data structure
            self._data: Dict[str, Any] = {}

            # Set up selection behavior
            self.tableView.setSelectionBehavior(
                QAbstractItemView.SelectionBehavior.SelectRows
            )

            # Initialize tab manager with enhanced features
            self.tabManager = TabManager(self)

            # Connect signals for performance monitoring
            self.file_loading_completed.connect(self._on_file_loaded)

            # Set up memory monitoring if available
            try:
                import psutil

                self._memory_timer = QTimer()
                self._memory_timer.timeout.connect(self._check_memory_usage)
                self._memory_timer.start(10000)  # Check every 10 seconds
            except ImportError:
                pass  # Memory monitoring not available

        except Exception as e:
            print(f"Error setting up MDA file manager: {e}")

    def setData(self, index: Optional[int] = None) -> None:
        """
        Enhanced data loading with async support and caching optimization.

        This method loads MDA file data with performance optimizations including
        asynchronous loading, intelligent caching, and memory management.

        Parameters:
            index (Optional[int]): The index of the file in the MDA file list.
                                 If None, clears the data.
        """
        if index is None:
            self._data = {}
            return

        try:
            # Get file information
        folder_path = self.dataPath()
            file_list = self.mdaFileList()

            if not file_list or index >= len(file_list):
                print(f"Invalid file index: {index}")
                self._data = {}
                return

            file_name = file_list[index]
            file_path = folder_path / file_name

            # Emit loading started signal
            self.file_loading_started.emit(str(file_path))

            # Track loading time
            start_time = time.time()

            # Try to load from cache first
            cache = get_global_cache()
            cached_data = cache.get(str(file_path))

            if cached_data:
                # Use cached data for immediate response
                self._populate_data_from_cache(cached_data, index)
                load_time = time.time() - start_time
                self._load_times[str(file_path)] = load_time
                self.file_loading_completed.emit(str(file_path), True)

                # Schedule preloading of adjacent files
                if self.preload_enabled:
                    self._schedule_preload(index)

                return

            # Load file data with optimization
            if self.enable_async_loading:
                self._load_file_async(file_path, index)
            else:
                self._load_file_sync(file_path, index)

        except Exception as e:
            print(f"Error in setData: {e}")
            self._create_fallback_data(index)
            self.file_loading_completed.emit(
                str(file_path) if "file_path" in locals() else "", False
            )

    def _load_file_sync(self, file_path: Path, index: int) -> None:
        """
        Synchronously load file data with optimizations.

        Parameters:
            file_path (Path): Path to the MDA file
            index (int): File index
        """
        try:
            start_time = time.time()

            # Use optimized file reader
            file_info = self._file_reader.read_file_optimized(file_path)
            if not file_info:
                raise ValueError(f"Could not read file: {file_path}")

            # Load full data using cache system
        cache = get_global_cache()
        cached_data = cache.get_or_load(str(file_path))

        if cached_data:
                self._populate_data_from_cache(cached_data, index)
            else:
                # Fallback direct loading
                self._load_direct(file_path, index)

            # Track performance
            load_time = time.time() - start_time
            self._load_times[str(file_path)] = load_time

            self.file_loading_completed.emit(str(file_path), True)

            # Schedule preloading
            if self.preload_enabled:
                self._schedule_preload(index)

        except Exception as e:
            print(f"Error loading file {file_path}: {e}")
            self._create_fallback_data(index)
            self.file_loading_completed.emit(str(file_path), False)

    def _load_file_async(self, file_path: Path, index: int) -> None:
        """
        Asynchronously load file data for better UI responsiveness.

        Parameters:
            file_path (Path): Path to the MDA file
            index (int): File index
        """
        if not self._executor:
            # Fallback to sync loading
            self._load_file_sync(file_path, index)
            return

        def load_worker():
            """Worker function for async loading."""
            try:
                start_time = time.time()

                # Load through cache system
                cache = get_global_cache()
                cached_data = cache.get_or_load(str(file_path))

                load_time = time.time() - start_time
                return cached_data, load_time, None

            except Exception as e:
                return None, 0.0, str(e)

        def on_complete(future):
            """Callback for async loading completion."""
            try:
                cached_data, load_time, error = future.result()

                if error:
                    print(f"Async loading error: {error}")
                    self._create_fallback_data(index)
                    self.file_loading_completed.emit(str(file_path), False)
                    return

                if cached_data:
                    self._populate_data_from_cache(cached_data, index)
                    self._load_times[str(file_path)] = load_time
                    self.file_loading_completed.emit(str(file_path), True)

                    # Schedule preloading
                    if self.preload_enabled:
                        self._schedule_preload(index)
                else:
                    self._create_fallback_data(index)
                    self.file_loading_completed.emit(str(file_path), False)

            except Exception as e:
                print(f"Error in async callback: {e}")
                self._create_fallback_data(index)
                self.file_loading_completed.emit(str(file_path), False)

        # Submit async task
        future = self._executor.submit(load_worker)
        future.add_done_callback(on_complete)

    def _populate_data_from_cache(
        self, cached_data: CachedFileData, index: int
    ) -> None:
        """
        Populate internal data structure from cached data.

        Parameters:
            cached_data (CachedFileData): Cached file data
            index (int): File index
        """
            self._data = {
                "fileName": cached_data.file_name,
                "filePath": cached_data.file_path,
                "folderPath": cached_data.folder_path,
                "metadata": cached_data.metadata,
                "scanDict": cached_data.scan_dict,
                "firstPos": cached_data.first_pos,
                "firstDet": cached_data.first_det,
                "pvList": cached_data.pv_list,
                "index": index,
            }

    def _load_direct(self, file_path: Path, index: int) -> None:
        """
        Direct file loading fallback method.

        Parameters:
            file_path (Path): Path to the MDA file
            index (int): File index
        """
            result = readMDA(str(file_path))
            if result is None:
            raise ValueError(f"Could not read file: {file_path}")

        file_metadata, file_data_dim1, *_ = result

        if file_metadata.get("rank", 0) > 1:
            print("WARNING: Multidimensional data not supported - ignoring ranks > 1.")

        scan_dict, first_pos, first_det = utils.get_scan(file_data_dim1)
        pv_list = [v["name"] for v in scan_dict.values()]

                self._data = {
                    "fileName": file_path.stem,
                    "filePath": str(file_path),
            "folderPath": str(file_path.parent),
            "metadata": file_metadata,
            "scanDict": scan_dict,
            "firstPos": first_pos,
            "firstDet": first_det,
            "pvList": pv_list,
                    "index": index,
                }

    def _create_fallback_data(self, index: int) -> None:
        """
        Create fallback data structure when loading fails.

        Parameters:
            index (int): File index
        """
        try:
            folder_path = self.dataPath()
            file_list = self.mdaFileList()

            if file_list and index < len(file_list):
                file_name = file_list[index]
                file_path = folder_path / file_name
            else:
                file_name = "unknown.mda"
                file_path = folder_path / file_name

            self._data = {
                "fileName": file_path.stem,
                "filePath": str(file_path),
                "folderPath": str(folder_path),
                "metadata": {},
                "scanDict": {},
                "firstPos": "P0",
                "firstDet": "D01",
                "pvList": [],
                "index": index,
            }
        except Exception as e:
            print(f"Error creating fallback data: {e}")
            self._data = {}

    def _schedule_preload(self, current_index: int) -> None:
        """
        Schedule preloading of adjacent files for faster navigation.

        Parameters:
            current_index (int): Current file index
        """
        if not self.preload_enabled:
            return

        # Delay preloading to avoid interfering with current operation
        self._preload_timer.start(500)  # 500ms delay

    def _perform_preload(self) -> None:
        """Perform preloading of adjacent files."""
        try:
            if not self._data or "index" not in self._data:
                return

            current_index = self._data["index"]
            file_list = self.mdaFileList()

            if not file_list:
                return

            folder_path = self.dataPath()
            cache = get_global_cache()

            # Determine files to preload (adjacent files)
            preload_indices = []
            for offset in range(1, self.max_preload_files + 1):
                # Next files
                if current_index + offset < len(file_list):
                    preload_indices.append(current_index + offset)
                # Previous files
                if current_index - offset >= 0:
                    preload_indices.append(current_index - offset)

            # Preload files that aren't already cached
            for idx in preload_indices:
                file_name = file_list[idx]
                file_path = str(folder_path / file_name)

                if not cache.get(file_path):
                    # Preload in background
                    cache.get_or_load(file_path)

        except Exception as e:
            print(f"Error during preloading: {e}")

    def _check_memory_usage(self) -> None:
        """Check memory usage and emit warnings if needed."""
        try:
            import psutil

            process = psutil.Process()
            memory_mb = process.memory_info().rss / (1024 * 1024)

            if memory_mb > self.memory_limit_mb:
                self.memory_warning.emit(memory_mb)
        except:
            pass

    def _on_file_loaded(self, file_path: str, success: bool) -> None:
        """
        Handle file loading completion.

        Parameters:
            file_path (str): Path of the loaded file
            success (bool): Whether loading was successful
        """
        if success and file_path in self._load_times:
            load_time = self._load_times[file_path]
            if load_time > 2.0:  # Slow loading threshold
                print(f"Slow file loading detected: {file_path} took {load_time:.2f}s")

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics for file operations.

        Returns:
            Dict[str, Any]: Performance statistics including load times and cache stats
        """
        stats = {
            "total_files_loaded": len(self._load_times),
            "average_load_time": sum(self._load_times.values()) / len(self._load_times)
            if self._load_times
            else 0.0,
            "slowest_file": max(self._load_times.items(), key=lambda x: x[1])
            if self._load_times
            else None,
            "preloaded_files": len(self._preloaded_files),
            "async_loading_enabled": self.enable_async_loading,
            "preload_enabled": self.preload_enabled,
        }

        return stats

    def cleanup(self) -> None:
        """Clean up resources and stop background operations."""
        try:
            # Stop timers
            if hasattr(self, "_preload_timer"):
                self._preload_timer.stop()
            if hasattr(self, "_memory_timer"):
                self._memory_timer.stop()

            # Shutdown executor
            if self._executor:
                self._executor.shutdown(wait=False)

            # Clear caches
            self._load_times.clear()
            self._preloaded_files.clear()
            self._loading_futures.clear()

        except Exception as e:
            print(f"Error during cleanup: {e}")

    def closeEvent(self, event) -> None:
        """Handle widget close event with proper cleanup."""
        self.cleanup()
        super().closeEvent(event)

    # Existing methods with type annotations added
    def dataPath(self) -> Path:
        """Get the data path for the current folder."""
        return self.mda_mvc.dataPath()

    def mdaFileList(self) -> List[str]:
        """Get the list of MDA file names."""
        return self.mda_mvc.mdaFileList()

    def data(self) -> Dict[str, Any]:
        """Get the current file data."""
        return self._data

    def setStatus(self, message: str) -> None:
        """Set status message."""
        self.mda_mvc.setStatus(message)


class TabManager(QObject):
    """
    Enhanced tab manager with performance optimizations.

    This class manages file tabs with improved memory management,
    lazy loading, and performance monitoring.
    """

    tabRemoved = pyqtSignal(str)  # file path

    def __init__(self, parent: MDAFile) -> None:
        """
        Initialize the enhanced tab manager.

        Parameters:
            parent (MDAFile): Parent MDA file manager
        """
        super().__init__(parent)
        self.mda_file = parent
        self._tab_cache: Dict[str, MDAFileTableView] = {}
        self._max_cached_tabs = 10  # Limit memory usage

    def addTab(self, file_path: str) -> Optional[MDAFileTableView]:
        """
        Add a new tab with caching support.

        Parameters:
            file_path (str): Path to the file

        Returns:
            Optional[MDAFileTableView]: The created tab view or None if failed
        """
        try:
            # Check if tab is already cached
            if file_path in self._tab_cache:
                return self._tab_cache[file_path]

            # Create new tab
            tab_view = MDAFileTableView(self.mda_file)

            # Cache with memory management
            if len(self._tab_cache) >= self._max_cached_tabs:
                # Remove oldest cached tab
                oldest_path = next(iter(self._tab_cache))
                del self._tab_cache[oldest_path]

            self._tab_cache[file_path] = tab_view
            return tab_view

        except Exception as e:
            print(f"Error creating tab for {file_path}: {e}")
            return None

    def removeTab(self, file_path: str) -> None:
        """
        Remove a tab and clean up resources.

        Parameters:
            file_path (str): Path to the file
        """
        try:
            if file_path in self._tab_cache:
                tab_view = self._tab_cache[file_path]
                # Clean up the tab view
                if hasattr(tab_view, "cleanup"):
                    tab_view.cleanup()
                del self._tab_cache[file_path]

            self.tabRemoved.emit(file_path)

        except Exception as e:
            print(f"Error removing tab for {file_path}: {e}")

    def clearCache(self) -> None:
        """Clear all cached tabs."""
        for tab_view in self._tab_cache.values():
            if hasattr(tab_view, "cleanup"):
                tab_view.cleanup()
        self._tab_cache.clear()
