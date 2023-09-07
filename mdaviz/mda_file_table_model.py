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
    checkboxToggled = QtCore.pyqtSignal(int, int)

    def __init__(self, data, parent):
        self.parent = parent
        super().__init__()

        self.actions_library = {
            "#": lambda i: self.detDict()[i][0],
            "x": lambda file: "TODO",
            "y": lambda file: "TODO",
            "Mon": lambda file: "TODO",
            "PV": lambda i: self.detDict()[i][1],
            "desc": lambda i: self.detDict()[i][2],
            "unit": lambda i: self.detDict()[i][3],
        }

        self.columnLabels = list(self.actions_library.keys())

        self._checkbox_states = {}  # Key: (row, col), Value: Qt.Checked or Qt.Unchecked
        self._detCount = 0

        self.checkboxToggled.connect(self.on_checkbox_toggled)

        self.setFile(data)  # here data is the file name
        self.setDetDict()

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
        row, col = index.row(), index.column()
        label = self.columnLabels[col]

        if role == QtCore.Qt.CheckStateRole and label in ["x", "y", "Mon"]:
            return self._checkbox_states.get((row, col), QtCore.Qt.Unchecked)

        if role == QtCore.Qt.DisplayRole:
            action = self.actions_library[label]
            if label not in ["x", "y", "Mon"]:
                return action(row)

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

    def get_det_dict(self, file):
        """det_dict = { index: [fieldname, name, desc, unit]}"""
        D = {}
        data = self.get_file_data(file)
        p_list = [data.p[i] for i in range(0, data.np)]
        d_list = [data.d[i] for i in range(0, data.nd)]
        for e, p in enumerate(p_list):
            D[e] = [
                utils.byte2str(p.fieldName),
                utils.byte2str(p.name),
                utils.byte2str(p.desc),
                utils.byte2str(p.unit),
            ]
        for e, d in enumerate(d_list):
            D[e + len(p_list)] = [
                utils.byte2str(d.fieldName),
                utils.byte2str(d.name),
                utils.byte2str(d.desc),
                utils.byte2str(d.unit),
            ]
        return D

    # # ------------ get & set methods

    def file(self):
        return self._data

    def detCount(self):
        return self._detCount

    def detDict(self):
        return self._detDict

    def dataPath(self):
        """Path (obj) of the selected data folder (folder + subfolder)."""
        return self.parent.dataPath()

    def setFile(self, file):
        self._data = file

    def setDetDict(self):
        file = self.file()
        self._detDict = self.get_det_dict(file)
        self._detCount = len(self._detDict)

    def setData(self, index, value, role):
        row, col = index.row(), index.column()
        label = self.columnLabels[col]
        if role == QtCore.Qt.CheckStateRole and label in ["x", "y", "Mon"]:
            self._checkbox_states[(row, col)] = value
            self.checkboxToggled.emit(row, col)
            return True
        return False

    def flags(self, index):
        original_flags = super().flags(index)
        label = self.columnLabels[index.column()]
        if label in ["x", "y", "Mon"]:
            return original_flags | QtCore.Qt.ItemIsUserCheckable
        return original_flags

    def get_checked_boxes(self):
        checked_boxes = []
        for (row, col), state in self._checkbox_states.items():
            if state == QtCore.Qt.Checked:
                checked_boxes.append((row, col))
        return checked_boxes

    def on_checkbox_toggled(self, row, col):
        label = self.columnLabels[col]
        det = self.detDict()[row]
        file = self.file()
        self.setStatus(f"{file}: {label} = {det}")

    def setStatus(self, text):
        self.parent.setStatus(text)
