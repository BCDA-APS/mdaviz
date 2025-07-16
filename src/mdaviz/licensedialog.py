from PyQt6.QtWidgets import QDialog

from . import utils


class LicenseDialog(QDialog):
    """Show license text in a GUI window."""

    # UI file name matches this module, different extension
    ui_file = utils.getUiFileName(__file__)

    def __init__(self, parent):
        self.parent = parent

        super().__init__(parent)
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()

    def setup(self):
        import pathlib

        # Find the LICENSE.txt file relative to the project root
        current_file = pathlib.Path(__file__)
        project_root = current_file.parent.parent.parent
        LICENSE_FILE = project_root / "LICENSE.txt"

        self.setModal(True)
        license_text = open(LICENSE_FILE, "r").read()
        self.license.setText(license_text)
