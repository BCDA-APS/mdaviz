from pathlib import Path
from PyQt5 import QtCore
from PyQt5 import QtWidgets

from . import APP_TITLE
from . import utils
from .app_settings import settings

UI_FILE = utils.getUiFileName(__file__)
DATA_FOLDER = Path(__file__).parent / "data"
MDA_SPEC_NAME = "mda folder"

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
        self._mdaFileName = None
        self._mdaFileList = None
        self.mvc_folder = None
    
        self.setWindowTitle(APP_TITLE)
        self.setRecent(None)
        self.actionOpen.triggered.connect(self.doOpen)
        self.actionAbout.triggered.connect(self.doAboutDialog)
        self.actionExit.triggered.connect(self.doClose)
        # TODO: set up open dialog for folder


        self.folder.currentTextChanged.connect(self.setFolderPath)
        self.files.currentTextChanged.connect(self.setFile)
        # TODO: populate the MVC with the content of first scan
        
        settings.restoreWindowGeometry(self, "mainwindow_geometry")

    @property
    def status(self):
        return self.statusbar.currentMessage()

    def setStatus(self, text, timeout=0):
        """Write new status to the main window."""
        self.statusbar.showMessage(str(text), msecs=timeout)
        # TODO: log the text

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

    # TODO: adapt doOpen to files and folders
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
        return self._folderName
    
    def folderPath(self):
        return self._folderPath
    
    def folderList(self):
        return self._folderList
    
    def mdaFileName(self):
        return self._mdaFileName
    
    # def mdaFilePath(self):
    #     return self._folderPath / self._mdaFileName
    
    def mdaFileList(self):
        return self._mdaFileList
    
    def setmdaFileList(self,folder_path):
        self._mdaFileList = sorted([file.name for file in folder_path.glob('*.mda')])
        # TODO: what if new file gets added to the directory, you want to append those to the list without the user having to reselect the file nor the entire MVC
        # TODO: check for new file automatically (every x seconds)
    
    def setFiles(self, files_list):
        """Set the file names in the pop-up list."""
        self.files.clear()
        self.files.addItems(files_list)   
        
    def setFile(self,mda_file):
        print(f"{mda_file=}")
        full_path_str=self.folderName()+'/'+mda_file
        self.setStatus(f"Selected file {full_path_str!r}.")      
        self._mdaFileName=mda_file
    
    def setFolderPath(self, folder_name = DATA_FOLDER):
        """A folder was selected (from the open dialog)."""
        # TODO: check for validity (does it has mda in there?)
        # if len(catalog_name) == 0 or catalog_name not in self.server():
        #     if len(catalog_name) > 0:
        #         self.setStatus(f"Catalog {catalog_name!r} is not supported now.")
        #     return
        
        folder_path = Path(folder_name)

        self._folderPath = folder_path
        self._folderName = folder_name
        

        if isinstance(folder_path,Path):   # FIXME not really useful at the moment since we convert the str to path just above
            from .mda_folder import MDA_MVC

            # TODO: check if the folder has mda files in it 
            spec_name = MDA_SPEC_NAME
            self.spec_name.setText(spec_name)
            self.setStatus(f"Folder path: {folder_name!r}")
            
            self.setmdaFileList(folder_path)
            mda_list = self.mdaFileList()
            self.setFiles(mda_list)

            layout = self.groupbox.layout()
            self.clearContent(clear_cat=False)
                
            self.mvc_folder = MDA_MVC(self)
            layout.addWidget(self.mvc_folder)

        else:
            self.mvc_folder = None
            layout.addWidget(QtWidgets.QWidget())  # nothing to show

  

    def setFolderList(self,folder_list=None):
        """Set the list of recent folder and remove duplicate"""
        unique_paths = set()
        new_path_list = []
        # TODO: save last folder in settings
        if not folder_list: 
            # TODO: create KEY for recent folder
            #previous_path = settings.getKey(TILED_SERVER_SETTINGS_KEY)
            #candidate_paths = ["", str(DATA_FOLDER), previous_path, "Other..."]
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
            # TODO: check that folder exist
            # TODO: same folder path to settings 
            # if url.isValid() and not url.isRelative():
            #     settings.setKey(TILED_SERVER_SETTINGS_KEY, server_uri)
            # else:
            #     return
            # previous_uri = settings.getKey(TILED_SERVER_SETTINGS_KEY) or ""
            if folder_path is None:
                self.setStatus("No folder selected.")
                return
            self.setFolderPath(folder_path) 

    def clearContent(self, clear_cat=True):
        layout = self.groupbox.layout()
        utils.removeAllLayoutWidgets(layout)
        if clear_cat:
            self.files.clear()



