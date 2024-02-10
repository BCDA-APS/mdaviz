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

        # Refreshing folder content:
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

        self._selection = None

        # save/restore splitter sizes in application settings
        for key in "hsplitter vsplitter".split():
            splitter = getattr(self, key)
            sname = self.splitter_settings_name(key)
            settings.restoreSplitter(splitter, sname)
            splitter.splitterMoved.connect(partial(self.splitter_moved, key))

    # # ------------ Folder & file selection methods:

    def doFileSelected(self, index):
        """
        Display field table view, file metadata, and plot first pos & det depending on mode.

        If the graph is blank, selecting a file:
                - auto-add: automatically plots the 1st pos/det
                - auto-replace : same
                - auto-off: nothing happens
        If the graph is NOT blank, selecting a file:
                - auto-add: automatically add to plot the same pos/det that was already plotted
                - auto-replace : automatically replace plot wiht the same pos/det that was already plotted
                - auto-off: nothing happens

        Args:
            index (int): file index
        """

        model = self.mda_folder_tableview.tableView.model()
        if model is not None:
            self.select_fields_tableview.displayTable(index.row())
            self.select_fields_tableview.displayMetadata(index.row())
            # Disconnect previous subcription from the signal emitted when selecting a new file:
            try:
                self.select_fields_tableview.selected.disconnect()
            except TypeError:  # No slots connected yet
                pass
            self.select_fields_tableview.selected.connect(self.doPlot)
            # Disconnect previous subcription from the signal emitted when selecting a new field:
            try:
                self.select_fields_tableview.tableView.model().checkboxStateChanged.disconnect()
            except TypeError:  # No slots connected yet
                pass
            self.select_fields_tableview.tableView.model().checkboxStateChanged.connect(
                self.onCheckboxStateChange
            )

            # Try something else:
            self.setStatus(
                f"\n\n======== Selected file: {self.mdaFileList()[index.row()]}"
            )

            first_pos_idx = self.select_fields_tableview.firstPos()
            first_det_idx = self.select_fields_tableview.firstDet()
            if first_pos_idx is not None and first_det_idx is not None:
                first_selection = {"X": first_pos_idx, "Y": [first_det_idx]}
                if self.select_fields_tableview.mode() == "Auto-add":
                    self.doPlot("add", first_selection)
                elif self.select_fields_tableview.mode() == "Auto-replace":
                    self.doPlot("replace", first_selection)
                else:
                    self.setStatus("Mode is set to Auto-off")
            else:
                self.setStatus("Could not find a (positioner,detector) pair to plot.")

    def selection(self):
        return self._selection

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

    def doPlot(self, *args, **kwargs):
        """Slot: data field selected (for plotting) button is clicked."""
        from .chartview import ChartViewMpl
        from .select_fields_table_view import to_datasets_mpl

        action = args[0]
        self._selection = args[1]
        y_rows = self._selection.get("Y", [])
        print(f"\ndoPlot called: {args=}")

        detsDict = self.select_fields_tableview.detsDict()
        fileName = self.select_fields_tableview.fileName()

        # Get dataset for the positioner/detector selection:
        datasets_mpl, options_mpl = to_datasets_mpl(
            fileName, detsDict, self.selection()
        )

        # Get the matplotlib chartview widget, if exists:
        layoutMpl = self.mda_file_visualization.plotPageMpl.layout()
        if layoutMpl.count() != 1:  # in case something changes ...
            raise RuntimeError("Expected exactly one widget in this layout!")
        widgetMpl = layoutMpl.itemAt(0).widget()

        if action in ("replace"):
            if not isinstance(widgetMpl, ChartViewMpl):
                widgetMpl = ChartViewMpl(self, **options_mpl)  # Make a blank chart.
            else:
                widgetMpl.clearPlot()
            for row, (ds, ds_options) in zip(y_rows, datasets_mpl):
                widgetMpl.plot(row, *ds, **ds_options)
            self.mda_file_visualization.setPlot(widgetMpl)

        elif action in ("add"):
            if not isinstance(widgetMpl, ChartViewMpl):
                widgetMpl = ChartViewMpl(self, **options_mpl)  # Make a blank chart.
            for row, (ds, ds_options) in zip(y_rows, datasets_mpl):
                widgetMpl.plot(row, *ds, **ds_options)
            self.mda_file_visualization.setPlot(widgetMpl)

        elif action in ("clear"):
            widgetMpl.clearPlot()
            self.select_fields_tableview.tableView.model().clearAllCheckboxes()

    # # ------------ Checkbox methods:

    def onCheckboxStateChange(self, selection):
        """Slot: data field (for plotting) changes."""
        from .chartview import ChartViewMpl
        from .select_fields_table_view import to_datasets_mpl

        previous_selection = self.selection()

        # Get the matplotlib chartview widget, if exists:
        layoutMpl = self.mda_file_visualization.plotPageMpl.layout()
        if layoutMpl.count() != 1:  # in case something changes ...
            raise RuntimeError("Expected exactly one widget in this layout!")
        widgetMpl = layoutMpl.itemAt(0).widget()

        mode = self.select_fields_tableview.mode()

        # Exceptions:
        if not selection.get("Y"):  # no DET selected
            widgetMpl.clearPlot()
            return
        if not selection.get("X"):  # if no POS, default to index
            widgetMpl.clearPlot()
            selection["X"] = 0
            self.select_fields_tableview.tableView.model().checkCheckBox(0, "X")

        if previous_selection:
            # if changing POS, clear the graph:
            if previous_selection.get("X") != selection.get("X"):
                widgetMpl.clearPlot()  #
            # if removing DET, clear the graph:
            if len(previous_selection.get("Y")) > len(selection.get("Y")):
                widgetMpl.clearPlot()

        # Get info for the file & POS/DET selection:
        detsDict = self.select_fields_tableview.detsDict()
        fileName = self.select_fields_tableview.fileName()
        datasets_mpl, options_mpl = to_datasets_mpl(fileName, detsDict, selection)
        self._selection = selection
        y_rows = selection.get("Y", [])
        print(f"\nonCheckboxStateChange called:  {mode} {fileName} with {selection}")

        if mode in ("Auto-replace"):
            if not isinstance(widgetMpl, ChartViewMpl):
                widgetMpl = ChartViewMpl(self, **options_mpl)  # Make a blank chart.
            else:
                widgetMpl.clearPlot()
            for row, (ds, ds_options) in zip(y_rows, datasets_mpl):
                widgetMpl.plot(row, *ds, **ds_options)
            self.mda_file_visualization.setPlot(widgetMpl)

        elif mode in ("Auto-add"):
            if not isinstance(widgetMpl, ChartViewMpl):
                widgetMpl = ChartViewMpl(self, **options_mpl)  # Make a blank chart.
            for row, (ds, ds_options) in zip(y_rows, datasets_mpl):
                widgetMpl.plot(row, *ds, **ds_options)
            self.mda_file_visualization.setPlot(widgetMpl)

        elif mode in ("Auto-off"):
            return

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
