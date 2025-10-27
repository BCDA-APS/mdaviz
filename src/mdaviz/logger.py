"""
Logging configuration for mdaviz application.

This module provides a centralized logging setup with configurable levels,
file output, and consistent formatting across all modules.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


class MDALogger:
    """Centralized logger for mdaviz application."""

    _instance: Optional["MDALogger"] = None
    _logger: Optional[logging.Logger] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._logger is None:
            self._setup_logger()

    def _setup_logger(self):
        """Setup the main application logger."""
        # Create logger
        self._logger = logging.getLogger("mdaviz")
        self._logger.setLevel(logging.DEBUG)

        # Prevent duplicate handlers
        if self._logger.handlers:
            return

        # Create formatters
        detailed_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
        )
        simple_formatter = logging.Formatter("%(levelname)s - %(name)s - %(message)s")

        # Console handler (INFO level and above)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        self._logger.addHandler(console_handler)

        # File handler (DEBUG level and above)
        log_file = self._get_log_file_path()
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(detailed_formatter)
            self._logger.addHandler(file_handler)

    def _get_log_file_path(self) -> Optional[Path]:
        """Get the log file path, creating directories if needed."""
        try:
            # Try to get user's home directory
            home_dir = Path.home()
            log_dir = home_dir / ".mdaviz" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)

            # Create log file with timestamp
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = log_dir / f"mdaviz_{timestamp}.log"

            return log_file
        except Exception:
            # Fallback to current directory if home directory is not accessible
            return Path("mdaviz.log")

    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        """Get a logger instance, optionally with a specific name."""
        if name:
            return logging.getLogger(f"mdaviz.{name}")
        # Ensure _logger is not None before returning
        if self._logger is None:
            self._setup_logger()
        assert self._logger is not None  # Type checker assertion
        return self._logger

    def set_level(self, level: str):
        """Set the logging level for all handlers."""
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }

        if level.upper() in level_map:
            # Ensure _logger is not None before using it
            if self._logger is None:
                self._setup_logger()
            assert self._logger is not None  # Type checker assertion
            self._logger.setLevel(level_map[level.upper()])
            for handler in self._logger.handlers:
                handler.setLevel(level_map[level.upper()])


# Global logger instance
_mda_logger = MDALogger()


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance for the specified module.

    Args:
        name: Optional module name (e.g., 'mda_file_viz', 'chartview')

    Returns:
        Logger instance configured for the mdaviz application
    """
    return _mda_logger.get_logger(name)


def set_log_level(level: str):
    """
    Set the logging level for the application.

    Args:
        level: Log level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
    """
    _mda_logger.set_level(level)


def enable_debug_mode():
    """Enable debug mode - sets log level to DEBUG."""
    set_log_level("DEBUG")


def disable_debug_mode():
    """Disable debug mode - sets log level to INFO."""
    set_log_level("INFO")


def list_log_files():
    """
    List all available log files.

    Returns:
        List of log file paths
    """
    try:
        home_dir = Path.home()
        log_dir = home_dir / ".mdaviz" / "logs"
        if log_dir.exists():
            return sorted(log_dir.glob("mdaviz_*.log"), reverse=True)
        return []
    except Exception:
        return []


def clear_old_logs(keep_days=7):
    """
    Clear old log files.

    Args:
        keep_days: Number of days to keep log files
    """
    from datetime import datetime, timedelta

    cutoff_time = datetime.now() - timedelta(days=keep_days)

    for log_file in list_log_files():
        try:
            # Try to parse timestamp from filename
            # Format: mdaviz_YYYYMMDD_HHMMSS.log
            timestamp_str = log_file.stem.split("_", 1)[1]
            file_time = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")

            if file_time < cutoff_time:
                log_file.unlink()
                print(f"Deleted old log file: {log_file}")
        except Exception as e:
            print(f"Error processing log file {log_file}: {e}")


# Convenience functions for common logging patterns
def debug(msg: str, *args, **kwargs):
    """Log a debug message."""
    logger = get_logger()
    logger.debug(msg, *args, **kwargs)


def info(msg: str, *args, **kwargs):
    """Log an info message."""
    logger = get_logger()
    logger.info(msg, *args, **kwargs)


def warning(msg: str, *args, **kwargs):
    """Log a warning message."""
    logger = get_logger()
    logger.warning(msg, *args, **kwargs)


def error(msg: str, *args, **kwargs):
    """Log an error message."""
    logger = get_logger()
    logger.error(msg, *args, **kwargs)


def critical(msg: str, *args, **kwargs):
    """Log a critical message."""
    logger = get_logger()
    logger.critical(msg, *args, **kwargs)
