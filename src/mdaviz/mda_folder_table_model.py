"""
QAbstractTableModel of folder content.

.. autosummary::

    ~MDAFolderTableModel
"""

from PyQt6.QtCore import QAbstractTableModel, Qt
from mdaviz.utils import HEADERS


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
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            # Center align specific columns
            label = self.columnLabels[index.column()]
            if label in ["Scan #", "Points", "Dim"]:
                return Qt.AlignmentFlag.AlignCenter
        return None

    def headerData(self, section, orientation, role):
        """Return the header data for the given section and role."""
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self.columnLabels[section]
            elif orientation == Qt.Orientation.Vertical:
                return str(section + 1)
        return None

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
