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

        # self._pvList = None
        self.setTabList()
        self.setData()

        self.addButton.hide()
        self.replaceButton.hide()
        self.addButton.clicked.connect(partial(self.responder, "add"))
        self.clearButton.clicked.connect(partial(self.responder, "clear"))
        self.replaceButton.clicked.connect(partial(self.responder, "replace"))

        options = ["Auto-replace", "Auto-add", "Auto-off"]
        self._mode = options[0]
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

    # def firstPos(self):
    #     return self._firstPos

    # def firstDet(self):
    #     return self._firstDet

    # def pvList(self):
    #     return self._pvList

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

        # QUESTION: do I need to store the "data" for all the open files or
        # (like right now) just the one I am dealing with now (i.e. selected
        # file)?

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
        - xy (list): The extracted data from the file.
        - metadata (dict): The extracted metadata from the file.
        - scanDict (dict): A dictionary of positioner & detector information.
        - firstPos (float): The first positioner (P1, or if no positioner, P0 = index).
        - firstDet (float): The first detector (D01).
        - pvList (list of str): List of detectors PV names as strings.

        Note: This method modifies the object's state by setting the `_data`
        attribute.
        """
        data = None
        if index is not None:
            data = {}
            file_name = self.mdaFileList()[index]
            file_path = self.dataPath() / file_name
            folder_path = self.dataPath()
            file_metadata, file_data = readMDA(file_path)
            scanDict, first_pos, first_det = utils.get_det(file_data)
            pvList = [utils.byte2str(v.name) for v in scanDict.values()]
            data = {
                "fileName": file_name.rsplit(".mda", 1)[0],
                "filePath": str(file_path),
                "folderPath": str(folder_path),
                "xy": file_data,
                "metadata": file_metadata,
                "scanDict": scanDict,
                "firstPos": first_pos,
                "firstDet": first_det,
                "pvList": pvList,
                "index": index,
            }
        self._data = data

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

    def addFileTab(self, index):
        """
        Adds a new tab with a QTableView and QLabel for the selected file.

        Parameters:
        - index (int): The index of the selected file in the MDA file list.
        """

        # TODO: make sure to not reopen a new tab with a file that is already opened.

        from .mda_file_table_view import MDAFileTableView

        # Get data for the selected file:
        self.setData(index)
        file_path = self.data()["filePath"]
        file_name = self.data()["fileName"]

        if file_path in tab_list:
            # If file already opened in a tab, just switch to that tab:
            tab_index = tab_list.index(file_path)
            self.tabWidget.setCurrentIndex(tab_index)

        else:
            # Create a new instance of MDAFileTableView for the selected file:
            self.file_tableview = MDAFileTableView(self)
            tab_index = self.tabWidget.addTab(self.file_tableview, file_name)
            self.tabWidget.setCurrentIndex(tab_index)

            self.file_tableview.displayTable()

            # Add selected file to the list of open tabs:
            tab_list.append(file_path)
            self.setTabList(tab_list)

            # Access and update the QLabel for the filePath:
            filePathLabel = self.file_tableview.filePath
            filePathLabel.setText(file_path)
            # change to full path vs just folder_path:
            # can't read the tab label when too many tabs open!

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

    # ------ Creating datasets for the selected file:

    # QUESTION: SHOULD THIS BE HERE OR IN MDA_FILE? WE NEED TO KEEP TRACK OF
    # THE FILE PATH (BETTER THAN INDEX, 2 DIFFERENT FILE IN DIFFERENT FOLDER CAN
    # HAVE THE SAME INDEX). =====> MAKE DATASETS PART OF SELF.MDA_FILE.DATA()

    def to_datasets(self):  # , selections):
        # I Want to save all the datasets for all the POS/DET in self.data()["scanDict"], will deal with the selection in mda_file_TV
        """Prepare datasets and options for plotting with Matplotlib."""

        from mda import scanPositioner, scanDetector

        datasets = []
        file_name = self.data()["fileName"]
        scan_dict = self.data()["scanDict"]
        first_pos = self.data()["firstPos"]
        first_det = self.data()["firstDet"]

        # Assuming detsDict is your dictionary and mda.scanPositioner and mda.scanDetector are your classes
        pos_list = [
            value for value in scan_dict.values() if isinstance(value, scanPositioner)
        ]
        det_list = [
            value for value in scan_dict.values() if isinstance(value, scanDetector)
        ]

        x_dataset = {}

        for e, x in enumerate(pos_list):
            x_data = x.data or None
            x_unit = utils.byte2str(x.unit) or "a.u."
            x_name = utils.byte2str(x.name) + f" ({x_unit})"
            x_dataset[e] = [x_data, x_unit, x_name]

            # y_axis is the list of row numbers
            y_names_with_units = []
            y_names_with_file_units = []
            for y_axis in selections.get("Y", []):
                y = dets_dict[y_axis]
                y_data = y.data
                # y labels:
                y_units = utils.byte2str(y.unit) if y.unit else "a.u."
                y_name = utils.byte2str(y.name)
                y_name_with_units = y_name + "  (" + y_units + ")"
                y_name_with_file_units = (
                    file_name + ": " + y_name + "  (" + y_units + ")"
                )
                y_names_with_units.append(y_name_with_units)
                y_names_with_file_units.append(y_name_with_file_units)
                # append to dataset:
                ds, ds_options = [], {}
                ds_options["label"] = y_name_with_file_units
                ds = [x_data, y_data] if x_data is not None else [y_data]
                datasets.append((ds, ds_options))

            plot_options = {
                "x": x_name,  # label for x axis
                "x_units": x_units,
                "y": ", ".join(y_names_with_units[0:1]),  # label for y axis
                "y_units": y_units,
                "title": "",
            }
        return datasets, plot_options
