"""
Data caching functionality for improved performance.

This module provides an LRU cache system for MDA file data with advanced
memory management and performance optimizations.

.. autosummary::

    ~DataCache
    ~CachedFileData
    ~get_global_cache
"""

import gc
import time
from collections import OrderedDict
from pathlib import Path
from typing import Optional, Any, Dict
from dataclasses import dataclass

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from PyQt6.QtCore import QObject, pyqtSignal
from mdaviz.synApps_mdalib.mda import readMDA
from mdaviz.utils import get_scan


@dataclass
class CachedFileData:
    """Container for cached MDA file data."""

    file_path: str
    metadata: Dict[str, Any]
    scan_dict: Dict[str, Any]
    first_pos: str
    first_det: str
    pv_list: list[str]
    file_name: str
    folder_path: str
    size_bytes: int
    cached_time: float = 0.0
    access_count: int = 0
    last_accessed: float = 0.0

    def __post_init__(self) -> None:
        """Initialize cache-specific fields."""
        current_time = time.time()
        if self.cached_time == 0.0:
            self.cached_time = current_time
        if self.last_accessed == 0.0:
            self.last_accessed = current_time

    def get_memory_estimate_mb(self) -> float:
        """
        Estimate memory usage of this cached data in megabytes.

        Returns:
            float: Estimated memory usage in MB
        """
        # Base size from file size
        base_size = self.size_bytes

        # Add estimated overhead for scan_dict data
        scan_dict_size = 0
        for key, value in self.scan_dict.items():
            if isinstance(value, dict) and "data" in value:
                data = value["data"]
                if hasattr(data, "__len__"):
                    # Estimate 8 bytes per numeric value
                    scan_dict_size += len(data) * 8

        # Add overhead for strings and objects (rough estimate)
        overhead = len(str(self.metadata)) + len(str(self.pv_list)) + 1024

        total_bytes = base_size + scan_dict_size + overhead
        return total_bytes / (1024 * 1024)

    def update_access(self) -> None:
        """Update access statistics."""
        self.last_accessed = time.time()
        self.access_count += 1


class DataCache(QObject):
    """
    Advanced LRU cache for MDA file data with smart memory management.

    This cache stores loaded MDA file data in memory and automatically evicts
    least recently used entries when memory limits are exceeded. It includes
    advanced features like access pattern analysis and adaptive cache sizing.

    Attributes:
        max_size_mb (float): Maximum cache size in megabytes
        max_entries (int): Maximum number of cached entries
        enable_compression (bool): Whether to compress cached data
        max_memory_mb (float): Maximum system memory usage in megabytes
        adaptive_sizing (bool): Whether to use adaptive cache sizing
        access_pattern_tracking (bool): Whether to track access patterns for better eviction
    """

    # Signals
    cache_hit = pyqtSignal(str)  # file path
    cache_miss = pyqtSignal(str)  # file path
    cache_eviction = pyqtSignal(str)  # file path
    cache_full = pyqtSignal()
    memory_warning = pyqtSignal(float)  # current memory usage in MB
    cache_stats_updated = pyqtSignal(dict)  # cache statistics

    def __init__(
        self,
        max_size_mb: float = 500.0,
        max_entries: int = 100,
        enable_compression: bool = False,
        max_memory_mb: float = 1000.0,
        adaptive_sizing: bool = True,
        access_pattern_tracking: bool = True,
    ) -> None:
        """
        Initialize the advanced data cache.

        Parameters:
            max_size_mb (float): Maximum cache size in megabytes
            max_entries (int): Maximum number of cached entries
            enable_compression (bool): Whether to compress cached data
            max_memory_mb (float): Maximum system memory usage in megabytes
            adaptive_sizing (bool): Whether to use adaptive cache sizing
            access_pattern_tracking (bool): Whether to track access patterns
        """
        super().__init__()
        self.max_size_mb = max_size_mb
        self.max_entries = max_entries
        self.enable_compression = enable_compression
        self.max_memory_mb = max_memory_mb
        self.adaptive_sizing = adaptive_sizing
        self.access_pattern_tracking = access_pattern_tracking

        self._cache: OrderedDict[str, CachedFileData] = OrderedDict()
        self._current_size_mb = 0.0
        self._last_memory_check = time.time()
        self._memory_check_interval = (
            30.0  # Check memory every 30 seconds (more frequent)
        )

        # Performance tracking
        self._cache_hits = 0
        self._cache_misses = 0
        self._evictions = 0
        self._last_stats_update = time.time()

    def _calculate_smart_eviction_score(self, cached_data: CachedFileData) -> float:
        """
        Calculate a smart eviction score based on multiple factors.

        Lower scores indicate higher priority for eviction.

        Parameters:
            cached_data (CachedFileData): Cached data to score

        Returns:
            float: Eviction score (lower = more likely to evict)
        """
        current_time = time.time()

        # Time-based factors
        time_since_cached = current_time - cached_data.cached_time
        time_since_accessed = current_time - cached_data.last_accessed

        # Access pattern factors
        access_frequency = cached_data.access_count / max(
            1, time_since_cached / 3600
        )  # per hour

        # Size factor (larger files have slight bias toward eviction)
        size_factor = cached_data.get_memory_estimate_mb() / max(
            1, self.max_size_mb / 10
        )

        # Calculate composite score
        # Higher access frequency and recent access = higher score (less likely to evict)
        recency_score = 1.0 / (1.0 + time_since_accessed / 3600)  # hours
        frequency_score = min(10.0, access_frequency)  # cap at 10 accesses/hour
        size_penalty = min(2.0, size_factor)  # cap penalty

        score = (recency_score * 2.0 + frequency_score) / size_penalty
        return score

    def _evict_smart(self) -> bool:
        """
        Perform smart eviction based on access patterns and file characteristics.

        Returns:
            bool: True if eviction was successful, False otherwise
        """
        if not self._cache:
            return False

        if self.access_pattern_tracking:
            # Use smart scoring for eviction
            scores = {}
            for file_path, cached_data in self._cache.items():
                scores[file_path] = self._calculate_smart_eviction_score(cached_data)

            # Evict the item with the lowest score
            evict_path = min(scores.keys(), key=lambda k: scores[k])
        else:
            # Fall back to LRU eviction
            evict_path = next(iter(self._cache))

        evicted_data = self._cache.pop(evict_path)
        self._current_size_mb -= evicted_data.get_memory_estimate_mb()
        self._evictions += 1

        self.cache_eviction.emit(evict_path)
        return True

    def _update_cache_stats(self) -> None:
        """Update and emit cache statistics."""
        current_time = time.time()
        if current_time - self._last_stats_update > 60.0:  # Update every minute
            stats = {
                "cache_size_mb": self._current_size_mb,
                "cache_entries": len(self._cache),
                "cache_hits": self._cache_hits,
                "cache_misses": self._cache_misses,
                "evictions": self._evictions,
                "hit_rate": self._cache_hits
                / max(1, self._cache_hits + self._cache_misses),
                "memory_usage_mb": self._check_memory_usage()
                if PSUTIL_AVAILABLE
                else 0.0,
            }
            self.cache_stats_updated.emit(stats)
            self._last_stats_update = current_time

    def _check_memory_usage(self) -> float:
        """
        Check current memory usage with improved monitoring.

        Returns:
            float: Current memory usage in MB
        """
        if not PSUTIL_AVAILABLE:
            return 0.0

        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024

            # Check if we need to perform memory cleanup
            current_time = time.time()
            if current_time - self._last_memory_check > self._memory_check_interval:
                self._last_memory_check = current_time

                # Adaptive memory management
                if self.adaptive_sizing:
                    system_memory = psutil.virtual_memory()
                    available_mb = system_memory.available / 1024 / 1024

                    # Adjust cache size based on available memory
                    if available_mb < 1000:  # Less than 1GB available
                        self.max_size_mb = min(self.max_size_mb, available_mb * 0.2)

                # Trigger cleanup if memory usage is high
                if memory_mb > self.max_memory_mb * 0.8:  # 80% threshold
                    self._perform_memory_cleanup()
                    memory_mb = process.memory_info().rss / 1024 / 1024

                # Emit warning if memory usage is critical
                if memory_mb > self.max_memory_mb * 0.9:  # 90% threshold
                    self.memory_warning.emit(memory_mb)

            return memory_mb

        except Exception as e:
            print(f"Error checking memory usage: {e}")
            return 0.0

    def _perform_memory_cleanup(self) -> None:
        """Perform intelligent memory cleanup when usage is high."""
        print(
            f"Performing smart memory cleanup - current cache: {len(self._cache)} entries"
        )

        # Calculate how much to clean based on current memory pressure
        target_reduction = 0.3  # Remove 30% of cache by default

        if PSUTIL_AVAILABLE:
            try:
                system_memory = psutil.virtual_memory()
                if system_memory.percent > 90:
                    target_reduction = 0.5  # More aggressive cleanup
                elif system_memory.percent > 80:
                    target_reduction = 0.4
            except Exception:
                pass

        # Remove entries using smart eviction
        entries_to_remove = int(len(self._cache) * target_reduction)
        for _ in range(entries_to_remove):
            if not self._evict_smart():
                break

        # Force garbage collection
        gc.collect()

        print(f"Memory cleanup complete - remaining cache: {len(self._cache)} entries")

    def get(self, file_path: str) -> Optional[CachedFileData]:
        """
        Get cached data with improved access tracking.

        Parameters:
            file_path (str): Path to the file

        Returns:
            CachedFileData or None: Cached data if available
        """
        if file_path in self._cache:
            cached_data = self._cache[file_path]

            # Move to end (most recently used) and update access stats
            self._cache.move_to_end(file_path)
            cached_data.update_access()

            self._cache_hits += 1
            self.cache_hit.emit(file_path)
            self._update_cache_stats()

            return cached_data

        self._cache_misses += 1
        self.cache_miss.emit(file_path)
        self._update_cache_stats()
        return None

    def put(self, file_path: str, cached_data: CachedFileData) -> bool:
        """
        Store data in cache with advanced management.

        Parameters:
            file_path (str): Path to the file
            cached_data (CachedFileData): Data to cache

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            data_size_mb = cached_data.get_memory_estimate_mb()

            # Don't cache extremely large files
            max_single_file_mb = self.max_size_mb * 0.3  # 30% of total cache
            if data_size_mb > max_single_file_mb:
                print(
                    f"Skipping cache for large file: {file_path} ({data_size_mb:.1f}MB)"
                )
                return False

            # Remove existing entry if present
            if file_path in self._cache:
                old_data = self._cache.pop(file_path)
                self._current_size_mb -= old_data.get_memory_estimate_mb()

            # Evict entries until we have space
            while (
                self._current_size_mb + data_size_mb > self.max_size_mb
                or len(self._cache) >= self.max_entries
            ):
                if not self._evict_smart():
                    # If we can't evict, don't cache this item
                    return False

            # Add new entry
            self._cache[file_path] = cached_data
            self._current_size_mb += data_size_mb

            # Check memory usage periodically
            self._check_memory_usage()
            self._update_cache_stats()

            return True

        except Exception as e:
            print(f"Error caching file {file_path}: {e}")
            return False

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
                print(
                    f"Warning: Large file ({file_size_mb:.1f}MB) and high memory usage ({current_memory:.1f}MB) - loading without caching"
                )
                return self._load_without_caching(path_obj)

            # Load the file data
            result = readMDA(str(path_obj))
            if result is None:
                print(f"Could not read file: {file_path}")
                return None

            file_metadata, file_data_dim1, *_ = result

            if file_metadata["rank"] > 1:
                print(
                    "WARNING: Multidimensional data not supported - ignoring ranks > 1."
                )

            scan_dict, first_pos, first_det = get_scan(file_data_dim1)
            pv_list = [v["name"] for v in scan_dict.values()]

            # Create cached data
            cached_data = CachedFileData(
                file_path=str(path_obj),
                metadata=file_metadata,
                scan_dict=scan_dict,
                first_pos=first_pos,
                first_det=first_det,
                pv_list=pv_list,
                file_name=path_obj.stem,
                folder_path=str(path_obj.parent),
                size_bytes=path_obj.stat().st_size,
            )

            # Cache the data
            self.put(file_path, cached_data)
            return cached_data

        except Exception as e:
            print(f"Error loading file {file_path}: {e}")
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
            scan_dict, first_pos, first_det = get_scan(file_data_dim1)
            pv_list = [v["name"] for v in scan_dict.values()]

            return CachedFileData(
                file_path=str(path_obj),
                metadata=file_metadata,
                scan_dict=scan_dict,
                first_pos=first_pos,
                first_det=first_det,
                pv_list=pv_list,
                file_name=path_obj.stem,
                folder_path=str(path_obj.parent),
                size_bytes=path_obj.stat().st_size,
            )
        except Exception as e:
            print(f"Error loading file without caching {path_obj}: {e}")
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
            self._current_size_mb -= cached_data.get_memory_estimate_mb()
            return True
        return False

    def clear(self) -> None:
        """Clear all cached data."""
        self._cache.clear()
        self._current_size_mb = 0.0

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
            "utilization_percent": (self._current_size_mb / self.max_size_mb) * 100
            if self.max_size_mb > 0
            else 0,
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
            if not self._evict_smart():  # Changed to _evict_smart
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
            if not self._evict_smart():  # Changed to _evict_smart
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
