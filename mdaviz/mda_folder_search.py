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

        super().__init__()
        utils.myLoadUi(self.ui_file, baseinstance=self)

    def folderPath(self):
        return self.parent.folderPath()

    def folderName(self):
        return self.parent.folderName()    
    
    # def mdaFilePath(self):
    #     return self.parent.mdaFilePath()  

    def mdaFileName(self):
        return self.parent.mdaFileName()  
    
    def mdaFileList(self):
        return self.parent.mdaFileList()       
        
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
            
   
    def doNext(self):
        self.doButton(1)
        print('do next')        
        
    def doPrevious(self):
        self.doButton(-1)
        print('do previous')
        
    def doButton(self,i):            
        current_mdaFile=self.mdaFileName()
        current_mdaIndex = self.mdaFileList().index(current_mdaFile)
        next_mdaIndex = current_mdaIndex+i
        next_mdaFile=self.mdaFileList()[next_mdaIndex]
        self.parent.parent.files.setCurrentIndex(next_mdaIndex)
        print(f"{current_mdaFile=}")        
        print(f"{next_mdaFile=}")
    
    

        
        
    def setStatus(self, text):
        self.parent.setStatus(text)


        





