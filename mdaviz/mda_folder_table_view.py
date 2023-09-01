"""
Search for mda files.

"""

from PyQt5 import QtCore, QtWidgets
from pathlib import Path
from . import utils
from functools import partial
       


class _AlignCenterDelegate(QtWidgets.QStyledItemDelegate):
    """https://stackoverflow.com/a/61722299"""

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = QtCore.Qt.AlignCenter
        
class MDAFolderTableView(QtWidgets.QWidget):
    ui_file = utils.getUiFileName(__file__)  # WARNING no ui file, just a tab in mda_folder_search.ui

    def __init__(self, parent):
        self.parent = parent

        super().__init__()
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()
        
    def setup(self):
        header = self.tableView.horizontalHeader()   #tableview belong to mda_folder_search
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)        
        
        # for button_name in "first back next last".split():
        #     button = getattr(self, button_name)
        #     # custom: pass the button name to the receiver
        #     button.released.connect(partial(self.doPagerButtons, button_name))
            
        # self.pageSize.currentTextChanged.connect(self.doPageSize)
        # self.doButtonPermissions()
        # self.setPagerStatus()
        self.tableView.doubleClicked.connect(self.doFileSelected)
        
    # def doPagerButtons(self, action, **kwargs):
    #     # self.setStatus(f"{action=} {kwargs=}")
    #     model = self.tableView.model()

    #     if model is not None:
    #         model.doPager(action)
    #         self.setStatus(f"{model.pageOffset()=}")
    #     self.doButtonPermissions()
    #     self.setPagerStatus()

    # def doPageSize(self, value):
    #     # self.setStatus(f"doPageSize {value =}")
    #     model = self.tableView.model()
    #     print(f"{value=}")
    #     if model is not None:
    #         print("no Model")
    #         model.doPager("pageSize", value)
    #     self.doButtonPermissions()
    #     self.setPagerStatus()

    # def doButtonPermissions(self):
    #     model = self.tableView.model()
    #     atStart = False if model is None else model.isPagerAtStart()
    #     atEnd = False if model is None else model.isPagerAtEnd()

    #     self.first.setEnabled(not atStart)
    #     self.back.setEnabled(not atStart)
    #     self.next.setEnabled(not atEnd)
    #     self.last.setEnabled(not atEnd)

    def displayTable(self):
        from mdaviz.mda_folder_table_model import MDAFolderTableModel
        data = self.mdaFileList()
        data_model = MDAFolderTableModel(data, self.parent)
        # print(f"{data_model=}")
        # page_size = self.pageSize.currentText()  # remember the current value
        # print(f"{page_size=}")
        self.tableView.setModel(data_model)
        # self.doPageSize(page_size)  # restore
        # self.setPagerStatus()
        
        labels = data_model.columnLabels
 
        def centerColumn(label):
            if label in labels:
                column = labels.index(label)
                delegate = _AlignCenterDelegate(self.tableView)
                self.tableView.setItemDelegateForColumn(column, delegate)

        centerColumn("Scan #")
        centerColumn("Points")
        centerColumn("Dim")

    # def setPagerStatus(self, text=None):
    #     if text is None:
    #         model = self.tableView.model()
    #         if model is not None:
    #             text = model.pagerStatus()

    #     self.status.setText(text)
    #     self.setStatus(text)

    def doFileSelected(self, index):
        model = self.tableView.model()
        if model is not None:
            self.setStatus(f"A file as been selected: {index!r}")

    def folderName(self):
        """Path (str) of the selected folder."""
        return self.parent.folderName()
    
    def folderPath(self):
        """Path (obj) of the selected folder."""
        return self.parent.folderPath()
    
    def folderSize(self):
        """Number of mda files in the selected folder."""
        return self.parent.folderSize()
    
    def mdaFileList(self):
        """List of mda file (name only) in the selected folder."""
        return self.parent.mdaFileList()


    def setStatus(self, text):
        self.parent.setStatus(text)


