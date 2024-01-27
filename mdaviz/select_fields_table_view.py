"""
Select data fields for plotting: QTableView.

Uses :class:`select_fields_tablemodel.SelectFieldsTableModel`.

.. autosummary::

    ~SelectFieldsTableView
"""

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
        self.removeButton.clicked.connect(partial(self.responder, "remove"))
        self.replaceButton.clicked.connect(partial(self.responder, "replace"))

    def file(self):
        return self._file

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

    def responder(self, action):
        """Modify the plot with the described action."""
        # print(f"Responder action: {action}, Widget state: {self.checkWidgetState()}")
        self.selected.emit(action, self.tableView.model().plotFields()[0])

    def checkWidgetState(self):
        # for debugging purposes
        return {
            "isVisible": self.isVisible(),
            "isEnabled": self.isEnabled(),
        }

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


def to_datasets_qt(detsDict, selections):
    """Prepare datasets and options for plotting."""

    from . import chartview

    datasets = []
    x_axis = selections.get("X")  # x_axis is the row number
    x_datetime = False  # special scaling using datetime: is it applicable for mda?
    if x_axis is None:
        x_data = None
    else:
        x = detsDict[x_axis]
        x_data = x.data
    y_names = []
    for y_axis in selections.get("Y", []):  # x_axis is the list of row number
        y = detsDict[y_axis]
        y_data = y.data
        y_units = utils.byte2str(y.unit)
        y_name = utils.byte2str(y.name)
        y_names.append(y_name)
        ds, ds_options = [], {}
        color = chartview.auto_color()
        symbol = chartview.auto_symbol()
        ds_options["name"] = f"{y_name})"  # label for this curve
        ds_options["pen"] = color  # line color                 $ color for this curve
        ds_options["symbol"] = symbol
        ds_options["symbolBrush"] = color  # fill color
        ds_options["symbolPen"] = color  # outline color
        # size in pixels (if pxMode==True, then data coordinates.)
        ds_options["symbolSize"] = 10  # default: 10
        ds_options["width"] = 2

        if x_data is None:
            ds = [y_data]  # , title=f"{y_name} v index"
        else:
            ds = [x_data, y_data]
        datasets.append((ds, ds_options))
    plot_options = {
        "x_datetime": x_datetime,
        "x_units": utils.byte2str(x.unit) if x_axis else "",
        "x": utils.byte2str(x.name) if x_axis else "Index",  # label for x axis
        "y_units": y_units,
        "y": ",\t".join(y_names),  # label for y axis
        "title": f"{y_names} v index",  # TODO: To be confirmed, is that a correct title?
    }

    return datasets, plot_options


def to_datasets_mpl(detsDict, selections):
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
    y_names = []
    for y_axis in selections.get("Y", []):
        y = detsDict[y_axis]
        y_data = y.data
        y_units = utils.byte2str(y.unit) if y.unit else "a.u."
        y_name = utils.byte2str(y.name) + f" ({y_units})"
        y_names.append(y_name)

        ds, ds_options = [], {}
        ds_options["label"] = f"{y_name}"
        ds = [x_data, y_data] if x_data is not None else [y_data]
        datasets.append((ds, ds_options))

    title = ""
    if len(y_names) == 1:
        title = f"{y_name} vs {x_name}"
    elif len(y_names) <= 3:
        title = "[" + " ,  ".join(y_names) + f"]\n vs {x_name}"
    else:
        title = "[" + " ,  ".join(y_names[0:3]) + f", ...]\n vs {x_name}"

    plot_options = {
        "x": x_name,  # label for x axis
        "x_units": x_units,
        "y": ", ".join(y_names[0:3]),  # label for y axis
        "y_units": y_units,
        "title": title,
    }

    return datasets, plot_options
