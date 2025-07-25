"""
Select data fields for plotting: QTableView.

Uses :class:`mda_file_table_model.MDAFileTableModel`.

.. autosummary::

    ~MDAFileTableView
"""

from PyQt6.QtWidgets import QWidget, QHeaderView
import numpy as np

from mdaviz import utils
from mdaviz.mda_file_table_model import ColumnDataType
from mdaviz.mda_file_table_model import FieldRuleType
from mdaviz.mda_file_table_model import TableColumn
from mdaviz.mda_file_table_model import TableField

HEADERS = "Field", "X", "Y", "I0", "Un", "PV", "DESC", "Unit"

COLUMNS = [
    TableColumn("Field", ColumnDataType.text),
    TableColumn("X", ColumnDataType.checkbox, rule=FieldRuleType.unique),  # type: ignore[arg-type]
    TableColumn("Y", ColumnDataType.checkbox, rule=FieldRuleType.multiple),  # type: ignore[arg-type]
    TableColumn("I0", ColumnDataType.checkbox, rule=FieldRuleType.unique),  # type: ignore[arg-type]
    TableColumn("Un", ColumnDataType.checkbox, rule=FieldRuleType.multiple),  # type: ignore[arg-type]
    TableColumn("PV", ColumnDataType.text),
    TableColumn("DESC", ColumnDataType.text),
    TableColumn("Unit", ColumnDataType.text),
]


class MDAFileTableView(QWidget):
    ui_file = utils.getUiFileName(__file__)

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
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

    def data(self):
        """Return the data from the table view:
        self.data=  {"fileInfo": fileInfo, "fields": fields}
        """
        return self._data

    def setData(self):
        """
        Populates the `_data` attribute with file information and data extracted
        from a file.

        The populated `_data` dictionary includes:
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

    def displayTable(self, selection_field):
        from mdaviz.mda_file_table_model import MDAFileTableModel
        from mdaviz.empty_table_model import EmptyTableModel

        if self.data() is not None:
            fields = self.data()["fields"]
            data_model = MDAFileTableModel(
                COLUMNS, fields, selection_field, self.mda_file.mda_mvc
            )
            self.tableView.setModel(data_model)
            # Hide Field column (Field = vertical header)
            # Note: I0 column (index 3) is now visible
            for i in [0]:
                self.tableView.hideColumn(i)
        else:
            # No MDA files to display, show an empty table with headers
            empty_model = EmptyTableModel(HEADERS)
            self.tableView.setModel(empty_model)

    def setStatus(self, text):
        self.mda_file.mda_mvc.setStatus(text)

    def clearContents(self):
        self.tableView.model().clearAllCheckboxes()
        self.tableView.setModel(None)

    def data2Plot(self, selections):
        """
        Extracts selected datasets for plotting from scanDict based on user selections.

        Parameters:
            - selections: A dictionary with keys "X", "Y", and optionally "I0", where "X" is the index for the x-axis data,
              "Y" is a list of indices for the y-axis data, and "I0" is the index for normalization data.

        Returns:
            - A tuple of (datasets, plot_options), where datasets is a list of tuples containing the
              data and options (label) for each dataset, and plot_options contains overall plotting configurations.

        """

        datasets, plot_options = [], {}

        if self.data() is not None:
            # ------ extract scan info:
            fileName = self.data()["fileInfo"]["fileName"]
            filePath = self.data()["fileInfo"]["filePath"]
            scanDict = self.data()["fileInfo"]["scanDict"]
            # ------ extract x data:
            x_index = selections.get("X")
            x_data = scanDict[x_index].get("data") if x_index in scanDict else None
            # ------ extract I0 data for normalization:
            i0_index = selections.get("I0")
            i0_data = scanDict[i0_index].get("data") if i0_index in scanDict else None
            # ------ extract y(s) data:
            y_index = selections.get("Y", [])
            un_index = selections.get("Un", [])
            y_first_unit = y_first_name = ""

            # Identify rows that need unscaling (have both Y and Un selected)
            unscaled_rows = set(y_index) & set(un_index)
            regular_y_rows = set(y_index) - unscaled_rows

            # Calculate global min/max for unscaling (from regular Y curves only)
            global_min = float("inf")
            global_max = float("-inf")
            if unscaled_rows and regular_y_rows:
                for y in regular_y_rows:
                    if y in scanDict:
                        y_data = scanDict[y].get("data")
                        if y_data is not None:
                            # Apply I0 normalization if I0 is selected
                            if i0_data is not None:
                                i0_data_safe = np.array(i0_data)
                                i0_data_safe[i0_data_safe == 0] = 1
                                y_data = np.array(y_data) / i0_data_safe
                            else:
                                y_data = np.array(y_data)
                            global_min = min(global_min, np.min(y_data))
                            global_max = max(global_max, np.max(y_data))

            # If no regular Y curves to reference, use 0 to 1 scale for unscaling
            if unscaled_rows and (
                global_min == float("inf") or global_max == float("-inf")
            ):
                global_min = 0.0
                global_max = 1.0

            # Process all Y curves
            for i, y in enumerate(y_index):
                if y not in scanDict:
                    continue
                y_data = scanDict[y].get("data")
                y_name = scanDict[y].get("name", "n/a")
                y_unit = scanDict[y].get("unit", "")

                # Apply I0 normalization if I0 is selected
                if i0_data is not None:
                    # Avoid division by zero
                    i0_data_safe = np.array(i0_data)
                    i0_data_safe[i0_data_safe == 0] = (
                        1  # Replace zeros with 1 to avoid division by zero
                    )
                    y_data = np.array(y_data) / i0_data_safe
                    # Display label shows base detector name with [norm] suffix for normalized data
                    y_label = f"{fileName}: {y_name} [norm]"
                    y_unit = ""  # Normalized data typically has no units
                else:
                    y_data = np.array(y_data)
                    y_unit = f"({y_unit})" if y_unit else ""
                    y_label = f"{fileName}: {y_name} {y_unit}"

                # Apply unscaling if this row has both Y and Un selected
                if (
                    y in unscaled_rows
                    and global_min != float("inf")
                    and global_max != float("-inf")
                ):
                    # Calculate min/max of this curve
                    m1, M1 = np.min(y_data), np.max(y_data)
                    # Apply unscaling formula: g(x) = ((f1(x) - m1) / (M1 - m1)) * (M23 - m23) + m23
                    if M1 != m1:  # Avoid division by zero
                        y_data = ((y_data - m1) / (M1 - m1)) * (
                            global_max - global_min
                        ) + global_min
                        y_label = f"{fileName}: {y_name} [unscaled]"
                        if i0_data is not None:
                            y_label = f"{fileName}: {y_name} [norm, unscaled]"

                if i == 0:
                    y_first_unit = y_unit
                    # y_first_name is used for y-axis label and shows normalization status
                    y_first_name = (
                        f"{y_name} [norm]"
                        if i0_data is not None
                        else f"{y_name} {y_unit}"
                    )

                # append to dataset:
                ds, ds_options = [], {}
                ds_options["label"] = y_label
                ds = [x_data, y_data] if x_data is not None else [y_data]
                datasets.append((ds, ds_options))

            # scanDict = {index: {'object': scanObject, 'data': [...], 'unit': '...', 'name': '...','type':...}}
            plot_options = {
                "x": scanDict[x_index].get("name", "") if x_index in scanDict else "",
                "x_unit": (
                    scanDict[x_index].get("unit", "") if x_index in scanDict else ""
                ),
                "y": y_first_name,
                "y_unit": y_first_unit,
                "title": "",
                "filePath": filePath,
                "fileName": fileName,
            }

        return datasets, plot_options
