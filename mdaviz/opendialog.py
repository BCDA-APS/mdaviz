from PyQt5.QtWidgets import QFileDialog

import os
from . import utils
from .app_settings import settings

DIR_SETTINGS_KEY = "directory"

class OpenDialog(QFileDialog):
    """Open a file dialog GUI window."""

    # UI file name matches this module, different extension
    ui_file = utils.getUiFileName(__file__)

    def __init__(self, parent):
        self.parent = parent

        super().__init__(parent)
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()

    def setup(self):
        self.setModal(True)
        recent_dirs_str = settings.getKey(DIR_SETTINGS_KEY)
        recent_dirs = recent_dirs_str.split(',') if recent_dirs_str else []
        default_dir = recent_dirs[0] if recent_dirs else os.path.expanduser("~")
        self.setDirectory(default_dir)
        
        