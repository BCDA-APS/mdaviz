from PyQt5 import QtWidgets



class OpenDialog(QtWidgets.QDialog.QFileDialog):
    """Open a file dialog GUI window."""

    # UI file name matches this module, different extension
    ui_file = utils.getUiFileName(__file__)

    def __init__(self, parent):
        self.parent = parent

        super().__init__(parent)
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()

    def setup(self):

        self.setModal(True)
