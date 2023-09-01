from pathlib import Path
from functools import partial
from PyQt5 import QtCore
from PyQt5 import QtWidgets

from . import APP_TITLE
from . import utils
from .app_settings import settings

UI_FILE = utils.getUiFileName(__file__)
DATA_FOLDER = Path(__file__).parent / "data"
DATA_FOLDER_UNVALID = Path(__file__).parent / "fake_folder"

class MainWindow(QtWidgets.QMainWindow):
    """The main window of the app, built in Qt designer."""

    def __init__(self):
        super().__init__()
        utils.myLoadUi(UI_FILE, baseinstance=self)
        self.setup()

    def setup(self):
        self._folderPath = None     # the full path obj
        self._folderName = None     # the full path str
        self._folderRoot = None     # the toor path obj
        self._folderList = None     # the list of folder in the pull down
        self._folderLength = None   # the number of mda files in the folder
        self._mdaFileList = None    # the list of mda file NAME str (name only)
        self._mdaFilePath = None    # the list of mda file PATH obj (full path)
        self.mvc_folder = None
    
        self.setWindowTitle(APP_TITLE)
        self.setRecent(None)
        self.actionOpen.triggered.connect(self.doOpen)
        self.actionAbout.triggered.connect(self.doAboutDialog)
        self.actionExit.triggered.connect(self.doClose)

        self.folder.currentTextChanged.connect(self.setFolderPath)
        self.subfolder.currentTextChanged.connect(self.setSubFolderPath)
        
        settings.restoreWindowGeometry(self, "mainwindow_geometry")

    @property
    def status(self):
        return self.statusbar.currentMessage()

    def setStatus(self, text, timeout=0):
        """Write new status to the main window."""
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
        self.clearContent()
        # can insert item in ComboBox with .insertItem(0,'something')
        # from .tiledserverdialog import TiledServerDialog

        # server_uri = TiledServerDialog.getServer(self)
        # if not server_uri:
        #     self.clearContent()
        # uri_list = self.serverList()
        # if uri_list[0] == "":
        #     uri_list[0] = server_uri
        # else:
        #     uri_list.insert(0, server_uri)
        # self.setServers(uri_list)

    def folderName(self):
        """Full path (str) of the selected folder."""
        return self._folderName
    
    def folderPath(self):
        """Full path (obj) of the selected folder."""
        return self._folderPath
    
    def folderRoot(self):
        """Root path (obj) of the selected folder."""
        return self._folderRoot
    
    def folderLength(self):
        """Number of mda files in the selected folder."""
        return self._folderLength
    
    def folderList(self):
        """Folder path (str) list in the pull down menu."""
        return self._folderList
    
    def mdaFileList(self):
        """List of mda file (name only) in the selected folder."""
        return self._mdaFileList
    
    def mdaFilePath(self):
        """List of mda path (obj) in the selected folder."""
        return self._mdaFileList    
    
    def setmdaFileList(self,folder_path):
        self._mdaFileList = sorted([file.name for file in folder_path.glob('*.mda')])
            
    def setSubfolderList(self, subfolder_list):
        """Set the subfolders path list in the pop-up list."""
        self.subfolder.clear()
        self.subfolder.addItems(subfolder_list)     

    def setFolderPath(self, folder_name = DATA_FOLDER):
        """A folder was selected (from the open dialog)."""

        folder_path = Path(folder_name)
        layout = self.groupbox.layout()    

        if folder_path.exists() and folder_path.is_dir():   # folder exists
            
            self._folderPath = folder_path
            self._folderName = folder_name
            self._folderRoot = folder_path.parent

            def get_all_subfolders(folder_path, parent_path=""):
                subfolder_list = []
                if parent_path:  # Don't add the root parent folder
                    subfolder_list.append(parent_path)
                for item in folder_path.iterdir():
                    if item.is_dir():
                        new_parent_path = f"{parent_path}/{item.name}" if parent_path else item.name
                        subfolder_list += get_all_subfolders(item, new_parent_path)

                return subfolder_list

            subfolder_list=get_all_subfolders(folder_path, folder_path.name)
            print(f"{folder_path=}")
            print(f"{subfolder_list=}")
            
            self.setSubfolderList(subfolder_list)
        else:
            comment=f"{folder_path} does not exist."
            self.folderNotValid(layout,comment)

            
    def setSubFolderPath(self,subfolder_name):
        folder_path=self.folderRoot() / Path(subfolder_name)
        layout = self.groupbox.layout()   
        
        mda_files_path = list(folder_path.glob("*.mda"))
        self._folderLength = len(mda_files_path)
        self.info.setText(f"{self._folderLength} mda files")
        
        if mda_files_path:                              # folder contains mda
            from .mda_folder import MDA_MVC 
            
            self._mdaFilePath = mda_files_path 
            self.setmdaFileList(folder_path)
            self.setStatus(f"Folder path: {str(folder_path)!r}")
            
            self.clearContent(clear_sub=False) 
            self.mvc_folder = MDA_MVC(self)
            layout.addWidget(self.mvc_folder)
            
        else:
            comment=f"No mda files found in {folder_path}."
            self.folderNotValid(layout,comment,clear_sub=False)

    def folderNotValid(self,layout,comment,clear_sub=True):
        """If folder not valid, display no MVC and indicates reason in app status."""
        self.clearContent(clear_sub)
        self.mvc_folder = None
        layout.addWidget(QtWidgets.QWidget())
        self.setStatus(comment)  

    def setFolderList(self,folder_list=None):
        """Set the list of recent folder and remove duplicate"""
        unique_paths = set()
        new_path_list = []
        if not folder_list: 
            candidate_paths = ["", str(DATA_FOLDER),str(DATA_FOLDER_UNVALID), "Other..."]
        else:
            candidate_paths = folder_list
        for p in candidate_paths:
            if p not in unique_paths:
                unique_paths.add(p)
                new_path_list.append(p)
        self._folderList = new_path_list            

    def setRecent(self,folder_list):
        """Set the server URIs in the pop-up list"""
        self.setFolderList(folder_list)
        folder_list = self.folderList()
        self.folder.clear()
        self.folder.addItems(folder_list)

    def connectFolder(self,folder_path):
        """Connect to the server URI and return URI and client"""
        self.clearContent()
        if folder_path == "Other...":
            self.doOpen()  
        else:
            if folder_path is None:
                self.setStatus("No folder selected.")
                return
            self.setFolderPath(folder_path) 

    def clearContent(self, clear_sub=True):
        layout = self.groupbox.layout()
        utils.removeAllLayoutWidgets(layout)
        if clear_sub:
            self.subfolder.clear()



