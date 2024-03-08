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
              self.data= fileName, scanDict, fields
        with:
        - fileInfo (dict): A dictionary of all the file information:
            - fileName (str): The name of the file without its extension.
            - filePath (str): The full path of the file.
            - folderPath (str): The full path of the parent folder.
            - metadata (dict): The extracted metadata from the file.
            - scanDict (dict): A dictionary of positioner & detector dataset for plot.
            - firstPos (float): The first positioner (P1, or if no positioner, P0 = index).
            - firstDet (float): The first detector (D01).
            - pvList (list of str): List of detectors PV names as strings.
        - field (list): List of TableField object, one for each det/pos:
                ([TableField(name='P0', selection=None,...
                ...desc='Index', pv='Index', unit='a.u'),...])
        """
        return self._data

    def setData(self):
        self._data = {}
        if self.mda_file.data() != {}:
            fileInfo = self.mda_file.data()
            scanDict = self.mda_file.data()["scanDict"]
            fields = [
                TableField(
                    v["fieldName"],
                    selection=None,
                    pv=v["name"],
                    desc=v["desc"],
                    unit=v["unit"],
                )
                for v in scanDict.values()
            ]
        self._data = {"fileInfo": fileInfo, "fields": fields}

    def displayTable(self):
        from .mda_file_table_model import MDAFileTableModel
        from .empty_table_model import EmptyTableModel

        print("\nEntering displayTable")
        if self.data() is not None:
            fields = self.data()["fields"]
            selection_field = self.mda_file.mda_mvc.selectionField()
            print(f"{selection_field=}")
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
        print(f"{self.data()['fileInfo']['fileName']=}")
        print("\nLeaving displayTable\n\n")

    def setStatus(self, text):
        self.mda_file.mda_mvc.setStatus(text)

    def clearContents(self):
        self.tableView.setModel(None)

    def data2Plot(self, selections):
        """
        Extracts selected datasets for plotting from scanDict based on user selections.

        Parameters:
        - selections: A dictionary with keys "X" and "Y", where "X" is the index for the x-axis data
        and "Y" is a list of indices for the y-axis data.

        Returns:
        - A tuple of (datasets, plot_options), where datasets is a list of tuples containing the
        data and options (label) for each dataset, and plot_options contains overall plotting configurations.

        Note:
        scanDict = {index: {'object': scanObject, 'data': [...], 'unit': '...', 'name': '...',
            'type':...}}.
        """

        datasets, plot_options = [], {}

        if self.data() is not None:
            # extract scan info:
            fileName = self.data()["fileInfo"]["fileName"]
            scanDict = self.data()["fileInfo"]["scanDict"]
            # extract x data:
            x_index = selections.get("X")
            x_data = scanDict[x_index]["data"] if x_index in scanDict else None
            # extract y(s) data:
            y_indeces = selections.get("Y", [])
            y_first_unit = y_first_name = ""
            for i, y in enumerate(y_indeces):
                if y not in scanDict:
                    continue
                y_data = scanDict[y]["data"]
                y_name = scanDict[y]["name"]
                y_unit = scanDict[y]["unit"]
                y_label = f"{fileName}: {y_name} ({y_unit})"
                if i == 0:
                    y_first_unit = y_unit
                    y_first_name = f"{y_name} ({y_unit})"
                # append to dataset:
                ds, ds_options = [], {}
                ds_options["label"] = y_label
                ds = [x_data, y_data] if x_data is not None else [y_data]
                datasets.append((ds, ds_options))

            plot_options = {
                "x": scanDict[x_index]["name"] if x_index in scanDict else "",
                "x_unit": scanDict[x_index]["unit"] if x_index in scanDict else "",
                "y": y_first_name,
                "y_unit": y_first_unit,
                "title": "",
                "folderPath": self.data()["fileInfo"]["folderPath"],
            }

        return datasets, plot_options
