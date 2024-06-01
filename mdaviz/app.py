#!/usr/bin/env python

"""
mdaviz: Python Qt5 application to visualize mda data.

.. autosummary::

    ~gui
    ~command_line_interface
    ~main
"""

import logging
import pathlib
import sys


def gui(directory):
    """Display the main window"""
    from PyQt5 import QtWidgets

    from .mainwindow import MainWindow

    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow(directory=directory)
    main_window.setStatus(
        f"Application started, loading {pathlib.Path(directory).absolute()} ..."
    )
    main_window.show()
    sys.exit(app.exec())


def command_line_interface():
    import argparse

    from . import __version__

    doc = __doc__.strip().splitlines()[0]
    parser = argparse.ArgumentParser(description=doc)

    # fmt: off
    parser.add_argument(
        "--log",
        default="warning",
        help=(
            "Provide logging level. "
            "Example '--log debug'. "
            "Default level: 'warning'"),
        choices=[k.lower() for k in logging.getLevelNamesMapping()],
    )
    # fmt: on

    parser.add_argument(
        "directory",
        help=("Directory loaded at start up. This argument is required."),
        type=str,
    )

    parser.add_argument("-v", "--version", action="version", version=__version__)

    return parser.parse_args()


def main():  # for future command-line options
    from pathlib import Path

    global logger

    try:
        options = command_line_interface()
    except SystemExit as e:
        print(
            "\n\nERROR: You must specified the directory:\n\tmdaviz /path/to/mda/data\n"
        )
        sys.exit(1)

    # Resolve the directory to an absolute path and remove trailing slash
    directory_path = Path(options.directory).resolve()
    directory = directory_path.as_posix().rstrip("/")

    # Ensure the path is absolute (starts with a "/")
    if not directory.startswith("/"):
        print(
            f"\n\nERROR: The specified directory is not an absolute path:\n\t{directory}\n"
        )
        sys.exit(1)

    # Check if the directory exists
    if not directory_path.exists() or not directory_path.is_dir():
        print(
            f"\n\nERROR: The specified directory does not exist or is not a directory:\n\t{directory}\n"
        )
        sys.exit(1)

    logging.basicConfig(level=options.log.upper())
    logger = logging.getLogger(__name__)
    logger.info("Logging level: %s", options.log)

    # set warning log level for (noisy) support packages
    for package in "httpcore httpx PyQt5 tiled".split():
        logging.getLogger(package).setLevel(logging.WARNING)

    gui(directory)


if __name__ == "__main__":
    main()
