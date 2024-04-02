from pathlib import Path
from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon

from . import APP_TITLE
from .mda_folder import MDA_MVC
from . import utils
from .user_settings import settings
from .opendialog import DIR_SETTINGS_KEY

UI_FILE = utils.getUiFileName(__file__)
MAX_RECENT_DIRS = 5
DATA_FOLDER_INVALID = Path(__file__).parent / "fake_folder"
MAX_DEPTH = 4
MAX_SUBFOLDERS_PER_DEPTH = 10


class MainWindow(QtWidgets.QMainWindow):
    """The main window of the app, built in Qt designer."""

    def __init__(self):
        super().__init__()
        utils.myLoadUi(UI_FILE, baseinstance=self)
        icon_path = Path(__file__).parent / "resources" / "viz.jpg"
        self.setWindowIcon(QIcon(str(icon_path)))
        self.setup()

    def setup(self):
        self._dataPath = None  # the combined data path obj (folder.parent + subfolder)
        self._folderPath = None  # the path obj from pull down 1
        self._folderList = []  # the list of folder in pull down 1
        self._subFolderPath = None  # the subfolder path obj selected in pull down 2
        self._subFolderList = []  # the list of subfolder in pull down 2
        self._mdaFileList = []  # the list of mda file NAME str (name only)
        self._mdaFileCount = 0  # the number of mda files in the list
        self.mvc_folder = None

        self.setWindowTitle(APP_TITLE)
        self.setRecent(None)
        self.actionOpen.triggered.connect(self.doOpen)
        self.actionAbout.triggered.connect(self.doAboutDialog)
        self.actionExit.triggered.connect(self.doClose)
        try:
            self.open.released.disconnect()
        except TypeError:  # No slots connected yet
            pass
        self.open.released.connect(self.doOpen)

        self.folder.currentTextChanged.connect(self.setFolderPath)
        self.subfolder.currentTextChanged.connect(self.setSubFolderPath)

        settings.restoreWindowGeometry(self, "mainwindow_geometry")
        print("Settings are saved in:", settings.fileName())

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
            if folder_list[0] == "":
                folder_list[0] = dir_name
            else:
                folder_list.insert(0, dir_name)
            self.setRecent(folder_list)

    def dataPath(self):
        """
        Full path object for the displayed data:
            dataPath = folderPath.parent + subFolderPath
        """
        return self._dataPath

    def subFolderPath(self):
        """Subfolder name (str) of the selected subfolder."""
        return self._subFolderPath

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

    def mdaFileCount(self):
        """Number of mda files in the selected folder."""
        return self._mdaFileCount

    def setMdaFileList(self, data_path):
        if data_path:
            self._mdaFileList = sorted([file.name for file in data_path.glob("*.mda")])
        else:
            self._mdaFileList = []

    def setSubFolderName(self):
        self._subFolderPath = Path(self.subfolder.currentText())

    def setSubfolderList(self, subfolder_list):
        """Set the subfolders path list in the pop-up list."""
        self._subFolderList = subfolder_list
        self.subfolder.clear()
        self.subfolder.addItems(subfolder_list)

    def setFolderPath(self, folder_name):
        """A folder was selected (from the open dialog)."""

        if folder_name == "Other...":
            self.doOpen()

        else:
            folder_path = Path(folder_name)
            layout = self.groupbox.layout()

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

                    return subfolder_list

                self.setSubfolderList(get_all_subfolders(folder_path, folder_path.name))

                # Update the list of recent directories in settings
                recent_dirs_str = settings.getKey(DIR_SETTINGS_KEY)
                recent_dirs = recent_dirs_str.split(",") if recent_dirs_str else []
                if folder_name in recent_dirs:
                    recent_dirs.remove(folder_name)
                recent_dirs.insert(0, str(folder_path))
                recent_dirs = recent_dirs[:MAX_RECENT_DIRS]
                recent_dirs = [dir for dir in recent_dirs if dir != "."]
                settings.setKey(DIR_SETTINGS_KEY, ",".join(recent_dirs))

            else:
                comment = f"\n{str(folder_path)!r} - invalid path."
                self._folderPath = None
                self._dataPath = None
                self._mdaFileList = []
                self._mdaFileCount = 0
                self.setSubfolderList([])
                self.setStatus(comment)
                if self.mvc_folder is not None:
                    # If MVC exists, display empty table views
                    self.mvc_folder.updateFolderView()
                    self.mvc_folder.mda_file.removeAllFileTabs()

    def setSubFolderPath(self, subfolder_name):
        if subfolder_name:
            data_path = self.folderPath().parent / Path(subfolder_name)
            self._dataPath = data_path
            layout = self.groupbox.layout()
            mda_files_path = list(data_path.glob("*.mda"))
            self._mdaFileCount = len(mda_files_path)
            self.setMdaFileList(data_path)
            self.info.setText(f"{self._mdaFileCount} mda files")
            if self.mvc_folder is None:
                self.mvc_folder = MDA_MVC(self)
                layout.addWidget(self.mvc_folder)
            else:
                # Always update the folder view since it is a new subfolder
                self.mvc_folder.updateFolderView()
            if mda_files_path == []:
                # If there are no MDA files, pass None to display empty table
                self.mvc_folder.updateFieldsView(None)
                self.setStatus("No MDA files found in the selected folder.")

    def setFolderList(self, folder_list=None):
        """Set the list of recent folder and remove duplicate"""
        unique_paths = set()
        new_path_list = []
        candidate_paths = ["", str(DATA_FOLDER_INVALID), "Other..."]
        if not folder_list:
            recent_dirs_str = settings.getKey(DIR_SETTINGS_KEY)
            recent_dirs = recent_dirs_str.split(",") if recent_dirs_str else []
            if recent_dirs:
                candidate_paths[1:1] = recent_dirs
        else:
            candidate_paths = folder_list
        for p in candidate_paths:
            if p not in unique_paths:
                unique_paths.add(p)
                new_path_list.append(p)
        self._folderList = new_path_list

    def setRecent(self, folder_list):
        """Sets the recent folder list, updating the internal folder list & populate the QComboBox"""
        self.setFolderList(folder_list)
        folder_list = self.folderList()
        self.folder.clear()
        self.folder.addItems(folder_list)

    ### Not in use at the moment, save for later?
    # Was working but I decided to keep empty table views (header only)
    # instead of removing the widgets completely.
    #
    # def clearContent(
    #     self,
    #     clear_sub=True,
    #     clear_folder_view=True,
    #     clear_field_view=True,
    #     clear_visualization=True,
    #     clear_all_layout=False,
    # ):
    #     if self.mvc_folder is not None:
    #         # Clear widgets from the folder view group box
    #         if clear_folder_view:
    #             layout_folder = self.mvc_folder.folder_groupbox.layout()
    #             for i in reversed(range(layout_folder.count())):
    #                 item = layout_folder.itemAt(i)
    #                 widget = item.widget() if item is not None else None
    #                 if widget is not None:
    #                     layout_folder.removeWidget(widget)
    #                     widget.deleteLater()

    #         # Clear widgets from the field view group box
    #         if clear_field_view:
    #             layout_field = self.mvc_folder.mda_groupbox.layout()
    #             for i in reversed(range(layout_field.count())):
    #                 item = layout_field.itemAt(i)
    #                 widget = item.widget() if item is not None else None
    #                 if widget is not None:
    #                     layout_field.removeWidget(widget)
    #                     widget.deleteLater()

    #         # Clear widgets from the visualization group box
    #         if clear_visualization:
    #             layout_viz = self.mvc_folder.viz_groupbox.layout()
    #             for i in reversed(range(layout_viz.count())):
    #                 item = layout_viz.itemAt(i)
    #                 widget = item.widget() if item is not None else None
    #                 if widget is not None:
    #                     layout_viz.removeWidget(widget)
    #                     widget.deleteLater()

    #     if clear_sub:
    #         self.subfolder.clear()

    #     if clear_all_layout:
    #         layout = self.groupbox.layout()
    #         utils.removeAllLayoutWidgets(layout)
