from PyQt5 import QtCore
from PyQt5.QtCore import QAbstractTableModel, QVariant, Qt
from . import utils


class DataTableModel(QAbstractTableModel):

    def __init__(self, detsDict, parent=None):
        """
                Create the model and connect with its parent.

                Here the number of row is going to be the indexes,
                with the number of rows being the number of points
                in the selected scan

                The number of column will either:
                    - (1) all the data: all pos + all dets
                    - or (2) just the number of element
                in selection, eg: selection = {Y:[2,3],X=[0]},
                then number of column will be 3
                not taking into account Mon and Norm for now.
                Do we want to always show indexes?
                For now (1) is easier, let's just do that.

        ,

                PARAMETERS
                headers:
                    will be defined by the selection from fields TV:
                    pos and det(s)
                parent object:
                    I don't know yet! I'd like it to be MDA_MVC but might end up being FTV
        """
        # TODO: confirm who's the parent: FTV or MDA_MVC?
        self.mda_mvc = parent
        super().__init__(parent)

        self.setAllData()
        self.setColumnLabels()

    def rowCount(self, parent=None):
        value = len(self.allData()[0]) if len(self.allData()) > 0 else 0
        return value

    def columnCount(self, parent=None):
        # Number of columns is determined by the number of pos(s) & det(s)
        return len(self.columnLabels())

    def data(self, index, role):
        # display data
        if role == QtCore.Qt.DisplayRole and self.setAllData is not {}:
            label = self.columnLabels[index.column()]
            value = self.allData()[label][index.row()]
            return value

    def headerData(self, section, orientation, role):
        # Provide header labels
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.columnLabels[section]
        return QVariant()

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self.columnLabels[section]
            else:
                return str(section + 1)  # may want to alter at some point

    # # # ------------ get & set methods

    def columnLabels(self):
        return self._columnLabels

    def setColumnLabels(self):
        self._columnLabels = list(self.allData.keys())
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
