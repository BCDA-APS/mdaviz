"""
QAbstractTableModel of folder content.

.. autosummary::

    ~MDAFolderTableModel
"""

from mda import readMDA
from pathlib import Path
from PyQt5 import QtCore
from . import utils


class MDAFolderTableModel(QtCore.QAbstractTableModel):
    def __init__(self, data, parent):
        # parent = <mdaviz.mda_folder.MDA_MVC object at 0x1101e7520>
        self.parent = parent
        self.actions_library = {
            "Prefix": lambda file: file.rsplit("_", 1)[0],
            "Scan #": lambda file: int(file.rsplit("_", 1)[1].split(".")[0]),
            "Points": lambda file: self.get_file_pts(file),
            "Dim": lambda file: self.get_file_dim(file),
            "Positioner": lambda file: self.get_file_pos(file),
            "Date": lambda file: self.get_file_date(file),
            "Size": lambda file: self.get_file_size(file),
        }

        self.columnLabels = list(self.actions_library.keys())
        self._fileListCount = 0

        super().__init__()

        self.setFileList(data)

    # ------------ methods required by Qt's view

    def rowCount(self, parent=None):
        # Want it to return the number of rows to be shown at a given time
        value = len(self.fileList())
        # value = self.mainWindow.mdaFileCount()
        return value

    def columnCount(self, parent=None):
        # Want it to return the number of columns to be shown at a given time
        value = len(self.columnLabels)
        return value

    def data(self, index, role=None):
        # display data
        if role == QtCore.Qt.DisplayRole:
            file = self.fileList()[index.row()]
            label = self.columnLabels[index.column()]
            action = self.actions_library[label]
            return action(file)

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self.columnLabels[section]
            else:
                return str(section + 1)  # may want to alter at some point

    # ------------ local methods

    def get_file_path(self, file):
        return self.dataPath() / file

    def get_file_size(self, file):
        filepath = self.get_file_path(file)
        return utils.human_readable_size(filepath.stat().st_size)

    def get_file_date(self, file):
        filepath = self.get_file_path(file)
        return utils.byte2str(readMDA(str(filepath))[1].time).split(".")[0]

    def get_file_pts(self, file):
        filepath = self.get_file_path(file)
        return readMDA(str(filepath))[1].curr_pt

    def get_file_dim(self, file):
        filepath = self.get_file_path(file)
        return readMDA(str(filepath))[1].dim

    def get_file_pos(self, file):
        filepath = self.get_file_path(file)
        pv = (
            utils.byte2str(readMDA(str(filepath))[1].p[0].name)
            if len(readMDA(str(filepath))[1].p)
            else "index"
        )
        desc = (
            utils.byte2str(readMDA(str(filepath))[1].p[0].desc)
            if len(readMDA(str(filepath))[1].p)
            else "index"
        )
        return desc if desc else pv

    # # ------------ get & set methods

    def dataPath(self):
        """Path (obj) of the selected data folder (folder + subfolder)."""
        return self.parent.dataPath()

    def fileList(self):
        """Here fileList = data arg = self.mainWindow.mdaFileList()
        ie the list of mda file NAME str (name only)
        """
        return self._data

    def setFileList(self, data):
        """Here data arg = self.mainWindow.mdaFileList()
        ie the list of mda file NAME str (name only)
        """
        self._data = data
        self._fileListCount = len(data)
