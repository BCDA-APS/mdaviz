"""
Defines MainWindow class.

.. autosummary::

    ~MainWindow
"""

from pathlib import Path
from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon

from . import APP_TITLE
from .mda_folder import MDA_MVC
from . import utils
from .user_settings import settings
from .opendialog import DIR_SETTINGS_KEY

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
        self.directory = directory
        utils.myLoadUi(UI_FILE, baseinstance=self)
        self.setup()

    def setup(self):
        self.initialize()
        self.connect()
        self.setFolderPath(self.directory)
        settings.restoreWindowGeometry(self, "mainwindow_geometry")
        print("Settings are saved in:", settings.fileName())

    def initialize(self):
        self.setWindowTitle(APP_TITLE)
        self.mvc_folder = None
        self.setDataPath()  # the combined data path obj (folder.parent + subfolder)
        self.setFolderList()  # the list of folder in pull down 1 (folder QCombobox)
        self.setSubFolderList()  # the list of subfolder in pull down 2 (subfolder QCombobox)
        self.setMdaFileList()  # the list of mda file NAME str (name only)

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

                def get_all_subfolders(
                    folder_path,
                    parent_path="",
                    current_depth=0,
                    max_depth=MAX_DEPTH,
                    max_subfolders_per_depth=MAX_SUBFOLDERS_PER_DEPTH,
                    depth_counter=None,
                ):
                    if depth_counter is None:
                        depth_counter = {depth: 0 for depth in range(1, max_depth + 1)}

                    subfolder_list = []
                    if parent_path:  # Don't add the root parent folder
                        subfolder_list.append(parent_path)

                    if current_depth >= max_depth:
                        print(f"{current_depth=}")
                        return subfolder_list

                    try:
                        for item in folder_path.iterdir():
                            # Check if we have collected enough subfolders for the current depth
                            if (
                                depth_counter[current_depth + 1]
                                >= max_subfolders_per_depth
                            ):
                                break

                            if item.is_dir() and not item.name.startswith("."):
                                full_path = (
                                    f"{parent_path}/{item.name}"
                                    if parent_path
                                    else item.name
                                )
                                subfolder_list.append(full_path)
                                # Addition of a subfolder that exists at one level deeper than the current level
                                depth_counter[current_depth + 1] += 1
                                # Recursively collect subfolders, passing the updated depth_counter
                                subfolder_list.extend(
                                    get_all_subfolders(
                                        item,
                                        full_path,
                                        current_depth + 1,
                                        max_depth,
                                        max_subfolders_per_depth,
                                        depth_counter,
                                    )
                                )
                    except PermissionError:
                        print(f"Permission denied for folder: {folder_path}")
                    subfolder_list = list(dict.fromkeys(sorted(subfolder_list)))

                    return subfolder_list

                self.setSubFolderList(get_all_subfolders(folder_path, folder_path.name))
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
