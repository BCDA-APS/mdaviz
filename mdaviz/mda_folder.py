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


class MDA_MVC(QtWidgets.QWidget):
    """Model View Controller class for mda files."""

    ui_file = utils.getUiFileName(__file__)
    motion_wait_time = 1

    def __init__(self, parent):
        """
        Initialize the model and connect with its parent.

        PARAMETERS

        parent object:
            Instance of mdaviz.mainwindow.MainWindow
        """

        self.mainWindow = parent
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
            self.mainWindow.refresh.released.disconnect()
        except TypeError:
            pass
        self.mainWindow.refresh.released.connect(self.doRefresh)

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
        self._saved_selection = None
        self._selection_model = None
        self._firstFileIndex = None
        self._lastFileIndex = None
        self._currentFileIndex = None
        model = self.mda_folder_tableview.tableView.model()
        if model is not None and self.mainWindow.mdaFileCount() > 0:
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
        return self.mainWindow.dataPath()

    def mdaFileCount(self):
        """Number of mda files in the selected folder."""
        return self.mainWindow.mdaFileCount()

    def mdaFileList(self):
        """List of mda file (name only) in the selected folder."""
        return self.mainWindow.mdaFileList()

    def currentFileIndex(self):
        return self._currentFileIndex

    def firstFileIndex(self):
        return self._firstFileIndex

    def lastFileIndex(self):
        return self._lastFileIndex

    # # ------------ Table view methods:

    def updateFolderView(self):
        """Clear existing data and set new data for mda_folder_tableview"""
        self.mda_folder_tableview.clearContents()
        self.mda_folder_tableview.displayTable()

    def updateFieldsView(self, index=None):
        """Clear existing data and set new data for select_fields_tableview"""
        index = self.currentFileIndex().row() if self.currentFileIndex() else index
        self.select_fields_tableview.clearContents()
        self.select_fields_tableview.displayTable(index)

    def doRefresh(self):
        self.setStatus("Refreshing folder...")
        current_folder = self.dataPath()
        current_mdaFileList = self.mdaFileList()
        self.mainWindow.setMdaFileList(current_folder)
        new_mdaFileList = self.mdaFileList()
        if new_mdaFileList:
            self.mda_folder_tableview.displayTable()
            difference = [
                item for item in new_mdaFileList if item not in current_mdaFileList
            ]
            if difference:
                self.setStatus(f"Loading new files: {difference}")
            else:
                self.setStatus("No new files.")
        else:
            self.setStatus("Nothing to update.")

    # # ------------ Fields selection methods:

    def selectionField(self):
        """
        Retrieves the current selection of positioner (X) and detectors (Y) to be plotted.

        This method returns a dictionary representing the indices of the selected positioner
        and detectors within the Fields Table View. Upon first invocation or if no selections
        have been made, it attempts to default to the first available positioner and detector,
        if they exist.

        The dictionary structure is as follows:
        {'X': index_of_positioner, 'Y': [indices_of_detectors]}
        For example, {'Y': [2, 3], 'X': 1}

        Returns:
            dict or None: A dictionary containing the selected indices for plotting or None
            if no valid selections can be made based on the available data.
        """
        if self._selection_field is None:
            first_pos_idx = self.select_fields_tableview.firstPos()
            first_det_idx = self.select_fields_tableview.firstDet()
            if first_pos_idx is not None and first_det_idx is not None:
                self._selection_field = {"X": first_pos_idx, "Y": [first_det_idx]}
            else:
                self._selection_field = None
        return self._selection_field

    def updateSelectionField(self, new_selection):
        self._selection_field = new_selection

    def updateSelectionForNewPVs(self, oldPvList, newPvList, verbose=False):
        """
        Update the selection of positioner (X) & detectors (Y) based on the new list of PVs
        after selecting a new file.

        Args:
            oldPvList (list): The list of PVs in the previously selected file.
            newPvList (list): The list of matching PVs in the newly selected file.

        Returns:
            dict: Updated selection with valid PVs for the new file.
        """
        changes_made = False
        new_selection = {"Y": [], "X": 0}
        # Process Y (detectors) selection: if PV exists, updates its index, otherwise, removes it.
        posY = self.selectionField()["Y"]
        for det_idx in posY:
            if det_idx < len(oldPvList):
                old_pv = oldPvList[det_idx]
                if old_pv in newPvList:
                    new_idx = newPvList.index(old_pv)
                    if verbose:
                        print(
                            f"Keeping PV: {old_pv=} was at index {det_idx}, now at index {new_idx}"
                        )
                    new_selection["Y"].append(new_idx)
                    if new_idx != det_idx:
                        changes_made = True

                else:
                    changes_made = True
                    if verbose:
                        print(f"Removing PV: {old_pv=} was at index {det_idx}")
        # Process X (positioner) selection: if 1st positioner, use it, otherwise default to Index
        old_posX = self.selectionField()["X"]
        new_posX = self.select_fields_tableview.firstPos()
        new_selection["X"] = new_posX
        if old_posX != new_posX:
            changes_made = True
        if changes_made:
            self.updateSelectionField(new_selection)
            self.select_fields_tableview.tableView.model().updateCheckboxes(
                utils.mda2ftm(new_selection), update_mda_mvc=False
            )
        if verbose:
            print(f"Change made to selection: {changes_made}")

    # # ------------ File selection methods:

    def doFileSelected(self, index, verbose=True):
        """
        Handles the selection of a new file in the folder table view. This method updates the UI
        to display the fields table view and metadata for the selected file, manages the connections
        for selection changes and checkbox state changes, and initiates plotting based on the
        current mode (Auto-add, Auto-replace, Auto-off).

        This method also ensures that the selection of positioners and detectors is updated
        to reflect the PVs available in the newly selected file, taking into account any changes
        from the previously selected file.

        Args:
            index (int): The index of the selected file in the file list. This index is used to
                        retrieve the file's details and update the UI accordingly.

        Behavior:
            - Displays the fields table view and metadata for the selected file.
            - Disconnects any existing signal connections for previous file selections and sets up
            new connections for the current selection.
            - Updates the status bar with the name of the selected file.
            - If a valid selection of positioner and detector is found, initiates plotting based on
            the selected mode. Otherwise, updates the status to indicate no valid pair was found.
            - Handles the case where no previous file was selected (e.g., at application start).

        Note:
            The method assumes that `mda_folder_tableview` and `select_fields_tableview` are
            initialized and correctly set up to interact with the underlying data model and UI.
        """

        self._currentFileIndex = index
        # If there is no Folder Table View, do nothing
        if self.mda_folder_tableview.tableView.model() is None:
            return

        oldPvList = self.select_fields_tableview.pvList()
        self.select_fields_tableview.displayTable(index.row())
        self.select_fields_tableview.displayMetadata(index.row())
        newPvList = self.select_fields_tableview.pvList()

        # Manage signal connections for the new file selection.
        self.disconnectSignals()
        self.select_fields_tableview.selected.connect(self.doPlot)
        self.select_fields_tableview.tableView.model().checkboxStateChanged.connect(
            self.onCheckboxStateChange
        )

        # Update the status and selection based on the new file.
        selectedFile = self.mdaFileList()[index.row()]
        selectedFields = self.selectionField()
        self.setStatus(
            f"\n\n========= Selected file: {selectedFile} in {str(self.dataPath())}"
        )
        if selectedFields:
            if verbose:
                print(f"\n----- Selection before clean up: {self.selectionField()}")
            if oldPvList is not None:
                self.updateSelectionForNewPVs(oldPvList, newPvList, verbose)
            if verbose:
                print(f"\n----- Selection after clean up: {self.selectionField()}")
            self.handlePlotBasedOnMode()
        else:
            self.setStatus("Could not find a (positioner,detector) pair to plot.")

    def disconnectSignals(self):
        """Disconnect signals for selection changes and checkbox state changes."""
        try:
            self.select_fields_tableview.selected.disconnect()
        except TypeError:  # No slots connected yet
            pass
        try:
            self.select_fields_tableview.tableView.model().checkboxStateChanged.disconnect()
        except TypeError:  # No slots connected yet
            pass

    # # ------------ Plot methods:

    def handlePlotBasedOnMode(self):
        """Handle plotting based on the current mode (add, replace, or auto-off)."""
        mode = self.select_fields_tableview.mode()
        if mode == "Auto-add":
            self.doPlot("add", self.selectionField())
        elif mode == "Auto-replace":
            self.doPlot("replace", self.selectionField())
        else:
            self.setStatus("Mode is set to Auto-off")

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

    # # ------------ Folder Table View navigation & selection highlight:

    def selectionModel(self):
        """
        Used to access the selection model associated with a view, such as MDAFolderTableView.
        The selection model manages the selection state (e.g., which rows or items are selected)
        within the view.
        """
        return self._selection_model

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
        self.mainWindow.setStatus(text)
