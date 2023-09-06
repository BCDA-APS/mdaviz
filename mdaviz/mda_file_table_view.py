"""
Search for mda files.
"""

from mda import readMDA
from PyQt5 import QtCore, QtWidgets
from . import utils


class MDAFileTableView(QtWidgets.QWidget):
    ui_file = utils.getUiFileName(__file__)

    def __init__(self, parent):
        self.parent = parent

        super().__init__()
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()

    def setup(self):
        header = self.tableView.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

    def displayTable(self, index):
        from mdaviz.mda_file_table_model import MDAFileTableModel

        data = self.mdaFileList()[index.row()]
        self.tabWidget.setTabText(0, data)
        data_model = MDAFileTableModel(data, self.parent)
        self.tableView.setModel(data_model)

    def dataPath(self):
        """Path (obj) of the data folder."""
        return self.parent.dataPath()

    def mdaFileList(self):
        """List of mda file (name only) in the selected folder."""
        return self.parent.mdaFileList()

    def setStatus(self, text):
        self.parent.setStatus(text)
