"""
Search for mda files.
"""

from PyQt5 import QtCore, QtWidgets
from . import utils
from .mda_folder_table_model import HEADERS


class _AlignCenterDelegate(QtWidgets.QStyledItemDelegate):
    """https://stackoverflow.com/a/61722299"""

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = QtCore.Qt.AlignCenter


class MDAFolderTableView(QtWidgets.QWidget):
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
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

    def displayTable(self):
        from .mda_folder_table_model import MDAFolderTableModel
        from .empty_table_model import EmptyTableModel

        from pathlib import Path

        data = self.mdaFileList()
        # data_path = Path(self.mda_mvc.dataPath())
        # data_path = (
        #     Path(self.mda_mvc.mainWindow.folder.currentText()).parent
        #     / self.mda_mvc.mainWindow.subfolder.currentText()
        # )
        # print(f"==== {data_path=}")
        # data = [file for file in data if (data_path / file).is_file()]
        if data:
            print(f"==== {data[0]=}")

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
            centerColumn("Positioner")
            centerColumn("Dim")
        else:
            empty_model = EmptyTableModel(HEADERS)
            self.tableView.setModel(empty_model)

    def mdaFileList(self):
        """List of mda file (name only) in the selected folder."""
        return self.mda_mvc.mdaFileList()

    def setStatus(self, text):
        self.mda_mvc.setStatus(text)

    def clearContents(self):
        # Clear the data model of the table view
        self.tableView.setModel(None)
