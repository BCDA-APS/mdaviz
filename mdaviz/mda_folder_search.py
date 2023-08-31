"""
Search for mda files.

"""

from PyQt5 import QtCore, QtWidgets
from pathlib import Path
from . import utils
from functools import partial


# class mdaSearchPanel(QtWidgets.QWidget):
#     """The panel to select mda files."""

#     # UI file name matches this module, different extension
#     ui_file = utils.getUiFileName(__file__)

#     def __init__(self, parent):
#         self.parent = parent
#         self._server = None

#         super().__init__()
#         utils.myLoadUi(self.ui_file, baseinstance=self)

#     def folderPath(self):
#         return self.parent.folderPath()

#     def folderName(self):
#         return self.parent.folderName()    
    
#     def mdaFilePath(self):
#         return self.parent.mdaFilePath()  

#     def mdaFileName(self):
#         return self.parent.mdaFileName()  
    
#     def mdaFileList(self):
#         return self.parent.mdaFileList()       
        
#     # TODO: self.mda_folder.mda_search_panel.setupFile(self,mda_file)    
#     def setupFile(self,filename):
#         if not filename:
#             pass
#         else:
#             # filename=self.mdaFile()? do I use the attribute or the arg?
#             filepath= self.folderPath() / filename
#             scan_prefix, scan_number_with_ext = filename.rsplit('_', 1)
#             scan_number = scan_number_with_ext.split('.')[0]
#             scan_size = utils.human_readable_size(filepath.stat().st_size)
#             scan_date = utils.ts2iso(round(filepath.stat().st_ctime))
#             self.file_name.setText(scan_prefix)
#             self.file_num.setText(scan_number)
#             self.file_size.setText(scan_size)
#             self.file_date.setText(scan_date)
#             # print(f"{scan_prefix=}")
#             # print(f"{scan_number=}")
#             # print(f"{scan_size=}")
#             # print(f"{scan_date=}")
            
   
#     def doNext(self):
#         self.doButton(1)
#         print('do next')        
        
#     def doPrevious(self):
#         self.doButton(-1)
#         print('do previous')
        
#     def doButton(self,i):            
#         current_mdaFile=self.mdaFileName()
#         current_mdaIndex = self.mdaFileList().index(current_mdaFile)
#         next_mdaIndex = current_mdaIndex+i
#         next_mdaFile=self.mdaFileList()[next_mdaIndex]
#         self.parent.parent.catalogs.setCurrentIndex(next_mdaIndex)
#         print(f"{current_mdaFile=}")        
#         print(f"{next_mdaFile=}")
        


class _AlignCenterDelegate(QtWidgets.QStyledItemDelegate):
    """https://stackoverflow.com/a/61722299"""

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = QtCore.Qt.AlignCenter
        
class mdaFolderTableView(QtWidgets.QWidget):
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

    def displayTable(self, parent):
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
        return self.parent.folderName()    
    
    def mdaFilePath(self):
        return self.parent.mdaFilePath()  

    def mdaFileName(self):
        return self.parent.mdaFileName()  
    
    def mdaFileList(self):
        return self.parent.mdaFileList()   
    
    def folderSize(self):
        return self.parent.folderSize 

    def setStatus(self, text):
        self.parent.setStatus(text)


