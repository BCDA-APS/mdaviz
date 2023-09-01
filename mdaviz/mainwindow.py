from pathlib import Path
from PyQt5 import QtCore
from PyQt5 import QtWidgets

from . import APP_TITLE
from . import utils
from .app_settings import settings

UI_FILE = utils.getUiFileName(__file__)
DATA_FOLDER = Path(__file__).parent / "data"

class MainWindow(QtWidgets.QMainWindow):
    """The main window of the app, built in Qt designer."""

    def __init__(self):
        super().__init__()
        utils.myLoadUi(UI_FILE, baseinstance=self)
        self.setup()

    def setup(self):
        self._folderPath = None
        self._folderName = None
        self._folderList = None
        self._folderLength = None
        self._mdaFileList = None
        self.mvc_folder = None
    
        self.setWindowTitle(APP_TITLE)
        self.setRecent(None)
        self.actionOpen.triggered.connect(self.doOpen)
        self.actionAbout.triggered.connect(self.doAboutDialog)
        self.actionExit.triggered.connect(self.doClose)

        self.folder.currentTextChanged.connect(self.setFolderPath)
        
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
        pass
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
        """Path (str) of the selected folder."""
        return self._folderName
    
    def folderPath(self):
        """Path (obj) of the selected folder."""
        return self._folderPath
    
    def folderLength(self):
        """Number of mda files in the selected folder."""
        return self._folderLength
    
    def folderList(self):
        """Folder path (str) list in the pull down menu."""
        return self._folderList
    
    def mdaFileList(self):
        """List of mda file (name only) in the selected folder."""
        return self._mdaFileList
    
    
    def setmdaFileList(self,folder_path):
        self._mdaFileList = sorted([file.name for file in folder_path.glob('*.mda')])
        self._folderLength = len(self._mdaFileList)
        self.info.setText(f"{self._folderLength} mda files")
    
    def setFiles(self, files_list):
        """Set the file names in the pop-up list."""
        self.subfolder.clear()
        self.subfolder.addItems(files_list)     
    
    def setFolderPath(self, folder_name = DATA_FOLDER):
        """A folder was selected (from the open dialog)."""
        folder_path = Path(folder_name)
        self._folderPath = folder_path
        self._folderName = folder_name
        
        # FIXME the is bellow is not longer very relevant since we now convert the str to path 
        # just above; need to check for validity instead
        if isinstance(folder_path,Path):   
            from .mda_folder import MDA_MVC

            self.setStatus(f"Folder path: {folder_name!r}")
            
            self.setmdaFileList(folder_path)
            mda_list = self.mdaFileList()
            #self.setFiles(mda_list)

            layout = self.groupbox.layout()
            self.clearContent(clear_sub=False)
                
            self.mvc_folder = MDA_MVC(self)
            layout.addWidget(self.mvc_folder)

        else:
            self.mvc_folder = None
            layout.addWidget(QtWidgets.QWidget())  # nothing to show

  

    def setFolderList(self,folder_list=None):
        """Set the list of recent folder and remove duplicate"""
        unique_paths = set()
        new_path_list = []
        if not folder_list: 
            candidate_paths = ["", str(DATA_FOLDER), "Other..."]
        else:
            candidate_paths = folder_list
        for p in candidate_paths:
            if p not in unique_paths:  # Check for duplicates
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



