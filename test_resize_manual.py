#!/usr/bin/env python3
"""
Manual test script to verify main window resizing functionality.

This script creates a main window and allows you to manually test resizing.
Run this script and try to resize the window to verify it works correctly.
"""

import sys
from PyQt5 import QtWidgets

# Add the src directory to the path so we can import mdaviz
sys.path.insert(0, "src")

from mdaviz.mainwindow import MainWindow


def main():
    """Run the manual resize test."""
    app = QtWidgets.QApplication(sys.argv)

    # Create the main window
    window = MainWindow()

    # Set a reasonable initial size
    window.resize(800, 600)

    # Show the window
    window.show()

    print("Main window created and shown.")
    print("Try resizing the window to verify it works correctly.")
    print("Press Ctrl+C to exit.")

    # Run the application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
