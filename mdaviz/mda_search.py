"""
Search for mda files.

"""

from PyQt5 import QtWidgets
from pathlib import Path
from . import utils


class mdaSearchPanel(QtWidgets.QWidget):
    """The panel to select mda files."""

    # UI file name matches this module, different extension
    ui_file = utils.getUiFileName(__file__)

    def __init__(self, parent):
        self.parent = parent
        self._server = None

        super().__init__()
        utils.myLoadUi(self.ui_file, baseinstance=self)

    def folderPath(self):
        return self.parent.folderPath()

    def folderName(self):
        return self.parent.folderName()    
    
    def mdaFilePath(self):
        return self.parent.mdaFilePath()  

    def mdaFileName(self):
        return self.parent.mdaFileName()  
    
    # TODO: already exist in mainwindow?
    def mdaFiles(self,folder_path, as_string=False):
        if as_string:
            return sorted([file.name for file in folder_path.glob('*.mda')])
        else:
            return [file for file in folder_path.glob('*.mda')]
        
        
    # TODO: self.mda_folder.mda_search_panel.setupFile(self,mda_file)    
    def setupFile(self,filename):
        if not filename:
            pass
        else:
            # filename=self.mdaFile()? do I use the attribute or the arg?
            filepath= self.folderPath() / filename
            scan_prefix, scan_number_with_ext = filename.rsplit('_', 1)
            scan_number = scan_number_with_ext.split('.')[0]
            scan_size = utils.human_readable_size(filepath.stat().st_size)
            scan_date = utils.ts2iso(round(filepath.stat().st_ctime))
            self.file_name.setText(scan_prefix)
            self.file_num.setText(scan_number)
            self.file_size.setText(scan_size)
            self.file_date.setText(scan_date)
            # print(f"{scan_prefix=}")
            # print(f"{scan_number=}")
            # print(f"{scan_size=}")
            # print(f"{scan_date=}")
        
    
    def setStatus(self, text):
        self.parent.setStatus(text)


        





