from PyQt6.QtWidgets import QDialog

from mdaviz import utils


class PopUp(QDialog):
    """Load a generic About... Dialog as a .ui file."""

    # UI file name matches this module, different extension
    ui_file = utils.getUiFileName(__file__)

    def __init__(self, parent, message):
        self.parent = parent

        super().__init__(parent)
        utils.myLoadUi(self.ui_file, baseinstance=self)

        self.message.setText(message)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def accept(self):
        """OK button was clicked"""
        super().accept()
        self.parent.proceed()

    def reject(self):
        """Cancel button was clicked"""
        super().reject()
        self.parent.cancel()
