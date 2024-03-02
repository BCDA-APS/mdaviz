from PyQt5 import QtCore, QtWidgets
from . import utils

HEADERS = ["X", "Y"]


class DataTableView(QtWidgets.QWidget):
    ui_file = utils.getUiFileName(__file__)

    def __init__(self, parent):
        """
        Create the table view and connect with its parent.

        PARAMETERS

        parent object:
            Instance of mdaviz.mda_folder.MDAMVC
        """

        self.mda_mvc = parent
        super().__init__()
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()

    def setup(self):
        header = self.tableView.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

    def displayTable(self):
        from .data_table_model import DataTableModel
        from .empty_table_model import EmptyTableModel

        data = self.detsDict()
        if len(data) > 0:
            data_model = DataTableModel(data, self.mda_mvc)
            self.tableView.setModel(data_model)
        else:
            empty_model = EmptyTableModel(HEADERS)
            self.tableView.setModel(empty_model)

    def detsDict(self):
        return self.mda_mvc.select_fields_tableview.detsDict()

    def setStatus(self, text):
        self.mda_mvc.setStatus(text)

    def clearContents(self):
        # Clear the data model of the table view
        self.tableView.setModel(None)


# self.select_fields_tableview.displayData(index.row())
