"""
Search for mda files.

"""

from PyQt5 import QtWidgets
from pathlib import Path
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

    def folderPath(self):
        return self.parent.folderPath()

    def folderName(self):
        return self.parent.folderName()      
    
    def mdaFiles(self,folder_path):
        mda_files = [file for file in folder_path.glob('*.mda')]
        return mda_files
    
    def setStatus(self, text):
        self.parent.setStatus(text)


        





