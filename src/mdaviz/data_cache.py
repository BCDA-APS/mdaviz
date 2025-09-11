"""
Data caching functionality for MDA files.

This module provides caching capabilities to improve performance when
loading and processing MDA files.

.. autosummary::

    ~DataCache
    ~CachedFileData
    ~get_global_cache
"""

import time
import gc
import psutil
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, field
from collections import OrderedDict
from PyQt6.QtCore import QObject, pyqtSignal
from mdaviz.synApps_mdalib.mda import readMDA
from mdaviz.utils import get_scan, get_scan_2d
from mdaviz.logger import get_logger

# Get logger for this module
logger = get_logger("data_cache")


@dataclass
class CachedFileData:
    """Cached file data with metadata."""

    file_path: str
    metadata: dict[str, Any]
    scan_dict: dict[str, Any]
    first_pos: int
    first_det: int
    pv_list: list
    file_name: str
    folder_path: str
    access_time: float = field(default_factory=time.time)
    size_bytes: int = 0
    # New fields for 2D+ data support
    scan_dict_2d: dict[str, Any] = field(default_factory=dict)
    scan_dict_inner: dict[str, Any] = field(
        default_factory=dict
    )  # Inner dimension data for 1D plotting
    is_multidimensional: bool = False
    rank: int = 1
    dimensions: list[int] = field(default_factory=list)
    acquired_dimensions: list[int] = field(default_factory=list)
    # File modification tracking
    file_mtime: float = field(default_factory=time.time)

    def update_access_time(self) -> None:
        """Update the last access time."""
        self.access_time = time.time()

    def get_size_mb(self) -> float:
        """Get the size in megabytes."""
        return self.size_bytes / (1024 * 1024)


class DataCache(QObject):
    """
    LRU cache for MDA file data to improve performance and manage memory usage.

    This cache stores loaded MDA file data in memory and automatically evicts
    least recently used entries when memory limits are exceeded.

    Attributes:
        max_size_mb (float): Maximum cache size in megabytes
        max_entries (int): Maximum number of cached entries
        enable_compression (bool): Whether to compress cached data
        max_memory_mb (float): Maximum system memory usage in megabytes
    """

    # Signals
    cache_hit = pyqtSignal(str)  # file path
    cache_miss = pyqtSignal(str)  # file path
    cache_eviction = pyqtSignal(str)  # file path
    cache_full = pyqtSignal()
    memory_warning = pyqtSignal(float)  # current memory usage in MB

    def __init__(
        self,
        max_size_mb: float = 500.0,
        max_entries: int = 100,
        enable_compression: bool = False,
        max_memory_mb: float = 1000.0,
    ):
        """
        Initialize the data cache.

        Parameters:
            max_size_mb (float): Maximum cache size in megabytes
            max_entries (int): Maximum number of cached entries
            enable_compression (bool): Whether to compress cached data
            max_memory_mb (float): Maximum system memory usage in megabytes
        """
        super().__init__()
        self.max_size_mb = max_size_mb
        self.max_entries = max_entries
        self.enable_compression = enable_compression
        self.max_memory_mb = max_memory_mb
        self._cache: OrderedDict[str, CachedFileData] = OrderedDict()
        self._current_size_mb = 0.0
        self._last_memory_check = time.time()
        self._memory_check_interval = 60.0  # Check memory every 60 seconds

    def _check_memory_usage(self) -> float:
        """
        Check current memory usage and trigger cleanup if needed.

        Returns:
            float: Current memory usage in MB
        """
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024

            # Check if we need to perform memory cleanup
            current_time = time.time()
            if (
                current_time - self._last_memory_check > self._memory_check_interval
                and memory_mb > self.max_memory_mb * 0.8
            ):  # 80% threshold
                self._perform_memory_cleanup()
                self._last_memory_check = current_time

                # Re-check memory after cleanup
                memory_mb = process.memory_info().rss / 1024 / 1024

            # Emit warning if memory usage is high
            if memory_mb > self.max_memory_mb * 0.9:  # 90% threshold
                self.memory_warning.emit(memory_mb)

            return memory_mb

        except ImportError:
            # psutil not available, skip memory monitoring
            return 0.0
        except Exception as e:
            logger.error(f"Error checking memory usage: {e}")
            return 0.0

    def _perform_memory_cleanup(self) -> None:
        """Perform aggressive memory cleanup when usage is high."""
        logger.info(
            f"Performing memory cleanup - current cache size: {len(self._cache)} entries"
        )

        # Clear half of the cache (least recently used)
        entries_to_remove = len(self._cache) // 2
        for _ in range(entries_to_remove):
            if not self._evict_lru():
                break

        # Force garbage collection
        gc.collect()

        logger.info(
            f"Memory cleanup complete - remaining cache size: {len(self._cache)} entries"
        )

    def get(self, file_path: str) -> Optional[CachedFileData]:
        """
        Get cached data for a file.

        Parameters:
            file_path (str): Path to the file

        Returns:
            CachedFileData or None: Cached data if available and not stale, None otherwise
        """
        # Check memory usage periodically
        self._check_memory_usage()

        if file_path in self._cache:
            cached_data = self._cache.pop(file_path)

            # Check if file has been modified since caching
            try:
                current_mtime = Path(file_path).stat().st_mtime
                print(
                    f"🔍 CACHE CHECK: {file_path}: cached_mtime={cached_data.file_mtime}, current_mtime={current_mtime}"
                )
                if current_mtime > cached_data.file_mtime:
                    # File has been modified, cache is stale
                    print(
                        f"⚠️ CACHE STALE: File {file_path} has been modified, invalidating cache"
                    )
                    self.cache_miss.emit(file_path)
                    return None
                else:
                    print(
                        f"✅ CACHE VALID: File {file_path} not modified, using cached data"
                    )
            except (OSError, FileNotFoundError):
                # File no longer exists or can't be accessed
                print(
                    f"❌ CACHE ERROR: File {file_path} no longer accessible, invalidating cache"
                )
                self.cache_miss.emit(file_path)
                return None

            # File is still valid, move to end (most recently used)
            self._cache[file_path] = cached_data
            cached_data.update_access_time()
            self.cache_hit.emit(file_path)
            return cached_data
        else:
            self.cache_miss.emit(file_path)
            return None

    def put(self, file_path: str, cached_data: CachedFileData) -> None:
        """
        Store data in the cache.

        Parameters:
            file_path (str): Path to the file
            cached_data (CachedFileData): Data to cache
        """
        # Check memory usage before adding new data
        current_memory = self._check_memory_usage()

        # Remove existing entry if present
        if file_path in self._cache:
            old_data = self._cache.pop(file_path)
            self._current_size_mb -= old_data.get_size_mb()

        # Check if we need to evict entries
        while (
            len(self._cache) >= self.max_entries
            or self._current_size_mb + cached_data.get_size_mb() > self.max_size_mb
            or (current_memory > 0 and current_memory > self.max_memory_mb * 0.9)
        ):
            if not self._evict_lru():
                # Cannot evict any more entries
                self.cache_full.emit()
                return

        # Add new entry
        self._cache[file_path] = cached_data
        self._current_size_mb += cached_data.get_size_mb()

    def load_and_cache(self, file_path: str) -> Optional[CachedFileData]:
        """
        Load file data and cache it.

        Parameters:
            file_path (str): Path to the file to load

        Returns:
            CachedFileData or None: Loaded and cached data
        """
        try:
            path_obj = Path(file_path)
            if not path_obj.exists():
                return None

            # Check memory usage before loading large files
            file_size_mb = path_obj.stat().st_size / (1024 * 1024)
            current_memory = self._check_memory_usage()

            # If file is large and memory usage is high, skip caching
            if file_size_mb > 100 and current_memory > self.max_memory_mb * 0.8:
                logger.warning(
                    f"Warning: Large file ({file_size_mb:.1f}MB) and high memory usage ({current_memory:.1f}MB) - loading without caching"
                )
                return self._load_without_caching(path_obj)

            # Load the file data
            result = readMDA(str(path_obj))
            if result is None:
                logger.error(f"Could not read file: {file_path}")
                return None

            file_metadata, file_data_dim1, *_ = result
            rank = file_metadata.get("rank", 1)
            dimensions = file_metadata.get("dimensions", [])
            acquired_dimensions = file_metadata.get("acquired_dimensions", [])

            # Process 1D data (always available)
            scan_dict, first_pos, first_det = get_scan(file_data_dim1)

            # Initialize 2D data fields
            scan_dict_2d = {}
            scan_dict_inner = {}
            is_multidimensional = rank > 1

            # Process 2D data if available
            if rank >= 2 and len(result) > 2:
                try:
                    file_data_dim2 = result[2]
                    scan_dict_2d, _, _ = get_scan_2d(file_data_dim1, file_data_dim2)
                    # Also store inner dimension data for 1D plotting
                    scan_dict_inner, _, _ = get_scan(file_data_dim2)
                except Exception as e:
                    logger.warning(f"Warning: Could not process 2D data: {e}")
                    scan_dict_2d = {}
                    scan_dict_inner = {}

            # Construct pv_list from appropriate data source
            # For 2D+ data, use scan_dict_inner (inner dimension PVs like P1, D1, etc.)
            # For 1D data, use scan_dict (outer dimension PVs)
            if is_multidimensional and scan_dict_inner:
                pv_list = [v["name"] for v in scan_dict_inner.values()]
            else:
                pv_list = [v["name"] for v in scan_dict.values()]

            # Create cached data
            file_stat = path_obj.stat()
            cached_data = CachedFileData(
                file_path=str(path_obj),
                metadata=file_metadata,
                scan_dict=scan_dict,
                first_pos=first_pos,
                first_det=first_det,
                pv_list=pv_list,
                file_name=path_obj.stem,
                folder_path=str(path_obj.parent),
                size_bytes=file_stat.st_size,
                scan_dict_2d=scan_dict_2d,
                scan_dict_inner=scan_dict_inner,
                is_multidimensional=is_multidimensional,
                rank=rank,
                dimensions=dimensions,
                acquired_dimensions=acquired_dimensions,
                file_mtime=file_stat.st_mtime,
            )

            # Cache the data
            self.put(file_path, cached_data)
            return cached_data

        except Exception as e:
            logger.error(f"Error loading file {file_path}: {e}")
            return None

    def _load_without_caching(self, path_obj: Path) -> Optional[CachedFileData]:
        """
        Load file data without caching it (for large files or high memory usage).

        Parameters:
            path_obj (Path): Path object to the file

        Returns:
            CachedFileData or None: Loaded data (not cached)
        """
        try:
            result = readMDA(str(path_obj))
            if result is None:
                return None

            file_metadata, file_data_dim1, *_ = result
            rank = file_metadata.get("rank", 1)
            dimensions = file_metadata.get("dimensions", [])
            acquired_dimensions = file_metadata.get("acquired_dimensions", [])

            scan_dict, first_pos, first_det = get_scan(file_data_dim1)
            pv_list = [v["name"] for v in scan_dict.values()]

            # Initialize 2D data fields
            scan_dict_2d = {}
            scan_dict_inner = {}
            is_multidimensional = rank > 1

            # Process 2D data if available
            if rank >= 2 and len(result) > 2:
                try:
                    file_data_dim2 = result[2]
                    scan_dict_2d, _, _ = get_scan_2d(file_data_dim1, file_data_dim2)
                    # Also store inner dimension data for 1D plotting
                    scan_dict_inner, _, _ = get_scan(file_data_dim2)
                except Exception as e:
                    logger.warning(f"Warning: Could not process 2D data: {e}")
                    scan_dict_2d = {}
                    scan_dict_inner = {}

            file_stat = path_obj.stat()
            return CachedFileData(
                file_path=str(path_obj),
                metadata=file_metadata,
                scan_dict=scan_dict,
                first_pos=first_pos,
                first_det=first_det,
                pv_list=pv_list,
                file_name=path_obj.stem,
                folder_path=str(path_obj.parent),
                size_bytes=file_stat.st_size,
                scan_dict_2d=scan_dict_2d,
                scan_dict_inner=scan_dict_inner,
                is_multidimensional=is_multidimensional,
                rank=rank,
                dimensions=dimensions,
                acquired_dimensions=acquired_dimensions,
                file_mtime=file_stat.st_mtime,
            )
        except Exception as e:
            logger.error(f"Error loading file without caching {path_obj}: {e}")
            return None

    def get_or_load(self, file_path: str) -> Optional[CachedFileData]:
        """
        Get cached data or load and cache it if not available.

        Parameters:
            file_path (str): Path to the file

        Returns:
            CachedFileData or None: Data from cache or newly loaded
        """
        cached_data = self.get(file_path)
        if cached_data is not None:
            return cached_data

        return self.load_and_cache(file_path)

    def remove(self, file_path: str) -> bool:
        """
        Remove a file from the cache.

        Parameters:
            file_path (str): Path to the file to remove

        Returns:
            bool: True if the file was in the cache, False otherwise
        """
        if file_path in self._cache:
            cached_data = self._cache.pop(file_path)
            self._current_size_mb -= cached_data.get_size_mb()
            return True
        return False

    def invalidate_file(self, file_path: str) -> bool:
        """
        Invalidate cached data for a specific file, forcing it to be reloaded.

        Parameters:
            file_path (str): Path to the file to invalidate

        Returns:
            bool: True if the file was in the cache and invalidated, False otherwise
        """
        return self.remove(file_path)

    def invalidate_folder(self, folder_path: str) -> int:
        """
        Invalidate cached data for all files in a specific folder.

        Parameters:
            folder_path (str): Path to the folder

        Returns:
            int: Number of files invalidated
        """
        folder_path = str(Path(folder_path).resolve())
        files_to_remove = []

        print(f"🔄 CACHE INVALIDATE: Starting invalidation for folder: {folder_path}")
        print(f"🔄 CACHE INVALIDATE: Current cache contains {len(self._cache)} files")

        for file_path in self._cache.keys():
            if str(Path(file_path).parent.resolve()) == folder_path:
                files_to_remove.append(file_path)
                print(f"🔄 CACHE INVALIDATE: Marking for invalidation: {file_path}")

        for file_path in files_to_remove:
            self.remove(file_path)
            print(f"🔄 CACHE INVALIDATE: Invalidated cache for: {file_path}")

        print(
            f"🔄 CACHE INVALIDATE: Invalidated cache for {len(files_to_remove)} files in folder {folder_path}"
        )
        return len(files_to_remove)

    def clear(self) -> None:
        """Clear all cached data."""
        self._cache.clear()
        self._current_size_mb = 0.0

    def _evict_lru(self) -> bool:
        """
        Evict the least recently used entry from the cache.

        Returns:
            bool: True if an entry was evicted, False if cache is empty
        """
        if not self._cache:
            return False

        # Remove the first (least recently used) entry
        file_path, cached_data = self._cache.popitem(last=False)
        self._current_size_mb -= cached_data.get_size_mb()
        self.cache_eviction.emit(file_path)
        return True

    def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            dict: Cache statistics including size, entry count, hit rate, etc.
        """
        return {
            "entry_count": len(self._cache),
            "current_size_mb": self._current_size_mb,
            "max_size_mb": self.max_size_mb,
            "max_entries": self.max_entries,
            "utilization_percent": (
                (self._current_size_mb / self.max_size_mb) * 100
                if self.max_size_mb > 0
                else 0
            ),
        }

    def set_max_size_mb(self, max_size_mb: float) -> None:
        """
        Set the maximum cache size.

        Parameters:
            max_size_mb (float): New maximum size in megabytes
        """
        self.max_size_mb = max_size_mb
        # Evict entries if necessary
        while self._current_size_mb > self.max_size_mb:
            if not self._evict_lru():
                break

    def set_max_entries(self, max_entries: int) -> None:
        """
        Set the maximum number of cache entries.

        Parameters:
            max_entries (int): New maximum number of entries
        """
        self.max_entries = max_entries
        # Evict entries if necessary
        while len(self._cache) > self.max_entries:
            if not self._evict_lru():
                break


# Global cache instance
_global_cache: Optional[DataCache] = None


def get_global_cache() -> DataCache:
    """
    Get the global data cache instance.

    Returns:
        DataCache: Global cache instance
    """
    global _global_cache
    if _global_cache is None:
        _global_cache = DataCache()
    return _global_cache


def set_global_cache(cache: DataCache) -> None:
    """
    Set the global data cache instance.

    Parameters:
        cache (DataCache): Cache instance to use globally
    """
    global _global_cache
    _global_cache = cache
