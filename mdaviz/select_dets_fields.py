"""
QWidget to select stream data fields for plotting.

.. autosummary::

    ~SelectStreamsWidget
"""

from PyQt5 import QtCore
from PyQt5 import QtWidgets

from . import utils
from .select_fields_table_model import ColumnDataType
from .select_fields_table_model import FieldRuleType
from .select_fields_table_model import TableColumn
from .select_fields_table_model import TableField
from .select_fields_table_view import SelectFieldsTableView

COLUMNS = [
    TableColumn("Field", ColumnDataType.text),
    TableColumn("X", ColumnDataType.checkbox, rule=FieldRuleType.unique),
    TableColumn("Y", ColumnDataType.checkbox, rule=FieldRuleType.multiple),
    TableColumn("I0", ColumnDataType.checkbox, rule=FieldRuleType.unique),
    TableColumn("PV", ColumnDataType.text),
    TableColumn("DESC", ColumnDataType.text),
]

# WARNING: who loads the ui? select dets ot table view?


class SelectDetsWidget(QtWidgets.QWidget):
    ui_file = utils.getUiFileName(__file__)
    selected = QtCore.pyqtSignal(str, str, dict)

    def __init__(self, parent, file):
        self.parent = parent
        self.file = file
        super().__init__()
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()

    def setup(self):
        pass

    def setStream(self, stream_name):
        from functools import partial

        # TODO: This is for 1-D.  Generalize for multi-dimensional.
        x_name = None
        y_name = None
        if stream_name == self.analysis.stream_name:
            if len(self.analysis.plot_axes) > 0:
                x_name = self.analysis.plot_axes[0]
            y_name = self.analysis.plot_signal

        # describe the data fields for the dialog.
        fields = []
        for field_name in tapi.stream_data_fields(stream):
            selection = None
            if x_name is not None and field_name == x_name:
                selection = "X"
            elif y_name is not None and field_name == y_name:
                selection = "Y"
            shape = tapi.stream_data_field_shape(stream, field_name)
            field = TableField(field_name, selection=selection, shape=shape)
            fields.append(field)
        print("fields=%s", fields)

        # build the view of this stream
        view = SelectFieldsTableView(self)
        view.displayTable(COLUMNS, fields)
        view.selected.connect(partial(self.relayPlotSelections, stream_name))

        layout = self.groupbox.layout()
        utils.removeAllLayoutWidgets(layout)
        layout.addWidget(view)

    def relayPlotSelections(self, stream_name, action, selections):
        """Receive selections from the dialog and relay to the caller."""
        # selections["stream_name"] = self.stream_name
        self.selected.emit(stream_name, action, selections)


def to_datasets(stream, selections):
    x_axis = selections.get("X")
    if x_axis is None:
        x_data = None
    else:
        x_data = stream["data"][x_axis].compute()
        x_shape = x_data.shape
        if len(x_shape) != 1:
            # fmt: off
            raise ValueError(
                "Can only plot 1-D data now."
                f" {x_axis} shape is {x_shape}"
            )
            # fmt: on
        # if x_axis == "time":  # pyqtgraph does not plot datetime objects
        #     x_data = list(map(datetime.datetime.fromtimestamp, x_data))
        # https://pyqtgraph.readthedocs.io/en/latest/_modules/pyqtgraph/graphicsItems/DateAxisItem.html#

    datasets = []
    for y_axis in selections.get("Y", []):
        y_data = stream["data"][y_axis].compute()
        if len(y_data.shape) != 1:
            # fmt: off
            raise ValueError(
                "Can only plot 1-D data now."
                f" {y_axis} shape is {y_data.shape}"
            )

        if x_axis is None:
            ds = [y_data]  # , title=f"{y_axis} v index"
        else:
            if x_shape != y_data.shape:
                raise ValueError(
                    "Cannot plot.  Different shapes for"
                    f" X ({x_shape!r})"
                    f" and Y ({y_data.shape!r}) data."
                )
            ds = [x_data, y_data]
        datasets.append(ds)

    return datasets
