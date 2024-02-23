"""
Search for mda files.
"""

from PyQt5 import QtCore, QtWidgets
from . import utils


class _AlignCenterDelegate(QtWidgets.QStyledItemDelegate):
    """https://stackoverflow.com/a/61722299"""

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = QtCore.Qt.AlignCenter


class MDAFolderTableView(QtWidgets.QWidget):
    ui_file = utils.getUiFileName(__file__)

    def __init__(self, parent):
        self.parent = parent

        super().__init__()
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()

    def setup(self):
        header = self.tableView.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

    def displayTable(self):
        from mdaviz.mda_folder_table_model import MDAFolderTableModel

        data = self.mdaFileList()
        if len(data)>0:
            print("YESSSSSSSSSSSSSSSSSSSSSSS")
            data_model = MDAFolderTableModel(data, self.parent)
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
            print("NOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO")
            # No MDA files to display, show an empty table with headers
            self.tableView.setModel(None)  # Clear existing model/data
            data_model = MDAFolderTableModel([], self.parent)  # Create a model with no data
            self.tableView.setModel(data_model)  # Set the model to display just the headers

            # Optionally, set a message or status indicating no files were found
            self.setStatus("No MDA files found in the selected folder.")
        
        
        
    def dataPath(self):
        """Path (obj) of the data folder."""
        return self.parent.dataPath()

    def mdaFileCount(self):
        """Number of mda files in the selected folder."""
        return self.parent.mdaFileCount()

    def mdaFileList(self):
        """List of mda file (name only) in the selected folder."""
        return self.parent.mdaFileList()

    def setStatus(self, text):
        self.parent.setStatus(text)
