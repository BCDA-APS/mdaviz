from contextlib import nullcontext as does_not_raise
import tempfile
import os

# TODO: (below) from PyQt5 import QtWidgets

from ..mainwindow import MainWindow

# FIXME: gui starts and waits for user to close it
# def test_app(qtbot):
#     """mdaviz app should start with no errors."""
#     from .. import app

#     gui = app.gui()
#     assert gui is not None


def test_app_startup(qtbot):
    """Repeat the steps here that start the GUI, don't wait for user."""
    with does_not_raise():
        # FIXME: dumps core
        # app = QtWidgets.QApplication([])
        # assert app is not None
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create necessary files in temp_dir
            # For example, if MainWindow requires an MDA file:
            mda_file_path = os.path.join(temp_dir, "sample.mda")
            with open(mda_file_path, "w") as f:
                f.write("Sample MDA content")  # Replace with minimal valid MDA content

            # Pass the temporary directory to MainWindow
            main_window = MainWindow(directory=temp_dir)
        assert main_window is not None
        # main_window.setStatus("Application started ...")
        # main_window.show()
