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
        - fileName (str): The name of the file without its extension.
        - scanDict (dict): A dictionary of positioner & detector information.
        - field (list): List of TableField object, one for each det/pos:
                ([TableField(name='P0', selection=None,...
                ...desc='Index', pv='Index', unit='a.u'),...])
        """
        return self._data

    def setData(self):
        self._data = None
        if self.mda_file.data() is not None:
            scanDict = self.mda_file.data()["scanDict"]
            fileName = self.mda_file.data()["fileName"]
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
        self._data = {"fileName": fileName, "scanDict": scanDict, "fields": fields}

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

    def subDatasets(self, selections):
        pass
