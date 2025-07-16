"""
Select data fields for 1-D plotting: QAbstractTableModel.

General plot model is: Y/Mon vs X.  If X is not selected, use index number. If
Mon is not selected, use 1.0 (trivial case, do not divide by Mon).

Data Field Selection Rules:

1. A data field selection could have one of four states:
    * unselected (`None`)
    * `"X"`: abscissa (independent axis)
    * `"Y"` : ordinate (dependent axes)
    * `"Mon"` : divide this array into each Y
2. Only zero or one data field can be selected as `"X"`.
3. Only zero or one data field can be selected as `"Mon"`.
4. One or more data fields can be selected as `"Y"`.

When Model/View is created, the view should call 'model.setFields(fields)' with
the list of field names for selection.  (If 'fields' is a different structure,
such a 'list(object)' or 'dict(str=object)', then change both 'columns()' and
'fields()' so that each returns 'list(str)'.)  Note that
'model.setFields(fields)' can only be called once.

.. autosummary::

    ~MDAFileTableModel
    ~ColumnDataType
    ~FieldRuleType
    ~TableColumn
    ~TableField
"""

from typing import Optional, List, Dict, Tuple
from .utils import mda2ftm, ftm2mda
from dataclasses import KW_ONLY
from dataclasses import dataclass

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtCore import QAbstractTableModel


class ColumnDataType:
    """Data types expected by TableColumn.column_type."""

    checkbox = "checkbox"
    text = "text"


class FieldRuleType:
    """Data field selection rule types."""

    multiple = "multiple"
    unique = "unique"

    def apply(self, *args, **kwargs):
        """Apply the selection rule."""


@dataclass(frozen=True)
class TableColumn:
    """One column of the table."""

    name: str
    column_type: str
    _: KW_ONLY  # all parameters below are specified by keyword
    rule: Optional[FieldRuleType] = None
    # This is an optional attribute.
    # It can either be an instance of FieldRuleType or None.
    # Its default value is None.


@dataclass(frozen=True)
class TableField:
    """One data field candidate for user-selection.

    NOTE: Data for the "Description" and "PV" TableColumns is
    provided by the "description" and "pv" attributes here
    using `cname.lower()`.  # WARNING: This could break if attribute names change.
    """

    name: str  # the "D#" column
    selection: Optional[str] = None  # either of these, selection rule 1.
    _: KW_ONLY  # all parameters below are specified by keyword
    desc: str = ""  # the "desc" column
    pv: str = ""  # the "PV" column
    unit: str = ""  # the "unit" column


class MDAFileTableModel(QAbstractTableModel):
    """
    Select fields for plots.

    .. autosummary::

        ~rowCount
        ~columnCount
        ~data
        ~headerData
        ~setData
        ~flags
        ~checkbox
        ~applySelectionRules
        ~updateCheckboxes
        ~logCheckboxSelections
        ~columnName
        ~columnNumber
        ~columns
        ~setColumns
        ~fieldName
        ~fieldText
        ~fields
        ~setFields
        ~plotFields

    https://doc.qt.io/qtforpython-5/PySide2/QtCore/QAbstractTableModel.html
    """

    # Signals in PyQt6 should be class attributes, not instance attributes, to work properly.
    # They need to be defined at the class level so that PyQt can set them up correctly when instances of the class are created.

    checkboxStateChanged = pyqtSignal(
        dict, list
    )  # emit field selection and the list containing the DET (Y field) that have been removed

    def __init__(self, columns, fields, selection_field, parent=None):
        """
        Create the table model and connect with its parent.

        PARAMETERS

        parent object:
            Instance of mdaviz.mda_folder.MDAMVC
        """
        super().__init__()
        self.mda_mvc = parent
        self.selections = mda2ftm(selection_field)
        self._columns_locked, self._fields_locked = False, False
        self.setColumns(columns)
        self.setFields(fields)
        self._columns_locked, self._fields_locked = True, True
        self.updateCheckboxes()
        self.highlightedRow = None

    # ------------ methods required by Qt's view

    def rowCount(self, parent=None):
        """Number of fields."""
        return len(self.fields())

    def columnCount(self, parent=None):
        """Return the number of columns in the table."""
        return len(self.columns())

    def data(self, index, role):
        """Return the data for the given index and role."""
        if not index.isValid():
            return None

        row = index.row()
        column = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            # Only show text for text columns
            if column in self.textColumns:
                if column == 0:  # Name column
                    return self.fieldName(row)
                else:
                    return self.fieldText(index)
            # For checkbox columns, return empty string for display role
            # (the checkbox will be shown via CheckStateRole)
            return ""

        elif role == Qt.ItemDataRole.CheckStateRole:
            # Only show checkboxes for checkbox columns
            if column in self.checkboxColumns:
                return self.checkbox(index)
            return None

        elif role == Qt.ItemDataRole.BackgroundRole:
            if row == self.highlightedRow:
                return QBrush(QColor(210, 226, 247))

        return None

    def headerData(self, section, orientation, role):
        """Return the header data for the given section and role."""
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self.columnName(section)
            elif orientation == Qt.Orientation.Vertical:
                return str(section + 1)
        return None

    def flags(self, index):
        """Return the flags for the given index."""
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags

        column = index.column()
        flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

        # Make checkbox columns checkable
        if column in self.checkboxColumns:
            flags |= Qt.ItemFlag.ItemIsUserCheckable

        return flags

    def setHighlightRow(self, row=None):
        self.highlightedRow = row
        self.layoutChanged.emit()  # Refresh the view

    def unhighlightRow(self, row):
        if self.highlightedRow == row:
            self.highlightedRow = None
            self.layoutChanged.emit()

    # ------------ checkbox methods

    def checkbox(self, index):
        """Return the checkbox state for a given cell: (row, column) = (index.row(), index.column())."""
        nm = self.columnName(index.column())  # selection name of THIS column
        selection = self.selections.get(index.row())  # user selection
        return Qt.CheckState.Checked if selection == nm else Qt.CheckState.Unchecked

    def setCheckbox(self, index, state):
        """Set the checkbox state."""
        old_selection = ftm2mda(self.selections)
        row, column = index.row(), index.column()
        column_name = self.columnName(column)
        checked = state == Qt.CheckState.Checked
        prior = self.selections.get(row)  # value if row exist as a key, None otherwise
        self.selections[row] = column_name if checked else None  # Rule 1
        changes = self.selections[row] != prior
        changes = self.applySelectionRules(index, changes)
        if changes:
            det_removed = self.updateCheckboxes(old_selection=old_selection)
            self.checkboxStateChanged.emit(self.plotFields(), det_removed)

    def checkCheckBox(self, row, column_name):
        self.selections[row] = (
            column_name  # Mark the checkbox as checked by updating 'selections'
        )
        col = self.columnNumber(column_name)  # Translate column name to its index
        index = self.index(row, col)
        self.dataChanged.emit(
            index, index, [Qt.ItemDataRole.CheckStateRole]
        )  # Update view with Qt.CheckStateRole

    def uncheckCheckBox(self, row):
        if row in self.selections:
            # Get the column index of the checkbox being unchecked
            col = self.columnNumber(self.selections[row])
            # Remove the selection
            del self.selections[row]
            # Update view
            index = self.index(row, col)
            self.dataChanged.emit(
                index, index, [Qt.ItemDataRole.CheckStateRole]
            )  # Qt.CheckStateRole
            # Update the mda_mvc selection
            self.updateMdaMvcSelection(self.selections)

    def clearAllCheckboxes(self):
        """
        Clears (unchecks) all checkboxes in the model.
        """
        # Check if there are any selections to clear
        if not self.selections:
            return  # No selections to clear
        self.selections.clear()
        topLeftIndex = self.index(0, 0)
        bottomRightIndex = self.index(self.rowCount() - 1, self.columnCount() - 1)
        self.dataChanged.emit(
            topLeftIndex,
            bottomRightIndex,
            [Qt.ItemDataRole.CheckStateRole],  # Qt.CheckStateRole
        )
        # Update the mda_mvc selection
        self.mda_mvc.setSelectionField()

    def applySelectionRules(self, index, changes=False):
        """Apply selection rules 2-4."""
        row = index.row()
        column_name = self.columnName(index.column())
        current_column_number = self.columnNumber(column_name)

        for r, v in sorted(self.selections.items()):
            if v is not None:
                v_column_number = self.columnNumber(v)
                # Only apply rules between unique selection columns
                if (
                    v_column_number in self.uniqueSelectionColumns
                    and current_column_number in self.uniqueSelectionColumns
                ):
                    if r != row and column_name == v:
                        self.selections[r] = None
                        changes = True
        return changes

    def updateCheckboxes(
        self, new_selection=None, old_selection=None, update_mda_mvc=True
    ):
        """Update checkboxes to agree with self.selections."""
        if new_selection is None:
            new_selection = self.selections
        if len(new_selection) > 0:  # was self.selections
            top, bottom = min(new_selection), max(new_selection)
        else:
            top, bottom = 0, self.rowCount() - 1
        left, right = min(self.checkboxColumns), max(self.checkboxColumns)
        # logger.debug("corners: (%d,%d)  (%d,%d)", top, left, bottom, right)
        # Re-evaluate the checkboxes bounded by the two corners (inclusive).
        corner1 = self.index(top, left)
        corner2 = self.index(bottom, right)
        self.dataChanged.emit(
            corner1, corner2, [Qt.ItemDataRole.CheckStateRole]
        )  # Qt.CheckStateRole
        # prune empty data from new_selection
        new_selection = {k: v for k, v in new_selection.items() if v is not None}
        self.selections = new_selection
        old_y_selection = old_selection.get("Y", []) if old_selection else []
        new_y_selection = ftm2mda(new_selection).get("Y", []) if new_selection else []
        det_removed = [y for y in old_y_selection if y not in new_y_selection]
        # Update the mda_mvc selection if needed:
        if update_mda_mvc:
            self.updateMdaMvcSelection(new_selection)
        return det_removed

    def updateMdaMvcSelection(self, new_selection):
        if new_selection is None:
            return
        new_selection = ftm2mda(new_selection)
        self.mda_mvc.setSelectionField(new_selection)

    def logCheckboxSelections(self):
        print("checkbox selections:")
        for r in range(self.rowCount()):
            text = ""
            for c in self.checkboxColumns:
                state = self.checkbox(self.index(r, c))
                choices = {
                    Qt.CheckState.Checked: "*",
                    Qt.CheckState.Unchecked: "-",
                }  # {Qt.Checked: "*", Qt.Unchecked: "-"}
                text += choices[state]
            text += f" {self.fieldName(r)}"
            print(text)

    # ------------ local methods

    def columnName(self, column: int):
        return self.columns()[column]

    def columnNumber(self, column_name):
        return self.columns().index(column_name)

    def columns(self):
        return list(self._columns)  # return list(str)

    def setColumns(self, columns):
        """Define the columns for the table."""
        if self._columns_locked:
            raise RuntimeError("Once defined, cannot change columns.")

        self._columns = {column.name: column for column in columns}
        # NOTE: list(int), not list(str): column _number_ (not column name)
        self.checkboxColumns = [
            column_number
            for column_number, column in enumerate(columns)
            if column.column_type == ColumnDataType.checkbox
        ]
        self.uniqueSelectionColumns = [
            column_number
            for column_number, column in enumerate(columns)
            if column.column_type == ColumnDataType.checkbox
            if column.rule == FieldRuleType.unique
        ]
        self.multipleSelectionColumns = [
            column_number
            for column_number, column in enumerate(columns)
            if column.column_type == ColumnDataType.checkbox
            if column.rule == FieldRuleType.multiple
        ]
        self.textColumns = [
            column_number
            for column_number, column in enumerate(columns)
            if column.column_type == ColumnDataType.text
        ]

    def fieldName(self, row):
        return self.fields()[row]

    def fieldText(self, index):
        row, column = index.row(), index.column()
        assert column in self.textColumns, f"{column=} is not text"
        fname = self.fieldName(row)
        cname = self.columnName(column)
        text = str(getattr(self._fields[fname], cname.lower(), ""))
        return text

    def fields(self):
        """Return a list of the field names."""
        return list(self._fields)  # return list(str)

    def setFields(self, fields):
        """Define the data fields (rows) for the table."""
        if self._fields_locked:
            raise RuntimeError("Once defined, cannot change fields.")
        self._fields = {field.name: field for field in fields}
        # Pre-select fields with columns, where fields is list(Field).
        for row, field in enumerate(fields):
            if field.selection is not None:
                column_number = self.columnNumber(field.selection)
                if column_number in self.checkboxColumns:
                    self.selections[row] = field.selection

    # ------------ reporting

    # TODO - later: we have to reformat plotfield to match selectionField and vice versa
    # (ftm2mvc <-> mvc2ftm), maybe avoid this but formating plotfield directly the right way?
    # Or, if it ain't broken, don't fix it...
    # NOTE: If plotfield/selectionField formatting becomes an issue, refactor as needed.

    def plotFields(self):
        """
        Returns a dictionary with the selected fields to be plotted.

        key=column_name, value= row_number(s) or fieldName(s)
        """
        choices = dict(Y=[])
        for row, column_name in self.selections.items():
            column_number = self.columnNumber(column_name)
            if column_number in self.uniqueSelectionColumns:
                choices[column_name] = row
            elif column_number in self.multipleSelectionColumns:
                choices[column_name].append(row)
        return choices

    def setStatus(self, text):
        self.mda_mvc.setStatus(text)

    def columnLabels(self) -> List[str]:
        """Return the column labels."""
        return [
            "Name",
            "Prefix",
            "Number",
            "Points",
            "Dimension",
            "Positioner",
            "Date",
            "Size",
        ]

    def sort(self, column, order):
        """Sort the data by the given column and order."""
        # Implement sorting logic here
        pass

    def getFileList(self) -> List[str]:
        """Return the list of file names."""
        return self._file_list

    def setFileList(self, file_list: List[str]) -> None:
        """Set the list of file names."""
        self._file_list = file_list
        self.layoutChanged.emit()

    def getPrefixList(self) -> List[str]:
        """Return the list of prefixes."""
        return self._prefix_list

    def setPrefixList(self, prefix_list: List[str]) -> None:
        """Set the list of prefixes."""
        self._prefix_list = prefix_list
        self.layoutChanged.emit()

    def getNumberList(self) -> List[int]:
        """Return the list of numbers."""
        return self._number_list

    def setNumberList(self, number_list: List[int]) -> None:
        """Set the list of numbers."""
        self._number_list = number_list
        self.layoutChanged.emit()

    def getPointsList(self) -> List[int]:
        """Return the list of points."""
        return self._points_list

    def setPointsList(self, points_list: List[int]) -> None:
        """Set the list of points."""
        self._points_list = points_list
        self.layoutChanged.emit()

    def getDimensionList(self) -> List[int]:
        """Return the list of dimensions."""
        return self._dimension_list

    def setDimensionList(self, dimension_list: List[int]) -> None:
        """Set the list of dimensions."""
        self._dimension_list = dimension_list
        self.layoutChanged.emit()

    def getPositionerList(self) -> List[str]:
        """Return the list of positioners."""
        return self._positioner_list

    def setPositionerList(self, positioner_list: List[str]) -> None:
        """Set the list of positioners."""
        self._positioner_list = positioner_list
        self.layoutChanged.emit()

    def getDateList(self) -> List[str]:
        """Return the list of dates."""
        return self._date_list

    def setDateList(self, date_list: List[str]) -> None:
        """Set the list of dates."""
        self._date_list = date_list
        self.layoutChanged.emit()

    def getSizeList(self) -> List[str]:
        """Return the list of sizes."""
        return self._size_list

    def setSizeList(self, size_list: List[str]) -> None:
        """Set the list of sizes."""
        self._size_list = size_list
        self.layoutChanged.emit()

    def getAllData(self) -> Dict[str, List]:
        """Return all data as a dictionary."""
        return {
            "Name": self._file_list,
            "Prefix": self._prefix_list,
            "Number": self._number_list,
            "Points": self._points_list,
            "Dimension": self._dimension_list,
            "Positioner": self._positioner_list,
            "Date": self._date_list,
            "Size": self._size_list,
        }

    def setAllData(self, data: Dict[str, List]) -> None:
        """Set all data from a dictionary."""
        self._file_list = data.get("Name", [])
        self._prefix_list = data.get("Prefix", [])
        self._number_list = data.get("Number", [])
        self._points_list = data.get("Points", [])
        self._dimension_list = data.get("Dimension", [])
        self._positioner_list = data.get("Positioner", [])
        self._date_list = data.get("Date", [])
        self._size_list = data.get("Size", [])
        self.layoutChanged.emit()

    def clearData(self) -> None:
        """Clear all data."""
        self._file_list = []
        self._prefix_list = []
        self._number_list = []
        self._points_list = []
        self._dimension_list = []
        self._positioner_list = []
        self._date_list = []
        self._size_list = []
        self.layoutChanged.emit()

    def getRowData(self, row: int) -> Tuple[str, str, int, int, int, str, str, str]:
        """Return the data for a specific row."""
        if row >= len(self._file_list):
            return ("", "", 0, 0, 1, "", "", "")

        return (
            self._file_list[row],
            self._prefix_list[row] if row < len(self._prefix_list) else "",
            self._number_list[row] if row < len(self._number_list) else 0,
            self._points_list[row] if row < len(self._points_list) else 0,
            self._dimension_list[row] if row < len(self._dimension_list) else 1,
            self._positioner_list[row] if row < len(self._positioner_list) else "",
            self._date_list[row] if row < len(self._date_list) else "",
            self._size_list[row] if row < len(self._size_list) else "",
        )

    def setRowData(
        self, row: int, data: Tuple[str, str, int, int, int, str, str, str]
    ) -> None:
        """Set the data for a specific row."""
        if row >= len(self._file_list):
            # Extend lists if needed
            while len(self._file_list) <= row:
                self._file_list.append("")
                self._prefix_list.append("")
                self._number_list.append(0)
                self._points_list.append(0)
                self._dimension_list.append(1)
                self._positioner_list.append("")
                self._date_list.append("")
                self._size_list.append("")

        self._file_list[row] = data[0]
        self._prefix_list[row] = data[1]
        self._number_list[row] = data[2]
        self._points_list[row] = data[3]
        self._dimension_list[row] = data[4]
        self._positioner_list[row] = data[5]
        self._date_list[row] = data[6]
        self._size_list[row] = data[7]

        # Emit data changed signal for the specific row
        self.dataChanged.emit(
            self.index(row, 0), self.index(row, len(self.columnLabels()) - 1)
        )

    def setData(self, index, value, role):
        """Set the data for the given index and role."""
        if not index.isValid():
            return False

        if role == Qt.ItemDataRole.CheckStateRole:
            # Handle checkbox state changes
            if index.column() in self.checkboxColumns:
                self.setCheckbox(index, value)
                return True

        elif role == Qt.ItemDataRole.EditRole:
            # Handle data editing if needed
            return True

        return False
