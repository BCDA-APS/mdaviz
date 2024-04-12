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

from mda import readMDA
from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5.QtCore import QItemSelectionModel
from PyQt5.QtWidgets import QAbstractItemView
import yaml

from . import utils
from .chartview import ChartView
from .mda_file_table_view import MDAFileTableView


class MDAFile(QtWidgets.QWidget):
    ui_file = utils.getUiFileName(__file__)
    # Emit the action when button is pushed:
    buttonPushed = QtCore.pyqtSignal(str)
    # Emit the new tab index (int), file path (str), data (dict) and selection field (dict):
    tabChanged = QtCore.pyqtSignal(int, str, dict, dict)

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
        self.setSelectionModel()
        self.tabManager = TabManager()  # Instantiate TabManager

        # Buttons handling:
        self.addButton.hide()
        self.replaceButton.hide()
        self.addButton.clicked.connect(partial(self.responder, "add"))
        self.clearButton.clicked.connect(partial(self.responder, "clear"))
        self.replaceButton.clicked.connect(partial(self.responder, "replace"))

        # Mode handling:
        options = ["Auto-replace", "Auto-add", "Auto-off"]
        self.setMode(options[0])
        self.autoBox.addItems(options)
        self.autoBox.currentTextChanged.connect(self.setMode)
        self.autoBox.currentTextChanged.connect(self.updateButtonVisibility)

        # Connect TabManager signals:
        # TODO: implement proper signal/slot tab managment via tabManager for tabAdded and allTabsRemoved
        #       - tabAdded: should doFileSelected emit a signal monitored by the tabManager?
        self.tabManager.tabAdded.connect(self.onTabAdded)
        self.tabManager.tabRemoved.connect(self.onTabRemoved)
        self.tabManager.allTabsRemoved.connect(self.onAllTabsRemoved)

        # Tab handling:
        self.tabWidget.currentChanged.connect(self.updateCurrentTabInfo)
        self.tabWidget.tabCloseRequested.connect(self.onTabCloseRequested)

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
        return self._mode

    def setMode(self, *args):
        self._mode = args[0]

    def data(self):
        return self._data

    def setData(self, index=None):
        """
        Populates the `_data` attribute with file information and data extracted
        from a specified file in the MDA file list at the provided index, if any.
        If no index is provided, `_data` is set to an empty dictionary.

        Parameters:
        - index (int, optional): The index of the file in the MDA
        file list to read and extract data from.
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
        file_metadata, file_data = readMDA(file_path)
        scanDict, first_pos, first_det = utils.get_scan(file_data)
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
        }

    def setSelectionModel(self, selection=None):
        """
        Sets the selection model for managing view selections.

        Args:
            selection (QItemSelectionModel, optional): The selection model to be associated
            with the view. Defaults to None.
        """
        self._selection_model = selection

    def selectionModel(self):
        """
        Accesses the selection model of the view managing the selection state.

        Returns:
            QItemSelectionModel: The selection model associated with a view,
            managing which rows/items are selected.
        """
        return self._selection_model

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
        self.mda_mvc.mda_file_viz.setTableData(tabledata)

    def defaultSelection(self, first_pos, first_det, selection_field):
        """Sets the default field selection if no selection is provided.
        Args:
            first_pos (int): The index of the first positioner.
            first_det (int): The index of the first detector.
            selection_field (dict): The current selection fields, if any.
        Returns:
            dict: The updated selection field.
        """
        if selection_field:
            return selection_field
        default = {"X": first_pos, "Y": [first_det]}
        self.mda_mvc.setSelectionField(default)
        return default

    # ------ Slots (UI):

    def onTabCloseRequested(self, index):
        file_path = self.tabIndex2Path(index)
        if file_path:
            self.tabManager.removeTab(file_path)

    def onTabAdded(self, file_path):
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
        pass

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
        if self.tabManager.getTabData(file_path):
            tab_index = self.tabPath2Index(file_path)
            self.tabWidget.setCurrentIndex(tab_index)
        else:
            mode = self.mode()
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

        # Field Selection Model :
        model = tableview.tableView.model()
        if model is not None:
            selection_model = tableview.tableView.selectionModel()
            self.setSelectionModel(selection_model)

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
        new_file_path = self.tabIndex2Path(new_tab_index)
        new_tab_data = self.tabManager.getTabData(new_file_path) or {}
        new_tab_tableview = self.tabWidget.widget(new_tab_index)
        if new_tab_tableview and new_tab_tableview.tableView.model():
            new_selection_field = new_tab_tableview.tableView.model().plotFields()[0]
        else:
            new_selection_field = {}
        self.tabChanged.emit(
            new_tab_index, new_file_path, new_tab_data, new_selection_field
        )

    def highlightRowInTab(self, file_path, row):
        tab_index = self.tabPath2Index(file_path)
        self.tabWidget.setCurrentIndex(tab_index)
        tableview = self.tabWidget.widget(tab_index)
        model = tableview.tableView.model()
        if model is not None:
            self.selectAndShowRow(tab_index, row)

    def selectAndShowRow(self, tab_index, row):
        """
        Selects a file by its row in the folder table view and ensures it is visible to the user
        by adjusting scroll position based on the field's position in the list

        Parameters:
        - row (int): row of the selected field.

        Details:
        - .
        """
        tableview = self.tabWidget.widget(tab_index)
        model = tableview.tableView.model()
        model.setHighlightRow(row)
        rowCount = model.rowCount()

        scrollHint = QAbstractItemView.EnsureVisible
        if row == 0:
            scrollHint = QAbstractItemView.PositionAtTop
        elif row == rowCount - 1:
            scrollHint = QAbstractItemView.PositionAtBottom
        # Get the QModelIndex for the specified row
        index = model.index(row, 0)
        tableview.tableView.scrollTo(index, scrollHint)

    # ------ Button methods:

    def responder(self, action):
        """Modify the plot with the described action.
        action:
            from buttons: add, clear, replace
        """
        print(f"\nResponder: {action=}")
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


class TabManager(QtCore.QObject):
    """
    Manages only the data aspects of tabs; does not handle UI elements (i.e. nothing
    related to tab index, such as switching tabs),  maintaining a clear separation
    between the application's data layer and its presentation (UI) layer.

    Features:
    - Tracks metadata and table data for each open tab.
    - Allows adding and removing tabs dynamically.
    - Emits signals to notify other components of tab-related changes.

    Signals:
    - tabAdded: Emitted when a new tab is added. Passes the file path of the added tab.
    - tabRemoved: Emitted when a tab is removed. Passes the file path of the removed tab.
    - allTabRemoved: Emitted when all tabs are removed. No parameters.
    """

    tabAdded = QtCore.pyqtSignal(str)  # Signal emitting file path of removed tab
    tabRemoved = QtCore.pyqtSignal(str)  # Signal emitting file path of removed tab
    allTabsRemoved = QtCore.pyqtSignal()  # Signal indicating all tabs have been removed

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
#         onCheckboxStateChange and doPlot) should be robust against changes in
#         the underlying data model. Ensure that selections are valid and that
#         the plotting functionality reacts correctly to changes in selected
#         fields.

#     Documentation and Code Comments: Your documentation and comments provide a
#         good overview of each method's purpose. Continuing to maintain this
#         level of documentation as your code evolves will be beneficial for
#         both your future self and others who may work with your code.
