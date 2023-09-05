"""
QAbstractTableModel of folder content.

.. autosummary::

    ~MDAFolderTableModel
"""

from PyQt5 import QtCore
from . import utils

DEFAULT_PAGE_SIZE = 20
DEFAULT_PAGE_OFFSET = 0


class MDAFolderTableModel(QtCore.QAbstractTableModel):
    def __init__(self, data, parent):
        self.parent = parent

        self.actions_library = {
            "Prefix": lambda file: file.rsplit("_", 1)[0],
            "Scan #": lambda file: int(file.rsplit("_", 1)[1].split(".")[0]),
            "Points": lambda file: "TODO",  # TODO: get_file_pts
            "Dim": lambda file: "TODO",  # TODO: get_file_dim
            "Size": lambda file: self.get_file_size(file),
            "Date": lambda file: self.get_file_date(file),
        }

        self.columnLabels = list(self.actions_library.keys())

        # self.setPageOffset(DEFAULT_PAGE_OFFSET, init=True)
        # self.setPageSize(DEFAULT_PAGE_SIZE, init=True)
        self.setAscending(True)
        self.folderLength = 0

        super().__init__()

        self.setFolder(data)
        self.setFileList(
            self._get_fileList()
        )  # this return the truncated list of file in the pager

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
            label = self.columnLabels[index.column()]
            action = self.actions_library[label]
            return action(file)

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self.columnLabels[section]
            else:
                return str(section + 1)  # may want to alter at some point

    # ------------ local methods

    def _get_fileList(self):
        folder = self.folder()
        ascending = 1 if self.ascending() else -1
        if ascending < 0:
            folder.reverse()
        return folder

    def get_file_path(self, file):
        return self.dataPath() / file

    def get_file_size(self, file):
        filepath = self.get_file_path(file)
        return utils.human_readable_size(filepath.stat().st_size)

    def get_file_date(self, file):
        filepath = self.get_file_path(file)
        return utils.ts2iso(round(filepath.stat().st_ctime))

    # # ------------ get & set methods

    def folder(self):  # in this case folder is the list of mda file name
        return self._data

    def folderLength(self):
        return self._folderLength

    def setFolder(self, folder):
        self._data = folder
        self._folderLength = len(folder)

    def fileList(self):  # truncated file list
        return self._fileList

    def setFileList(self, value):
        self._fileList = value

    def dataPath(self):
        """Path (obj) of the selected data folder (folder + subfolder)."""
        return self.parent.dataPath()

    def ascending(self):
        return self._ascending

    def setAscending(self, value):
        self._ascending = value
