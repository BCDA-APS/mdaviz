"""
Display content of the currently selected files.

.. autosummary::

    ~MDAFile
"""

from mda import readMDA
from PyQt5 import QtCore
from PyQt5 import QtWidgets
import yaml

from . import utils
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

        self.setData()
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

        # Tab handling:
        self.tabWidget.currentChanged.connect(self.onSwitchTab)
        self.tabWidget.tabCloseRequested.connect(self.removeFileTab)
        # Connect TabManager signals:
        # self.tabManager.allTabsRemoved.connect(self.onAllTabsRemoved)
        # self.tabManager.tabRemoved.connect(self.onTabRemoved)
        # TODO - question: are those redundant with tabCloseRequested? I think so
        # removeFileTab takes care of cleaning everything up when the last tab is closed

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
            "unit": byte2str(X.unit) if X.unit else "a.u.",
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
            "fileName": file_name.rsplit(".mda", 1)[0],
            "filePath": str(file_path),
            "folderPath": str(folder_path),
            "metadata": file_metadata,
            "scanDict": scanDict,
            "firstPos": first_pos,
            "firstDet": first_det,
            "pvList": pvList,
            "index": index,
        }

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

    # ------ Tabs management (UI):

    def onTabRemoved(self, file_path):
        # FIXME - sync tab with graph: handle the UI update or other actions needed when a new tab is removed
        # e.g.:    close tab ---> remove curve  NO !
        # This can be handled by self.removeFileTabs() that gets triggered when a tab is removed.
        # Unless we need something for the other way around:
        # e.g.:    remove curve ---> close tab  YES
        pass

    # def onAllTabsRemoved(self):
    #     # TODO - question: same as bove: sync tab with UI: handle the UI update or other actions needed when a all tabs are removed
    #     # e.g. disable certain UI elements that require a file to be selected (buttons?)
    #     # This is already done by self.removeAllFileTabs() that gets triggered when the last tab is removed.
    #     pass

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
        - Updates the filePath Qlabel within MDAFileTableView to reflect the selected file's path.

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

    def removeFileTab(self, index=None):
        """
        Removes a tab from the tab widget based on its index. If it's the last tab,
        it calls removeAllTabs() to ensure consistent cleanup.
        """
        if self.tabWidget.count() == 1:
            self.removeAllFileTabs()
        elif index is not None and index < self.tabWidget.count():
            current_tab = self.tabWidget.widget(index)
            file_path = current_tab.filePath.text() if current_tab else None
            # Ensure filepath is in tab_dict before attempting to remove:
            if file_path and self.tabManager.getTabData(file_path):
                self.tabWidget.removeTab(index)
                self.tabManager.removeTab(file_path)
                self.setStatus(f"Closed file tab {index=}, {file_path=}")
            else:
                self.setStatus(
                    f"Cannot find corresponding file tab: {index}, {file_path}"
                )
        else:
            self.setStatus("Invalid tab index provided.")

    def removeAllFileTabs(self):
        """
        Removes all tabs from the tab widget.
        """
        while self.tabWidget.count() > 0:
            self.tabWidget.removeTab(self.tabWidget.count() - 1)
        # Clear all data associated with the tabs from the TabManager.
        self.tabManager.removeAllTabs()
        # Clear all content from the visualization panel as well, if no tabs are open.
        self.mda_mvc.mda_file_viz.clearContents()
        # Update the status to reflect that all tabs have been closed.
        self.setStatus("All file tabs have been closed.")

    def onSwitchTab(self, new_tab_index):
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
    related to tab index, such as switching tabs).

    Features:
    - Tracks metadata and table data for each open tab.
    - Allows adding and removing tabs dynamically.
    - Emits signals to notify other components of tab-related changes.

    Signals:
    - tabAdded: Emitted when a new tab is added. Passes the file path of the added tab.
    - tabRemoved: Emitted when a tab is removed. Passes the file path of the removed tab.
    - allTabRemoved: Emitted when all tabs are removed. No parameters.
    """

    # TODO - question: same as above, they are probably useless
    # tabRemoved = QtCore.pyqtSignal(str)  # Signal emitting file path of removed tab
    # allTabsRemoved = QtCore.pyqtSignal()  # Signal indicating all tabs have been removed

    def __init__(self):
        super().__init__()
        self._tabs = {}

    def addTab(self, file_path, metadata, tabledata):
        """Adds a new tab with specified metadata and table data."""
        if file_path not in self._tabs:  # Check if the tab doesn't already exist
            self._tabs[file_path] = {"metadata": metadata, "tabledata": tabledata}

    def removeTab(self, file_path):
        """Removes the tab associated with the given file path."""
        if file_path in self._tabs:  # Check if the tab exists
            del self._tabs[file_path]
            # self.tabRemoved.emit(file_path)

    def removeAllTabs(self):
        """Removes all tabs."""
        self._tabs.clear()
        # self.allTabsRemoved.emit()

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

#     Removal of Tabs and Associated Data: In removeFileTab, you handle the
#         removal process properly by checking if the tab exists in TabManager
#         before attempting to remove it. Just make sure this also covers any
#         associated data cleanup that might be needed to prevent memory leaks
#         or stale data.

#     Switching Tabs: When switching tabs (onSwitchTab), ensure that any
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
