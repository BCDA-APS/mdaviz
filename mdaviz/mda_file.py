"""
MVC implementation of mda files.

* MDA: BlueskyRunsCatalog
* MVC: Model View Controller

.. autosummary::

    ~MDA_MVC
"""


import time
from functools import partial

from PyQt5 import QtWidgets

from . import utils

class MDA_MVC(QtWidgets.QWidget):
    """MVC class for mda files."""
    # UI file name matches this module, different extension
    ui_file = utils.getUiFileName(__file__)
    motion_wait_time = 1  # wait for splitter motion to stop to update settings

    def __init__(self, parent):
        self.parent = parent

        super().__init__()
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()

    def setup(self):
        from .app_settings import settings
        from .mda_search import mdaSearchPanel
        # from .mda_table_view import mdaTableView
        # from .mda_viz import mdaVisualization
        
        self.mda_search_panel = mdaSearchPanel(self)
        layout = self.file_groupbox.layout()
        layout.addWidget(self.mda_search_panel)
        self.mda_search_panel.setupFile(self.fileName())

        # self.mda_tableview = mdaTableView(self)
        # layout = self.mda_groupbox.layout()
        # layout.addWidget(self.mda_tableview)
        # self.mda_tableview.displayTable()

        # self.mda_viz = mdaRunVisualization(self)
        # layout = self.viz_groupbox.layout()
        # layout.addWidget(self.mda_viz)

        # # connect search signals with tableview update
        # # fmt: off
        # widgets = [
        #     [self.brc_search_panel.plan_name, "returnPressed"],
        #     [self.brc_search_panel.scan_id, "returnPressed"],
        #     [self.brc_search_panel.status, "returnPressed"],
        #     [self.brc_search_panel.positioners, "returnPressed"],
        #     [self.brc_search_panel.detectors, "returnPressed"],
        #     [self.brc_search_panel.date_time_widget.apply, "released"],
        # ]
        # # fmt: on
        # for widget, signal in widgets:
        #     getattr(widget, signal).connect(self.brc_tableview.displayTable)

        # save/restore splitter sizes in application settings
        for key in "hsplitter vsplitter".split():
            splitter = getattr(self, key)
            sname = self.splitter_settings_name(key)
            settings.restoreSplitter(splitter, sname)
            splitter.splitterMoved.connect(partial(self.splitter_moved, key))

    def file(self):
        return self.parent.file()

    def fileName(self):
        return self.parent.fileName()
    
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
        from .app_settings import settings

        splitter = getattr(self, key)
        while time.time() < getattr(self, f"{key}_deadline"):
            # self.setStatus(
            #     f"Wait: {time.time()=:.3f}"
            #     f"  {getattr(self, f'{key}_deadline')=:.3f}"
            # )
            time.sleep(self.motion_wait_time * 0.1)

        sname = self.splitter_settings_name(key)
        self.setStatus(f"Update settings: {sname=} {splitter.sizes()=}")
        settings.saveSplitter(splitter, sname)

    def setStatus(self, text):
        self.parent.setStatus(text)