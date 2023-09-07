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

    def data(self):
        return self._data

    def dataModel(self):
        return self._dataModel

    def setData(self, index):
        data = self.mdaFileList()[index]
        self._data = data

    def setDataModel(self, index):
        from mdaviz.mda_file_table_model import MDAFileTableModel

        self.setData(index)
        data = self.data()
        self._dataModel = MDAFileTableModel(data, self.parent)

    def displayTable(self, index):
        self.setDataModel(index)
        model = self.dataModel()
        self.tabWidget.setTabText(0, self.data())
        self.tableView.setModel(model)

    def displayMetadata(self, index):
        self.setDataModel(index)
        model = self.dataModel()
        self.parent.mda_file_visualization.setMetadata(model.getMetadata())

    def dataPath(self):
        """Path (obj) of the data folder."""
        return self.parent.dataPath()

    def mdaFileList(self):
        """List of mda file (name only) in the selected folder."""
        return self.parent.mdaFileList()

    def setStatus(self, text):
        self.parent.setStatus(text)
