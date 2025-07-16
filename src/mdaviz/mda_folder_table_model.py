"""
QAbstractTableModel of folder content.

.. autosummary::

    ~MDAFolderTableModel
"""

from PyQt6.QtCore import QAbstractTableModel
from .utils import HEADERS


class MDAFolderTableModel(QAbstractTableModel):
    def __init__(self, data, parent):
        """
        Create the model and connect with its parent.

        PARAMETERS

        parent object:
            Instance of mdaviz.mda_folder.MDAMVC
        """

        self.mda_mvc = parent
        super().__init__()

        self.columnLabels = HEADERS
        self.setFileInfoList(data)

    # ------------ methods required by Qt's view

    def rowCount(self, parent=None):
        # Want it to return the number of rows to be shown at a given time
        value = len(self.fileInfoList())
        return value

    def columnCount(self, parent=None):
        # Want it to return the number of columns to be shown at a given time
        value = len(self.columnLabels)
        return value

    def data(self, index, role=None):
        # display data
        if role == 0:  # Qt.DisplayRole
            label = self.columnLabels[index.column()]
            file_info = self.fileInfoList()[index.row()]
            value = file_info[label]
            return value

    def headerData(self, section, orientation, role=0):  # 0 = Qt.DisplayRole
        if role == 0:  # Qt.DisplayRole
            if orientation == 1:  # Qt.Horizontal
                return self.columnLabels[section]
            else:
                return str(section + 1)  # may want to alter at some point

    # # ------------ get & set methods

    def fileInfoList(self):
        """Here fileList = data arg = self.mainWindow.mdaInfoList()
        ie the list of mda files info
        """
        return self._data

    def setFileInfoList(self, data):
        """Here data arg = self.mainWindow.mdaInfoList()
        ie the list of mda files info
        """
        self._data = data
