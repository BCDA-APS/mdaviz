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
        # parent = <mdaviz.mda_folder.MDA_MVC object at 0x1101e7520>
        self.parent = parent
        super().__init__()
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()

    def setup(self):
        header = self.tableView.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

    def displayTable(self):
        from mdaviz.mda_folder_table_model import MDAFolderTableModel
        from .empty_table_model import EmptyTableModel

        data = self.mdaFileList()
        if len(data) > 0:
            data_model = MDAFolderTableModel(data, self.parent)
            self.tableView.setModel(data_model)
            # # sets the tab label to be the folder name
            # folder_path = str(self.parent.dataPath())
            # print("Hello", folder_name)
            # # Make sure to strip the trailing slash if it exists
            # folder_path = (
            #     folder_path.rstrip("/") if isinstance(folder_path, str) else folder_path
            # )
            # # Then get the last subfolder name
            # folder_name = folder_path.parts[-1] if folder_path.parts else None

            # # self.tabWidget.setTabText(0, self.file().name)
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

    # def dataPath(self):
    #     """Path (obj) of the data folder."""
    #     return self.parent.dataPath()

    # def mdaFileCount(self):
    #     """Number of mda files in the selected folder."""
    #     return self.parent.mdaFileCount()

    def mdaFileList(self):
        """List of mda file (name only) in the selected folder."""
        return self.parent.mdaFileList()

    def setStatus(self, text):
        self.parent.setStatus(text)

    def clearContents(self):
        # Clear the data model of the table view
        self.tableView.setModel(None)
