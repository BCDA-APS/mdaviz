"""
MVC implementation of mda files.

* MVC: Model View Controller

.. Summary::

    ~MDA_MVC
        
        General initialization and setup methods:
        - __init__: Initializes the MDA_MVC instance, linking it with the main application window.
        - setup: Sets up folder and file table views, data visualization components, and establishes 
        signal-slot connections.
        
        Data Access and Management:
        - dataPath: Provides the path to the folder containing MDA files.
        - mdaFileList: Fetches names of MDA files in the selected folder.
        
        User interaction handling methods:
        - doRefresh: Refreshes the view to display updated MDA files from the selected folder.
        - doFileSelected: Handles user selection of MDA files, updating UI and initiating data plotting.
        - doPlot: Initiates data plotting based on user selections and current plot mode. It checks for the
        selected positioner and detectors, retrieves the corresponding data, and plots it in the visualization panel.
        - onCheckboxStateChange: Responds to user changes in checkbox states within the MDA file table, 
        triggering a re-plot of selected data.
        - handlePlotBasedOnMode: Determines plot updates based on the user-selected mode, e.g. Auto-add or Auto-replace.
    
        
        Navigation and UI state management:
        - goToFirst, goToLast, goToNext, goToPrevious: Methods for navigating through the list of MDA files.
        - selectAndShowIndex: Selects and highlights a file in the folder view based on index.
        - selectionModel, setSelectionModel: Get and set methods for the current selection model, managing 
        item selections within the view.
        - setCurrentFileTableview, currentFileTableview: Manages the table view for the currently active file.
         
        Selection Configuration:
        - updateDetectorSelection: Maps user-selected detectors across file changes to ensure consistency 
        despite changes in detector ordering or availability
        - updateSelectionForNewPVs: Updates to both detector and positioner selections for a new file.
        - applySelectionChanges: Updates the UI with new selections after a file change.
        - setSelectionField, selectionField: Sets and retrieves field selections for plotting.
            
        Splitter position management:
        - setSplitterSettingsName, setSplitterMoved, setSplitterWaitChanges: Methods for managing user-adjusted 
        splitter positions and saving these settings for future sessions.
        
    Flow Chart:
        
        Refresh Button Press
        |___> doRefresh
            |___> mda_folder_tableview.displayTable()   (to reload folder content)

        File Selection (Double Click or Navigation Button)
        |___> doFileSelected
            |___> Update UI (Tabs, Metadata, Data Display)
            |___> doPlot (Based on current mode and selections)
                |___> Retrieve and plot data based on selected positioner and detectors
        
        Checkbox State Change in File View
        |___> onCheckboxStateChange
            |___> doPlot (Replot based on new selections)
                |___> Retrieve and plot data based on selected positioner and detectors  
"""

import time
from functools import partial
from pathlib import Path

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
        utils.reconnect(self.mainWindow.refresh.released, self.doRefresh)

        # File table view:
        self.mda_file = MDAFile(self)
        layout = self.mda_groupbox.layout()
        layout.addWidget(self.mda_file)

        # Data vizualisation:
        self.mda_file_viz = MDAFileVisualization(self)
        layout = self.viz_groupbox.layout()
        layout.addWidget(self.mda_file_viz)

        # Initialize attributes:
        self.setSelectionField()
        self.setSelectionModel()
        self.setCurrentFileTableview()

        # File Selection Model & Focus for keyboard arrow keys:
        model = self.mda_folder_tableview.tableView.model()
        if model is not None and len(self.mdaFileList()) > 0:
            self.mda_folder_tableview.tableView.setFocus()
            selection_model = self.mda_folder_tableview.tableView.selectionModel()
            self.setSelectionModel(selection_model)

        # Folder table view signal/slot connections:
        self.mda_folder_tableview.tableView.doubleClicked.connect(self.doFileSelected)
        self.mda_folder_tableview.firstButton.clicked.connect(self.goToFirst)
        self.mda_folder_tableview.lastButton.clicked.connect(self.goToLast)
        self.mda_folder_tableview.backButton.clicked.connect(self.goToPrevious)
        self.mda_folder_tableview.nextButton.clicked.connect(self.goToNext)

        # MDAFile Tab connection:
        utils.reconnect(self.mda_file.tabChanged, self.onTabChanged)

        # MDAFile Push buttons connection:
        utils.reconnect(self.mda_file.buttonPushed, self.doPlot)

        # Debug signals:
        self.mda_folder_tableview.tableView.doubleClicked.connect(utils.debug_signal)
        self.mda_folder_tableview.firstButton.clicked.connect(utils.debug_signal)
        self.mda_folder_tableview.lastButton.clicked.connect(utils.debug_signal)
        self.mda_folder_tableview.backButton.clicked.connect(utils.debug_signal)
        self.mda_folder_tableview.nextButton.clicked.connect(utils.debug_signal)
        # self.mda_file.tabChanged(utils.debug_signal)
        # self.mda_file.buttonPushed(utils.debug_signal)

        # save/restore splitter sizes in application settings
        for key in "hsplitter vsplitter".split():
            splitter = getattr(self, key)
            sname = self.splitter_settings_name(key)
            settings.restoreSplitter(splitter, sname)
            splitter.splitterMoved.connect(partial(self.splitter_moved, key))

    # # ------------ set & get methods:

    def setSelectionModel(self, selection=None):
        """
        Sets the selection model for managing view selections.

        Args:
            selection (QItemSelectionModel, optional): The selection model to be associated with the view. Defaults to None.
        """

    def dataPath(self):
        """
        Retrieves the path of the currently selected data folder.

        Returns:
            str: The path to the data folder as determined by the folder +
            subfolder comboBoxes in the mainWindow.
        """
        return self.mainWindow.dataPath()

    def mdaFileList(self):
        """
        Fetches a list of MDA file names from the currently selected folder.

        Returns:
            list: A list of strings representing the names of MDA files in the selected folder.
        """
        return self.mainWindow.mdaFileList()

    def currentFileTableview(self):
        """
        Gets the current file TableView being displayed in the active tab.

        Returns:
            QTableView: The TableView widget associated with the currently selected MDA file.
        """
        return self._currentFileTableview

    def setCurrentFileTableview(self, tableview=None):
        """
        Sets the current file TableView to be displayed.

        Args:
            tableview (QTableView, optional): The TableView widget to be set as
            the current file TableView. Defaults to None.
        """
        self._currentFileTableview = tableview

    def selectionModel(self):
        """
        Accesses the selection model of the view (e.g. MDAFolderTableView)
        managing the selection state.

        Returns:
            QItemSelectionModel: The selection model associated with a view,
            managing which rows/items are selected.
        """
        return self._selection_model

    def setSelectionModel(self, selection=None):
        """
        Sets the selection model for managing view selections.

        Args:
            selection (QItemSelectionModel, optional): The selection model to be
            associated with the view. Defaults to None.
        """
        self._selection_model = selection

    # # ------------ Folder table view methods:

    def updateFolderView(self):
        """Clear existing data and set new data for the folder tableview"""
        self.mda_folder_tableview.clearContents()
        self.mda_folder_tableview.displayTable()

    def doRefresh(self):
        """
        Refreshes the file list in the currently selected folder
        - Re-fetch the list of MDA files in the current folder.
        - Display the updated file list in the MDA folder table view.
        """
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
        Retrieves the current field selection for plotting.
        - Returns a dictionary with selected positioner and detectors indices.
        - Format: {'X': positioner_index, 'Y': [detector_indices]}.
        - Returns None if no selection is made.
        """
        return self._selection_field

    def setSelectionField(self, new_selection=None):
        """
        Updates the current field selection for plotting.
        - Accepts a dictionary specifying new selection of positioner and detectors.
        - Resets to None if given an empty dictionary.
        - Format for new_selection: {'X': positioner_index, 'Y': [detector_indices]}.
        """
        self._selection_field = new_selection if new_selection != {} else None

    def applySelectionChanges(self, new_selection):
        """
        Applies changes to the field selection and updates checkboxes accordingly:
        - Updates the selection field with the new selection.
        - Updates checkboxes in the current file's table view based on the new selection.
        """
        tableview = self.currentFileTableview()
        self.setSelectionField(new_selection)
        tableview.tableView.model().updateCheckboxes(
            utils.mda2ftm(new_selection), update_mda_mvc=False
        )

    def updateSelectionForNewPVs(
        self, old_selection, oldPvList, newPvList, verbose=False
    ):
        """
        Updates field selection based on new PV list when a new file is selected.
        - Adjusts selection indices for POS and DET to match new PVs indexes.
        - Directly updates the selection field if changes are made.

        Args:
            old_selection (dict): selection fields for the previously selected file.
            oldPvList (list): PVs in the previously selected file.
            newPvList (list): Matching PVs in the newly selected file.
            verbose (bool): If True, print detailed changes.

        Returns:
            None: Updates the selection field directly if changes are made.
        """
        if not old_selection:
            print("No previous selection.")
            return

        if verbose:
            print(f"\n----- Selection before clean up: {old_selection}")
        changes_made = False
        tableview = self.currentFileTableview()
        new_selection = {"Y": [], "X": None}
        # Update Y selections: if either left operand or right operand is True, result will be True.
        changes_made |= self.updateDetectorSelection(
            oldPvList, old_selection, newPvList, new_selection, verbose
        )
        # Update X selection and check for changes: if X was 0 or None, set to 0; if not, set to 1st POS
        old_idx = old_selection.get("X")
        if old_idx:
            new_idx = tableview.data()["fileInfo"]["firstPos"]
        else:
            new_idx = 0
        if old_idx != new_idx:
            changes_made = True
            if verbose:
                print(
                    f"POS <{oldPvList[old_idx]}> changed from {old_idx} to {new_idx} <{newPvList[new_idx]}>"
                )
        if changes_made:
            self.applySelectionChanges(new_selection)
        if verbose:
            print(f"----- Selection After clean up: {self.selectionField()}\n")

    def updateDetectorSelection(
        self, oldPvList, old_selection, newPvList, new_selection, verbose
    ):
        """
        Helper function to update detector selections in the new selection field.
        - Iterates through old detector selections and updates based on new PVs.
        - Adds updated detector indices to new_selection['Y'].
        - Returns True if changes were made, otherwise False.
        """
        changes_made = False
        for old_index in old_selection.get("Y", []):
            if old_index < len(oldPvList):
                old_pv = oldPvList[old_index]
                if old_pv in newPvList:
                    new_index = newPvList.index(old_pv)
                    new_selection["Y"].append(new_index)
                    if new_index != old_index:
                        changes_made = True
                        if verbose:
                            print(
                                f"DET <{old_pv}> changed from {old_index} to {new_index}"
                            )
                else:
                    changes_made = True
                    if verbose:
                        print(f"DET <{old_pv}> was removed")
        return changes_made

    # # ------------ File selection methods:

    def doFileSelected(self, index, verbose=True):
        """
        - Handles the selection of a new file in the folder table view.
        - Updates the UI to:
            - Add a tab with the selected file content in a table view.
            - Display the data for the selected file.
            - Display the metadata for the selected file.
        - Manages connections for:
            - Selection changes in the folder table view.
            - Checkbox state changes in the file's data view.
        - Initiates plotting based on the current mode, which can be:
            - Auto-add: Automatically adds new data to the existing plot.
            - Auto-replace: Automatically replaces the existing plot with new data.
            - Auto-off: Does not automatically plot new data; requires manual action to plot.

        This method ensures the selection of positioners and detectors reflects the PVs available
        in the newly selected file, accounting for  index changes from the previously selected file.
            - addFileTab -> tabWidget.setCurrentIndex updates -> onTabChanged triggered
                         -> setCurrentFileTableview()
                         -> updateSelectionField() (if selectionField was None only)
                         -> mda_file.setData()
                         -> mda_file.displayMetadata(metadata)
                         -> mda_file.displayData(tabledata)
        Args:
            index (QModelIndex): The model index of the selected file in the file list.
        """
        selected_file = self.mdaFileList()[index.row()]
        self.setStatus(f"\n\n========= {selected_file} in {str(self.dataPath())}")

        # If there is no Folder Table View, do nothing
        if self.mda_folder_tableview.tableView.model() is None:
            return

        # If no tabs are open, oldPvList should be None:
        if self.mda_file.tabWidget.count() == 0:
            old_pv_list = None
        # otherwise, store the previous selection and PV list:
        else:
            old_tab_tableview = self.currentFileTableview()
            old_pv_list = old_tab_tableview.data()["fileInfo"]["pvList"]
            old_selection = self.selectionField()

        # Add (or replace) a tab & update selectionField() to default if it was None:
        self.mda_file.addFileTab(index.row(), self.selectionField())
        new_pv_list = self.mda_file.data().get("pvList")
        new_tab_tableview = self.currentFileTableview()
        # Manage signal connections for the new file selection.
        utils.reconnect(
            new_tab_tableview.tableView.model().checkboxStateChanged,
            self.onCheckboxStateChange,
        )
        # selectionField() may have changed when calling addFileTab
        if self.selectionField():
            if old_pv_list is not None:
                self.updateSelectionForNewPVs(
                    old_selection, old_pv_list, new_pv_list, verbose
                )
            self.handlePlotBasedOnMode()
        else:
            self.setStatus("Could not find a (positioner,detector) pair to plot.")

    # # ------------ Plot methods:

    def handlePlotBasedOnMode(self):
        """Handle plotting based on the current mode (add, replace, or auto-off)."""
        mode = self.mda_file.mode()
        if mode == "Auto-add":
            self.doPlot("add")
        elif mode == "Auto-replace":
            self.doPlot("replace")
        else:
            self.setStatus("Mode is set to Auto-off")

    def doPlot(self, *args, **kwargs):
        """
        Initiates plotting based on the currently selected file & selection field, and the specified action
        ('add', 'replace', or 'clear').
        - Retrieves and plots datasets based on the selection for actions 'add' or 'replace'.
        - Uses a ChartView widget for plotting within a specified layout.

        Parameters:
        - args[0] (str): The plotting action to be taken ('add', 'replace', or 'clear').
        - kwargs (dict): Additional options for plotting, if any.

        Behavior:
        - 'clear': Removes all tabs and clears the visualization.
        - 'add'/'replace': Plots new data according to the current selection, adding to existing plots or replacing them.
        - Exits with a status message if no file is selected or no detectors (Y) are selected for plotting.
        """

        from .chartview import ChartView

        action = args[0]
        tableview = self.currentFileTableview()
        selection = self.selectionField()

        # Clear all content from the file table view & viz panel:
        if action in ("clear"):
            print("\n\nPushButton Clear...")
            self.mda_file.removeAllFileTabs()
            return

        # If there is no file selected (ie no tableview) or no DET:
        if not tableview or not selection.get("Y"):
            self.setStatus("Nothing to plot.")
            return

        print(f"\ndoPlot called: {action=}, {selection=}")

        # Get the matplotlib chartview widget, if exists:
        layoutMpl = self.mda_file_viz.plotPageMpl.layout()
        if layoutMpl.count() != 1:  # in case something changes ...
            raise RuntimeError("Expected exactly one widget in this layout!")
        widgetMpl = layoutMpl.itemAt(0).widget()

        if action in ("replace", "add"):
            # Get dataset for the positioner/detector selection:
            datasets, plot_options = tableview.data2Plot(selection)
            y_index = selection.get("Y", [])
            if not isinstance(widgetMpl, ChartView):  # Make a blank chart.
                widgetMpl = ChartView(self, **plot_options)
            if action in ("replace"):
                widgetMpl.curveManager.removeAllCurves()
            for i, (ds, ds_options) in zip(y_index, datasets):
                # ds: [x_data, y_data]
                # ds_options: {"label":y_label} (for legend)
                # plot_options: {"x" (label), "x_unit", "y" (label), "y_unit", "title", "folderPath"}
                options = {"ds_options": ds_options, "plot_options": plot_options}
                widgetMpl.plot(i, *ds, **options)
            self.mda_file_viz.setPlot(widgetMpl)

    def onTabChanged(self, index, file_path, file_data, selection_field):
        """
        Updates UI to reflect the content of the newly selected tab or resets UI if no tab is selected.
        - Activates the corresponding table view for the new tab, displaying the selected file's metadata and data.
        - Resets UI to a default state if no tab is selected (index == -1), indicating no active file.
        - Connected to the `tabChanged` signal to handle UI updates when a tab is switched.

        Parameters:
        - index (int): Index of the newly selected tab; -1 indicates no tab is selected.
        - file_path (str): Path of the file associated with the newly selected tab.
        - file_data (dict): Contains metadata and table data for the file. Expected keys: 'metadata', 'tabledata'.
        - selection_field (dict or None): Specifies the fields (POS/DET) selected for plotting.

        Notes: This method is connected to the `tabChanged` signal of the MDAFile's QTabWidget:
        In MDAFile:
            self.mda_file.tabWidget.currentChanged.connect [signal: emits new_tab_index]
                --> self.mda_file.onSwitchTab(new_tab_index) [slot]
                    --> self.mda_file.tabChanged.emit  [QtCore.pyqtSignal]
                        emits: new_tab_index, _file_path, _tab_data, _selection_field
        In MDA_MVC:
            self.mda_file.tabChanged.connect
                --> self.onTabChanged(new_tab_index, _file_path, _tab_data, _selection_field)
        """

        if index == -1:
            self.setCurrentFileTableview()  # Reset to indicate no active file table view
            self.setSelectionField()  # Reset selection field to default
            print("No file currently selected.")
            return

        # Retrieve the table view for the currently selected tab:
        new_tab_tableview = self.mda_file.tabIndex2Tableview(index)
        self.setCurrentFileTableview(new_tab_tableview)
        self.setSelectionField(selection_field)

        # Fetch and display the metadata and data associated with the file path
        if file_data:
            print(f"Displaying data and metadata for {Path(file_path).name}.")
            self.mda_file.displayMetadata(file_data.get("metadata", None))
            self.mda_file.displayData(file_data.get("tabledata", None))

        # TODO - check:  disable UI elements or actions that require an active file to be meaningful: Add, replace...
        # TODO - check:  disable UI elements or actions that require an active Folder to be meaningful: GoTo...

    # # ------------ Folder Table View navigation & selection highlight:

    def goToFirst(self):
        """
        Navigates to and selects the first file in the folder table view.
        """
        model = self.mda_folder_tableview.tableView.model()
        if model is not None and model.rowCount() > 0:
            firstIndex = model.index(0, 0)
            self.selectAndShowIndex(firstIndex)

    def goToLast(self):
        """
        Navigates to and selects the last file in the folder table view.
        """
        model = self.mda_folder_tableview.tableView.model()
        if model is not None and model.rowCount() > 0:
            lastIndex = model.index(model.rowCount() - 1, 0)
            self.selectAndShowIndex(lastIndex)

    def goToNext(self):
        """
        Navigates to and selects the next file relative to the current selection in the folder table view.
        """
        try:
            if self.mdaFileList() and self.selectionModel():
                currentIndex = self.selectionModel().currentIndex()
                nextIndex = currentIndex.sibling(
                    currentIndex.row() + 1, currentIndex.column()
                )
                if nextIndex.isValid():
                    self.selectAndShowIndex(nextIndex)
        except RuntimeError as e:
            print("The selection model is no longer valid:", e)

    def goToPrevious(self):
        """
        Navigates to and selects the previous file relative to the current selection in the folder table view.
        """
        try:
            if self.mdaFileList() and self.selectionModel():
                currentIndex = self.selectionModel().currentIndex()
                prevIndex = currentIndex.sibling(
                    currentIndex.row() - 1, currentIndex.column()
                )
                if prevIndex.isValid():
                    self.selectAndShowIndex(prevIndex)
        except RuntimeError as e:
            print("The selection model is no longer valid:", e)

    def selectAndShowIndex(self, index):
        """
        Selects a file by its index in the folder table view and ensures it is visible to the user.

        Parameters:
        - index (QModelIndex): Index of the file to select.

        Details:
        - Focuses on the table view for visual feedback (blue highlight in Mac OS).
        - Adjusts scroll position based on the file's position in the list.
        - Trigger actions associated with file selection (doFileSelected).
        """
        # Ensure the table view has focus:
        self.mda_folder_tableview.tableView.setFocus()
        # Determine the appropriate scrollHint based on the row position:
        model = self.mda_folder_tableview.tableView.model()
        rowCount = model.rowCount()
        scrollHint = QAbstractItemView.EnsureVisible
        if index.row() == 0:
            scrollHint = QAbstractItemView.PositionAtTop
        elif index.row() == rowCount - 1:
            scrollHint = QAbstractItemView.PositionAtBottom
        # Select the row and ensure it's visible:
        self.selectionModel().setCurrentIndex(
            index, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows
        )
        self.mda_folder_tableview.tableView.scrollTo(index, scrollHint)
        # Trigger actions associated with file selection
        self.doFileSelected(index)

    # # ------------ Checkbox methods:

    def onCheckboxStateChange(self, selection):
        """TODO: write docstring: Slot: data field (for plotting) changes."""
        from .chartview import ChartView

        # TODO - check: do I need a flag here to prevent "onCheckboxChange" to apply
        # when selecting a new file: selecting a new file triggers it since
        # the checkbox status might changes (if set to default 1st POS 1st DET).

        tableview = self.currentFileTableview()
        previous_selection = self.selectionField()

        # Get the matplotlib chartview widget, if exists:
        layoutMpl = self.mda_file_viz.plotPageMpl.layout()
        if layoutMpl.count() != 1:  # in case something changes ...
            raise RuntimeError("Expected exactly one widget in this layout!")
        widgetMpl = layoutMpl.itemAt(0).widget()

        mode = self.mda_file.mode()

        # Exceptions:
        if not selection.get("Y"):  # if no DET: clear plot
            # TODO: if in auto-add, don;t clear the plot,
            # just remove the curve - there could be plot from other tableviews
            # widgetMpl.curveManager.removeAllCurves() #doNotClearCheckboxes = True or False
            return
        if not selection.get("X"):  # if no POS: default to index
            widgetMpl.clearPlot()
            selection["X"] = 0
            tableview.tableView.model().checkCheckBox(0, "X")

        # if previous_selection:   # TODO This needs to be changed, not that simple
        #     # if changing POS, clear the graph:
        #     if previous_selection.get("X") != selection.get("X"):
        #         widgetMpl.curveManager.removeAllCurves() #doNotClearCheckboxes = True or False

        #     # if removing DET, clear the graph:
        #     if len(previous_selection.get("Y")) > len(selection.get("Y")):
        #         widgetMpl.curveManager.removeAllCurves() #doNotClearCheckboxes = True or False

        #     # BUG - that is weird, why? only should clear if there is no Y left
        #     # that is the behavior that I observe in Auto-Replace
        #     # in Auto-Add, should remove it from the graph but it doesn't
        #     # if there are curve from a different folder or file, that will be a problem
        #     # lots of stuff to fix here

        # Get dataset for the positioner/detector selection:
        self.setSelectionField(selection)
        datasets, plot_options = tableview.data2Plot(self.selectionField())

        y_rows = selection.get("Y", [])
        if mode in ("Auto-replace", "Auto-add"):
            if not isinstance(widgetMpl, ChartView):
                widgetMpl = ChartView(self, **plot_options)  # Make a blank chart.
            if mode in ("Auto-replace"):
                widgetMpl.curveManager.removeAllCurves()
            for row, (ds, ds_options) in zip(y_rows, datasets):
                # ds_options: label (for legend)
                # plot_options: xlabel, ylabel, title
                options = {"ds_options": ds_options, "plot_options": plot_options}
                widgetMpl.plot(row, *ds, **options)
            self.mda_file_viz.setPlot(widgetMpl)

        elif mode in ("Auto-off"):
            return

    # # ------------ splitter methods

    def splitter_moved(self, key, *arg, **kwargs):
        """
        Handles a splitter's movement by initiating a delay before updating the settings.
        - Sets a deadline for changes and starts a new thread if one isn't already monitoring changes.
        - Ensures settings are updated only after movement has ceased for a defined interval.

        Parameters:
        - key (str): Identifier for the splitter ('hsplitter' or 'vsplitter').
        """
        thread = getattr(self, f"{key}_wait_thread", None)
        setattr(self, f"{key}_deadline", time.time() + self.motion_wait_time)
        if thread is None or not thread.is_alive():
            self.setStatus(f"Start new thread now.  {key=}")
            setattr(self, f"{key}_wait_thread", self.splitter_wait_changes(key))

    def splitter_settings_name(self, key):
        """
        Generates a unique settings name for the given splitter.
        - Formats the name based on the class name and splitter identifier.

        Parameters:
        - key (str): Identifier for the splitter.

        Returns:
        - str: A unique name for storing splitter settings.
        """
        return f"{self.__class__.__name__.lower()}_{key}"

    @utils.run_in_thread
    def splitter_wait_changes(self, key):
        """
        Monitors splitter movement and updates settings after movement ceases.
        - Waits until there have been no changes to the splitter position for a set interval.
        - Updates application settings with the new splitter sizes.

        Parameters:
        - key (str): Identifier for the splitter being monitored '(hsplitter' or 'vsplitter')
        """
        from .user_settings import settings

        splitter = getattr(self, key)
        while time.time() < getattr(self, f"{key}_deadline"):
            time.sleep(self.motion_wait_time * 0.1)

        sname = self.splitter_settings_name(key)
        self.setStatus(f"Update settings: {sname=} {splitter.sizes()=}")
        settings.saveSplitter(splitter, sname)

    # # ------------ Status method

    def setStatus(self, text):
        """
        Updates the application's status bar with the provided message.
        """
        self.mainWindow.setStatus(text)
