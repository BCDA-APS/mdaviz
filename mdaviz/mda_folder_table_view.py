from PyQt5 import QtCore, QtWidgets

import utils

class _AlignCenterDelegate(QtWidgets.QStyledItemDelegate):
    """https://stackoverflow.com/a/61722299"""

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = QtCore.Qt.AlignCenter
        
class MdaFolderTableView(QtWidgets.QWidget):
    # ui_file = utils.getUiFileName(__file__)  # WARNING no ui file, just a tab in mda_folder_search.ui

    def __init__(self, parent):
        self.parent = parent
        super().__init__()
        # utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()
        
    def setup(self):
        header = self.parent.tableView.horizontalHeader()   #tableview belong to mda_folder_search
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)        