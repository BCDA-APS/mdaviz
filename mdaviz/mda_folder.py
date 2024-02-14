"""
MVC implementation of mda files.

* MVC: Model View Controller

.. autosummary::

    ~MDA_MVC
"""

import time
from functools import partial

from PyQt5 import QtWidgets
from PyQt5.QtCore import QItemSelectionModel
from PyQt5.QtWidgets import QAbstractItemView


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

        # Folders table view:
        self.mda_folder_tableview = MDAFolderTableView(self)
        layout = self.folder_groupbox.layout()
        layout.addWidget(self.mda_folder_tableview)
        self.mda_folder_tableview.displayTable()
        try:
            self.parent.refresh.released.disconnect()
        except TypeError:
            pass
        self.parent.refresh.released.connect(self.doRefresh)

        # Fields table view:
        self.select_fields_tableview = SelectFieldsTableView(self)
        layout = self.mda_groupbox.layout()
        layout.addWidget(self.select_fields_tableview)

        # Data vizualisation:
        self.mda_file_visualization = MDAFileVisualization(self)
        layout = self.viz_groupbox.layout()
        layout.addWidget(self.mda_file_visualization)

        # Initialize File and Field Selection
        self._selection_field = None
        self._selection_model = None
        self._firstFileIndex = None
        self._lastFileIndex = None
        self._currentFileIndex = None
        model = self.mda_folder_tableview.tableView.model()
        if model is not None:
            self.mda_folder_tableview.tableView.setFocus()
            self._firstFileIndex = model.index(0, 0)
            self._lastFileIndex = model.index(model.rowCount() - 1, 0)
            # Highlight (select) and plot the first file:
            self._selection_model = self.mda_folder_tableview.tableView.selectionModel()
            self.highlightNewFile(0)
            self.doFileSelected(model.index(0, 0))

        # Folder table view signal/slot connections:
        self.mda_folder_tableview.tableView.clicked.connect(self.doFileSelected)
        self.mda_folder_tableview.firstButton.clicked.connect(self.goToFirst)
        self.mda_folder_tableview.lastButton.clicked.connect(self.goToLast)
        self.mda_folder_tableview.backButton.clicked.connect(self.goToBack)
        self.mda_folder_tableview.nextButton.clicked.connect(self.goToNext)

        # save/restore splitter sizes in application settings
        for key in "hsplitter vsplitter".split():
            splitter = getattr(self, key)
            sname = self.splitter_settings_name(key)
            settings.restoreSplitter(splitter, sname)
            splitter.splitterMoved.connect(partial(self.splitter_moved, key))

    def dataPath(self):
        """Path (obj) of the data folder (folder comboBox + subfolder comboBox)."""
        return self.parent.dataPath()

    def mdaFileCount(self):
        """Number of mda files in the selected folder."""
        return self.parent.mdaFileCount()

    def mdaFileList(self):
        """List of mda file (name only) in the selected folder."""
        return self.parent.mdaFileList()

    def selectionField(self):
        return self._selection_field

    def selectionModel(self):
        return self._selection_model

    def currentFileIndex(self):
        return self._currentFileIndex

    def firstFileIndex(self):
        return self._firstFileIndex

    def lastFileIndex(self):
        return self._lastFileIndex

    def highlightNewFile(self, row):
        if self.selectionModel() and self.mda_folder_tableview.tableView.model():
            # Ensure the table view has focus to get the blue highlight on Mac OS
            self.mda_folder_tableview.tableView.setFocus()
            # Select the row to highlight
            index = self.mda_folder_tableview.tableView.model().index(row, 0)
            self.selectionModel().select(
                index, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows
            )

            # Set the selection mode and behavior to mimic clicking on a row with the mouse
            self.mda_folder_tableview.tableView.setSelectionMode(
                QAbstractItemView.SingleSelection
            )
            self.mda_folder_tableview.tableView.setSelectionBehavior(
                QAbstractItemView.SelectRows
            )

            # Scroll to the selected row to ensure it's visible
            # Use PositionAtTop or PositionAtBottom for the first/last file respectively
            scrollHint = QAbstractItemView.EnsureVisible
            if row == 0:
                scrollHint = QAbstractItemView.PositionAtTop
            elif row == self.mda_folder_tableview.tableView.model().rowCount() - 1:
                scrollHint = QAbstractItemView.PositionAtBottom
            self.mda_folder_tableview.tableView.scrollTo(index, scrollHint)

    def goToFirst(self):
        if self.firstFileIndex():
            index = self.firstFileIndex()
            row = index.row()
            self.highlightNewFile(row)
            self.doFileSelected(index)

    def goToLast(self):
        if self.lastFileIndex():
            index = self.lastFileIndex()
            row = index.row()
            self.highlightNewFile(row)
            self.doFileSelected(index)

    def goToNext(self):
        if self.selectionModel() and self.lastFileIndex():
            i = self.currentFileIndex()
            if i.row() == self.lastFileIndex().row():
                return
            if i != None:
                i = self.mda_folder_tableview.tableView.model().index(i.row() + 1, 0)
                self.highlightNewFile(i.row())
                self.doFileSelected(i)

    def goToBack(self):
        if self.currentFileIndex() and self.firstFileIndex():
            i = self.currentFileIndex()
            if i.row() == self.firstFileIndex().row():
                return
            if i != None:
                i = self.mda_folder_tableview.tableView.model().index(i.row() - 1, 0)
                self.highlightNewFile(i.row())
                self.doFileSelected(i)

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
        self._currentFileIndex = index
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
        from .chartview import ChartView
        from .select_fields_table_view import to_datasets

        action = args[0]
        self._selection_field = args[1]
        y_rows = self._selection_field.get("Y", [])

        print(f"\ndoPlot called: {args=}")

        # Get the matplotlib chartview widget, if exists:
        layoutMpl = self.mda_file_visualization.plotPageMpl.layout()
        if layoutMpl.count() != 1:  # in case something changes ...
            raise RuntimeError("Expected exactly one widget in this layout!")
        widgetMpl = layoutMpl.itemAt(0).widget()

        if action in ("replace", "add"):
            # Get dataset for the positioner/detector selection:
            detsDict = self.select_fields_tableview.detsDict()
            fileName = self.select_fields_tableview.fileName()
            datasets, plot_options = to_datasets(
                fileName, detsDict, self.selectionField()
            )

            if not isinstance(widgetMpl, ChartView):
                widgetMpl = ChartView(self, **plot_options)  # Make a blank chart.
            if action in ("replace"):
                widgetMpl.clearPlot()
            for row, (ds, ds_options) in zip(y_rows, datasets):
                kwargs = {"ds_options": ds_options, "plot_options": plot_options}
                widgetMpl.plot(row, *ds, **kwargs)
            self.mda_file_visualization.setPlot(widgetMpl)

        elif action in ("clear"):
            widgetMpl.clearPlot()
            self.select_fields_tableview.tableView.model().clearAllCheckboxes()

    # # ------------ Checkbox methods:

    def onCheckboxStateChange(self, selection):
        """Slot: data field (for plotting) changes."""
        from .chartview import ChartView
        from .select_fields_table_view import to_datasets

        previous_selection = self.selectionField()

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
        datasets, plot_options = to_datasets(fileName, detsDict, selection)

        self._selection_field = selection
        y_rows = selection.get("Y", [])
        print(f"\nonCheckboxStateChange called:  {mode} {fileName} with {selection}")

        if mode in ("Auto-replace", "Auto-add"):
            if not isinstance(widgetMpl, ChartView):
                widgetMpl = ChartView(self, **plot_options)  # Make a blank chart.
            if mode in ("Auto-replace"):
                widgetMpl.clearPlot()
            for row, (ds, ds_options) in zip(y_rows, datasets):
                # ds_options: label (for legend)
                # plot_options: xlabel, ylabel, title
                kwargs = {"ds_options": ds_options, "plot_options": plot_options}
                widgetMpl.plot(row, *ds, **kwargs)
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
