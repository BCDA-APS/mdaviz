"""
Search for mda files.

"""

from PyQt5 import QtWidgets

from . import utils


class mdaSearchPanel(QtWidgets.QWidget):
    """The panel to select mda files."""

    # UI file name matches this module, different extension
    ui_file = utils.getUiFileName(__file__)

    def __init__(self, parent):
        self.parent = parent
        self._server = None

        super().__init__()
        utils.myLoadUi(self.ui_file, baseinstance=self)

    def file(self):
        return self.parent.file()

    def setStatus(self, text):
        self.parent.setStatus(text)
