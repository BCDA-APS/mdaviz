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
    fieldchange = QtCore.pyqtSignal(str, dict)

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

        self.setTabList()
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

        self.tabWidget.tabCloseRequested.connect(self.removeFileTab)

    def dataPath(self):
        """Path (obj) of the data folder."""
        return self.mda_mvc.dataPath()

    def mdaFileList(self):
        """List of mda file (name only) in the selected folder."""
        return self.mda_mvc.mdaFileList()

    # ------ Get & set methods:

    def mode(self):
        return self._mode

    def setMode(self, *args):
        self._mode = args[0]

    def tabList(self):
        """The list of opened tabs"""
        return self._tabList

    def setTabList(self, new_tab_list=None):
        self._tabList = new_tab_list or []

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
        Defaults to None, resulting in self._data = None.

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

    def metadata(self):
        """Provide a text view of the file metadata."""
        metadata = utils.get_md(self.data()["metadata"])
        return yaml.dump(metadata, default_flow_style=False)

    def displayMetadata(self):
        """Display metadata in the vizualization panel."""
        self.mda_mvc.mda_file_visualization.setMetadata(self.metadata())

    def displayData(self):
        """Display pos(s) & det(s) values as a tableview in the vizualization panel."""
        self.mda_mvc.mda_file_visualization.setTableData(self.data()["scanDict"])

    def addFileTab(self, index, selection_field):
        """
        Adds a new tab with a QTableView and QLabel for the selected file.

        Parameters:
        - index (int): The index of the selected file in the MDA file list.
        """

        from .mda_file_table_view import MDAFileTableView

        print("\nEntering addFileTab")

        # Get data for the selected file:
        self.setData(index)
        file_path = self.data()["filePath"]
        file_name = self.data()["fileName"]
        first_pos = self.data()["firstPos"]
        first_det = self.data()["firstDet"]
        print(f"{first_pos=}")
        print(f"{first_det=}")

        print(f"\nBefore default: {selection_field=}")

        def defaultSelection(first_pos_idx=None, first_det_idx=None):
            print(f"\nIn default: {first_pos_idx=},{first_det_idx=}")
            if first_pos_idx is not None and first_det_idx is not None:
                default_selection = {"X": first_pos_idx, "Y": [first_det_idx]}
            else:
                default_selection = None
            print(f"\nResult: {default_selection=}")
            return default_selection

        if selection_field is None:
            default = defaultSelection(first_pos, first_det)

            self.mda_mvc.setSelectionField(default)
            selection_field = default
            print(f"\nAfter default: {selection_field=}")

        tab_list = self.tabList()
        if file_path in tab_list:
            # If file already opened in a tab, just switch to that tab:
            tab_index = tab_list.index(file_path)
            self.tabWidget.setCurrentIndex(tab_index)

        else:
            # Create a new instance of MDAFileTableView for the selected file:
            self.file_tableview = MDAFileTableView(self)
            # addTab returns the index of the new tab:
            tab_index = self.tabWidget.addTab(self.file_tableview, file_name)
            self.tabWidget.setCurrentIndex(tab_index)

            self.file_tableview.displayTable(selection_field)

            # Add selected file to the list of open tabs:
            tab_list.append(file_path)
            self.setTabList(tab_list)

            # Access and update the QLabel for the filePath:
            filePathLabel = self.file_tableview.filePath
            filePathLabel.setText(file_path)
        print(f"{self.data()['fileName']=}")
        print("\nLeaving addFileTab")

    def removeFileTab(self, *args):
        """

        Removes a tab from the tab widget based on a file path or index (1st arg).

        If the file path or index is valid and corresponds to an open tab, removes
        the tab from the widget and updates the status. If no valid arguments are
        provided or the tab cannot be found, the status is updated with an error
        message.

        Parameters:
        - args: can either be a string (file path) or an integer (index).
        """

        tab_list = self.tabList()
        filepath = None
        index = None
        if not args:
            self.setStatus("No arguments provided to removeTab method.")
            return
        if isinstance(args[0], int):
            index = args[0]
            if index < len(tab_list):
                filepath = tab_list[index]
            else:
                index = None
        elif isinstance(args[0], str):
            filepath = args[0]
            if filepath in tab_list:
                index = tab_list.index(filepath)
            else:
                filepath = None
        # If both index and filepath are determined successfully, remove the tab
        if index is not None and filepath is not None:
            self.tabWidget.removeTab(index)
            tab_list.remove(filepath)  # Safely remove filepath since we know it exists
            self.setTabList(tab_list)
            self.setStatus(f"Closed file tab {index=}, {filepath=}")
        else:
            self.setStatus(
                f"Cannot find corresponding file tab:  {index=}, {filepath=}"
            )

    # TODO# TODO# TODO# TODO# TODO# TODO# TODO# TODO# TODO# TODO# TODO# TODO
    # TODO : need a switch tab: update metadata and data, not plot    # TODO
    # TODO# TODO# TODO# TODO# TODO# TODO# TODO# TODO# TODO# TODO# TODO# TODO

    # ------ Button methods:

    def responder(self, action):
        """Modify the plot with the described action

        PARAMETERS

        action:
            from buttons: add, clear, replace

        """
        print(f"\nResponder: {action=}")
        self.selected.emit(action, self.tableView.model().plotFields()[0])

    def updateButtonVisibility(self):
        """Check the current text in "mode" pull down and show/hide buttons accordingly"""
        if self.autoBox.currentText() == "Auto-off":
            self.addButton.show()
            self.replaceButton.show()
        else:
            self.addButton.hide()
            self.replaceButton.hide()
