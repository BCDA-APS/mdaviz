"""
QAbstractTableModel of folder content.

.. autosummary::

    ~MDAFileTableModel
"""

from mda import readMDA
from pathlib import Path
from PyQt5 import QtCore
from . import utils


# For this purpose, p and d will all be called detectors
# since you can plot d vs p, but also d vd d


class MDAFileTableModel(QtCore.QAbstractTableModel):
    def __init__(self, data, parent):
        self.parent = parent

        self.actions_library = {
            "PV": lambda i: self.get_det_list(i),
            "x": lambda file: "TODO",
            "y": lambda file: "TODO",
            "Mon": lambda file: "TODO",
        }

        self.columnLabels = list(self.actions_library.keys())

        self._detCount = 0

        super().__init__()

        self.setFile(data)  # here data is the file name
        self.setDetList(data)

    # ------------ methods required by Qt's view

    def rowCount(self, parent=None):
        # Want it to return the number of rows to be shown at a given time
        value = self.detCount()
        return value

    def columnCount(self, parent=None):
        # Want it to return the number of columns to be shown at a given time
        value = len(self.columnLabels)
        return value

    def data(self, index, role=None):
        # display data
        if role == QtCore.Qt.DisplayRole:
            # print("Display role:", index.row(), index.column())
            label = self.columnLabels[index.column()]
            action = self.actions_library[label]
            return action(index.row())

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self.columnLabels[section]
            else:
                return str(section + 1)  # may want to alter at some point

    # ------------ local methods

    def get_file_path(self, file):
        # here file is a Path obj Path('mda.0001.mda')
        return self.dataPath() / file

    def get_file_data(self, file):
        filepath = str(self.get_file_path(file))
        return readMDA(filepath)[1]

    def get_det_list(self, file):
        data = self.get_file_data(file)
        p_list = [utils.byte2str(data.p[i].name) for i in range(0, data.np)]
        d_list = [utils.byte2str(data.d[i].name) for i in range(0, data.nd)]
        return p_list + d_list

    # # ------------ get & set methods

    def file(self):
        return self._data

    def detCount(self):
        return self._detCount

    def detList(self):
        return self._detList

    def setFile(self, file):
        self._data = file

    def setDetList(self):
        file = self.file()
        self._detList = self.get_det_list(file)
        self._detCount = len(self._detList)

    def dataPath(self):
        """Path (obj) of the selected data folder (folder + subfolder)."""
        return self.parent.dataPath()
