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
        self.removeButton.clicked.connect(partial(self.responder, "remove"))
        self.replaceButton.clicked.connect(partial(self.responder, "replace"))

    def data(self):
        return self._data

    def metadata(self):
        return self._metadata

    def setData(self, index):
        file_name = self.mdaFileList()[index]
        file_path = self.dataPath() / file_name
        file_data = readMDA(file_path)[1]
        file_metadata = readMDA(file_path)[0]

        def get_det_dict(file_data):
            """det_dict = { index: [fieldname, pv, desc, unit]}"""
            D = {}
            p_list = [file_data.p[i] for i in range(0, file_data.np)]
            d_list = [file_data.d[i] for i in range(0, file_data.nd)]
            for e, p in enumerate(p_list):
                D[e] = [
                    utils.byte2str(p.fieldName),
                    utils.byte2str(p.name),
                    utils.byte2str(p.desc),
                    utils.byte2str(p.unit),
                ]
            for e, d in enumerate(d_list):
                D[e + len(p_list)] = [
                    utils.byte2str(d.fieldName),
                    utils.byte2str(d.name),
                    utils.byte2str(d.desc),
                    utils.byte2str(d.unit),
                ]
            return D

        dets = get_det_dict(file_data)
        fields = [
            TableField(v[0], selection=None, pv=v[1], desc=v[2], unit=v[3])
            for k, v in dets.items()
        ]
        self._data = fields
        self._metadata = file_metadata

    def responder(self, action):
        """Modify the plot with the described action."""
        self.selected.emit(action, self.tableView.model().plotFields())

    def displayTable(self, index):
        from .select_fields_table_model import SelectFieldsTableModel

        self.setData(index)
        data = self.data()
        data_model = SelectFieldsTableModel(
            COLUMNS, data, self.parent
        )  # here data is a list of TableField object
        self.tableView.setModel(data_model)
        # self.parent.mda_file_visualization.setMetadata(self.metadata())

    # def displayMetadata(self, index):
    #     self.setDataModel(index)
    #     model = self.dataModel()
    #     self.parent.mda_file_visualization.setMetadata(model.getMetadata())

    #################

    # def get_file_path(self, file):
    #     # here file is a Path obj Path('mda.0001.mda')
    #     return self.dataPath() / file

    # def get_file_data(self, file):
    #     filepath = str(self.get_file_path(file))
    #     return readMDA(filepath)[1]

    # def get_file_metadata(self, file):
    #     filepath = str(self.get_file_path(file))
    #     return readMDA(filepath)[0]

    # def get_det_dict(self, file):
    #     """det_dict = { index: [fieldname, pv, desc, unit]}"""
    #     D = {}
    #     data = self.get_file_data(file)
    #     p_list = [data.p[i] for i in range(0, data.np)]
    #     d_list = [data.d[i] for i in range(0, data.nd)]
    #     for e, p in enumerate(p_list):
    #         D[e] = [
    #             utils.byte2str(p.fieldName),
    #             utils.byte2str(p.name),
    #             utils.byte2str(p.desc),
    #             utils.byte2str(p.unit),
    #         ]
    #     for e, d in enumerate(d_list):
    #         D[e + len(p_list)] = [
    #             utils.byte2str(d.fieldName),
    #             utils.byte2str(d.name),
    #             utils.byte2str(d.desc),
    #             utils.byte2str(d.unit),
    #         ]
    #     return D

    ####################

    def dataPath(self):
        """Path (obj) of the data folder."""
        return self.parent.dataPath()

    def mdaFileList(self):
        """List of mda file (name only) in the selected folder."""
        return self.parent.mdaFileList()

    def setStatus(self, text):
        self.parent.setStatus(text)
