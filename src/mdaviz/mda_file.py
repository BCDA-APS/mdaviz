"""
Display content of the currently selected files.

.. autosummary::

    ~MDAFile
    ~tabManager

User: tabCloseRequested.connect (emit: index)

    --> onTabCloseRequested(index --> file_path)
    --> tabManager.removeTab(file_path)
    --> tabManager.tabRemoved.emit(file_path)
    --> onTabRemoved(file_path --> index)

User: clearButton.clicked (emit: no data)

    --> onClearAllTabsRequested()
    --> tabManager.removeAllTabs()
    --> tabManager.allTabsRemoved.emit()
    --> onAllTabsRemoved()
    --> removeAllFileTabs()



"""

from mdaviz.synApps_mdalib.mda import readMDA
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QAbstractItemView, QWidget
from PyQt6.QtCore import QObject
import yaml

from mdaviz import utils
from mdaviz.mda_file_table_view import MDAFileTableView
from mdaviz.data_cache import get_global_cache
from mdaviz.logger import get_logger

# Get logger for this module
logger = get_logger("mda_file")


class MDAFile(QWidget):
    ui_file = utils.getUiFileName(__file__)
    # Emit the action when button is pushed:
    buttonPushed = pyqtSignal(str)
    # Emit the new tab index (int), file path (str), data (dict) and selection field (dict):
    tabChanged = pyqtSignal(int, str, dict, dict)
    # Emit X2 value changes for 2D data:
    x2ValueChanged = pyqtSignal(int)

    def __init__(self, parent):
        """
        Create the table view and connect with its parent.

        parent object:
            Instance of mdaviz.mda_folder.MDAMVC
        """

        self.mda_mvc = parent
        super().__init__()
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()

    def setup(self):
        from functools import partial

        # Initialize attributes:
        self.setData()
        self.tabManager = TabManager()  # Instantiate TabManager
        self.currentHighlightedRow = None  # To store the current highlighted row
        self.currentHighlightedFilePath = (
            None  # To store the current highlighted row's file path
        )
        self.currentHighlightedModel = (
            None  # To store the current highlighted's row model
        )

        # Buttons handling:
        self.addButton.hide()
        self.replaceButton.hide()
        self.addButton.clicked.connect(partial(self.responder, "add"))
        self.clearButton.clicked.connect(partial(self.responder, "clear"))
        self.replaceButton.clicked.connect(partial(self.responder, "replace"))
        self.clearGraphButton.clicked.connect(self.onClearGraphRequested)

        # Mode handling:
        options = ["Auto-replace", "Auto-add", "Auto-off"]
        self.setMode(options[0])
        self.autoBox.addItems(options)
        self.autoBox.currentTextChanged.connect(self.setMode)
        self.autoBox.currentTextChanged.connect(self.updateButtonVisibility)

        # Connect TabManager signals:
        # DESIGN NOTE: Implement proper signal/slot tab management via tabManager for tabAdded and allTabsRemoved if needed.
        self.tabManager.tabAdded.connect(self.onTabAdded)
        self.tabManager.tabRemoved.connect(self.onTabRemoved)
        self.tabManager.allTabsRemoved.connect(self.onAllTabsRemoved)

        # Tab handling:
        self.tabWidget.currentChanged.connect(self.updateCurrentTabInfo)
        self.tabWidget.tabCloseRequested.connect(self.onTabCloseRequested)

        # NOTE: Consider setting tab tool tip for Data & Metadata tabs and updating dynamically when switching file.

        # # Debug signals:
        # self.addButton.clicked.connect(utils.debug_signal)
        # self.clearButton.clicked.connect(utils.debug_signal)
        # self.replaceButton.clicked.connect(utils.debug_signal)
        # self.autoBox.currentTextChanged.connect(utils.debug_signal)
        # self.autoBox.currentTextChanged.connect(utils.debug_signal)
        # self.tabManager.tabAdded.connect(utils.debug_signal)
        # self.tabManager.tabRemoved.connect(utils.debug_signal)
        # self.tabManager.allTabsRemoved.connect(utils.debug_signal)
        # self.tabWidget.currentChanged.connect(utils.debug_signal)
        # self.tabWidget.tabCloseRequested.connect(utils.debug_signal)

    def dataPath(self):
        """Path (obj) of the data folder (folder comboBox + subfolder comboBox)."""
        return self.mda_mvc.dataPath()

    def mdaFileList(self):
        """List of mda file (name only) in the selected folder."""
        return self.mda_mvc.mdaFileList()

    # ------ Get & set methods:

    def mode(self):
        """
        "Auto-replace", "Auto-add", "Auto-off"
        """
        return self._mode

    def setMode(self, *args):
        self._mode = args[0]

    def data(self):
        """
        The data to display in the table view.
        """
        return self._data

    def setData(self, index=None):
        """
        Populates the `_data` attribute with file information and data extracted
        from a specified file in the MDA file list at the provided index, if any.
        If no index is provided, `_data` is set to an empty dictionary.

        Parameters:
        - index (int, optional): The index of the file in the MDA file list to read and extract data from.
          Defaults to None, resulting in self._data = {}.

        The populated `_data` dictionary includes:
        - fileName (str): The name of the file without its extension.
        - filePath (str): The full path of the file.
        - folderPath (str): The full path of the parent folder.
        - metadata (dict): The extracted metadata from the file.
        - scanDict (dict): A dictionary of positioner & detector information
            "object": mda object X (scanPositioner or scanDetector)
            "type": "POS" (if scanPositioner) or "DET" (if scanDetector),
            "data": X.data or [],
            "unit": byte2str(X.unit) if X.unit else "",
            "name": byte2str(X.name) if X.name else "n/a",
            "desc": byte2str(X.desc) if X.desc else "",
            "fieldName": byte2str(X.fieldName)
        - firstPos (float): The first positioner (P1, or if no positioner, P0 = index).
        - firstDet (float): The first detector (D01).
        - pvList (list of str): List of detectors PV names as strings.
        """
        if index is None:
            self._data = {}
            return

        folder_path = self.dataPath()
        file_name = self.mdaFileList()[index]
        file_path = self.dataPath() / file_name

        # Debug: print the paths to see what's happening
        logger.debug(f"folder_path: {folder_path}")
        logger.debug(f"file_name: {file_name}")
        logger.debug(f"file_path: {file_path}")
        logger.debug(f"file_path.exists(): {file_path.exists()}")

        # Use data cache for better performance
        cache = get_global_cache()
        print(f"🔍 CACHE DEBUG: Loading data for file: {file_path}")
        print(f"🔍 CACHE DEBUG: Cache object: {cache}")
        cached_data = cache.get_or_load(str(file_path))
        print(f"🔍 CACHE DEBUG: Cache result: {cached_data}")
        if cached_data:
            print(f"✅ CACHE DEBUG: Using cached data for: {file_path}")
        else:
            print(
                f"❌ CACHE DEBUG: No cached data available for: {file_path}, falling back to direct loading"
            )

        if cached_data:
            # Use cached data
            self._data = {
                "fileName": cached_data.file_name,
                "filePath": cached_data.file_path,
                "folderPath": cached_data.folder_path,
                "metadata": cached_data.metadata,
                "scanDict": cached_data.scan_dict,
                "firstPos": cached_data.first_pos,
                "firstDet": cached_data.first_det,
                "pvList": cached_data.pv_list,
                "index": index,
                # Add 2D data support
                "scanDict2D": cached_data.scan_dict_2d,
                "scanDictInner": cached_data.scan_dict_inner,
                "isMultidimensional": cached_data.is_multidimensional,
                "rank": cached_data.rank,
                "dimensions": cached_data.dimensions,
                "acquiredDimensions": cached_data.acquired_dimensions,
            }
        else:
            # Fallback to direct loading if cache fails
            result = readMDA(str(file_path))
            if result is None:
                self.setStatus(f"Could not read file: {file_path}")
                # Still populate basic file info even if data can't be read
                self._data = {
                    "fileName": file_path.stem,
                    "filePath": str(file_path),
                    "folderPath": str(folder_path),
                    "metadata": {},
                    "scanDict": {},
                    "firstPos": 0,
                    "firstDet": 1,
                    "pvList": [],
                    "index": index,
                    # Add 2D data support
                    "scanDict2D": {},
                    "scanDictInner": {},
                    "isMultidimensional": False,
                    "rank": 1,
                    "dimensions": [],
                    "acquiredDimensions": [],
                }
                return

            file_metadata, file_data_dim1, *_ = result
            rank = file_metadata.get("rank", 1)
            dimensions = file_metadata.get("dimensions", [])
            acquired_dimensions = file_metadata.get("acquired_dimensions", [])

            scanDict, first_pos, first_det = utils.get_scan(file_data_dim1)

            # Initialize 2D data fields
            scanDict2D = {}
            scan_dict_inner = {}
            is_multidimensional = rank > 1

            # Process 2D data if available
            if rank >= 2 and len(result) > 2:
                try:
                    file_data_dim2 = result[2]
                    scanDict2D, _, _ = utils.get_scan_2d(file_data_dim1, file_data_dim2)
                    # Also store inner dimension data for 1D plotting
                    scan_dict_inner, _, _ = utils.get_scan(file_data_dim2)
                except Exception as e:
                    logger.warning(f"Warning: Could not process 2D data: {e}")
                    scanDict2D = {}
                    scan_dict_inner = {}

            # Construct pvList from appropriate data source
            # For 2D+ data, use scan_dict_inner (inner dimension PVs like P1, D1, etc.)
            # For 1D data, use scanDict (outer dimension PVs)
            if is_multidimensional and scan_dict_inner:
                pvList = [v["name"] for v in scan_dict_inner.values()]
            else:
                pvList = [v["name"] for v in scanDict.values()]

            self._data = {
                "fileName": file_path.stem,  # file_name.rsplit(".mda", 1)[0]
                "filePath": str(file_path),
                "folderPath": str(folder_path),
                "metadata": file_metadata,
                "scanDict": scanDict,
                "firstPos": first_pos,
                "firstDet": first_det,
                "pvList": pvList,
                "index": index,
                # Add 2D data support
                "scanDict2D": scanDict2D,
                "scanDictInner": scan_dict_inner,
                "isMultidimensional": is_multidimensional,
                "rank": rank,
                "dimensions": dimensions,
                "acquiredDimensions": acquired_dimensions,
            }

    def handle2DMode(self):
        """Handle 2D data setup - update controls but don't change mode."""
        if self._data.get("isMultidimensional", False):
            # Update 2D controls in table view
            table_view = self.tabIndex2Tableview(self.tabWidget.currentIndex())
            if table_view:
                dimensions = self._data.get("dimensions", [])
                acquired_dimensions = self._data.get("acquiredDimensions", [])
                logger.debug(f"handle2DMode - dimensions: {dimensions}")
                logger.debug(
                    f"handle2DMode - acquired_dimensions: {acquired_dimensions}"
                )

                # Extract X2 positioner information from scanDict2D
                x2_positioner_info = None
                scan_dict_2d = self._data.get("scanDict2D", {})
                logger.debug(
                    f"handle2DMode - scanDict2D keys: {list(scan_dict_2d.keys())}"
                )
                if scan_dict_2d:
                    # Find the X2 positioner (first positioner in 2D data)
                    # In 2D data, the first positioner (index 0) is typically X2
                    for key, value in scan_dict_2d.items():
                        logger.debug(
                            f"handle2DMode - Field {key}: type={value.get('type')}, name={value.get('name')}"
                        )
                        if (
                            value.get("type") == "POS" and key == 0
                        ):  # First positioner is X2
                            x2_positioner_info = {
                                "name": value.get("name", "X2"),
                                "unit": value.get("unit", ""),
                                "data": value.get("data", []),
                            }
                            logger.debug(
                                f"handle2DMode - X2 positioner found: {x2_positioner_info['name']}"
                            )
                            break

                table_view.update2DControls(
                    is_multidimensional=self._data.get("isMultidimensional", False),
                    dimensions=dimensions,
                    acquired_dimensions=acquired_dimensions,
                    x2_positioner_info=x2_positioner_info,
                )

    def setStatus(self, text):
        self.mda_mvc.setStatus(text)

    # ------ Tab utilities:

    def tabPath2Index(self, file_path):
        """Finds and returns the index of a tab based on its associated file path."""
        if file_path is not None:
            for tab_index in range(self.tabWidget.count()):
                tab_tableview = self.tabWidget.widget(tab_index)
                if tab_tableview.filePath.text() == file_path:
                    return tab_index
        return None  # Return None if the file_path is not found.

    def tabIndex2Path(self, index):
        """Returns the file path associated with a given tab index."""
        if 0 <= index < self.tabWidget.count():
            tab_tableview = self.tabWidget.widget(index)
            return tab_tableview.filePath.text()
        return None  # Return None if the index is out of range.

    def tabPath2Tableview(self, file_path):
        """Finds and returns the tableview of a tab based on its associated file path."""
        if file_path is not None:
            for tab_index in range(self.tabWidget.count()):
                tab_tableview = self.tabWidget.widget(tab_index)
                if tab_tableview.filePath.text() == file_path:
                    return tab_tableview
        return None  # Return None if the file_path is not found.

    def tabIndex2Tableview(self, index):
        """Returns the Tableview associated with a given tab index."""
        if 0 <= index < self.tabWidget.count():
            tab_tableview = self.tabWidget.widget(index)
            return tab_tableview
        return None  # Return None if the index is out of range.

    # ------ Populating UIs with selected file content:

    def displayMetadata(self, metadata):
        """Display metadata in the vizualization panel."""
        if not metadata:
            return
        metadata = utils.get_md(metadata)
        metadata = yaml.dump(metadata, default_flow_style=False)
        self.mda_mvc.mda_file_viz.setMetadata(metadata)

    def displayData(self, tabledata):
        """Display pos(s) & det(s) values as a tableview in the vizualization panel."""
        if not self.data():
            return
        # Pass full data structure instead of just scanDict for 2D support
        self.mda_mvc.mda_file_viz.setTableData(self.data())

    def defaultSelection(self, first_pos, first_det, selection_field):
        """
        Sets the default field selection if no selection is provided.

        Args:
            first_pos (int): The index of the first positioner.
            first_det (int): The index of the first detector.
            selection_field (dict): The current selection fields, if any.

        Returns:
            dict: The updated selection field.
        """
        if selection_field and selection_field.get("Y"):
            return selection_field
        default = {"X": first_pos, "Y": [first_det]}
        self.mda_mvc.setSelectionField(default)
        return default

    # ------ Slots (UI):

    def onTabCloseRequested(self, index):
        """
        Handles tab close request by calling the tab manager.
        """
        file_path = self.tabIndex2Path(index)
        if file_path:
            self.tabManager.removeTab(file_path)

    def onTabAdded(self, file_path):
        """To be implemented"""
        pass

    def onTabRemoved(self, file_path):
        """
        Removes a tab from the tab widget based on its file_path.
        If it's the last tab, it calls removeAllTabs() to ensure consistent cleanup.
        """
        index = self.tabPath2Index(file_path)
        if self.tabWidget.count() == 1 and index == 0:
            self.removeAllFileTabs()
        elif index is not None and index < self.tabWidget.count():
            self.tabWidget.removeTab(index)

    def onAllTabsRemoved(self):
        """To be implemented"""
        pass

    def onClearGraphRequested(self):
        """Clear only the graph area in the visualization panel."""
        # Get the chart view and clear all curves with checkboxes
        layout = self.mda_mvc.mda_file_viz.plotPageMpl.layout()
        if layout.count() > 0:
            plot_widget = layout.itemAt(0).widget()
            if hasattr(plot_widget, "curveManager"):
                plot_widget.curveManager.removeAllCurves(doNotClearCheckboxes=False)
        self.setStatus("Graph cleared.")

    # ------ Tabs management:

    def addFileTab(self, index, selection_field):
        """
        Handles adding or activating a file tab within the tab widget.
        - Retrieves data for the selected file based on its index in the MDA file list.
        - Updates display for metadata and table data in the visualization panel.
        - Determines and applies the default selection of fields if necessary.
        - Checks if a tab for the file already exists; if so, activates it.
        - If the file is new, depending on the mode (Auto-add, Auto-replace, Auto-off),
        it creates a new tab or replaces existing tabs with the new file tab.

        Parameters:
        - index (int): The index of the file in the MDA file list.
        - selection_field (dict): Specifies the fields (positioners/detectors) for display
        and plotting.
        """

        # Get data for the selected file:
        self.setData(index)
        data = self.data()
        file_path = data["filePath"]
        file_name = data["fileName"]
        first_pos = data["firstPos"]
        first_det = data["firstDet"]
        metadata = data["metadata"]
        tabledata = data["scanDict"]

        # Update data, metadata & selection field (if needed):
        self.displayMetadata(metadata)
        self.displayData(tabledata)
        selection_field = self.defaultSelection(first_pos, first_det, selection_field)
        # Update tab widget:
        mode = self.mode()
        if self.tabManager.getTabData(file_path):
            # File already exists in tab manager
            if mode in ("Auto-replace"):
                # In auto-replace mode, clear all tabs and recreate this one
                while self.tabWidget.count() > 0:
                    self.tabWidget.removeTab(0)
                self.tabManager.removeAllTabs()
                # Add this tab to the UI:
                self.createNewTab(file_name, file_path, selection_field)
                # Add new tab to tabManager:
                self.tabManager.addTab(file_path, metadata, tabledata)
            else:
                # In auto-add/auto-off mode, just switch to existing tab
                tab_index = self.tabPath2Index(file_path)
                self.tabWidget.setCurrentIndex(tab_index)
        else:
            # File is new
            if mode in ("Auto-add", "Auto-off"):
                # Add this tab to the UI:
                self.createNewTab(file_name, file_path, selection_field)
            elif mode in ("Auto-replace"):
                # Clear all existing tabs:
                while self.tabWidget.count() > 0:
                    self.tabWidget.removeTab(0)
                self.tabManager.removeAllTabs()
                # Add this tab to the UI:
                self.createNewTab(file_name, file_path, selection_field)
            # Add new tab to tabManager:
            self.tabManager.addTab(file_path, metadata, tabledata)

        # Handle mode switching for 2D data AFTER tab management is complete
        if self._data.get("isMultidimensional", False):
            self.handle2DMode()
            # Set 2D data in visualization
            self.mda_mvc.mda_file_viz.set2DData(self._data)
        else:
            # Clear 2D data for 1D files
            self.mda_mvc.mda_file_viz.set2DData(None)
            # Hide 2D controls for 1D files
            table_view = self.tabIndex2Tableview(self.tabWidget.currentIndex())
            if table_view:
                table_view.update2DControls(
                    is_multidimensional=False, dimensions=None, x2_positioner_info=None
                )

    def createNewTab(self, file_name, file_path, selection_field):
        """
        Creates and activates a new tab with a MDAFileTableView for the selected file.
        - Initializes a new MDAFileTableView with data based on the provided file and selection field.
        - Adds a new tab to the tab widget.
        - Labels the new tab with the file's name.
        - Sets the new tab as the current active tab.
        - Updates the file path Qlabel (named filePath) within MDAFileTableView to reflect the selected file's path.

        Parameters:
        - file_name (str): The name of the file, used as the tab's label.
        - file_path (str): The full path to the file, used to populate the table view and label.
        - selection_field (dict): Specifies the data fields (positioners/detectors) for display in the table view.
        """
        tableview = MDAFileTableView(self)
        tab_index = self.tabWidget.addTab(tableview, file_name)
        self.tabWidget.setCurrentIndex(tab_index)
        tableview.displayTable(selection_field)
        tableview.filePath.setText(file_path)
        self.tabWidget.setTabToolTip(tab_index, file_path)
        # NOTE: Consider setting tab tool tip for Data & Metadata tabs and updating dynamically when switching file.

    def removeAllFileTabs(self):
        """
        Removes all tabs from the tab widget.
        """
        while self.tabWidget.count() > 0:
            self.tabWidget.removeTab(self.tabWidget.count() - 1)
        # Clear all data associated with the tabs from the TabManager.
        self.tabManager.removeAllTabs()
        # Clear all content from the visualization panel except for graph, if no tabs are open.
        self.mda_mvc.mda_file_viz.clearContents(plot=False)
        # Update the status to reflect that all tabs have been closed.
        self.setStatus("All file tabs have been closed.")

    def updateCurrentTabInfo(self, new_tab_index):
        """
        When the current tab is changed, sends a signal to the MDA_MVC with the info
        corresponding to the new selected tab:
            new_tab_index, new_file_path, new_tab_data, new_selection_field
        """
        new_file_path = self.tabIndex2Path(new_tab_index)
        new_tab_data = self.tabManager.getTabData(new_file_path) or {}
        new_tab_tableview = self.tabWidget.widget(new_tab_index)
        if new_tab_tableview and new_tab_tableview.tableView.model():
            new_selection_field = new_tab_tableview.tableView.model().plotFields()
        else:
            new_selection_field = {}
        self.tabChanged.emit(
            new_tab_index, new_file_path, new_tab_data, new_selection_field
        )

    def highlightRowInTab(self, file_path, row):
        """
        Switch to the tab corresponding to the given file path and highlight a specific row.

        Args:
            file_path (str): _description_
            row (int): _description_
        """
        tab_index = self.tabPath2Index(file_path)
        self.tabWidget.setCurrentIndex(tab_index)
        tableview = self.tabWidget.widget(tab_index)
        model = tableview.tableView.model()
        if model is not None:
            # Unhighlight the previous row if it exists
            if (
                self.currentHighlightedRow is not None
                and self.currentHighlightedModel is not None
            ):
                self.currentHighlightedModel.unhighlightRow(self.currentHighlightedRow)

            # Highlight the new row
            self.selectAndShowRow(tab_index, row)

            # Update the current highlighted row, file path, and model
            self.currentHighlightedRow = row
            self.currentHighlightedFilePath = file_path
            self.currentHighlightedModel = model

    def selectAndShowRow(self, tab_index, row):
        """
        Selects a field by its row in the file table view and ensures it is visible to the user
        by adjusting scroll position based on the field's position in the list

        Args:
        - row (int): row of the selected field.
        """
        tableview = self.tabWidget.widget(tab_index)
        model = tableview.tableView.model()
        model.setHighlightRow(row)
        rowCount = model.rowCount()
        scrollHint = QAbstractItemView.ScrollHint.EnsureVisible
        if row == 0:
            scrollHint = QAbstractItemView.ScrollHint.PositionAtTop
        elif row == rowCount - 1:
            scrollHint = QAbstractItemView.ScrollHint.PositionAtBottom
        # Get the QModelIndex for the specified row
        index = model.index(row, 0)
        tableview.tableView.scrollTo(index, scrollHint)

    # ------ Button methods:

    def responder(self, action):
        """Modify the plot with the described action.
        action:
            from buttons: add, clear, replace
        """
        logger.debug(f"\nResponder: {action=}")
        self.buttonPushed.emit(action)

    def updateButtonVisibility(self):
        """Check the current text in "mode" pull down and show/hide buttons accordingly"""
        if self.autoBox.currentText() == "Auto-off":
            self.addButton.show()
            self.replaceButton.show()
        else:
            self.addButton.hide()
            self.replaceButton.hide()


# ------ Tabs management (data):


class TabManager(QObject):
    """
    Manages the content of the currently opened tabs (data aspect only).

    The TabManager does not handle UI elements (i.e. nothing related to tab index, such as switching tabs),
    maintaining a clear separation between the application's data layer and its presentation (UI) layer.

    Features:
    - Tracks metadata and table data for each open tab.
    - Allows adding and removing tabs dynamically.
    - Emits signals to notify other components of tab-related changes.

    Signals:
    - tabAdded: Emitted when a new tab is added. Passes the file path of the added tab.
    - tabRemoved: Emitted when a tab is removed. Passes the file path of the removed tab.
    - allTabRemoved: Emitted when all tabs are removed. No parameters.
    """

    tabAdded = pyqtSignal(str)  # Signal emitting file path of removed tab
    tabRemoved = pyqtSignal(str)  # Signal emitting file path of removed tab
    allTabsRemoved = pyqtSignal()  # Signal indicating all tabs have been removed

    def __init__(self):
        super().__init__()
        self._tabs = {}

    def addTab(self, file_path, metadata, tabledata):
        """Adds a new tab with specified metadata and table data."""
        if file_path not in self._tabs:
            self._tabs[file_path] = {"metadata": metadata, "tabledata": tabledata}
            self.tabAdded.emit(file_path)

    def removeTab(self, file_path):
        """
        Removes the tab associated with the given file path.
        Emits corresponding file path & index.
        """
        if file_path in self._tabs:
            del self._tabs[file_path]
            self.tabRemoved.emit(file_path)

    def removeAllTabs(self):
        """Removes all tabs."""
        self._tabs.clear()
        self.allTabsRemoved.emit()

    def getTabData(self, file_path):
        """Returns the metatdata & data for the tab associated with the given file path."""
        return self._tabs.get(file_path)

    def tabs(self):
        """Returns a read-only view of the currently managed tabs."""
        return dict(self._tabs)


# chatGPT review:
# Your implementation of addFileTab and createNewTab seems well thought out with
# a clear workflow. Here are some considerations to ensure the TabManager's
# state aligns with the UI:

#     Synchronization Between Data and UI: Every action that affects tabs
#         (adding, removing, switching) should reflect both in the UI and the
#         data managed by TabManager. It looks like you're adding and removing
#         tabs through the TabManager correctly. Just ensure that every UI
#         action triggers the corresponding data update in TabManager.

#     Error Handling for Tab Operations: Consider adding error handling or
#         checks for situations where tab operations might fail or behave
#         unexpectedly. For example, what happens if createNewTab is called with
#         a file_path that already exists in TabManager? Although your logic
#         should prevent this, defensive programming can help catch unexpected
#         issues.

#     Consistent State After Operations: After operations like adding a new tab
#         or removing all tabs, verify that the application's state is
#         consistent (e.g., no dangling references to removed tabs, UI elements
#         are enabled/disabled appropriately).

#     Update UI Responsively: Make sure the UI updates are responsive to changes
#         in the TabManager. For instance, when a tab is added or removed, any
#         UI elements depending on the number of open tabs (like "Close All
#         Tabs" button) should update accordingly.

#     onTabRemoved and onAllTabsRemoved Slots: You've mentioned placeholders for
#         these methods but haven't detailed their implementations. These are
#         crucial for handling UI updates or cleanup when tabs are removed.
#         Ensure they're implemented to handle any necessary UI adjustments when
#         tabs change.

#     Removal of Tabs and Associated Data: In removeTabUI, you handle the
#         removal process properly by checking if the tab exists in TabManager
#         before attempting to remove it. Just make sure this also covers any
#         associated data cleanup that might be needed to prevent memory leaks
#         or stale data.

#     Switching Tabs: When switching tabs (updateCurrentTabInfo), ensure that any
#         context-sensitive UI elements (like metadata display, data tables,
#         etc.) update to reflect the content of the newly active tab.

# Overall, your methods for handling tab addition and removal appear to be on
# the right track. Thorough testing, especially with scenarios involving rapid
# addition/removal of tabs and switching between tabs, will help ensure that the
# UI and TabManager remain in sync.


# For MDA_MVC:

#     Your MDA_MVC class implementation appears comprehensive and
#     well-organized. You've covered a broad range of functionalities essential
#     for the MVC architecture in managing MDA files. Here are a few points to
#     consider, focusing on ensuring coherence and functionality:

#     Signal and Slot Connections: Ensure all signal connections are correctly
#         established, especially for newly introduced signals related to
#         TabManager. It's crucial that all parts of your MVC architecture
#         communicate as intended.

#     UI and Data Synchronization: Given your use of TabManager for managing tab
#         data, verify that UI changes (e.g., tab switches, adds, and removes)
#         are always in sync with the data model. This includes handling of
#         signals like onTabRemoved and onAllTabsRemoved effectively to update
#         the UI accordingly.

#     Error Handling: Consider adding error handling for cases where operations
#         might not go as expected. For example, what happens if doFileSelected
#         is triggered but the file cannot be processed for some reason?
#         Providing feedback or ensuring the application can gracefully handle
#         such scenarios is important.

#     Refreshing and Updating UI: The method doRefresh should ensure that the UI
#         correctly reflects the current state of the file system or data source
#         it's representing. This might involve more than just updating the
#         table views, such as resetting selections or clearing data
#         visualizations if necessary.

#     Responsiveness to User Actions: Methods like goToFirst, goToLast,
#         goToNext, and goToPrevious are crucial for navigating through files.
#         Ensure these actions feel responsive to the user and that any
#         associated data visualization updates occur without noticeable delay.

#     Consistency in UI Updates: When tabs are changed via onCurrentTabChanged,
#         ensure that the displayed metadata and data are always consistent with
#         the selected tab. This includes proper handling of cases where a tab
#         might not contain the expected data (e.g., if the file has been moved
#         or deleted outside the application).

#     Field Selection and Plotting Logic: The logic handling field selection for
#         plotting and subsequent plot updates (in methods like
#         onCheckboxStateChanged and doPlot) should be robust against changes in
#         the underlying data model. Ensure that selections are valid and that
#         the plotting functionality reacts correctly to changes in selected
#         fields.

#     Documentation and Code Comments: Your documentation and comments provide a
#         good overview of each method's purpose. Continuing to maintain this
#         level of documentation as your code evolves will be beneficial for
#         both your future self and others who may work with your code.
