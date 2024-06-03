"""
QAbstractTableModel of folder content.

.. autosummary::

    ~MDAFolderTableModel
"""

from .synApps_mdalib.mda import readMDA
import re
from PyQt5 import QtCore
from . import utils

HEADERS = "Prefix", "Scan #", "Points", "Dim", "Positioner", "Date", "Size"


class MDAFolderTableModel(QtCore.QAbstractTableModel):

    def __init__(self, data, parent):
        """
        Create the model and connect with its parent.

        PARAMETERS

        parent object:
            Instance of mdaviz.mda_folder.MDAMVC
        """

        self.mda_mvc = parent
        super().__init__()

        self.columnLabels = HEADERS
        self.setFileList(data)

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
            file = self.fileList()[index.row()]
            label = self.columnLabels[index.column()]
            file_info = self.get_file_info(file)
            value = file_info[label]
            return value

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self.columnLabels[section]
            else:
                return str(section + 1)  # may want to alter at some point

    # ------------ local methods

    def get_file_info(self, file):

        def extract_prefix(filename, scan_number):
            """Create a pattern that matches the prefix followed by an optional separator and the scan number with possible leading zeros
            The separators considered here are underscore (_), hyphen (-), dot (.), and space ( )
            """
            scan_number = str(scan_number)
            pattern = rf"^(.*?)[_\-\. ]?0*{scan_number}\.mda$"
            match = re.match(pattern, filename)
            if match:
                return match.group(1)
            return None

        file_path = self.mda_mvc.dataPath() / file
        file_data = readMDA(str(file_path))[1]
        file_metadata = readMDA(str(file_path))[0]
        file_num = file_metadata.get("scan_number", None)
        file_prefix = extract_prefix(file, file_num)
        file_size = utils.human_readable_size(file_path.stat().st_size)
        file_date = utils.byte2str(file_data.time).split(".")[0]
        file_pts = file_data.curr_pt
        file_dim = file_data.dim
        pv = utils.byte2str(file_data.p[0].name) if len(file_data.p) else "index"
        desc = utils.byte2str(file_data.p[0].desc) if len(file_data.p) else "index"
        file_pos = desc if desc else pv

        fileInfo = {}
        # HEADERS = "Prefix", "Scan #", "Points", "Dim", "Positioner", "Date", "Size"
        values = [
            file_prefix,
            file_num,
            file_pts,
            file_dim,
            file_pos,
            file_date,
            file_size,
        ]
        for k, v in zip(HEADERS, values):
            fileInfo[k] = v
        return fileInfo

    # # ------------ get & set methods

    def fileList(self):
        """Here fileList = data arg = self.mainWindow.mdaFileList()
        ie the list of mda file NAME str (name only)
        """
        return self._data

    def setFileList(self, data):
        """Here data arg = self.mainWindow.mdaFileList()
        ie the list of mda file NAME str (name only)
        """
        self._data = data
