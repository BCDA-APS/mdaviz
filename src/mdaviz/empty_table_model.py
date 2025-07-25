from PyQt6.QtCore import QVariant
from PyQt6.QtCore import QAbstractTableModel


class EmptyTableModel(QAbstractTableModel):
    def __init__(self, headers, parent=None):
        super().__init__(parent)
        self.headers = headers

    def rowCount(self, parent=None):
        # No rows of data
        return 0

    def columnCount(self, parent=None):
        # Number of columns is determined by the number of headers
        return len(self.headers)

    def data(self, index, role):
        # No data is provided
        return QVariant()

    def headerData(self, section, orientation, role):
        # Provide header labels
        if role == 0 and orientation == 1:  # Qt.DisplayRole and Qt.Horizontal
            return self.headers[section]
        return QVariant()

    def clearAllCheckboxes(self):
        # no check box to clear in an empty table
        return

    def uncheckCheckBox(self, row):
        # no check box to uncheck in an empty table
        return
