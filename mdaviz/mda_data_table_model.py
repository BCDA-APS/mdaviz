"""
QAbstractTableModel of folder content.

.. autosummary::

    ~MDAFileTableModel
"""
from mda import readMDA
from PyQt5 import QtCore
import yaml
from . import utils


# Here data =  [file, {(3, 1): 2, (4, 3): 2, (5, 2): 2, (4, 1): 0}]  (row,col): 2 (checked, 0 unchecked)


class MDADataTableModel(QtCore.QAbstractTableModel):
    def __init__(self, data, parent):
        self.parent = parent
        super().__init__()

        self.columnLabels = [
            "x",
            "y",
            "Mon",
        ]  # do I want to add mon? what if there is no mon?

        self._npts = 0

        self.setMDAData(data)

    # ------------ methods required by Qt's view

    def rowCount(self, parent=None):
        # Want it to return the number of rows to be shown at a given time
        value = self.npts()
        return value

    def columnCount(self, parent=None):
        # Want it to return the number of columns to be shown at a given time
        value = len(self.columnLabels)
        return value

    def data(self, index, role=None):
        row, col = index.row(), index.column()
        label = self.columnLabels[col]

        if role == QtCore.Qt.DisplayRole:
            # TODO
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
        """det_dict = { index: [fieldname, number]}"""
        D = {}
        data = self.get_file_data(file)
        p_list = [data.p[i] for i in range(0, data.np)]
        d_list = [data.d[i] for i in range(0, data.nd)]
        for e, p in enumerate(p_list):
            D[e] = [p.fieldName, p.number]
        for e, d in enumerate(d_list):
            D[e + len(p_list)] = [d.fieldName, d.number]
        return D

    def get_data(self, file, n):
        D = self.get_det_dict(file)
        data = self.get_file_data(file)
        det_type = D[n][0][0]
        det_index = D[n][1]
        if det_type == "P":
            return data.p[det_index].data
        if det_type == "D":
            return data.d[det_index].data

    # # ------------ get & set methods

    def dataPath(self):
        """Path (obj) of the selected data folder (folder + subfolder)."""
        return self.parent.dataPath()

    def mdaData(self):
        return self._data

    def file(self):
        return self._file

    def npts(self):
        return self._npts

    def x(self):
        return self._x

    def y(self):
        return self._y

    def i0(self):
        return self._i0

    def setMDAData(self, data):
        self._data = data
        self._file = data[0]
        self._npts = self.get_file_data(self._file).curr_pt
        self._x, self._y, self._i0 = None, None, None
        for key, value in data[1].items():
            if key[1] == 1 and value == 2:  # col 'x'
                self._x = key[0]
            elif key[1] == 2 and value == 2:  # col 'y'
                self._y = key[0]
            elif key[1] == 3 and value == 2:  # col 'Mon'
                self._i0 = key[0]
        for key, value in data[1].items:
            self._x = data[1][key][0] if key[1] == 1 and value == 2 else None
            self._y = data[1][key][0] if key[1] == 2 and value == 2 else None
            self._i0 = data[1][key][0] if key[1] == 3 and value == 2 else None

        # x = 4, y =3, i0 =5
        # BUT I need to know what correspond to which index in the table! => get_data

    def setStatus(self, text):
        self.parent.setStatus(text)
