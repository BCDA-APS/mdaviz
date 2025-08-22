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
        - onFileSelected: Handles user selection of MDA files, updating UI and initiating data plotting.
        - doPlot: Initiates data plotting based on user selections and current plot mode. It checks for the
        selected positioner and detectors, retrieves the corresponding data, and plots it in the visualization panel.
        - onCheckboxStateChanged: Responds to user changes in checkbox states within the MDA file table,
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
        |___> onFileSelected
            |___> Update UI (Tabs, Metadata, Data Display)
            |___> doPlot (Based on current mode and selections)
                |___> Retrieve and plot data based on selected positioner and detectors

        Checkbox State Change in File View
        |___> onCheckboxStateChanged
            |___> doPlot (Replot based on new selections)
                |___> Retrieve and plot data based on selected positioner and detectors
"""

import time
from functools import partial
from pathlib import Path

from PyQt6 import QtCore
from PyQt6.QtCore import QItemSelectionModel, Qt, pyqtSignal
from PyQt6.QtWidgets import QAbstractItemView, QWidget

from mdaviz import utils
from mdaviz.logger import get_logger

# Get logger for this module
logger = get_logger("mda_folder")


class MDA_MVC(QWidget):
    """Model View Controller class for mda files."""

    # DESIGN NOTE: Should this signal be emitted here or in MDA_FILE_TM? Review if refactoring signal emission logic.
    detRemoved = pyqtSignal(
        str, int
    )  # Emit the file path and row when a DET checkbox is unchecked

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
        from mdaviz.user_settings import settings
        from mdaviz.mda_folder_table_view import MDAFolderTableView
        from mdaviz.mda_file_viz import MDAFileVisualization
        from mdaviz.mda_file import MDAFile

        # Folders table view:
        self.mda_folder_tableview = MDAFolderTableView(self)
        layout = self.folder_groupbox.layout()
        layout.addWidget(self.mda_folder_tableview)
        self.mda_folder_tableview.displayTable()

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

        # Set Selection Model & Focus for keyboard arrow keys to Folder Table View:
        model = self.mda_folder_tableview.tableView.model()
        if model is not None and len(self.mdaFileList()) > 0:
            self.mda_folder_tableview.tableView.setFocus()
            selection_model = self.mda_folder_tableview.tableView.selectionModel()
            self.setSelectionModel(selection_model)
        # Ensure focus policy and selection mode for keyboard navigation
        self.mda_folder_tableview.tableView.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.mda_folder_tableview.tableView.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.mda_folder_tableview.tableView.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        # Folder table view signal/slot connections:
        self.mda_folder_tableview.tableView.doubleClicked.connect(self.onFileSelected)
        self.mda_folder_tableview.tableView.clicked.connect(self.onFileSelected)
        self.mda_folder_tableview.firstButton.clicked.connect(self.goToFirst)
        self.mda_folder_tableview.lastButton.clicked.connect(self.goToLast)
        self.mda_folder_tableview.backButton.clicked.connect(self.goToPrevious)
        self.mda_folder_tableview.nextButton.clicked.connect(self.goToNext)
        if self.selectionModel():
            utils.reconnect(self.selectionModel().currentChanged, self.onFileSelected)

        # MDAFile Tab connection:
        utils.reconnect(self.mda_file.tabChanged, self.onTabChanged)

        # MDAFile Push buttons connection:
        utils.reconnect(self.mda_file.buttonPushed, self.doPlot)

        # MDAFile X2 value changes connection:
        utils.reconnect(self.mda_file.x2ValueChanged, self.doPlot)

        # Debug signals:
        # self.mda_folder_tableview.tableView.doubleClicked.connect(utils.debug_signal)
        # self.mda_folder_tableview.firstButton.clicked.connect(utils.debug_signal)
        # self.mda_folder_tableview.lastButton.clicked.connect(utils.debug_signal)
        # self.mda_folder_tableview.backButton.clicked.connect(utils.debug_signal)
        # self.mda_folder_tableview.nextButton.clicked.connect(utils.debug_signal)

        # save/restore splitter sizes in application settings
        for key in "hsplitter vsplitter".split():
            splitter = getattr(self, key)
            sname = self.splitter_settings_name(key)
            settings.restoreSplitter(splitter, sname)
            splitter.splitterMoved.connect(partial(self.splitter_moved, key))

    # # ------------ set & get methods:

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

    def mdaInfoList(self):
        """
        Fetches a list of MDA file info from the currently selected folder.

        Returns:
            list: A list of dictionary containing the high level info for the MDA files in the selected folder.
        """
        return self.mainWindow.mdaInfoList()

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
        model = self.mda_folder_tableview.tableView.model()
        if model is not None and len(self.mdaFileList()) > 0:
            self.mda_folder_tableview.tableView.setFocus()
            selection_model = self.mda_folder_tableview.tableView.selectionModel()
            self.setSelectionModel(selection_model)
            utils.reconnect(self.selectionModel().currentChanged, self.onFileSelected)

    # # ------------ Fields selection methods:

    def selectionField(self):
        """
        Retrieves the current field selection for plotting.
        - Returns a dictionary with selected positioner, detectors, and I0 indices.
        - Format: {'X': positioner_index, 'Y': [detector_indices], 'I0': i0_index}.
        - Returns None if no selection is made.
        """
        return self._selection_field

    def setSelectionField(self, new_selection=None):
        """
        Updates the current field selection for plotting.
        - Accepts a dictionary specifying new selection of positioner, detectors, and I0.
        - Resets to None if given an empty dictionary.
        - Format for new_selection: {'X': positioner_index, 'Y': [detector_indices], 'I0': i0_index}.
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
        - Adjusts selection indices for POS, DET, and I0 to match new PVs indexes.
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
            logger.debug("No previous selection.")
            return

        if verbose:
            logger.debug(f"\n----- Selection before clean up: {old_selection}")
        changes_made = False
        tableview = self.currentFileTableview()
        new_selection = {"Y": [], "X": 0}
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
            new_selection["X"] = new_idx

        # Update I0 selection and check for changes
        old_i0_idx = old_selection.get("I0")
        if old_i0_idx is not None:
            if old_i0_idx < len(oldPvList):
                old_i0_pv = oldPvList[old_i0_idx]
                if old_i0_pv in newPvList:
                    new_i0_idx = newPvList.index(old_i0_pv)
                    new_selection["I0"] = new_i0_idx
                    if new_i0_idx != old_i0_idx:
                        changes_made = True
                        if verbose:
                            logger.debug(
                                f"I0 <{old_i0_pv}> changed from {old_i0_idx} to {new_i0_idx}"
                            )
                else:
                    changes_made = True
                    if verbose:
                        logger.debug(
                            f"I0 <{old_i0_pv}> was removed - auto-unchecking I0"
                        )
                    # I0 PV doesn't exist in new file, so uncheck the I0 checkbox
                    tableview.tableView.model().uncheckCheckBox(old_i0_idx)
            else:
                changes_made = True
                if verbose:
                    logger.debug(
                        f"I0 index {old_i0_idx} out of range - auto-unchecking I0"
                    )
                # I0 index was invalid, so uncheck the I0 checkbox
                tableview.tableView.model().uncheckCheckBox(old_i0_idx)

        if changes_made:
            self.applySelectionChanges(new_selection)
        if verbose:
            logger.debug(f"----- Selection After clean up: {self.selectionField()}\n")

    def updateDetectorSelection(
        self, oldPvList, old_selection, newPvList, new_selection, verbose=False
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
                            logger.debug(
                                f"DET <{old_pv}> changed from {old_index} to {new_index}"
                            )
                else:
                    changes_made = True
                    if verbose:
                        logger.debug(f"DET <{old_pv}> was removed")
        return changes_made

    # # ------------ File selection methods:

    def onFileSelected(self, index, verbose=False):
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
        file_path = f"{str(self.dataPath())}/{selected_file}"
        self.setStatus(f"\nLoading {file_path}")

        # Ensures the table view scrolls to the selected item.
        if isinstance(index, QtCore.QModelIndex):
            self.mda_folder_tableview.tableView.scrollTo(index)

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
            self.onCheckboxStateChanged,
        )
        # selectionField() may have changed when calling addFileTab
        if self.selectionField():
            if old_pv_list is not None:
                try:
                    self.updateSelectionForNewPVs(
                        old_selection, old_pv_list, new_pv_list, verbose=False
                    )
                except Exception as exc:
                    logger.error(str(exc))

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
        - args[0] (str or int): The plotting action to be taken ('add', 'replace', or 'clear'),
          or an integer representing the X2 value change.
        - kwargs (dict): Additional options for plotting, if any.

        Behavior:
        - 'clear': Removes all tabs and clears the visualization.
        - 'add'/'replace': Plots new data according to the current selection, adding to existing plots or replacing them.
        - X2 value change: Replots the current selection with the new X2 slice.
        - Exits with a status message if no file is selected or no detectors (Y) are selected for plotting.
        """

        from mdaviz.chartview import ChartView

        # Handle X2 value changes
        if isinstance(args[0], int):
            # This is an X2 value change, respect the current mode
            mode = self.mda_file.mode()
            if mode == "Auto-add":
                action = "add"
            elif mode == "Auto-off":
                # Do nothing in auto-off mode - user must manually add/replace
                logger.debug(
                    f"\ndoPlot called for X2 value change: X2={args[0]}, mode={mode}, action=ignore"
                )
                return
            else:
                action = "replace"  # Default for Auto-replace
            logger.debug(
                f"\ndoPlot called for X2 value change: X2={args[0]}, mode={mode}, action={action}"
            )
        else:
            action = args[0]
            logger.debug(f"\ndoPlot called: action={action}")

        tableview = self.currentFileTableview()

        # Check if this is a 2D selection (has X1, X2 keys)
        is_2d_selection = (
            len(args) > 1
            and isinstance(args[1], dict)
            and "X1" in args[1]
            and "X2" in args[1]
        )
        logger.debug(f"doPlot - is_2d_selection: {is_2d_selection}")

        if is_2d_selection:
            # Handle 2D plotting - use the passed selection
            selection = args[1]
            logger.debug("doPlot - Handling 2D plotting")
            self._doPlot2D(action, selection)
            return

        # For 1D plotting, use the selection from the table view
        selection = self.selectionField()

        # Clear all content from the file table view & viz panel:
        if action in ("clear"):
            logger.debug("\n\nPushButton Clear...")
            self.mda_file.removeAllFileTabs()
            return

        # If there is no file selected (ie no tableview) or no selection or no DET:
        if not tableview or not selection or not selection.get("Y"):
            self.setStatus("Nothing to plot.")
            return

        logger.debug(f"\ndoPlot called: {action=}, {selection=}")

        # Handle 1D plotting (existing logic)
        # Get the matplotlib chartview widget, if exists:
        layoutMpl = self.mda_file_viz.plotPageMpl.layout()
        if layoutMpl.count() != 1:  # in case something changes ...
            raise RuntimeError("Expected exactly one widget in this layout!")
        widgetMpl = layoutMpl.itemAt(0).widget()

        if action in ("replace", "add"):
            # Get dataset for the positioner/detector selection:
            datasets, plot_options = tableview.data2Plot(selection)
            logger.debug(f"doPlot - Received plot_options: {plot_options}")
            y_index = selection.get("Y", [])
            if not isinstance(widgetMpl, ChartView):  # Make a blank chart.
                widgetMpl = ChartView(self, **plot_options)
                # Connect fit signals to main window
                if hasattr(self.mainWindow, "connectToFitSignals"):
                    self.mainWindow.connectToFitSignals(widgetMpl)

                # Apply stored log scale state to the new chart
                if hasattr(self.mda_file_viz, "getLogScaleState"):
                    stored_log_x, stored_log_y = self.mda_file_viz.getLogScaleState()
                    widgetMpl.setLogScales(stored_log_x, stored_log_y)

            if action in ("replace"):
                widgetMpl.curveManager.removeAllCurves()
            for i, (ds, ds_options) in zip(y_index, datasets):
                # ds: [x_data, y_data]
                # ds_options: {"label":y_label} (for legend)
                # plot_options: {"x" (label), "x_unit", "y" (label), "y_unit", "title", "folderPath"}
                options = {"ds_options": ds_options, "plot_options": plot_options}
                # Add X2 index to options if available
                if "x2_index" in plot_options:
                    options["x2_index"] = plot_options["x2_index"]
                    logger.debug(
                        f"doPlot - Passing x2_index: {plot_options['x2_index']}"
                    )
                else:
                    logger.debug("doPlot - No x2_index in plot_options")
                widgetMpl.plot(i, *ds, **options)
            self.mda_file_viz.setPlot(widgetMpl)

    def _doPlot2D(self, action, selection):
        """
        Handle 2D plotting with the given selection.

        Parameters:
            action (str): 'add' or 'replace'
            selection (dict): 2D selection with X1, X2, Y, I0, plot_type keys
        """
        logger.debug(f"_doPlot2D - action: {action}, selection: {selection}")

        tableview = self.currentFileTableview()
        if not tableview:
            logger.debug("_doPlot2D - No tableview available")
            return

        # Convert 2D selection to 1D format for data2Plot2D
        # data2Plot2D expects: {'X': x_index, 'Y': [y_indices], 'I0': i0_index}
        converted_selection = {
            "X": selection.get("X1"),
            "Y": selection.get("Y", []),
            "I0": selection.get("I0"),
            "log_y": selection.get("log_y", False),
        }

        logger.debug(f"_doPlot2D - Converted selection: {converted_selection}")

        # Get 2D data and plot options
        try:
            datasets, plot_options = tableview.data2Plot2D(converted_selection)
            logger.debug(
                f"_doPlot2D - Got datasets: {len(datasets)}, plot_options: {plot_options}"
            )

            # Update the 2D plot in the 2D tab
            self.mda_file_viz.update2DPlot()

            # Set the plot type in the 2D chart view
            plot_type = selection.get("plot_type", "heatmap")
            if (
                hasattr(self.mda_file_viz, "widgetMpl2D")
                and self.mda_file_viz.widgetMpl2D
            ):
                self.mda_file_viz.widgetMpl2D.set_plot_type(plot_type)
                logger.debug(f"_doPlot2D - Set plot type to: {plot_type}")

        except Exception as e:
            logger.debug(f"_doPlot2D - Error: {e}")
            self.setStatus(f"Error plotting 2D data: {e}")

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
                --> self.mda_file.updateCurrentTabInfo(new_tab_index) [slot]
                    --> self.mda_file.tabChanged.emit  [QtCore.pyqtSignal]
                        emits: new_tab_index, _file_path, _tab_data, _selection_field
        In MDA_MVC:
            self.mda_file.tabChanged.connect
                --> self.onTabChanged(new_tab_index, _file_path, _tab_data, _selection_field)
        """

        if index == -1:
            self.setCurrentFileTableview()  # Reset to indicate no active file table view
            self.setSelectionField()  # Reset selection field to default
            return

        # Retrieve the table view for the currently selected tab:
        new_tab_tableview = self.mda_file.tabIndex2Tableview(index)
        self.setCurrentFileTableview(new_tab_tableview)
        self.setSelectionField(selection_field)

        # Fetch and display the metadata and data associated with the file path
        if file_data:
            logger.debug(f"Displaying data and metadata for {Path(file_path).name}.")
            self.mda_file.displayMetadata(file_data.get("metadata", None))
            # Reconstruct full data structure for 2D support by setting data again
            # This ensures we have scanDict, scanDict2D, isMultidimensional, etc.
            if file_path:
                # Find the file index in the current folder
                try:
                    file_name = Path(file_path).name
                    file_index = self.mdaFileList().index(file_name)
                    # Set the data again to get the full structure
                    self.mda_file.setData(file_index)
                    # Now display the full data structure
                    self.mda_file.displayData(self.mda_file.data())
                except ValueError:
                    # File not found in current folder, use fallback
                    self.mda_file.displayData(file_data)

        # Highlight the corresponding file in the folder table view if it belongs to the current folder
        if file_path:
            file_name = Path(file_path).name
            current_folder_path = str(self.dataPath())

            # Check if the file belongs to the currently loaded folder
            if file_path.startswith(current_folder_path):
                try:
                    # Find the index of the file in the current folder's file list
                    file_index = self.mdaFileList().index(file_name)

                    # Get the model and create the index
                    model = self.mda_folder_tableview.tableView.model()
                    if model and file_index < model.rowCount():
                        index = model.index(file_index, 0)

                        # Temporarily disconnect the currentChanged signal to avoid triggering onFileSelected
                        if self.selectionModel():
                            self.selectionModel().currentChanged.disconnect(
                                self.onFileSelected
                            )

                        # Highlight the file in the folder table view
                        self.mda_folder_tableview.tableView.setFocus()
                        self.selectionModel().setCurrentIndex(
                            index,
                            QItemSelectionModel.SelectionFlag.ClearAndSelect
                            | QItemSelectionModel.SelectionFlag.Rows,
                        )
                        self.mda_folder_tableview.tableView.scrollTo(
                            index, QAbstractItemView.ScrollHint.EnsureVisible
                        )

                        # Reconnect the currentChanged signal
                        if self.selectionModel():
                            self.selectionModel().currentChanged.connect(
                                self.onFileSelected
                            )

                except ValueError:
                    # File not found in the current folder's file list, ignore
                    pass

        # NOTE: Consider disabling UI elements or actions that require an active file/folder to be meaningful.

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
            logger.error("The selection model is no longer valid:", e)

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
            logger.error("The selection model is no longer valid:", e)

    def selectAndShowIndex(self, index):
        """
        Selects a file by its index in the folder table view and ensures it is visible to the user.

        Parameters:
        - index (QModelIndex): Index of the file to select.

        Details:
        - Focuses on the table view for visual feedback (blue highlight in Mac OS).
        - Adjusts scroll position based on the file's position in the list.
        - Trigger actions associated with file selection (onFileSelected).
        """
        # Ensure the table view has focus:
        self.mda_folder_tableview.tableView.setFocus()
        # Determine the appropriate scrollHint based on the row position:
        model = self.mda_folder_tableview.tableView.model()
        rowCount = model.rowCount()
        scrollHint = QAbstractItemView.ScrollHint.EnsureVisible
        if index.row() == 0:
            scrollHint = QAbstractItemView.ScrollHint.PositionAtTop
        elif index.row() == rowCount - 1:
            scrollHint = QAbstractItemView.ScrollHint.PositionAtBottom
        # Select the row and ensure it's visible:
        self.selectionModel().setCurrentIndex(
            index,
            QItemSelectionModel.SelectionFlag.ClearAndSelect
            | QItemSelectionModel.SelectionFlag.Rows,
        )
        self.mda_folder_tableview.tableView.scrollTo(index, scrollHint)
        # Trigger actions associated with file selection
        self.onFileSelected(index)

    # # ------------ Checkbox methods:

    def onCheckboxStateChanged(self, selection, det_removed):
        """
        Responds to changes in checkbox states within the file's data view.
         - adjusts the plot based on the selection of detectors and I0.
         - updates the selection field with the new selection and initiates plotting based
         on the current mode (Auto-add, Auto-replace, or Auto-off).

        Parameters:
        - selection (dict): The current selection of detectors (Y), positioner (X), and I0 for plotting.
        - det_removed (bool): Indicates if a detector has been removed (unchecked).

        Notes:
        - The selection dict format: {'X': int, 'Y': list[int], 'I0': int}.
        - If 'Auto-off' mode is active, the method returns without updating the plot.
        - If no positioner is selected, default to Index.
        - If no detectors are selected or if all curves are removed, the plot is cleared.
        - If a detector is unchecked, the corresponding curve is removed from the plot.
        - If I0 is selected, Y data will be normalized as Y/I0.
        """

        from mdaviz.chartview import ChartView

        mode = self.mda_file.mode()
        tableview = self.currentFileTableview()
        new_y_selection = selection.get("Y", [])

        # Get the matplotlib chartview widget, if exists:
        layoutMpl = self.mda_file_viz.plotPageMpl.layout()
        if layoutMpl.count() != 1:  # in case something changes ...
            raise RuntimeError("Expected exactly one widget in this layout!")
        widgetMpl = layoutMpl.itemAt(0).widget()

        # ----------- Exceptions:

        # In auto-off mode: no synchronisation - user needs to push a button.
        if mode in ("Auto-off"):
            return

        # If no POS, default to index:
        if not selection or not selection.get("X"):
            selection = selection or {}
            selection["X"] = 0
            tableview.tableView.model().checkCheckBox(0, "X")

        # If no DET and there is only 1 tab open, clear the graph
        if not new_y_selection and self.mda_file.tabWidget.count() == 1:
            widgetMpl.curveManager.removeAllCurves()
            return

        # Handle detector removal - emit signals but don't return early
        if det_removed:
            for y in det_removed:
                tab_index = self.mda_file.tabWidget.currentIndex()
                file_path = self.mda_file.tabIndex2Path(tab_index)
                self.detRemoved.emit(file_path, y)

        # Get dataset for the positioner/detector selection:
        datasets, plot_options = tableview.data2Plot(selection)
        logger.debug(f"doPlot - Received plot_options: {plot_options}")

        if not isinstance(widgetMpl, ChartView):
            widgetMpl = ChartView(self, **plot_options)  # Make a blank chart.
            # Connect fit signals to main window
            if hasattr(self.mainWindow, "connectToFitSignals"):
                self.mainWindow.connectToFitSignals(widgetMpl)

            # Apply stored log scale state to the new chart
            if hasattr(self.mda_file_viz, "getLogScaleState"):
                stored_log_x, stored_log_y = self.mda_file_viz.getLogScaleState()
                widgetMpl.setLogScales(stored_log_x, stored_log_y)

        if mode in ("Auto-replace"):
            widgetMpl.curveManager.removeAllCurves()
        for row, (ds, ds_options) in zip(new_y_selection, datasets):
            # ds_options: label (for legend)
            # plot_options: xlabel, ylabel, title
            options = {"ds_options": ds_options, "plot_options": plot_options}
            # Add X2 index to options if available
            if "x2_index" in plot_options:
                options["x2_index"] = plot_options["x2_index"]
                logger.debug(f"doPlot - Passing x2_index: {plot_options['x2_index']}")
            else:
                logger.debug("doPlot - No x2_index in plot_options")
            widgetMpl.plot(row, *ds, **options)
        self.mda_file_viz.setPlot(widgetMpl)

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
        from mdaviz.user_settings import settings

        splitter = getattr(self, key)
        while time.time() < getattr(self, f"{key}_deadline"):
            time.sleep(self.motion_wait_time * 0.1)

        sname = self.splitter_settings_name(key)
        self.setStatus(f"Update settings: {sname=} {splitter.sizes()=}")
        settings.saveSplitter(splitter, sname)

    # # ------------ Status method

    def setStatus(self, text):
        """Set status text."""
        self.mainWindow.setStatus(text)

    def getCurrentFilePath(self):
        """Get the file path of the currently active tab."""
        try:
            # Get the current tab index
            current_index = self.mda_file.tabWidget.currentIndex()
            logger.debug(f"getCurrentFilePath - Current tab index: {current_index}")

            if current_index >= 0:
                # Get the file path directly from the tab manager using the current tab
                # We can get this from the current file tableview's data
                current_tableview = self.currentFileTableview()
                if current_tableview and hasattr(current_tableview, "data"):
                    file_info = current_tableview.data().get("fileInfo", {})
                    file_path = file_info.get("filePath")
                    if file_path:
                        logger.debug(
                            f"getCurrentFilePath - Found file path: {file_path}"
                        )
                        return file_path

                logger.debug(
                    "getCurrentFilePath - No file path found in current tableview"
                )
            return None
        except Exception as e:
            logger.debug(f"getCurrentFilePath - Error: {e}")
            return None

    def clearOtherTabs(self, keep_file_path):
        """Clear all tabs except the one with the specified file path."""
        try:
            logger.debug(
                f"clearOtherTabs - Starting with keep_file_path: {keep_file_path}"
            )

            # Get all file paths from tab manager
            all_file_paths = list(self.mda_file.tabManager.tabs().keys())
            logger.debug(f"clearOtherTabs - All file paths: {all_file_paths}")

            tabs_to_remove = []

            # Find file paths to remove (all except keep_file_path)
            for file_path in all_file_paths:
                if file_path != keep_file_path:
                    tabs_to_remove.append(file_path)
                    logger.debug(f"clearOtherTabs - Will remove: {file_path}")

            logger.debug(f"clearOtherTabs - Tabs to remove: {tabs_to_remove}")

            # Remove tabs using the tab manager
            for file_path in tabs_to_remove:
                logger.debug(f"clearOtherTabs - Removing tab: {file_path}")
                self.mda_file.tabManager.removeTab(file_path)

            logger.debug(
                f"clearOtherTabs - Removed {len(tabs_to_remove)} tabs, kept: {keep_file_path}"
            )
        except Exception as e:
            logger.debug(f"clearOtherTabs - Error: {e}")
