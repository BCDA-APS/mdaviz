"""
MVC implementation of mda files.

* MVC: Model View Controller

.. autosummary::

    ~MDA_MVC
"""


import time
from functools import partial

from PyQt5 import QtWidgets

from . import utils

MYFILE = "mda_0001.mda"


class MDA_MVC(QtWidgets.QWidget):
    """MVC class for mda files."""

    ui_file = utils.getUiFileName(__file__)
    motion_wait_time = 1

    def __init__(self, parent):
        self.parent = parent

        super().__init__()
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()

    def setup(self):
        from .user_settings import settings
        from .mda_folder_table_view import MDAFolderTableView
        from .mda_file_table_view import MDAFileTableView
        from .mda_file_viz import MDAFileVisualization
        from .select_fields_table_view import SelectFieldsTableView

        self.mda_folder_tableview = MDAFolderTableView(self)
        layout = self.folder_groupbox.layout()
        layout.addWidget(self.mda_folder_tableview)
        self.mda_folder_tableview.displayTable()

        try:
            self.parent.refresh.released.disconnect()
        except TypeError:  # No slots connected yet
            pass
        self.parent.refresh.released.connect(self.doRefresh)

        self.select_fields_tableview = SelectFieldsTableView(self)
        layout = self.mda_groupbox.layout()
        layout.addWidget(self.select_fields_tableview)

        # self.mda_file_tableview = MDAFileTableView(self)
        # layout = self.mda_groupbox.layout()
        # layout.addWidget(self.mda_file_tableview)

        self.mda_file_visualization = MDAFileVisualization(self)
        layout = self.viz_groupbox.layout()
        layout.addWidget(self.mda_file_visualization)

        # self.mda_folder_tableview.tableView.doubleClicked.connect(self.doFileSelected)

        self.mda_folder_tableview.tableView.doubleClicked.connect(self.doFileSelected)

        # save/restore splitter sizes in application settings
        for key in "hsplitter vsplitter".split():
            splitter = getattr(self, key)
            sname = self.splitter_settings_name(key)
            settings.restoreSplitter(splitter, sname)
            splitter.splitterMoved.connect(partial(self.splitter_moved, key))

    def doFileSelected(self, index):
        model = self.mda_folder_tableview.tableView.model()
        if model is not None:
            # self.mda_file_tableview.displayMetadata(index.row())
            # self.mda_file_tableview.displayTable(index.row())
            self.select_fields_tableview.displayTable(index.row())
            self.setStatus(f"Selected file: {self.mdaFileList()[index.row()]}")

    def dataPath(self):
        """Path (obj) of the data folder (folder comboBox + subfolder comboBox)."""
        return self.parent.dataPath()

    def mdaFileCount(self):
        """Number of mda files in the selected folder."""
        return self.parent.mdaFileCount()

    def mdaFileList(self):
        """List of mda file (name only) in the selected folder."""
        return self.parent.mdaFileList()

    def doRefresh(self):
        self.setStatus("Refreshing folder...")
        current_folder = self.dataPath()
        current_mdaFileList = self.mdaFileList()
        self.parent.setMdaFileList(current_folder)
        new_mdaFileList = self.mdaFileList()
        if new_mdaFileList:
            self.mda_folder_tableview.displayTable()
            difference = [
                item for item in new_mdaFileList if item not in current_mdaFileList
            ]
            if difference:
                self.setStatus(f"Loading new files: {difference}")
            else:
                self.setStatus(f"No new files.")
        else:
            self.setStatus(f"Nothing to update.")

    # # ------------ splitter methods

    def splitter_moved(self, key, *arg, **kwargs):
        thread = getattr(self, f"{key}_wait_thread", None)
        setattr(self, f"{key}_deadline", time.time() + self.motion_wait_time)
        if thread is None or not thread.is_alive():
            self.setStatus(f"Start new thread now.  {key=}")
            setattr(self, f"{key}_wait_thread", self.splitter_wait_changes(key))

    def splitter_settings_name(self, key):
        """Name to use with settings file for 'key' splitter."""
        return f"{self.__class__.__name__.lower()}_{key}"

    @utils.run_in_thread
    def splitter_wait_changes(self, key):
        """
        Wait for splitter to stop changing before updating settings.

        PARAMETERS

        key *str*:
            Name of splitter (either 'hsplitter' or 'vsplitter')
        """
        from .user_settings import settings

        splitter = getattr(self, key)
        while time.time() < getattr(self, f"{key}_deadline"):
            time.sleep(self.motion_wait_time * 0.1)

        sname = self.splitter_settings_name(key)
        self.setStatus(f"Update settings: {sname=} {splitter.sizes()=}")
        settings.saveSplitter(splitter, sname)

    def setStatus(self, text):
        self.parent.setStatus(text)
