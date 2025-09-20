#!/usr/bin/env python

"""
mdaviz: Python Qt5 application to visualize mda data.

.. autosummary::

    ~gui
    ~command_line_interface
    ~main
"""

import sys
from PyQt6 import QtWidgets
from mdaviz.mainwindow import MainWindow
import argparse
from mdaviz.logger import get_logger, set_log_level, enable_debug_mode
from mdaviz.logging_config import clear_old_logs

# Get logger for this module
logger = get_logger("app")


def gui() -> None:
    """Display the main window."""
    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow()
    main_window.setStatus("Application started ...")
    main_window.show()
    sys.exit(app.exec())


def command_line_interface() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    from mdaviz import __version__

    # Handle case where __doc__ is None (PyInstaller environment)
    doc = (
        __doc__.strip().splitlines()[0]
        if __doc__
        else "mdaviz: Python Qt5 application to visualize mda data."
    )
    parser = argparse.ArgumentParser(description=doc)

    # fmt: off
    parser.add_argument(
        "--log",
        default="warning",
        help=(
            "Provide logging level. "
            "Example '--log debug'. "
            "Default level: 'warning'"),
        choices=["debug", "info", "warning", "error", "critical"],
    )
    # fmt: on

    parser.add_argument("-v", "--version", action="version", version=__version__)

    return parser.parse_args()


def main() -> None:  # for future command-line options
    """Main entry point for the application."""
    options = command_line_interface()

    # Clean up old log files (keep logs from last 1 day)
    clear_old_logs(keep_days=1)

    # Configure logging level based on command line argument or environment variable
    import os
    import logging

    # Set external package loggers to WARNING to reduce noise
    for package in ["httpcore", "httpx", "PyQt6"]:
        logging.getLogger(package).setLevel(logging.WARNING)

    # Use command line argument first, then environment variable as fallback
    if options.log != "warning":  # If user specified a log level
        set_log_level(options.log.upper())
        logger.info("Starting mdaviz application")
    elif os.environ.get("MDAVIZ_DEBUG", "").lower() in ("1", "true", "yes"):
        # Fallback to environment variable if no command line argument
        enable_debug_mode()
        logger.info("Debug mode enabled via environment variable")
    else:
        # Default to command line argument (warning)
        set_log_level(options.log.upper())
        logger.info("Starting mdaviz application")

    logger.info("Logging level: %s", options.log)

    gui()


if __name__ == "__main__":
    main()
