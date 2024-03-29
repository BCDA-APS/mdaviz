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


class MDAFile(QtWidgets.QWidget):
    ui_file = utils.getUiFileName(__file__)
    selected = QtCore.pyqtSignal(str, dict)
    # fieldchange = QtCore.pyqtSignal(str, dict)  # TODO: not used?
    currentTabChanged = QtCore.pyqtSignal(int)  # Emit the index of the current tab

    def __init__(self, parent):
        """
        Create the table view and connect with its parent.

        PARAMETERS

        parent object:
            Instance of mdaviz.mda_folder.MDAMVC
        """

        self.mda_mvc = parent
        super().__init__()
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()

    def setup(self):
        from functools import partial

        self.setTabDict()
        self.setData()

        self.addButton.hide()
        self.replaceButton.hide()
        self.addButton.clicked.connect(partial(self.responder, "add"))
        self.clearButton.clicked.connect(partial(self.responder, "clear"))
        self.replaceButton.clicked.connect(partial(self.responder, "replace"))

        options = ["Auto-replace", "Auto-add", "Auto-off"]
        self.setMode(options[0])
        self.autoBox.addItems(options)
        self.autoBox.currentTextChanged.connect(self.setMode)
        self.autoBox.currentTextChanged.connect(self.updateButtonVisibility)

        self.tabWidget.currentChanged.connect(self.onCurrentTabChanged)
        self.tabWidget.tabCloseRequested.connect(self.removeFileTab)

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

    def tabDict(self):
        """The dict of opened tabs"""
        return self._tabDict

    def setTabDict(self, new_tab_dict=None):
        self._tabDict = new_tab_dict or {}

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

    # ------ Populating GUIs with selected file content:

    def displayMetadata(self, metadata):
        """Display metadata in the vizualization panel."""
        if not metadata:
            return
        metadata = utils.get_md(metadata)
        metadata = yaml.dump(metadata, default_flow_style=False)
        self.mda_mvc.mda_file_visualization.setMetadata(metadata)

    def displayData(self, tabledata):
        """Display pos(s) & det(s) values as a tableview in the vizualization panel."""
        if not self.data():
            return
        self.mda_mvc.mda_file_visualization.setTableData(tabledata)

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

    def addFileTab(self, index, selection_field):
        """
        Adds a new tab with a QTableView and QLabel for the selected file.

        Parameters:
        - index (int): The index of the selected file in the MDA file list.
        - selection_field (dict): The dictionary containing the selection of pos/det(s) to plot.
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

        # Update data & metadata:
        self.displayMetadata(metadata)
        self.displayData(tabledata)
        # Determine default selection if needed:
        selection_field = self.defaultSelection(first_pos, first_det, selection_field)

        # If file already opened in a tab, just switch to that tab:
        if file_path in self.tabDict():
            for tab_index in range(self.tabWidget.count()):
                widget = self.tabWidget.widget(tab_index)
                if widget.filePath.text() == file_path:
                    # Found the tab, switch to it
                    self.tabWidget.setCurrentIndex(tab_index)
                    break  # Exit the loop after switching to the tab

        # TODO: Directly Accessing Widgets for File Path: Accessing
        # widget.filePath.text() directly is fine as long as every widget added
        # to the tabWidget has a filePath attribute. Ensure this is consistently
        # applied across all widgets. An alternative approach is to use
        # QTabWidget's setTabData and tabData methods to store and retrieve the
        # file path or other metadata, which could abstract away the need to
        # directly interact with widget properties.

        # If opening a new file, create a new tab and update tab dictionary:
        else:
            mode = self.mode()  # ["Auto-replace", "Auto-add", "Auto-off"]
            if mode == "Auto-add":
                self.createNewTab(file_name, file_path, selection_field)
                tab_dict = self.tabDict()
                tab_dict[file_path] = {"metadata": metadata, "tabledata": tabledata}

            elif mode == "Auto-replace":
                # Clear all existing tabs:
                while self.tabWidget.count() > 0:
                    self.tabWidget.removeTab(0)
                self.createNewTab(file_name, file_path, selection_field)
                tab_dict = {}  # Starting fresh
                tab_dict[file_path] = {"metadata": metadata, "tabledata": tabledata}

            # Update the tab dictionary:
            self.setTabDict(tab_dict)

            # TODO implement auto-off: nothing happens?
            # the addition of a new tab /update of existing tab will only happen when Replace or Add is pushed?

    def createNewTab(self, file_name, file_path, selection_field):
        from .mda_file_table_view import MDAFileTableView

        # Create a new instance of MDAFileTableView for the selected file:
        self.file_tableview = MDAFileTableView(self)
        tab_index = self.tabWidget.addTab(self.file_tableview, file_name)
        self.tabWidget.setCurrentIndex(tab_index)
        self.file_tableview.displayTable(selection_field)
        # Access and update the QLabel for the filePath:
        filePathLabel = self.file_tableview.filePath
        filePathLabel.setText(file_path)

    def removeFileTab(self, index=None):
        """
        Removes a tab from the tab widget based on its index.
        """
        tab_dict = self.tabDict()
        if index is not None and index < self.tabWidget.count():
            current_tab = self.tabWidget.widget(index)
            filepath = current_tab.filePath.text() if current_tab else None
            # Ensure filepath is in tab_dict before attempting to remove
            if filepath and filepath in tab_dict:
                self.tabWidget.removeTab(index)
                tab_dict.pop(filepath, None)
                self.setTabDict(tab_dict)
                self.setStatus(f"Closed file tab {index=}, {filepath=}")
            else:
                self.setStatus(
                    f"Cannot find corresponding file tab: {index}, {filepath}"
                )
        else:
            self.setStatus("Invalid tab index provided.")

        if not tab_dict:  # If the dict of tabs is empty after removing one
            self.mda_mvc.mda_file_visualization.clearAllContent()  # Clear all content from the viz panel

    def onCurrentTabChanged(self, index):
        # index is the new current tab's index
        # Emit the signal to inform MDA_MVC about the change
        self.currentTabChanged.emit(index)

    # ------ Button methods:

    # FIXME: repsonder is no longer working

    def responder(self, action):
        """Modify the plot with the described action.
        action:
            from buttons: add, clear, replace
        """
        # TODO: need to use the UPDATED file_tableview, ie the one in the tab that is currently selected
        # would this be handled with mda_folder when it connects to it? I m not sure since it emits the stuff
        # from self.file_tableview

        print(
            f"\nResponder: {action=} - {self.file_tableview.tableView.model().plotFields()[0]}"
        )
        self.selected.emit(
            action, self.file_tableview.tableView.model().plotFields()[0]
        )

    def updateButtonVisibility(self):
        """Check the current text in "mode" pull down and show/hide buttons accordingly"""
        if self.autoBox.currentText() == "Auto-off":
            self.addButton.show()
            self.replaceButton.show()
        else:
            self.addButton.hide()
            self.replaceButton.hide()
