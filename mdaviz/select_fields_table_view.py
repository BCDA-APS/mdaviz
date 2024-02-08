"""
Select data fields for plotting: QTableView.

Uses :class:`select_fields_tablemodel.SelectFieldsTableModel`.

.. autosummary::

    ~SelectFieldsTableView
"""

import datetime
from mda import readMDA
from PyQt5 import QtCore
from PyQt5 import QtWidgets
import yaml


from . import utils
from .select_fields_table_model import ColumnDataType
from .select_fields_table_model import FieldRuleType
from .select_fields_table_model import TableColumn
from .select_fields_table_model import TableField

COLUMNS = [
    TableColumn("Field", ColumnDataType.text),
    TableColumn("X", ColumnDataType.checkbox, rule=FieldRuleType.unique),
    TableColumn("Y", ColumnDataType.checkbox, rule=FieldRuleType.multiple),
    TableColumn("I0", ColumnDataType.checkbox, rule=FieldRuleType.unique),
    TableColumn("PV", ColumnDataType.text),
    TableColumn("DESC", ColumnDataType.text),
    TableColumn("Unit", ColumnDataType.text),
]


class SelectFieldsTableView(QtWidgets.QWidget):
    ui_file = utils.getUiFileName(__file__)
    selected = QtCore.pyqtSignal(str, dict)

    def __init__(self, parent):
        self.parent = parent
        super().__init__()
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()

    def setup(self):
        from functools import partial

        # since we cannot set header's ResizeMode in Designer ...
        header = self.tableView.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

        self.addButton.clicked.connect(partial(self.responder, "add"))
        self.clearButton.clicked.connect(partial(self.responder, "clear"))
        self.replaceButton.clicked.connect(partial(self.responder, "replace"))

        options = ["Auto-add", "Auto-replace", "Auto-off"]
        self._mode = options[0]
        self.autoBox.addItems(options)
        self.autoBox.currentTextChanged.connect(self.setMode)

    def responder(self, action):
        """Modify the plot with the described action."""
        print(f"/nResponder: {action=}")
        self.selected.emit(action, self.tableView.model().plotFields()[0])

    def file(self):
        return self._file

    def fileName(self):
        # File name without the .mda extension
        return self._fileName

    def data(self):
        return self._data

    def firstPos(self):
        return self._firstPos

    def firstDet(self):
        return self._firstDet

    def metadata(self):
        return self._metadata

    def detsDict(self):
        return self._detsDict

    def mode(self):
        return self._mode

    def setMode(self, *args):
        self._mode = args[0]

    def displayTable(self, index):
        from .select_fields_table_model import SelectFieldsTableModel

        self.setData(index)
        # here data is a list of TableField objects
        fields, first_pos, first_det = self.data()
        data_model = SelectFieldsTableModel(
            COLUMNS, fields, first_pos, first_det, self.parent
        )
        self.tableView.setModel(data_model)
        # sets the tab label to be the file name
        self.tabWidget.setTabText(0, self.file().name)

    def displayMetadata(self, index):
        self.parent.mda_file_visualization.setMetadata(self.getMetadata())

    def setData(self, index):
        file_name = self.mdaFileList()[index]
        file_path = self.dataPath() / file_name
        file_data = readMDA(file_path)[1]
        file_metadata = readMDA(file_path)[0]
        detsDict, first_pos, first_det = utils.get_det(file_data)
        fields = [
            TableField(
                utils.byte2str(v.fieldName),
                selection=None,
                pv=utils.byte2str(v.name),
                desc=utils.byte2str(v.desc),
                unit=utils.byte2str(v.unit),
            )
            for v in detsDict.values()
        ]
        self._firstPos = first_pos
        self._firstDet = first_det
        self._file = file_path
        self._fileName = file_name.rsplit(".mda", 1)[0]
        self._detsDict = detsDict
        self._data = fields, first_pos, first_det
        self._metadata = file_metadata

    def getMetadata(self):
        """Provide a text view of the file metadata."""
        metadata = utils.get_md(self.metadata())
        return yaml.dump(metadata, default_flow_style=False)

    def dataPath(self):
        """Path (obj) of the data folder."""
        return self.parent.dataPath()

    def mdaFileList(self):
        """List of mda file (name only) in the selected folder."""
        return self.parent.mdaFileList()

    def setStatus(self, text):
        self.parent.setStatus(text)


def to_datasets_mpl(fileName, detsDict, selections):
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
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    title = f"Plot Date & Time: {now}"

    plot_options = {
        "x": x_name,  # label for x axis
        "x_units": x_units,
        "y": ", ".join(y_names_with_units[0:1]),  # label for y axis
        "y_units": y_units,
        "title": title,
    }

    return datasets, plot_options
