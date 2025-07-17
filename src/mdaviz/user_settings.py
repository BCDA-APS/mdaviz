"""
Enhanced user settings management with validation and error handling.

This module provides robust user settings management with comprehensive error
handling, validation, backup/restore functionality, and performance optimizations.

.. autosummary::

    ~ApplicationQSettings
    ~SettingsError
    ~SettingsManager
"""

import datetime
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Type

from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QMainWindow

logger = logging.getLogger(__name__)

GLOBAL_GROUP = "general"
APP_NAME = "mdaviz"
ORG_NAME = "APS"

# Global settings instance
settings = None

# Default configuration values with type information
DEFAULT_SETTINGS: Dict[str, Dict[str, Any]] = {
    "general": {
        "auto_load": True,
        "recent_folders": [],
        "max_recent_folders": 10,
        "timestamp": "",
        "window_theme": "system",
        "show_tooltips": True,
    },
    "performance": {
        "cache_size_mb": 500,
        "max_concurrent_operations": 4,
        "lazy_loading_enabled": True,
        "preload_adjacent_files": True,
        "memory_limit_mb": 1000,
    },
    "visualization": {
        "plot_max_height": 800,
        "default_plot_backend": "matplotlib",
        "enable_animations": True,
        "auto_scale_plots": True,
        "curve_line_width": 1.0,
    },
    "data": {
        "auto_save_enabled": True,
        "backup_count": 5,
        "compression_enabled": False,
        "export_format": "csv",
    },
}

# Type mappings for validation
TYPE_MAPPINGS = {
    bool: bool,
    int: int,
    float: float,
    str: str,
    list: list,
    dict: dict,
}


class SettingsError(Exception):
    """Exception raised for settings-related errors."""

    def __init__(
        self, message: str, key: Optional[str] = None, value: Any = None
    ) -> None:
        """
        Initialize settings error.

        Parameters:
            message (str): Error message
            key (Optional[str]): Settings key that caused the error
            value (Any): Value that caused the error
        """
        super().__init__(message)
        self.message = message
        self.key = key
        self.value = value

    def __str__(self) -> str:
        """Get string representation of the error."""
        if self.key:
            return f"Settings error for key '{self.key}': {self.message}"
        return f"Settings error: {self.message}"


class SettingsValidator:
    """Validator for settings values."""

    @staticmethod
    def validate_value(key: str, value: Any, expected_type: Type) -> Any:
        """
        Validate and convert a settings value.

        Parameters:
            key (str): Settings key
            value (Any): Value to validate
            expected_type (Type): Expected type

        Returns:
            Any: Validated and converted value

        Raises:
            SettingsError: If validation fails
        """
        try:
            # Handle None values
            if value is None:
                if expected_type is bool:
                    return False
                elif expected_type in (int, float):
                    return 0
                elif expected_type is str:
                    return ""
                elif expected_type in (list, dict):
                    return expected_type()
                else:
                    return None

            # Type conversion and validation
            if expected_type is bool:
                if isinstance(value, str):
                    return value.lower() in ("true", "1", "yes", "on")
                return bool(value)

            elif expected_type is int:
                return int(float(value))  # Handle string representations

            elif expected_type is float:
                return float(value)

            elif expected_type is str:
                return str(value)

            elif expected_type is list:
                if isinstance(value, str):
                    try:
                        return json.loads(value)
                    except json.JSONDecodeError:
                        return value.split(",") if value else []
                return list(value) if hasattr(value, "__iter__") else [value]

            elif expected_type is dict:
                if isinstance(value, str):
                    try:
                        return json.loads(value)
                    except json.JSONDecodeError:
                        return {}
                return dict(value) if isinstance(value, dict) else {}

            else:
                return value

        except (ValueError, TypeError) as e:
            raise SettingsError(
                f"Cannot convert value to {expected_type.__name__}: {e}",
                key=key,
                value=value,
            )

    @staticmethod
    def validate_range(
        key: str,
        value: Union[int, float],
        min_val: Optional[Union[int, float]] = None,
        max_val: Optional[Union[int, float]] = None,
    ) -> Union[int, float]:
        """
        Validate that a numeric value is within the specified range.

        Parameters:
            key (str): Settings key
            value (Union[int, float]): Value to validate
            min_val (Optional[Union[int, float]]): Minimum allowed value
            max_val (Optional[Union[int, float]]): Maximum allowed value

        Returns:
            Union[int, float]: Validated value

        Raises:
            SettingsError: If value is out of range
        """
        if min_val is not None and value < min_val:
            raise SettingsError(
                f"Value {value} is below minimum {min_val}", key=key, value=value
            )

        if max_val is not None and value > max_val:
            raise SettingsError(
                f"Value {value} is above maximum {max_val}", key=key, value=value
            )

        return value


class ApplicationQSettings(QSettings):
    """
    Enhanced QSettings with validation, error handling, and backup functionality.

    This class extends QSettings with type validation, error handling,
    backup/restore capabilities, and comprehensive settings management.
    """

    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize enhanced application settings.

        Parameters:
            *args: Arguments passed to QSettings
            **kwargs: Keyword arguments passed to QSettings
        """
        super().__init__(*args, **kwargs)

        self.validator = SettingsValidator()
        self._backup_dir = Path(self.fileName()).parent / "backups"
        self._ensure_backup_dir()

        # Initialize with defaults if empty
        if not self.allKeys():
            self.init_global_keys()

    def _ensure_backup_dir(self) -> None:
        """Ensure backup directory exists."""
        try:
            self._backup_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(f"Could not create backup directory: {e}")

    def _keySplit_(self, full_key: str) -> tuple[str, str]:
        """
        Split full_key into (group, key) tuple with enhanced error handling.

        Parameters:
            full_key (str): Either `key` or `group/key`

        Returns:
            tuple[str, str]: (group, key) tuple

        Raises:
            SettingsError: If key format is invalid
        """
        if not full_key or not isinstance(full_key, str):
            raise SettingsError("Key must be a non-empty string", key=full_key)

        parts = full_key.split("/")
        if len(parts) > 2:
            raise SettingsError(
                f"Too many '/' separators in key: {full_key}", key=full_key
            )

        if len(parts) == 1:
            group, key = GLOBAL_GROUP, str(parts[0])
        else:
            group, key = map(str, parts)

        return group, key

    def keyExists(self, key: str) -> bool:
        """
        Check if the named key exists.

        Parameters:
            key (str): Key to check

        Returns:
            bool: True if key exists
        """
        try:
            return key in self.allKeys()
        except Exception as e:
            logger.warning(f"Error checking key existence '{key}': {e}")
            return False

    def getKey(
        self, key: str, default: Any = None, validate_type: Optional[Type] = None
    ) -> Any:
        """
        Get a configuration value with enhanced error handling and type validation.

        Parameters:
            key (str): Configuration key
            default (Any): Default value if key doesn't exist
            validate_type (Optional[Type]): Expected type for validation

        Returns:
            Any: Configuration value
        """
        try:
            # Handle missing slash in global keys
            if "/" not in key and not self.keyExists(key):
                key = f"{GLOBAL_GROUP}/{key}"

            value = self.value(key, default)

            # Type validation if requested
            if validate_type is not None and value is not None:
                value = self.validator.validate_value(key, value, validate_type)

            return value

        except Exception as e:
            logger.warning(f"Error getting key '{key}': {e}")
            return default

    def setKey(
        self,
        key: str,
        value: Any,
        validate_type: Optional[Type] = None,
        backup: bool = True,
    ) -> bool:
        """
        Set a configuration value with validation and optional backup.

        Parameters:
            key (str): Configuration key
            value (Any): Value to set
            validate_type (Optional[Type]): Expected type for validation
            backup (bool): Whether to create a backup before changing

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create backup if requested
            if backup and self.keyExists(key):
                self._create_backup()

            # Type validation if requested
            if validate_type is not None:
                value = self.validator.validate_value(key, value, validate_type)

            # Split key into group and key components
            group, k = self._keySplit_(key)

            # Remove existing key
            self.remove(key)

            # Set new value
            self.beginGroup(group)
            self.setValue(k, value)
            self.endGroup()

            # Update timestamp (but don't create infinite recursion)
            if key != "timestamp":
                self.updateTimeStamp()

            return True

        except Exception as e:
            logger.error(f"Error setting key '{key}' to '{value}': {e}")
            return False

    def getKeyWithRange(
        self,
        key: str,
        default: Union[int, float],
        min_val: Optional[Union[int, float]] = None,
        max_val: Optional[Union[int, float]] = None,
    ) -> Union[int, float]:
        """
        Get a numeric key with range validation.

        Parameters:
            key (str): Configuration key
            default (Union[int, float]): Default value
            min_val (Optional[Union[int, float]]): Minimum allowed value
            max_val (Optional[Union[int, float]]): Maximum allowed value

        Returns:
            Union[int, float]: Validated numeric value
        """
        try:
            value_type = type(default)
            value = self.getKey(key, default, value_type)
            return self.validator.validate_range(key, value, min_val, max_val)
        except SettingsError:
            logger.warning(
                f"Range validation failed for key '{key}', using default: {default}"
            )
            return default

    def updateDefaults(self, new_defaults: Dict[str, Dict[str, Any]]) -> None:
        """
        Update default settings with new values.

        Parameters:
            new_defaults (Dict[str, Dict[str, Any]]): New default settings
        """
        try:
            for group, settings in new_defaults.items():
                for key, value in settings.items():
                    full_key = f"{group}/{key}"
                    if not self.keyExists(full_key):
                        self.setKey(full_key, value, backup=False)
        except Exception as e:
            logger.error(f"Error updating defaults: {e}")

    def resetDefaults(self) -> bool:
        """
        Reset all application settings to default values.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create backup before reset
            self._create_backup()

            # Clear all keys
            for key in self.allKeys():
                self.remove(key)

            # Reinitialize with defaults
            self.init_global_keys()

            logger.info("Settings reset to defaults")
            return True

        except Exception as e:
            logger.error(f"Error resetting to defaults: {e}")
            return False

    def init_global_keys(self) -> None:
        """Initialize settings with default values."""
        try:
            for group, settings in DEFAULT_SETTINGS.items():
                for key, value in settings.items():
                    full_key = f"{group}/{key}"
                    if not self.keyExists(full_key):
                        self.setKey(full_key, value, backup=False)

            self.updateTimeStamp()

        except Exception as e:
            logger.error(f"Error initializing default keys: {e}")

    def updateTimeStamp(self) -> None:
        """Update the timestamp."""
        try:
            timestamp = str(datetime.datetime.now())
            self.setKey("timestamp", timestamp, backup=False)
        except Exception as e:
            logger.warning(f"Error updating timestamp: {e}")

    def exportSettings(self, file_path: Union[str, Path]) -> bool:
        """
        Export settings to a JSON file.

        Parameters:
            file_path (Union[str, Path]): Path to export file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            file_path = Path(file_path)

            # Collect all settings
            settings_data = {}
            for key in self.allKeys():
                value = self.value(key)
                settings_data[key] = value

            # Write to file
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(settings_data, f, indent=2, default=str)

            logger.info(f"Settings exported to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error exporting settings to {file_path}: {e}")
            return False

    def importSettings(self, file_path: Union[str, Path], merge: bool = True) -> bool:
        """
        Import settings from a JSON file.

        Parameters:
            file_path (Union[str, Path]): Path to import file
            merge (bool): Whether to merge with existing settings or replace

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            file_path = Path(file_path)

            if not file_path.exists():
                raise SettingsError(f"Import file does not exist: {file_path}")

            # Create backup before import
            self._create_backup()

            # Clear existing settings if not merging
            if not merge:
                for key in self.allKeys():
                    self.remove(key)

            # Load settings from file
            with open(file_path, "r", encoding="utf-8") as f:
                settings_data = json.load(f)

            # Apply settings
            for key, value in settings_data.items():
                self.setKey(key, value, backup=False)

            logger.info(f"Settings imported from {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error importing settings from {file_path}: {e}")
            return False

    def _create_backup(self) -> bool:
        """
        Create a backup of current settings.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self._backup_dir / f"settings_backup_{timestamp}.json"

            return self.exportSettings(backup_file)

        except Exception as e:
            logger.warning(f"Error creating settings backup: {e}")
            return False

    def restoreFromBackup(self, backup_file: Optional[Union[str, Path]] = None) -> bool:
        """
        Restore settings from a backup file.

        Parameters:
            backup_file (Optional[Union[str, Path]]): Specific backup file to restore.
                                                     If None, uses the most recent backup.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if backup_file is None:
                # Find most recent backup
                backup_files = list(self._backup_dir.glob("settings_backup_*.json"))
                if not backup_files:
                    raise SettingsError("No backup files found")
                backup_file = max(backup_files, key=lambda p: p.stat().st_mtime)

            return self.importSettings(backup_file, merge=False)

        except Exception as e:
            logger.error(f"Error restoring from backup: {e}")
            return False

    def cleanupBackups(self, keep_count: int = 5) -> None:
        """
        Clean up old backup files, keeping only the most recent ones.

        Parameters:
            keep_count (int): Number of backups to keep
        """
        try:
            backup_files = list(self._backup_dir.glob("settings_backup_*.json"))

            if len(backup_files) > keep_count:
                # Sort by modification time
                backup_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

                # Remove old backups
                for old_backup in backup_files[keep_count:]:
                    old_backup.unlink()

                logger.info(
                    f"Cleaned up {len(backup_files) - keep_count} old backup files"
                )

        except Exception as e:
            logger.warning(f"Error cleaning up backups: {e}")

    def validateAllSettings(self) -> Dict[str, List[str]]:
        """
        Validate all current settings against defaults.

        Returns:
            Dict[str, List[str]]: Dictionary of validation errors by group
        """
        errors = {}

        try:
            for group, settings in DEFAULT_SETTINGS.items():
                group_errors = []

                for key, default_value in settings.items():
                    full_key = f"{group}/{key}"

                    try:
                        current_value = self.getKey(full_key)
                        expected_type = type(default_value)

                        # Validate type
                        self.validator.validate_value(
                            full_key, current_value, expected_type
                        )

                        # Additional validations based on key
                        if "mb" in key.lower() and isinstance(
                            current_value, (int, float)
                        ):
                            self.validator.validate_range(
                                full_key, current_value, 0, 10000
                            )

                    except SettingsError as e:
                        group_errors.append(str(e))

                if group_errors:
                    errors[group] = group_errors

            return errors

        except Exception as e:
            logger.error(f"Error validating settings: {e}")
            return {"general": [f"Validation error: {e}"]}


def restoreWindowGeometry(window: QMainWindow, key: str = "geometry") -> bool:
    """
    Restore window geometry from settings.

    Parameters:
        window (QMainWindow): Window to restore
        key (str): Settings key for geometry

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        global settings
        if settings is None:
            return False

        geometry = settings.value(key)
        if geometry:
            window.restoreGeometry(geometry)
            return True
        return False

    except Exception as e:
        logger.warning(f"Error restoring window geometry: {e}")
        return False


def saveWindowGeometry(window: QMainWindow, key: str = "geometry") -> bool:
    """
    Save window geometry to settings.

    Parameters:
        window (QMainWindow): Window to save
        key (str): Settings key for geometry

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        global settings
        if settings is None:
            return False

        geometry = window.saveGeometry()
        settings.setValue(key, geometry)
        return True

    except Exception as e:
        logger.warning(f"Error saving window geometry: {e}")
        return False


def initialize_settings() -> ApplicationQSettings:
    """
    Initialize the global settings instance.

    Returns:
        ApplicationQSettings: Initialized settings instance
    """
    global settings

    try:
        settings = ApplicationQSettings(
            QSettings.Format.IniFormat, QSettings.Scope.UserScope, ORG_NAME, APP_NAME
        )

        logger.info(f"Settings initialized: {settings.fileName()}")
        return settings

    except Exception as e:
        logger.error(f"Error initializing settings: {e}")
        # Fallback to default QSettings
        settings = ApplicationQSettings()
        return settings


# Initialize settings when module is imported
settings = initialize_settings()
