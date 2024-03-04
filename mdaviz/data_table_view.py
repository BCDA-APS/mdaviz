from PyQt5 import QtCore, QtWidgets
from . import utils

HEADERS = ["X", "Y"]


class DataTableView(QtWidgets.QWidget):

    def __init__(self, data, parent):
        """
        This class is responsible for setting up a table view widget, managing the data displayed within it,
        and connecting the table view with its parent visualization component. It supports displaying both
        populated and empty datasets, dynamically adjusting the presentation according to the data provided.

        Attributes:
            mda_viz (MDAFileVisualization): The parent visualization component that this table view is associated with.

        Parameters:
            data (dict): The initial dataset to be displayed in the table view. Defaults to an empty dict if not provided.
            parent (MDAFileVisualization): The parent visualization component that this table view is part of.
        """

        self.mda_viz = parent
        super().__init__()
        self.setup()
        self.setData(data)

    def setup(self):
        # Hide the vertical header since the index is already provided as a column.
        self.mda_viz.tableView.verticalHeader().hide()
        # Configure the horizontal header to resize based on content.
        header = self.mda_viz.tableView.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

    def displayTable(self):
        from .data_table_model import DataTableModel
        from .empty_table_model import EmptyTableModel

        data = self.data()
        if len(data) > 0:
            data_model = DataTableModel(data)
            self.mda_viz.tableView.setModel(data_model)
        else:
            empty_model = EmptyTableModel(HEADERS)
            self.mda_viz.tableView.setModel(empty_model)

    def data(self):
        return self._data

    def setData(self, data=None):
        data = data or {}
        self._data = data

    def setStatus(self, text):
        self.mda_viz.mda_mvc.setStatus(text)

    def clearContents(self):
        # Clear the data model of the table view
        self.mda_viz.tableView.setModel(None)
