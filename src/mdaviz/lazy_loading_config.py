"""
Configuration management for lazy loading functionality.

This module provides configuration management for the lazy loading system,
allowing users to customize behavior and persist settings.

.. autosummary::

    ~LazyLoadingConfig
    ~ConfigManager
    ~get_config
    ~update_config
"""

import json
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, asdict
from PyQt6.QtCore import QObject, pyqtSignal


@dataclass
class LazyLoadingConfig:
    """
    Configuration for lazy loading behavior.

    This class contains all the configuration options for the lazy loading
    system, including cache sizes, batch sizes, and performance settings.
    """

    # Folder scanning settings
    folder_scan_batch_size: int = 50
    folder_scan_max_files: int = 10000
    folder_scan_use_lightweight: bool = True

    # Data cache settings
    data_cache_max_size_mb: float = 500.0
    data_cache_max_entries: int = 100
    data_cache_enable_compression: bool = False

    # Virtual table settings
    virtual_table_page_size: int = 100
    virtual_table_preload_pages: int = 2

    # Performance settings
    enable_progress_dialogs: bool = True
    enable_memory_monitoring: bool = True
    memory_warning_threshold_mb: float = 1000.0

    # UI settings
    show_cache_stats: bool = False
    auto_clear_cache_on_low_memory: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LazyLoadingConfig":
        """Create configuration from dictionary."""
        return cls(**data)

    def save_to_file(self, file_path: Path) -> bool:
        """
        Save configuration to file.

        Parameters:
            file_path (Path): Path to save configuration

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(file_path, "w") as f:
                json.dump(self.to_dict(), f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False

    @classmethod
    def load_from_file(cls, file_path: Path) -> Optional["LazyLoadingConfig"]:
        """
        Load configuration from file.

        Parameters:
            file_path (Path): Path to load configuration from

        Returns:
            LazyLoadingConfig or None: Configuration if successful, None otherwise
        """
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            return cls.from_dict(data)
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return None


class ConfigManager(QObject):
    """
    Manager for lazy loading configuration.

    This class manages the loading, saving, and updating of lazy loading
    configuration settings.
    """

    # Signal emitted when configuration changes
    config_changed = pyqtSignal(object)  # LazyLoadingConfig

    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize the configuration manager.

        Parameters:
            config_file (Path, optional): Path to configuration file
        """
        super().__init__()
        self.config_file = (
            config_file or Path.home() / ".mdaviz" / "lazy_loading_config.json"
        )
        self.config = self._load_config()

    def _load_config(self) -> LazyLoadingConfig:
        """Load configuration from file or create default."""
        if self.config_file.exists():
            config = LazyLoadingConfig.load_from_file(self.config_file)
            if config:
                return config

        # Create default configuration
        config = LazyLoadingConfig()
        self.save_config(config)
        return config

    def get_config(self) -> LazyLoadingConfig:
        """Get the current configuration."""
        return self.config

    def update_config(self, **kwargs) -> bool:
        """
        Update configuration with new values.

        Parameters:
            **kwargs: Configuration values to update

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            for key, value in kwargs.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
                else:
                    print(f"Unknown configuration key: {key}")

            # Save updated configuration
            success = self.save_config(self.config)
            if success:
                self.config_changed.emit(self.config)
            return success
        except Exception as e:
            print(f"Error updating configuration: {e}")
            return False

    def save_config(self, config: LazyLoadingConfig) -> bool:
        """
        Save configuration to file.

        Parameters:
            config (LazyLoadingConfig): Configuration to save

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            return config.save_to_file(self.config_file)
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False

    def reset_to_defaults(self) -> bool:
        """
        Reset configuration to default values.

        Returns:
            bool: True if successful, False otherwise
        """
        self.config = LazyLoadingConfig()
        success = self.save_config(self.config)
        if success:
            self.config_changed.emit(self.config)
        return success

    def get_memory_usage_mb(self) -> float:
        """
        Get current memory usage in megabytes.

        Returns:
            float: Memory usage in MB
        """
        try:
            import psutil

            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)
        except ImportError:
            # Fallback if psutil is not available
            return 0.0

    def is_memory_usage_high(self) -> bool:
        """
        Check if memory usage is above the warning threshold.

        Returns:
            bool: True if memory usage is high
        """
        memory_usage = self.get_memory_usage_mb()
        return memory_usage > self.config.memory_warning_threshold_mb


# Global configuration manager instance
_global_config_manager: Optional[ConfigManager] = None


def get_global_config_manager() -> ConfigManager:
    """
    Get the global configuration manager instance.

    Returns:
        ConfigManager: Global configuration manager
    """
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = ConfigManager()
    return _global_config_manager


def get_config() -> LazyLoadingConfig:
    """
    Get the current lazy loading configuration.

    Returns:
        LazyLoadingConfig: Current configuration
    """
    return get_global_config_manager().get_config()


def update_config(**kwargs) -> bool:
    """
    Update the lazy loading configuration.

    Parameters:
        **kwargs: Configuration values to update

    Returns:
        bool: True if successful, False otherwise
    """
    return get_global_config_manager().update_config(**kwargs)
