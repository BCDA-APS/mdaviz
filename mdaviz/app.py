#!/usr/bin/env python

"""
mdaviz: Python Qt5 application to visualize Bluesky data from tiled server.
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
        default=".",
        help=(
            "Directory loaded at start up."
            "  If omitted, use the present working directory"
            f" ({pathlib.Path('.').absolute()})."
        ),
        nargs="?",
        type=str,
    )

    parser.add_argument("-v", "--version", action="version", version=__version__)

    return parser.parse_args()


def main():  # for future command-line options
    global logger

    options = command_line_interface()

    print(f"{options.directory=!r}")

    logging.basicConfig(level=options.log.upper())
    logger = logging.getLogger(__name__)
    logger.info("Logging level: %s", options.log)

    # set warning log level for (noisy) support packages
    for package in "httpcore httpx PyQt5 tiled".split():
        logging.getLogger(package).setLevel(logging.WARNING)

    gui(options.directory)


if __name__ == "__main__":
    main()
