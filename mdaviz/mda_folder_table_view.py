from functools import partial

from PyQt5 import QtCore, QtWidgets

class _AlignCenterDelegate(QtWidgets.QStyledItemDelegate):
    """https://stackoverflow.com/a/61722299"""

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = QtCore.Qt.AlignCenter
        
class mdaFolderTableView(QtWidgets.QWidget):
    # ui_file = utils.getUiFileName(__file__)  # WARNING no ui file, just a tab in mda_folder_search.ui

    def __init__(self, parent):
        self.parent = parent
        
        super().__init__()
        # utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()
        
    def setup(self):
        header = self.parent.tableview.horizontalHeader()   #tableview belong to mda_folder_search
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)        
        
        for button_name in "first back next last".split():
            button = getattr(self.parent, button_name)
            # custom: pass the button name to the receiver
            button.released.connect(partial(self.doPagerButtons, button_name))
            
        self.parent.pageSize.currentTextChanged.connect(self.doPageSize)
        self.doButtonPermissions()
        self.setPagerStatus()
        self.parent.tableview.doubleClicked.connect(self.doFileSelected)
        
    def doPagerButtons(self, action, **kwargs):
        # self.setStatus(f"{action=} {kwargs=}")
        model = self.parent.tableview.model()

        if model is not None:
            model.doPager(action)
            self.setStatus(f"{model.pageOffset()=}")
        self.doButtonPermissions()
        self.setPagerStatus()

    def doPageSize(self, value):
        # self.setStatus(f"doPageSize {value =}")
        model = self.parent.tableview.model()

        if model is not None:
            model.doPager("pageSize", value)
        self.doButtonPermissions()
        self.setPagerStatus()

    def doButtonPermissions(self):
        model = self.parent.tableview.model()
        atStart = False if model is None else model.isPagerAtStart()
        atEnd = False if model is None else model.isPagerAtEnd()

        self.parent.first.setEnabled(not atStart)
        self.parent.back.setEnabled(not atStart)
        self.parent.next.setEnabled(not atEnd)
        self.parent.last.setEnabled(not atEnd)

    def displayTable(self):
        from mdaviz.mda_folder_table_model import MDAFolderTableModel

        self.folder = self.parent.mdaFileList()
        data_model = MDAFolderTableModel(self.folder)
        page_size = self.parent.pageSize.currentText()  # remember the current value
        self.parent.tableview.setModel(data_model)
        self.doPageSize(page_size)  # restore
        self.setPagerStatus()
        
        labels = data_model.columnLabels

        def centerColumn(label):
            if label in labels:
                column = labels.index(label)
                delegate = _AlignCenterDelegate(self.parent.tableview)
                self.parent.tableview.setItemDelegateForColumn(column, delegate)

        centerColumn("Scan #")
        centerColumn("Points")
        centerColumn("Dim")

    def setPagerStatus(self, text=None):
        if text is None:
            model = self.parent.tableview.model()
            if model is not None:
                text = model.pagerStatus()

        self.status.setText(text)
        self.setStatus(text)

    def doFileSelected(self, index):
        model = self.parent.tableview.model()
        if model is not None:
            self.setStatus(f"A file as been selected: {index=}")

    def setStatus(self, text):
        self.parent.setStatus(text)