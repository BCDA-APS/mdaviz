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

        self.tabWidget.tabCloseRequested.connect(self.removeTab)

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
        file list to read and extract data from. Defaults to None, resulting in
        no operation.

        The populated `_data` dictionary includes:
        - fileName (str): The name of the file without its extension.
        - filePath (Path): The full path of the file as a Path object.
        - xy (list): The extracted data from the file.
        - metadata (dict): The extracted metadata from the file.
        - detsDict (dict): A dictionary of positioner & detector information.
        - firstPos (float): The first positioner (P1, or if no positioner, P0 = index).
        - firstDet (float): The first detector (D01).
        - pvList (list of str): List of detectors PV names as strings.

        Note: This method modifies the object's state by setting the `_data`
        attribute.
        """
        data = {}
        if index is not None:
            file_name = self.mdaFileList()[index]
            file_path = self.dataPath() / file_name
            file_metadata, file_data = readMDA(file_path)
            detsDict, first_pos, first_det = utils.get_det(file_data)
            pvList = [utils.byte2str(v.name) for v in detsDict.values()]
            data = {
                "fileName": file_name.rsplit(".mda", 1)[0],
                "filePath": file_path,
                "xy": file_data,
                "metadata": file_metadata,
                "detsDict": detsDict,
                "firstPos": first_pos,
                "firstDet": first_det,
                "pvList": pvList,
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
        self.mda_mvc.mda_file_visualization.setMetadata(self.metadata())

    def displayData(self):
        self.mda_mvc.mda_file_visualization.setTableData(self.data()["detsDict"])

    def addFileTab(self, index, tableModel=None):
        """
        Adds a new tab with a QTableView and QLabel for the file path.

        Parameters:
        tableModel (QAbstractTableModel): The model to set for the QTableView.
        """
        from .mda_file_table_view import MDAFileTableView

        self.setData(index)

        tab_list = self.tabList()
        print(f"\n{tab_list=}")
        file_path = str(self.data()["filePath"])
        print(f"{file_path=}")
        tab_list.append(file_path)
        print(f"{tab_list=}")
        self.setTabList(tab_list)
        print(f"{self.tabList()}=")

        self.file_tableview = MDAFileTableView(self)
        self.tabWidget.addTab(self.file_tableview, self.data()["fileName"])

        filePathLabel = self.file_tableview.filePath  # Access the QLabel for FilePath
        filePathLabel.setText(str(self.data()["filePath"].parent))

    def removeTab(self, *args):
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

    # def displayTable(self, index):
    #     from .select_fields_table_model import SelectFieldsTableModel
    #     from .empty_table_model import EmptyTableModel

    #     if index is not None and self.mdaFileList():
    #         self.setData(index)
    #         filePathLabel = self.mda_mvc.findChild(QtWidgets.QLabel, "filePath_FTV")
    #         filePathLabel.setText(str(self.file().parent))
    #         fields, first_pos, first_det = self.data()
    #         selection_field = self.mda_mvc.selectionField()
    #         data_model = SelectFieldsTableModel(
    #             COLUMNS, fields, selection_field, self.mda_mvc
    #         )
    #         self.tableView.setModel(data_model)
    #         # sets the tab label to be the file name
    #         self.tabWidget.setTabText(0, self.file().name)
    #         # Hide Field/Mon/Norm columns (Field = vertical header, Mon & Norm not yet implemented)
    #         for i in [0, 3, 4]:
    #             self.tableView.hideColumn(i)
    #     else:
    #         # No MDA files to display, show an empty table with headers
    #         empty_model = EmptyTableModel(HEADERS)
    #         self.tableView.setModel(empty_model)

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


def to_datasets(fileName, detsDict, selections):
    """Prepare datasets and options for plotting with Matplotlib."""
    datasets = []

    # x_axis is the row number
    x_axis = selections.get("X")
    x_data = detsDict[x_axis].data if x_axis is not None else None
    x_units = utils.byte2str(detsDict[x_axis].unit) if x_axis is not None else "a.u."
    x_name = (
        utils.byte2str(detsDict[x_axis].name) + f" ({x_units})"
        if x_axis is not None
        else "Index"
    )

    # y_axis is the list of row numbers
    y_names_with_units = []
    y_names_with_file_units = []
    for y_axis in selections.get("Y", []):
        y = detsDict[y_axis]
        y_data = y.data
        # y labels:
        y_units = utils.byte2str(y.unit) if y.unit else "a.u."
        y_name = utils.byte2str(y.name)
        y_name_with_units = y_name + "  (" + y_units + ")"
        y_name_with_file_units = fileName + ": " + y_name + "  (" + y_units + ")"
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
