"""
Search for mda files.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QStyledItemDelegate, QWidget, QHeaderView
from mdaviz import utils
from mdaviz.mda_folder_table_model import HEADERS


class _AlignCenterDelegate(QStyledItemDelegate):
    """https://stackoverflow.com/a/61722299"""

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = Qt.AlignmentFlag.AlignCenter


class MDAFolderTableView(QWidget):
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
        # Configure the horizontal header to resize based on content.
        header = self.tableView.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

    def displayTable(self):
        from mdaviz.mda_folder_table_model import MDAFolderTableModel
        from mdaviz.empty_table_model import EmptyTableModel

        data = self.mdaInfoList()
        if len(data) > 0:
            data_model = MDAFolderTableModel(data, self.mda_mvc)
            self.tableView.setModel(data_model)
            labels = data_model.columnLabels

            def centerColumn(label):
                if label in labels:
                    column = labels.index(label)
                    delegate = _AlignCenterDelegate(self.tableView)
                    self.tableView.setItemDelegateForColumn(column, delegate)

            centerColumn("Scan #")
            centerColumn("Points")
            centerColumn("Dim")
        else:
            empty_model = EmptyTableModel(HEADERS)
            self.tableView.setModel(empty_model)

    def mdaInfoList(self):
        """List of mda file (name only) in the selected folder."""
        return self.mda_mvc.mdaInfoList()

    def setStatus(self, text):
        self.mda_mvc.setStatus(text)

    def clearContents(self):
        # Clear the data model of the table view
        self.tableView.setModel(None)
