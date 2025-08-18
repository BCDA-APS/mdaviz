"""
Logging configuration for mdaviz application.

This module provides easy configuration options for the logging system.
"""

import os
from pathlib import Path
from mdaviz.logger import set_log_level, enable_debug_mode, disable_debug_mode


def configure_logging():
    """
    Configure logging based on environment variables and user preferences.

    Environment variables:
    - MDAVIZ_LOG_LEVEL: Set to DEBUG, INFO, WARNING, ERROR, or CRITICAL
    - MDAVIZ_DEBUG: Set to 1, true, or yes to enable debug mode
    - MDAVIZ_LOG_FILE: Path to log file (optional, defaults to ~/.mdaviz/logs/)
    """

    # Check for debug mode
    if os.environ.get("MDAVIZ_DEBUG", "").lower() in ("1", "true", "yes"):
        enable_debug_mode()
        return

    # Check for specific log level
    log_level = os.environ.get("MDAVIZ_LOG_LEVEL", "INFO").upper()
    set_log_level(log_level)


def get_log_file_path():
    """
    Get the current log file path.

    Returns:
        Path to the current log file
    """
    from mdaviz.logger import _mda_logger

    return _mda_logger._get_log_file_path()


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


# Convenience functions for common use cases
def enable_verbose_logging():
    """Enable verbose logging (DEBUG level)."""
    enable_debug_mode()


def enable_normal_logging():
    """Enable normal logging (INFO level)."""
    disable_debug_mode()


def enable_quiet_logging():
    """Enable quiet logging (WARNING level and above only)."""
    set_log_level("WARNING")
