"""
Data cache module for lazy loading of MDA file data.

This module provides a caching mechanism for MDA file data to improve performance
and reduce memory usage when working with large datasets.

.. autosummary::

    ~DataCache
    ~CachedFileData
"""

import os
import time
from pathlib import Path
from typing import Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import OrderedDict
from PyQt5 import QtCore
from .synApps_mdalib.mda import readMDA
from .utils import get_scan


@dataclass
class CachedFileData:
    """Cached file data with metadata."""
    
    file_path: str
    metadata: Dict[str, Any]
    scan_dict: Dict[str, Any]
    first_pos: int
    first_det: int
    pv_list: list
    file_name: str
    folder_path: str
    access_time: float = field(default_factory=time.time)
    size_bytes: int = 0
    
    def update_access_time(self) -> None:
        """Update the last access time."""
        self.access_time = time.time()
    
    def get_size_mb(self) -> float:
        """Get the size in megabytes."""
        return self.size_bytes / (1024 * 1024)


class DataCache(QtCore.QObject):
    """
    LRU cache for MDA file data to improve performance and manage memory usage.
    
    This cache stores loaded MDA file data in memory and automatically evicts
    least recently used entries when memory limits are exceeded.
    
    Attributes:
        max_size_mb (float): Maximum cache size in megabytes
        max_entries (int): Maximum number of cached entries
        enable_compression (bool): Whether to compress cached data
    """
    
    # Signals
    cache_hit = QtCore.pyqtSignal(str)  # file path
    cache_miss = QtCore.pyqtSignal(str)  # file path
    cache_eviction = QtCore.pyqtSignal(str)  # file path
    cache_full = QtCore.pyqtSignal()
    
    def __init__(self, max_size_mb: float = 500.0, max_entries: int = 100, 
                 enable_compression: bool = False):
        """
        Initialize the data cache.
        
        Parameters:
            max_size_mb (float): Maximum cache size in megabytes
            max_entries (int): Maximum number of cached entries
            enable_compression (bool): Whether to compress cached data
        """
        super().__init__()
        self.max_size_mb = max_size_mb
        self.max_entries = max_entries
        self.enable_compression = enable_compression
        self._cache: OrderedDict[str, CachedFileData] = OrderedDict()
        self._current_size_mb = 0.0
        
    def get(self, file_path: str) -> Optional[CachedFileData]:
        """
        Get cached data for a file.
        
        Parameters:
            file_path (str): Path to the file
            
        Returns:
            CachedFileData or None: Cached data if available, None otherwise
        """
        if file_path in self._cache:
            # Move to end (most recently used)
            cached_data = self._cache.pop(file_path)
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
        # Remove existing entry if present
        if file_path in self._cache:
            old_data = self._cache.pop(file_path)
            self._current_size_mb -= old_data.get_size_mb()
        
        # Check if we need to evict entries
        while (len(self._cache) >= self.max_entries or 
               self._current_size_mb + cached_data.get_size_mb() > self.max_size_mb):
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
            
            # Load the file data
            result = readMDA(str(path_obj))
            if result is None:
                print(f"Could not read file: {file_path}")
                return None
            
            file_metadata, file_data_dim1, *_ = result
            
            if file_metadata["rank"] > 1:
                print("WARNING: Multidimensional data not supported - ignoring ranks > 1.")
            
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
                size_bytes=path_obj.stat().st_size
            )
            
            # Cache the data
            self.put(file_path, cached_data)
            return cached_data
            
        except Exception as e:
            print(f"Error loading file {file_path}: {e}")
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
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            dict: Cache statistics including size, entry count, hit rate, etc.
        """
        return {
            'entry_count': len(self._cache),
            'current_size_mb': self._current_size_mb,
            'max_size_mb': self.max_size_mb,
            'max_entries': self.max_entries,
            'utilization_percent': (self._current_size_mb / self.max_size_mb) * 100 if self.max_size_mb > 0 else 0
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