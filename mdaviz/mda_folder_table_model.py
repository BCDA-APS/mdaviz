"""
QAbstractTableModel of folder content.

.. autosummary::

    ~MDAFolderTableModel
"""

from PyQt5 import QtCore

DEFAULT_PAGE_SIZE = 20
DEFAULT_PAGE_OFFSET = 0




class MDAFolderTableModel(QtCore.QAbstractTableModel):

    def __init__(self, data):
        
        self.actions_library = {
            "Scan prefix": lambda file: file.rsplit('_', 1)[0],
            "Scan #": lambda file: file.rsplit('_', 1)[1].split('.')[0],
            "Points": lambda file: 'TODO',# TODO: get_file_pts
            "Dim": lambda file: 'TODO',   # TODO: get_file_dim need to extract data from the file for that, will need parent (file path)
            "Size": lambda file: 'TODO',  # TODO: get_size_size need parent (file path)
            "Date": lambda file: 'TODO',  # TODO
        }
        
        self.columnLabels = list(self.actions_library.keys())
        
        # self.setPageOffset(DEFAULT_PAGE_OFFSET, init=True)
        # self.setPageSize(DEFAULT_PAGE_SIZE, init=True)
        self.setAscending(True)
        self.folderSize = 0   # FIXME: using parent.folderSize for debugging; will need to change that (if folder grows)

        super().__init__()
        
        self.setFolder(data)
        self.setFileList(self._get_fileList())   # this return the truncated list of file in the pager 

    # ------------ methods required by Qt's view

    def rowCount(self, parent=None):
        # Want it to return the number of rows to be shown at a given time
        value = len(self.fileList())
        return value

    def columnCount(self, parent=None):
        # Want it to return the number of columns to be shown at a given time
        value = len(self.columnLabels)
        return value

    def data(self, index, role=None):
        # display data
        if role == QtCore.Qt.DisplayRole:
            # print("Display role:", index.row(), index.column())
            file = self.fileList()[index.row()]
            print(f"{file=}")
            label = self.columnLabels[index.column()]
            action = self.actions_library[label]
            return action(file)

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self.columnLabels[section]
            else:
                return str(section + 1)  # may want to alter at some point
            
    # ------------ methods required by the results table

    # def doPager(self, action, value=None):
    #     # print(f"doPager {action =}, {value =}")

    #     folder_size = self.folderSize()
    #     offset = self.pageOffset()
    #     size = self.pageSize()
    #     # print(f"{folder_size=} {offset=}  {size=}")

    #     if action == "first":
    #         self.setPageOffset(0)
    #     elif action == "pageSize":
    #         self.setPageSize(value)
    #     elif action == "back":
    #         value = offset - size
    #         value = min(value, folder_size)
    #         value = max(value, 0)
    #         self.setPageOffset(value)
    #     elif action == "next":
    #         value = offset + size
    #         value = min(value, folder_size - size)
    #         value = max(value, 0)
    #         self.setPageOffset(value)
    #     elif action == "last":
    #         value = folder_size - size
    #         value = max(value, 0)
    #         self.setPageOffset(value)

    #     self.setFileList(self._get_fileList())
    #     # print(f"{self.pageOffset()=} {self.pageSize()=}")

    # def isPagerAtStart(self):
    #     return self.pageOffset() == 0

    # def isPagerAtEnd(self):
    #     # number is zero-based
    #     last_row_number = self.pageOffset() + len(self.fileList())
    #     return last_row_number >= self.folderSize()

    # ------------ local methods

    def _get_fileList(self):
        folder = self.folder()
        # start = self.pageOffset()
        # end = start + self.pageSize()
        # gen = folder[start-1: end]
        # ascending = 1 if self.ascending() else -1
        # if ascending < 0:
        #     gen.reverse()
        # return list(gen) 
        ascending = 1 if self.ascending() else -1
        if ascending < 0:
            folder.reverse()
        return folder

    # # ------------ get & set methods
    
    
    def folderPath(self):
        return self.parent.folderPath()    
    
    def folder(self):   # in this case folder is the list of mda file name
        return self._data

    def folderSize(self):
        return self._folderSize    

    # def folderSize(self):
    #     return self.parent.folderSize 

    def setFolder(self,folder):
        self._data = folder
        self._folderSize=len(folder)
        print(f"{folder=}")
        print(f"{len(folder)=}")
    
    def fileList(self):  # truncated file list
        return self._fileList

    def setFileList(self, value):
        self._fileList = value

    # def pageOffset(self):
    #     return self._pageOffset

    # def pageSize(self):
    #     return self._pageSize

    # def setPageOffset(self, offset, init=False):
    #     """Set the pager offset."""
    #     offset = int(offset)
    #     if init:
    #         self._pageOffset = offset
    #     elif offset != self._pageOffset:
    #         self._pageOffset = offset
    #         self.layoutChanged.emit()

    # def setPageSize(self, value, init=False):
    #     """Set the pager size."""
    #     value = int(value)
    #     if init:
    #         self._pageSize = value
    #     elif value != self._pageSize:
    #         self._pageSize = value
    #         self.layoutChanged.emit()

    def ascending(self):
        return self._ascending

    def setAscending(self, value):
        self._ascending = value

    # def pagerStatus(self):
    #     total = self.folderSize()
    #     if total == 0:
    #         text = "No files"
    #     else:
    #         start = self.pageOffset()
    #         end = start + len(self.fileList())
    #         text = f"{start + 1}-{end} of {total} files"
    #     return text

