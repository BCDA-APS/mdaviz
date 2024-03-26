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
        from .mda_file import MDAFile

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

        ########################################################################
        # TODO : need to remove tab for folder! I am not doing that again 
        # TODO: there are too many layout, we are loosing some precious real estate; can we remove some layers?
        ########################################################################
        
        # File table view:
        self.mda_file = MDAFile(self)
        layout = self.mda_groupbox.layout()
        layout.addWidget(self.mda_file)

        # Data vizualisation:
        self.mda_file_visualization = MDAFileVisualization(self)
        layout = self.viz_groupbox.layout()
        layout.addWidget(self.mda_file_visualization)

        # Initialize attributes:
        self.setSelectionField()
        self.setSelectionModel()
        self.setSavedSelection()
        self.setFirstFileIndex()
        self.setLastFileIndex()
        self.setCurrentFileIndex()
        self.setCurrentFileTV()

        # File Selection Model & Focus
        model = self.mda_folder_tableview.tableView.model()
        if model is not None and len(self.mdaFileList()) > 0:
            self.mda_folder_tableview.tableView.setFocus()
            selection_model = self.mda_folder_tableview.tableView.selectionModel()
            self.setSelectionModel(selection_model)
            first_file_index = model.index(0, 0)
            last_file_index = model.index(model.rowCount() - 1, 0)
            self.setFirstFileIndex(first_file_index)
            self.setLastFileIndex(last_file_index)

        # Folder table view signal/slot connections:
        self.mda_folder_tableview.tableView.clicked.connect(self.doFileSelected)    
        self.mda_folder_tableview.firstButton.clicked.connect(self.goToFirst)
        self.mda_folder_tableview.lastButton.clicked.connect(self.goToLast)
        self.mda_folder_tableview.backButton.clicked.connect(self.goToPrevious)
        self.mda_folder_tableview.nextButton.clicked.connect(self.goToNext)

        # save/restore splitter sizes in application settings
        for key in "hsplitter vsplitter".split():
            splitter = getattr(self, key)
            sname = self.splitter_settings_name(key)
            settings.restoreSplitter(splitter, sname)
            splitter.splitterMoved.connect(partial(self.splitter_moved, key))

    # # ------------ set & get methods:

    def dataPath(self):
        """Path (obj) of the data folder (folder comboBox + subfolder comboBox)."""
        return self.mainWindow.dataPath()

    def mdaFileList(self):
        """List of mda file (name only) in the selected folder."""
        return self.mainWindow.mdaFileList()

    def currentFileTV(self):
        return self._currentFileTV

    def currentFileIndex(self):
        return self._currentFileIndex

    def firstFileIndex(self):
        return self._firstFileIndex

    def lastFileIndex(self):
        return self._lastFileIndex

    def selectionModel(self):
        """
        Used to access the selection model associated with a view, such as MDAFolderTableView.
        The selection model manages the selection state (e.g., which rows or items are selected)
        within the view.
        """
        return self._selection_model

    def savedSelection(self):  # TODO is this used at all?
        return self._saved_selection

    def setSelectionModel(self, selection=None):
        self._selection_model = selection

    def setSavedSelection(self, selection=None):
        self._saved_selection = selection

    def setCurrentFileTV(self, tableview=None):
        self._currentFileTV = tableview

    def setCurrentFileIndex(self, index=None): 
        self._currentFileIndex = index

    def setFirstFileIndex(self, index=None):
        self._firstFileIndex = index

    def setLastFileIndex(self, index=None):
        self._lastFileIndex = index

    # # ------------ Table view methods:

    def updateFolderView(self):
        """Clear existing data and set new data for mda_folder_tableview"""
        self.mda_folder_tableview.clearContents()
        self.mda_folder_tableview.displayTable()




    def updateFileView(self, index=None):
        """Clear existing data and set new data for mda_file_tableview"""
        # NOTE: Here I cannot use currentIndex = self.selectionModel().currentIndex()
        # since here's a distinction between navigating through the table view (using arrow keys, 
        # which doesn't trigger plotting) and actively selecting a file for display (through 
        # double-clicking or using navigation buttons like first/next/previous/last, which triggers plotting)       
        index = self.currentFileIndex().row() if self.currentFileIndex() else index
        tableview = self.currentFileTV()
        ## TODO need to keep track of which tab here? 1 tab is 1 tableview for one file
        tableview.clearContents()
        tableview.displayTable(index)

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
        # TODO Update this:
        Retrieves the current selection of positioner (X) and detectors (Y) to be plotted.

        This method returns a dictionary representing the indices of the selected positioner
        and detectors within the MDA File Table View. Upon first invocation or if no selections
        have been made, it attempts to default to the first available positioner and detector,
        if they exist.

        The dictionary structure is as follows:
        {'X': index_of_positioner, 'Y': [indices_of_detectors]}
        For example, {'Y': [2, 3], 'X': 1}

        Returns:
            dict or None: A dictionary containing the selected indices for plotting or None
            if no valid selections can be made based on the available data.
        """
        return self._selection_field

    def setSelectionField(self, new_selection=None):
        self._selection_field = new_selection if new_selection != {} else None

    def updateSelectionForNewPVs(self, oldPvList, newPvList, verbose=False):
        """
        Update the selection of positioners (X) and detectors (Y) based on a new list of PVs
        after selecting a new file.

        Args:
            oldPvList (list): PVs in the previously selected file.
            newPvList (list): Matching PVs in the newly selected file.
            verbose (bool): If True, print detailed changes.

        Returns:
            None: Updates the selection field directly if changes are made.
        """
        if verbose:
            print(f"\n----- Selection before clean up: {self.selectionField()}\n")
        changes_made = False
        tableview = self.currentFileTV()
        new_selection = {"Y": [], "X": tableview.data()["fileInfo"]["firstPos"]}
        # Update Y selections
        changes_made |= self.updateDetectorSelection(
            oldPvList, newPvList, new_selection, verbose
        )
        # Update X selection and check for changes
        old_idx = self.selectionField()["X"]
        new_idx = new_selection["X"]
        if old_idx != new_idx:
            changes_made = True
            if verbose:
                print(
                    f"Positioner <{oldPvList[old_idx]}> changed from {old_idx} to {new_idx} <{newPvList[new_idx]}>"
                )
        if changes_made:
            self.applySelectionChanges(new_selection)
        if verbose:
            print(f"\n----- Selection After clean up: {self.selectionField()}\n")

    def updateDetectorSelection(self, oldPvList, newPvList, new_selection, verbose):
        changes_made = False
        for old_idx in self.selectionField()["Y"]:
            if old_idx < len(oldPvList):
                old_pv = oldPvList[old_idx]
                if old_pv in newPvList:
                    new_idx = newPvList.index(old_pv)
                    new_selection["Y"].append(new_idx)
                    if new_idx != old_idx:
                        changes_made = True
                        if verbose:
                            print(
                                f"Detector <{old_pv}> changed from {old_idx} to {new_idx}"
                            )
                else:
                    changes_made = True
                    if verbose:
                        print(f"Detector <{old_pv}> was removed")
        return changes_made

        ################################################################################
        # TODO : need to keep track of which tab here? 1 tab is 1 tableview for one file
        ################################################################################


    def applySelectionChanges(self, new_selection):
        print("\n\n\n\n\nEntering applySelectionChanges")
        tableview = self.currentFileTV()
        self.setSelectionField(new_selection)
        tableview.tableView.model().updateCheckboxes(
            utils.mda2ftm(new_selection), update_mda_mvc=False
        )
        print("\nLeaving applySelectionChanges")

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
        selectedFile = self.mdaFileList()[index.row()]
        self.setCurrentFileIndex(index)
        #file_path = str(self.dataPath() / selectedFile)
        #self.setCurrentFileSelected(file_path)  # TODO am I using this?
        
        # If there is no Folder Table View, do nothing
        if self.mda_folder_tableview.tableView.model() is None:
            return

        print(f"\n{index.row()=}")

        current_tab_index = self.mda_file.tabWidget.count()
        # if no tab open, currentIndex would return -1:
        if self.mda_file.tabWidget.count() == 0:
            oldPvList = None
        else:
            # access the instance of tableView for the current tab:
            current_tab_index = self.mda_file.tabWidget.currentIndex()
            oldTabTableview = self.mda_file.tabWidget.widget(current_tab_index)
            oldPvList = oldTabTableview.data()["fileInfo"]["pvList"]

        print(f"\nBefore addTab: {self.selectionField()=}")
        self.mda_file.addFileTab(index.row(), self.selectionField())
        print(f"\nAfter addTab: {self.selectionField()=}")
        self.mda_file.displayMetadata()
        self.mda_file.displayData()
        newPvList = self.mda_file.data().get("pvList")

        current_tab_index = self.mda_file.tabWidget.currentIndex()
        newTabTableview = self.mda_file.tabWidget.widget(current_tab_index)
        self.setCurrentFileTV(newTabTableview)

        # Manage signal connections for the new file selection.
        self.disconnectSignals(newTabTableview)
        newTabTableview.selected.connect(self.doPlot)
        newTabTableview.tableView.model().checkboxStateChanged.connect(
            self.onCheckboxStateChange
        )

        self.setStatus(
            f"\n\n========= Selected file: {selectedFile} in {str(self.dataPath())}"
        )
        # selectionField() may have changed when calling addFileTab:
        if self.selectionField():
            if oldPvList is not None:
                self.updateSelectionForNewPVs(oldPvList, newPvList, verbose)
            self.handlePlotBasedOnMode()
        else:
            self.setStatus("Could not find a (positioner,detector) pair to plot.")

    def disconnectSignals(self, tableview):
        """Disconnect signals for selection changes and checkbox state changes."""
        try:
            tableview.selected.disconnect()
        except TypeError:  # No slots connected yet
            pass
        try:
            tableview.tableView.model().checkboxStateChanged.disconnect()
        except TypeError:  # No slots connected yet
            pass

    # # ------------ Plot methods:

    def handlePlotBasedOnMode(self):
        """Handle plotting based on the current mode (add, replace, or auto-off)."""
        print("\nEntering handlePlotBasedOnMode")
        mode = self.mda_file.mode()
        if mode == "Auto-add":
            self.doPlot("add", self.selectionField())
        elif mode == "Auto-replace":
            print(f"{mode=}")
            print(f"{self.selectionField()=}")
            self.doPlot("replace", self.selectionField())
        else:
            self.setStatus("Mode is set to Auto-off")
        print("\nLeaving handlePlotBasedOnMode\n\n")

    def doPlot(self, *args, **kwargs):
        """Slot: data field selected (for plotting) button is clicked."""
        from .chartview import ChartView

        tableview = self.currentFileTV()

        action = args[0]
        self.setSelectionField(args[1])
        y_rows = self.selectionField().get("Y", [])

        print(f"\ndoPlot called: {args=}")

        # Get the matplotlib chartview widget, if exists:
        layoutMpl = self.mda_file_visualization.plotPageMpl.layout()
        if layoutMpl.count() != 1:  # in case something changes ...
            raise RuntimeError("Expected exactly one widget in this layout!")
        widgetMpl = layoutMpl.itemAt(0).widget()
        
        ########################################################################
        # TODO : need to fix button, not working anymore                  # ####
        ########################################################################

        if action in ("replace", "add"):
            # # Get dataset for the positioner/detector selection:
            datasets, plot_options = tableview.data2Plot(self.selectionField())

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
            tableview.clearContents()

    # # ------------ Folder Table View navigation & selection highlight:
    
    
    def goToFirst(self):
        model = self.mda_folder_tableview.tableView.model()
        if model.rowCount() > 0:
            firstIndex = model.index(0, 0)
            self.selectAndShowIndex(firstIndex)

    def goToLast(self):
        model = self.mda_folder_tableview.tableView.model()
        if model.rowCount() > 0:
            lastIndex = model.index(model.rowCount() - 1, 0)
            self.selectAndShowIndex(lastIndex)

    def goToNext(self):
        currentIndex = self.selectionModel().currentIndex()
        nextIndex = currentIndex.sibling(currentIndex.row() + 1, currentIndex.column())
        if nextIndex.isValid():
            self.selectAndShowIndex(nextIndex)

    def goToPrevious(self):
        currentIndex = self.selectionModel().currentIndex()
        prevIndex = currentIndex.sibling(currentIndex.row() - 1, currentIndex.column())
        if prevIndex.isValid():
            self.selectAndShowIndex(prevIndex)

    def selectAndShowIndex(self, index):
        # Ensure the table view has focus to get the blue highlight on Mac OS
        self.mda_folder_tableview.tableView.setFocus()
        # Determine the appropriate scrollHint based on the row position
        model = self.mda_folder_tableview.tableView.model()
        rowCount = model.rowCount()
        scrollHint = QAbstractItemView.EnsureVisible
        if index.row() == 0:
            scrollHint = QAbstractItemView.PositionAtTop
        elif index.row() == rowCount - 1:
            scrollHint = QAbstractItemView.PositionAtBottom
        # Select the row and ensure it's visible
        self.selectionModel().setCurrentIndex(index, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)
        self.mda_folder_tableview.tableView.scrollTo(index, scrollHint)
        # Emit the file selected signal
        self.doFileSelected(index)


    # # ------------ Checkbox methods:

    def onCheckboxStateChange(self, selection):
        """Slot: data field (for plotting) changes."""
        from .chartview import ChartView

        tableview = self.currentFileTV()
        previous_selection = self.selectionField()

        # Get the matplotlib chartview widget, if exists:
        layoutMpl = self.mda_file_visualization.plotPageMpl.layout()
        if layoutMpl.count() != 1:  # in case something changes ...
            raise RuntimeError("Expected exactly one widget in this layout!")
        widgetMpl = layoutMpl.itemAt(0).widget()

        mode = self.mda_file.mode()

        # Exceptions:
        if not selection.get("Y"):  # no DET selected
            widgetMpl.clearPlot()
            return
        if not selection.get("X"):  # if no POS, default to index
            widgetMpl.clearPlot()
            selection["X"] = 0
            tableview.tableView.model().checkCheckBox(0, "X")

        if previous_selection:
            # if changing POS, clear the graph:
            if previous_selection.get("X") != selection.get("X"):
                widgetMpl.clearPlot()  #
            # if removing DET, clear the graph:   #TODO why?
            if len(previous_selection.get("Y")) > len(selection.get("Y")):
                widgetMpl.clearPlot()

        # Get dataset for the positioner/detector selection:
        datasets, plot_options = tableview.data2Plot(self.selectionField())

        self.setSelectionField(selection)
        y_rows = selection.get("Y", [])
        # print(f"\nonCheckboxStateChange called:  {mode} {fileName} with {selection}")
        print(f"\nonCheckboxStateChange called:  {mode} with {selection}")

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
