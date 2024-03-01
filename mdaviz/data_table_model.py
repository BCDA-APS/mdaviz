from PyQt5.QtCore import QAbstractTableModel, QVariant, Qt


class DataTableModel(QAbstractTableModel):

    def __init__(self, data, parent=None):
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
            I don't know yet! I'd like it to be mda_folder
        """
        self.parent = parent  #TODO: rename when I know who's the parent
        super().__init__(parent)
        self.columnLabels = headers

    def rowCount(self, parent=None):
        value = len(self.data())
        return value

    def columnCount(self, parent=None):
        # Number of columns is determined by the number of headers
        return len(self.columnLabels)

    def data(self, index, role):
        # No data is provided
        return QVariant()

    def headerData(self, section, orientation, role):
        # Provide header labels
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.columnLabels[section]
        return QVariant()

    # # ------------ local methods

    # def get_file_data(self, file, selection):
    #     """Here dataList is going to be something like:
    #     X (eg P1) = [1,2,3,4,5,6,7,8,9]
    #     Y1 (eg D01) = [corresponding value for this detector]
    #     Y2 (eg D08) = [corresponding value for this detector]
    #     """       


    # # # ------------ get & set methods

    def data(self):
        """Here data is the content of a file?
        """
        return self._data

    def setData(self, data):
        """Here arg data is?
        """
        self._data = data
