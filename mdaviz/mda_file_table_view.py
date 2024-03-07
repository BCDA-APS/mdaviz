"""
Select data fields for plotting: QTableView.

Uses :class:`select_fields_tablemodel.SelectFieldsTableModel`.

.. autosummary::

    MDAFileTableView
"""

from mda import readMDA
from PyQt5 import QtCore
from PyQt5 import QtWidgets


from . import utils
from .mda_file_table_model import ColumnDataType
from .mda_file_table_model import FieldRuleType
from .mda_file_table_model import TableColumn
from .mda_file_table_model import TableField

HEADERS = "Field", "X", "Y", "Mon", "Norm", "PV", "DESC", "Unit"

COLUMNS = [
    TableColumn("Field", ColumnDataType.text),
    TableColumn("X", ColumnDataType.checkbox, rule=FieldRuleType.unique),
    TableColumn("Y", ColumnDataType.checkbox, rule=FieldRuleType.multiple),
    TableColumn("Mon", ColumnDataType.checkbox, rule=FieldRuleType.unique),
    TableColumn("Norm", ColumnDataType.checkbox, rule=FieldRuleType.multiple),
    TableColumn("PV", ColumnDataType.text),
    TableColumn("DESC", ColumnDataType.text),
    TableColumn("Unit", ColumnDataType.text),
]


class MDAFileTableView(QtWidgets.QWidget):
    ui_file = utils.getUiFileName(__file__)
    selected = QtCore.pyqtSignal(str, dict)
    fieldchange = QtCore.pyqtSignal(str, dict)

    def __init__(self, parent):
        """
        Create the table view and connect with its parent.

        PARAMETERS

        parent object:
            Instance of mdaviz.mda_file.MDAFile
        """

        self.mda_file = parent
        super().__init__()
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()

    def setup(self):
        self.setData()
        # Configure the horizontal header to resize based on content.
        header = self.tableView.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

    def data(self):
        """Return the data from the table view:
              self.data= fileName, detsDict, fields
        with:
        - fileName (str): The name of the file without its extension.
        - detsDict (dict): A dictionary of positioner & detector information.
        - field (list): List of TableField object, one for each det/pos:
                ([TableField(name='P0', selection=None,...
                ...desc='Index', pv='Index', unit='a.u'),...])
        """
        return self._data

    def setData(self):
        self._data = None
        if self.mda_file.data() is not None:
            detsDict = self.mda_file.data()["detsDict"]
            fileName = self.mda_file.data()["fileName"]
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
        self._data = {"fileName": fileName, "detsDict": detsDict, "fields": fields}

    def displayTable(self):
        from .mda_file_table_model import MDAFileTableModel
        from .empty_table_model import EmptyTableModel

        if self.data() is not None:
            fields = self.data()["fields"]
            selection_field = self.mda_file.mda_mvc.selectionField()
            data_model = MDAFileTableModel(
                COLUMNS, fields, selection_field, self.mda_file.mda_mvc
            )
            self.tableView.setModel(data_model)
            # Hide Field/Mon/Norm columns (Field = vertical header, Mon & Norm not yet implemented)
            for i in [0, 3, 4]:
                self.tableView.hideColumn(i)
        else:
            # No MDA files to display, show an empty table with headers
            empty_model = EmptyTableModel(HEADERS)
            self.tableView.setModel(empty_model)

    def setStatus(self, text):
        self.mda_file.mda_mvc.setStatus(text)

    def clearContents(self):
        self.tableView.setModel(None)

    # ------ Creating datasets for the selected file:

    # QUESTION: SHOULD THIS BE HERE OR IN MDA_FILE? WE NEED TO KEEP TRACK OF
    # THE FILE PATH (BETTER THAN INDEX, 2 DIFFERENT FILE IN DIFFERENT FOLDER CAN
    # HAVE THE SAME INDEX). =====> MAKE DATASETS PART OF SELF.MDA_FILE.DATA()

    def to_datasets(self, selections):
        """Prepare datasets and options for plotting with Matplotlib."""
        datasets = []
        file_name = self.data()["fileName"]
        detsDict = self.data()["detsDict"]

        # x_axis is the row number
        x_axis = selections.get("X")
        x_data = detsDict[x_axis].data if x_axis is not None else None
        x_units = (
            utils.byte2str(detsDict[x_axis].unit) if x_axis is not None else "a.u."
        )
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
            y_name_with_file_units = file_name + ": " + y_name + "  (" + y_units + ")"
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
