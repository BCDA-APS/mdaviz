from PyQt5.QtWidgets import QFileDialog

from pathlib import Path
from .user_settings import settings

DIR_SETTINGS_KEY = "directory"


class OpenDialog(QFileDialog):
    """Open a file dialog GUI window that shows folder contents including mda files."""

    def __init__(self, parent):
        self.parent = parent

        super().__init__(parent)
        self.setup()

    def setup(self):
        self.setModal(True)

        # Configure dialog to show files but only allow directory selection
        self.setFileMode(QFileDialog.Directory)
        self.setOption(QFileDialog.ShowDirsOnly, False)
        self.setOption(QFileDialog.DontUseNativeDialog, False)

        # Set up file filters to show mda files prominently
        self.setNameFilter("MDA files (*.mda);;All files (*)")

        # Set up options to show file details and counts
        self.setViewMode(QFileDialog.Detail)

        # Set recent directory
        recent_dirs_str = settings.getKey(DIR_SETTINGS_KEY)
        recent_dirs = recent_dirs_str.split(",") if recent_dirs_str else []
        default_dir = recent_dirs[0] if recent_dirs else str(Path.home())
        self.setDirectory(default_dir)
