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

        self.mda_file_visualization = MDAFileVisualization(self)
        layout = self.viz_groupbox.layout()
        layout.addWidget(self.mda_file_visualization)

        self.mda_folder_tableview.tableView.doubleClicked.connect(self.doFileSelected)

        # save/restore splitter sizes in application settings
        for key in "hsplitter vsplitter".split():
            splitter = getattr(self, key)
            sname = self.splitter_settings_name(key)
            settings.restoreSplitter(splitter, sname)
            splitter.splitterMoved.connect(partial(self.splitter_moved, key))

    # # ------------ Folder & file selection methods:

    def doFileSelected(self, index):
        model = self.mda_folder_tableview.tableView.model()
        if model is not None:
            self.select_fields_tableview.displayTable(index.row())
            self.select_fields_tableview.displayMetadata(index.row())
            self.select_fields_tableview.selected.connect(self.doPlot)
            self.setStatus(f"Selected file: {self.mdaFileList()[index.row()]}")

            # if the graph(s) is(are) blank ( as of now, Qt blank = Mpl blank), selecting a file automatically plots the first pos. vs first det.
            # TODO: this should depend on the selection: auto-replace vs auto-add; if auto-replace, will plot even if graph is not blank.
            if (
                self.mda_file_visualization.isPlotBlankQt()
                or self.mda_file_visualization.isPlotBlankMpl()
            ):
                first_pos_idx = self.select_fields_tableview.firstPos()
                first_det_idx = self.select_fields_tableview.firstDet()
                if first_pos_idx is not None and first_det_idx is not None:
                    first_selections = {"X": first_pos_idx, "Y": [first_det_idx]}
                    self.doPlot("replace", first_selections)
                else:
                    self.setStatus(
                        "Could not find a (positioner,detector) pair to plot."
                    )

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

    # # ------------ Plot methods:

    def doPlot(self, *args):
        """Slot: data field selected (for plotting) button is clicked."""
        from .chartview import ChartViewQt
        from .chartview import ChartViewMpl
        from .select_fields_table_view import to_datasets_qt
        from .select_fields_table_view import to_datasets_mpl

        action = args[0]
        selections = args[1]
        print(f"doPlot called with action: {action}, args: {args}")

        detsDict = self.select_fields_tableview.detsDict()
        fileName = self.select_fields_tableview.fileName()

        # setup datasets
        datasets_qt, options_qt = to_datasets_qt(detsDict, selections)
        datasets_mpl, options_mpl = to_datasets_mpl(fileName, detsDict, selections)

        # get the pyQtchart chartview widget, if exists:
        layoutQt = self.mda_file_visualization.plotPageQt.layout()
        if layoutQt.count() != 1:  # in case something changes ...
            raise RuntimeError("Expected exactly one widget in this layout!")
        widgetQt = layoutQt.itemAt(0).widget()
        if not isinstance(widgetQt, ChartViewQt) or action == "replace":
            widgetQt = ChartViewQt(self, **options_qt)  # Make a blank chart.
            if action == "add":
                action == "replace"

        # # get the matplotlib chartview widget, if exists:
        layoutMpl = self.mda_file_visualization.plotPageMpl.layout()
        if layoutMpl.count() != 1:  # in case something changes ...
            raise RuntimeError("Expected exactly one widget in this layout!")
        widgetMpl = layoutMpl.itemAt(0).widget()
        if not isinstance(widgetMpl, ChartViewMpl) or action == "replace":
            widgetMpl = ChartViewMpl(self, **options_mpl)  # Make a blank chart.
            if action == "add":
                action == "replace"

        if action in ("clear"):
            widgetQt.clearPlot()
            widgetMpl.clearPlot()

        if action in ("replace", "add"):
            for ds, ds_options in datasets_qt:
                widgetQt.plot(*ds, **ds_options)
            self.mda_file_visualization.setPlotQt(widgetQt)
            for ds, ds_options in datasets_mpl:
                widgetMpl.plot(*ds, **ds_options)
            self.mda_file_visualization.setPlotMpl(widgetMpl)

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
