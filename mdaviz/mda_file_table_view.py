"""
Select data fields for plotting: QTableView.

Uses :class:`select_fields_tablemodel.SelectFieldsTableModel`.

.. autosummary::

    MDAFileTableView
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
            Instance of mdaviz.mda_file.MdaFile
        """

        self.mda_file = parent
        super().__init__()
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()

    def setup(self):

        self._pvList = None

        # Configure the horizontal header to resize based on content.
        header = self.tableView.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

    # def responder(self, action):
    #     """Modify the plot with the described action."""
    #     print(f"\nResponder: {action=}")
    #     self.selected.emit(action, self.tableView.model().plotFields()[0])

    def file(self):
        """Path object containing the entire absolute file path"""
        return self._file

    def fileName(self):
        """File name without the .mda extension"""
        return self._fileName

    def data(self):
        """Return the data from the table view:
        e.g. self.data=([TableField(name='P0', selection=None,...
                ...desc='Index', pv='Index', unit='a.u')
        """
        return self._data

    def firstPos(self):
        return self._firstPos

    def firstDet(self):
        return self._firstDet

    def pvList(self):
        return self._pvList

    def detsDict(self):
        return self._detsDict
            
       

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

    def displayTable(self, index):
        from .select_fields_table_model import SelectFieldsTableModel
        from .empty_table_model import EmptyTableModel

        if index is not None and self.mdaFileList():
            self.setData(index)
            fields = self.data()[0]     # entire list of TableFields ojects (all pos & dets) 
            selection_field = self.mda_file.mda_mvc.selectionField() 
            data_model = SelectFieldsTableModel(
                COLUMNS, fields, selection_field, self.mda_mvc
            )
            self.tableView.setModel(data_model)
            
            tab_list=self.tabList()
            
            if tab_list:
                ##### THIS IS WHERE MY PROBLEM IS?
                self.tabWidget.addTab()
                self.tabWidget.setTabText(len(tab_list), self.fileName())
            else:
                self.tabWidget.setTabText(0, self.fileName())
            # add entry to the list:
            tab_list.append(str(self.file()))
            self.setTabList(tab_list)
            
            # sets the tab label & file path QLabel:
            self.tabWidget.setTabText(0, self.fileName())
            filePath_QLabel = self.mda_mvc.findChild(QtWidgets.QLabel, "filePath_FTV")
            filePath_QLabel.setText(str(self.file().parent))

            
            
            # Hide Field/Mon/Norm columns (Field = vertical header, Mon & Norm not yet implemented)
            for i in [0, 3, 4]:
                self.tableView.hideColumn(i)
        else:
            # No MDA files to display, show an empty table with headers
            empty_model = EmptyTableModel(HEADERS)
            self.tableView.setModel(empty_model)

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
        self._pvList = [utils.byte2str(v.name) for v in detsDict.values()]

    def dataPath(self):
        """Path (obj) of the data folder."""
        return self.mda_file.mda_mvc.dataPath()

    def mdaFileList(self):
        """List of mda file (name only) in the selected folder."""
        return self.mda_file.mda_mvc.mdaFileList()

    def setStatus(self, text):
        self.mda_file.mda_mvc.setStatus(text)

    def clearContents(self):
        self.tableView.setModel(None)


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
