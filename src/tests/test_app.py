from contextlib import nullcontext as does_not_raise

# TODO: (below) from PyQt5 import QtWidgets

from mdaviz.mainwindow import MainWindow

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
        main_window = MainWindow()
        assert main_window is not None
        # main_window.setStatus("Application started ...")
        # main_window.show()
