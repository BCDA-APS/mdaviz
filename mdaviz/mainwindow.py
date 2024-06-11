"""
Defines MainWindow class.

.. autosummary::

    ~MainWindow
"""

from pathlib import Path
from PyQt5 import QtWidgets
import re
from .synApps_mdalib.mda import readMDA

from . import APP_TITLE
from .mda_folder import MDA_MVC
from . import utils
from .user_settings import settings
from .opendialog import DIR_SETTINGS_KEY

HEADERS = "Prefix", "Scan #", "Points", "Dim", "Positioner", "Date", "Size"
UI_FILE = utils.getUiFileName(__file__)
MAX_RECENT_DIRS = 10
MAX_DEPTH = 4
MAX_SUBFOLDERS_PER_DEPTH = 10


class MainWindow(QtWidgets.QMainWindow):
    """The main window of the app, built in Qt designer.

    .. autosummary::

        ~setup
        ~status
        ~setStatus
        ~doAboutDialog
        ~closeEvent
        ~doClose
        ~doOpen
        ~dataPath
        ~folderPath
        ~folderList
        ~subFolderList
        ~mdaFileList
        ~mdaFileCount
        ~setMdaFileList
        ~setSubFolderList
        ~setFolderPath
        ~setSubFolderPath
        ~setFolderList
        ~_buildFolderList
        ~_updateRecentFolders
    """

    def __init__(self, directory):
        super().__init__()
        utils.myLoadUi(UI_FILE, baseinstance=self)
        self.setWindowTitle(APP_TITLE)

        self.directory = directory
        self.mvc_folder = None
        self.setDataPath()  # the combined data path obj (folder.parent + subfolder)
        self.setFolderList()  # the list of recent folders in pull down 1 (folder QCombobox)
        self.setSubFolderList()  # the list of subfolder in pull down 2 (subfolder QCombobox)
        self.setMdaFileList()  # the list of mda file NAME str (name only)
        self.setMdaInfoList()

        self.connect()
        self.setFolderPath(self.directory)

        settings.restoreWindowGeometry(self, "mainwindow_geometry")
        print("Settings are saved in:", settings.fileName())

    def connect(self):
        self.actionOpen.triggered.connect(self.doOpen)
        self.actionAbout.triggered.connect(self.doAboutDialog)
        self.actionExit.triggered.connect(self.doClose)
        utils.reconnect(self.open.released, self.doOpen)
        self.folder.currentTextChanged.connect(self.setFolderPath)
        self.subfolder.currentTextChanged.connect(self.setSubFolderPath)

    @property
    def status(self):
        return self.statusbar.currentMessage()

    def setStatus(self, text, timeout=0):
        """Write new status to the main window and terminal output."""
        print(text)
        self.statusbar.showMessage(str(text), msecs=timeout)

    def doAboutDialog(self, *args, **kw):
        """
        Show the "About ..." dialog
        """
        from .aboutdialog import AboutDialog

        about = AboutDialog(self)
        about.open()

    def closeEvent(self, event):
        """
        User clicked the big [X] to quit.
        """
        self.doClose()
        event.accept()  # let the window close

    def doClose(self, *args, **kw):
        """
        User chose exit (or quit), or closeEvent() was called.
        """
        self.setStatus("Application quitting ...")
        settings.saveWindowGeometry(self, "mainwindow_geometry")
        self.close()

    def doOpen(self, *args, **kw):
        """
        User chose to open (connect with) a tiled server.
        """
        from .opendialog import OpenDialog

        self.setStatus("Please select a folder...")
        open_dialog = OpenDialog(self)
        dir_name = open_dialog.getExistingDirectory(self, "Select a Directory")
        if dir_name:
            folder_list = self.folderList()
            folder_list.insert(0, dir_name)
            self.setFolderList(folder_list)

    def dataPath(self):
        """
        Full path object for the displayed data:
            dataPath = folderPath.parent + subFolderPath
        """
        return self._dataPath

    def folderPath(self):
        """Full path (obj) of the selected folder."""
        return self._folderPath

    def folderList(self):
        """Folder path (str) list in the pull down menu."""
        return self._folderList

    def subFolderList(self):
        """Subfolder path (str) list in the pull down menu."""
        return self._subFolderList

    def mdaFileList(self):
        """List of mda file (name only) in the selected folder."""
        return self._mdaFileList

    def mdaInfoList(self):
        return self._mdaInfoList

    def setMdaInfoList(self, infoList=None):
        self._mdaInfoList = infoList if infoList else []

    def setDataPath(self, path=None):
        self._dataPath = path

    def setMdaFileList(self, path=None):
        self._mdaFileList = (
            sorted([file.name for file in path.glob("*.mda")]) if path else []
        )

    def setFolderPath(self, folder_name):
        """A folder was selected (from the open dialog)."""
        if folder_name == "Other...":
            self.doOpen()
        else:
            folder_path = Path(folder_name)
            if folder_path.exists() and folder_path.is_dir():  # folder exists
                self._folderPath = folder_path
                mda_list = [self._get_file_info(f) for f in folder_path.glob("*.mda")]
                mda_list = sorted(mda_list, key=lambda x: x["Name"])
                self.setMdaInfoList(mda_list)
                self.setSubFolderList([str(folder_path)])
                self._updateRecentFolders(str(folder_path))
            else:
                self._folderPath = None
                self.setDataPath()
                self.setMdaFileList()
                self.setSubFolderList([])
                self.setStatus(f"\n{str(folder_path)!r} - invalid path.")
                if self.mvc_folder is not None:
                    # If MVC exists, clear table view:
                    self.mvc_folder.mda_folder_tableview.clearContents()

    def setSubFolderPath(self, subfolder_name):
        if subfolder_name:
            data_path = self.folderPath().parent / Path(subfolder_name)
            self.setDataPath(data_path)
            layout = self.groupbox.layout()
            mda_files_path = list(data_path.glob("*.mda"))
            # TODO I am building twice this list, here and in setMdaFileList? Only diff if here it is not sorted
            self.setMdaFileList(data_path)
            self.info.setText(f"{len(mda_files_path)} mda files")
            if self.mvc_folder is None:
                self.mvc_folder = MDA_MVC(self)
                layout.addWidget(self.mvc_folder)
            else:
                # Always update the folder view since it is a new subfolder
                # TODO:should I check if it is the same subfolder? so I don;t reload if not necessary?
                self.mvc_folder.updateFolderView()
            if mda_files_path == []:
                # If there are no MDA files, clear table view:
                self.mvc_folder.mda_folder_tableview.clearContents()
                self.setStatus("No MDA files found in the selected folder.")

    def setSubFolderList(self, subfolder_list=[]):
        """Set the subfolders path list and populate the subfolder QComboBox."""
        self.subfolder.clear()
        self.subfolder.addItems(subfolder_list)
        self._subFolderList = subfolder_list

    def setFolderList(self, folder_list=None):
        """Set the folder path list & populating the folder QComboBox.

        - If folder_list is not None, it will remove its duplicates.
        - If folder_list is None, the call to buildFolderList will take care of building the list
          based on the recent list of folder saved in the app settings.

        Args:
            folder_list (list, optional): the current list of recent folders. Defaults to None.
        """
        folder_list = self._buildFolderList(folder_list)
        self.folder.clear()
        self.folder.addItems(folder_list)
        self._folderList = folder_list

    def _buildFolderList(self, folder_list=None):
        """Build the list of recent folders and remove duplicates from the folder list.

        - If folder_list is not None (after a doOpen call), it just removes duplicates.
        - If folder_list is None, it grabs the list of recent folder from the app settings.
          The directory loaded at start-up and the "Other..." option will be added at index
          0 and -1, respectively.

        Args:
            folder_list (list, optional): a list folders. Defaults to None.

        Returns:
            list: list of folders to be populated in the QComboBox
        """
        unique_paths = set()
        candidate_paths = [self.directory, "Other..."]
        if not folder_list:
            recent_dirs = (
                settings.getKey(DIR_SETTINGS_KEY).split(",")
                if settings.getKey(DIR_SETTINGS_KEY)
                else []
            )
            if recent_dirs:
                candidate_paths[1:1] = recent_dirs
        else:
            candidate_paths = folder_list
        new_path_list = [
            p
            for p in candidate_paths
            if p not in unique_paths and (unique_paths.add(p) or True)
        ]
        return new_path_list

    def _updateRecentFolders(self, folder_path):
        """Add a new folder path to the list of recent folders in the app settings.

        Args:
            folder_path (str): The path of the folder to be added.
        """
        recent_dirs = (
            settings.getKey(DIR_SETTINGS_KEY).split(",")
            if settings.getKey(DIR_SETTINGS_KEY)
            else []
        )
        if folder_path in recent_dirs:
            recent_dirs.remove(folder_path)
        recent_dirs.insert(0, str(folder_path))
        recent_dirs = [dir for dir in recent_dirs if dir != "."]
        settings.setKey(DIR_SETTINGS_KEY, ",".join(recent_dirs[:MAX_RECENT_DIRS]))

    def _get_file_info(self, file_path):
        file_name = file_path.name
        file_data = readMDA(str(file_path))[1]
        file_metadata = readMDA(str(file_path))[0]
        file_num = file_metadata.get("scan_number", None)
        file_prefix = self._extract_prefix(file_name, file_num)
        file_size = utils.human_readable_size(file_path.stat().st_size)
        file_date = utils.byte2str(file_data.time).split(".")[0]
        file_pts = file_data.curr_pt
        file_dim = file_data.dim
        pv = utils.byte2str(file_data.p[0].name) if len(file_data.p) else "index"
        desc = utils.byte2str(file_data.p[0].desc) if len(file_data.p) else "index"
        file_pos = desc if desc else pv

        fileInfo = {"Name": file_name}
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

    def _extract_prefix(self, file_name, scan_number):
        """Create a pattern that matches the prefix followed by an optional separator and the scan number with possible leading zeros
        The separators considered here are underscore (_), hyphen (-), dot (.), and space ( )
        """
        scan_number = str(scan_number)
        pattern = rf"^(.*?)[_\-\. ]?0*{scan_number}\.mda$"
        match = re.match(pattern, file_name)
        if match:
            return match.group(1)
        return None
