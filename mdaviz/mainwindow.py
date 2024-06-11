"""
Defines MainWindow class.

.. autosummary::

    ~MainWindow
"""

from pathlib import Path
from PyQt5 import QtWidgets

from . import APP_TITLE
from .mda_folder import MDA_MVC
from . import utils
from .user_settings import settings
from .opendialog import DIR_SETTINGS_KEY

UI_FILE = utils.getUiFileName(__file__)
MAX_FILES = 100
MAX_RECENT_DIRS = 10


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
        ~folderList
        ~mdaFileList
        ~mdaFileCount
        ~setMdaFileList
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
        self.setDataPath()  # the combined data path obj
        self.setFolderList()  # the list of recent folders in folder QCombobox
        self.setMdaFileList()  # the list of mda file NAME str (name only)
        self.setMdaInfoList()  # the list of mda file Info (all the data necessary to fill the table view)

        self.connect()
        self.setDataPath(self.directory)

        settings.restoreWindowGeometry(self, "mainwindow_geometry")
        print("Settings are saved in:", settings.fileName())

    def connect(self):
        self.actionOpen.triggered.connect(self.doOpen)
        self.actionAbout.triggered.connect(self.doAboutDialog)
        self.actionExit.triggered.connect(self.doClose)
        utils.reconnect(self.open.released, self.doOpen)
        self.folder.currentTextChanged.connect(self.onFolderSelected)

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
            dataPath = folderPath
        """
        return self._dataPath

    # def folderPath(self):
    #     """Full path (obj) of the selected folder."""
    #     return self._folderPath

    # def folderList(self):
    #     """Folder path (str) list in the pull down menu."""
    #     return self._folderList

    def mdaFileList(self):
        """List of mda file (name only) in the selected folder."""
        return self._mdaFileList

    def mdaInfoList(self):
        return self._mdaInfoList

    def setMdaInfoList(self, infoList=None):
        self._mdaInfoList = infoList if infoList else []

    def setDataPath(self, path=None):
        self._dataPath = path

    def setMdaFileList(self, mda_file_list=None):
        self._mdaFileList = mda_file_list if mda_file_list else []

    # def setFolderPath(self, folder_path=None):
    #     self._folderPath = folder_path

    def onFolderSelected(self, folder_name):
        """A folder was selected (from the open dialog or pull down menu)."""
        if folder_name == "Other...":
            self.doOpen()
        else:
            folder_path = Path(folder_name)
            if folder_path.exists() and folder_path.is_dir():  # folder exists
                # self.setFolderPath(folder_path)
                self.setDataPath(folder_path)
                mda_list = [utils.get_file_info(f) for f in folder_path.glob("*.mda")]
                if mda_list:
                    mda_list = sorted(mda_list, key=lambda x: x["Name"])
                    mda_name_list = [entry["Name"] for entry in mda_list]
                    self.info.setText(f"{len(mda_list)} mda files")
                    self.setMdaInfoList(mda_list)
                    self.setMdaFileList(mda_name_list)
                    self._updateRecentFolders(str(folder_path))
                    layout = self.groupbox.layout()
                    if self.mvc_folder is None:
                        self.mvc_folder = MDA_MVC(self)
                        layout.addWidget(self.mvc_folder)
                    else:
                        # Always update the folder view since it is a new folder
                        self.mvc_folder.updateFolderView()
                else:
                    self.reset_mainwindow()
                    self.setStatus("No MDA files found in the selected folder.")
            else:
                self.reset_mainwindow()
                self.setStatus(f"\n{str(folder_path)!r} - invalid path.")

    def reset_mainwindow(self):
        # self.setFolderPath()
        self.setDataPath()
        self.setMdaInfoList()
        self.setMdaFileList()
        if self.mvc_folder is not None:
            # If MVC exists, clear table view:
            self.mvc_folder.mda_folder_tableview.clearContents()

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
