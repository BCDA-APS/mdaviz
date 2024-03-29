from PyQt5 import QtCore
from PyQt5.QtCore import QAbstractTableModel, QVariant, Qt
from . import utils


class DataTableModel(QAbstractTableModel):
    """
    This model is designed to handle data represented as a dictionary where keys correspond to column labels and values are lists of data points for each column.

    Parameters:
    - detsDict (dict): A dictionary where keys are column labels (as strings) and values are lists of data points. Each key-value pair represents a column and its corresponding data in the table.
    - parent (QObject, optional): The parent object for this table model, default is None.

    Methods:
    - rowCount: Returns the number of rows in the table model.
    - columnCount: Returns the number of columns in the table model.
    - data: Returns the data to be displayed for a given index and role.
    - headerData: Provides the header labels for the table model.
    - columnLabels: Returns a list of column labels.
    - setColumnLabels: Sets the column labels based on keys from the input dictionary.
    - allData: Returns the current data stored in the model.
    - setAllData: Sets the model's data using the input dictionary.

    The model dynamically adjusts to changes in the input data, updating both the data displayed and the column headers as necessary.
    """

    def __init__(self, detsDict, parent=None):
        """ """
        super().__init__(parent)

        self.setAllData(detsDict)
        self.setColumnLabels()

    def rowCount(self, parent=None):
        value = len(self.allData()["Index"]) if len(self.allData()) > 0 else 0
        return value

    def columnCount(self, parent=None):
        # Number of columns is determined by the number of pos(s) & det(s)
        return len(self.columnLabels())

    def data(self, index, role):
        # display data
        if role == QtCore.Qt.DisplayRole and self.setAllData is not {}:
            label = self.columnLabels()[index.column()]
            value = self.allData()[label][index.row()]
            return value

    def headerData(self, section, orientation, role):
        """
        Provide horizontal header labels only, nothing for vertical headers (Index is always the first column).
        """
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.columnLabels()[section]
        return QVariant()

    # # # ------------ get & set methods

    def columnLabels(self):
        return self._columnLabels

    def setColumnLabels(self):
        self._columnLabels = list(self.allData().keys())
        return self._columnLabels

    def allData(self):
        return self._allData

    def setAllData(self, detsDict):
        self._allData = {}
        if detsDict:
            for v in list(detsDict.values()):
                pv = utils.byte2str(v.name)
                data = v.data
                self._allData[pv] = data
        return self._allData
