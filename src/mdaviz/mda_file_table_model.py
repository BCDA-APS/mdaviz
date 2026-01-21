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

from typing import Optional
from mdaviz.utils import mda2ftm, ftm2mda
from dataclasses import KW_ONLY
from dataclasses import dataclass

from PyQt6.QtCore import pyqtSignal, Qt, QAbstractTableModel
from PyQt6.QtGui import QBrush, QColor
from mdaviz.logger import get_logger

# Get logger for this module
logger = get_logger("mda_file_table_model")


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
    selection: Optional[str] = None  # None, "X", "Y", "I0", etc.
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

    def isI0Selected(self):
        """Check if I0 is selected in any row."""
        plot_fields = self.plotFields()
        return "I0" in plot_fields

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
            # Highlight row if it's the highlighted row
            if row == self.highlightedRow:
                return QBrush(QColor(0xE2E2EC))
            # Highlight I0 column if I0 is selected
            elif column == self.columnNumber("I0") and self.isI0Selected():
                return QBrush(QColor(0xE2E2EC))

        elif role == Qt.ItemDataRole.ToolTipRole:
            # Provide tooltips for checkbox columns
            if column in self.checkboxColumns:
                column_name = self.columnName(column)
                if column_name == "X":
                    return "Select this field as the X-axis (independent variable). Only one X selection allowed."
                elif column_name == "Y":
                    return "Select this field as a Y-axis (dependent variable). Multiple Y selections allowed."
                elif column_name == "I0":
                    return "Select this field for normalization (divide Y data by this field). Only one I0 selection allowed."
                elif column_name == "Un":
                    return "Unscale this curve to match the range of other Y curves. Requires Y selection on same row. Multiple Un selections allowed."

        return None

    def headerData(self, section, orientation, role):
        """Return the header data for the given section and role."""
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self.columnName(section)
            elif orientation == Qt.Orientation.Vertical:
                # Return field name instead of row number
                if section < len(self._fields):
                    field_names = list(self._fields.keys())
                    return field_names[section]
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

        # Handle both single selections (str) and multiple selections (list)
        if isinstance(selection, list):
            return Qt.CheckState.Checked if nm in selection else Qt.CheckState.Unchecked
        else:
            return Qt.CheckState.Checked if selection == nm else Qt.CheckState.Unchecked

    def setCheckbox(self, index, state):
        """Set the checkbox state."""
        old_selection = ftm2mda(self.selections)
        row, column = index.row(), index.column()
        column_name = self.columnName(column)
        checked = state == Qt.CheckState.Checked
        prior = self.selections.get(row)  # value if row exist as a key, None otherwise

        logger.debug(
            f"setCheckbox - row={row}, column_name={column_name}, checked={checked}"
        )
        logger.debug(f"setCheckbox - prior={prior}")

        # Handle multiple selections per row
        if isinstance(prior, list):
            new_selection = prior.copy() if prior else []
            if checked and column_name not in new_selection:
                new_selection.append(column_name)
            elif not checked and column_name in new_selection:
                new_selection.remove(column_name)
                if not new_selection:  # If the list is now empty, set to None
                    new_selection = None
            self.selections[row] = new_selection
            changes = new_selection != prior
            logger.debug(
                f"setCheckbox - multiple selection: new_selection={new_selection}, changes={changes}"
            )
        else:
            # Handle single selection (backward compatibility)
            if checked:
                # If we're adding any column to a row that already has a selection, convert to multiple selection
                if prior is not None:
                    new_selection = [prior, column_name]
                    self.selections[row] = new_selection
                    changes = True
                    logger.debug(
                        f"setCheckbox - converting to multiple selection: new_selection={new_selection}"
                    )
                else:
                    # Normal single selection replacement
                    new_selection = column_name
                    self.selections[row] = new_selection
                    changes = new_selection != prior
                    logger.debug(
                        f"setCheckbox - single selection replacement: new_selection={new_selection}, changes={changes}"
                    )
            else:
                # Unchecking - just clear the selection
                new_selection = None
                self.selections[row] = new_selection
                changes = new_selection != prior
                logger.debug(
                    f"setCheckbox - unchecking: new_selection={new_selection}, changes={changes}"
                )

        changes = self.applySelectionRules(index, changes)
        logger.debug(f"setCheckbox - after applySelectionRules: changes={changes}")
        if changes:
            det_removed = self.updateCheckboxes(old_selection=old_selection)
            self.checkboxStateChanged.emit(self.plotFields(), det_removed)
            # Refresh background highlighting for I0 column if I0 selection changed
            if column_name == "I0" or prior == "I0":
                self.layoutChanged.emit()

    def checkCheckBox(self, row, column_name):
        self.selections[row] = (
            column_name  # Mark the checkbox as checked by updating 'selections'
        )
        col = self.columnNumber(column_name)  # Translate column name to its index
        index = self.index(row, col)
        self.dataChanged.emit(
            index, index, [Qt.ItemDataRole.CheckStateRole]
        )  # Update view with Qt.CheckStateRole
        # Refresh background highlighting for I0 column if I0 selection changed
        if column_name == "I0":
            self.layoutChanged.emit()

    def uncheckCheckBox(self, row):
        if row in self.selections:
            # Get the column index of the checkbox being unchecked
            selection = self.selections[row]
            if isinstance(selection, list):
                # For multiple selections, we need to determine which column to update
                # This method is called from chartview when a curve is removed,
                # so we'll just clear all selections for this row
                was_i0 = "I0" in selection
                del self.selections[row]
                # Update all checkbox columns for this row
                for col in self.checkboxColumns:
                    index = self.index(row, col)
                    self.dataChanged.emit(
                        index, index, [Qt.ItemDataRole.CheckStateRole]
                    )  # Qt.CheckStateRole
            else:
                # Handle single selection (backward compatibility)
                col = self.columnNumber(selection)
                was_i0 = selection == "I0"
                del self.selections[row]
                # Update view
                index = self.index(row, col)
                self.dataChanged.emit(
                    index, index, [Qt.ItemDataRole.CheckStateRole]
                )  # Qt.CheckStateRole

            # Update the mda_mvc selection
            self.updateMdaMvcSelection(self.selections)
            # Refresh background highlighting for I0 column if I0 selection changed
            if was_i0:
                self.layoutChanged.emit()

    def clearAllCheckboxes(self):
        """
        Clears (unchecks) all checkboxes in the model.
        """
        # Check if there are any selections to clear
        if not self.selections:
            return  # No selections to clear
        # Check if I0 was selected before clearing
        had_i0 = any(selection == "I0" for selection in self.selections.values())
        self.selections.clear()
        topLeftIndex = self.index(0, 0)
        bottomRightIndex = self.index(self.rowCount() - 1, self.columnCount() - 1)
        self.dataChanged.emit(
            topLeftIndex,
            bottomRightIndex,
            [Qt.ItemDataRole.CheckStateRole],  # Qt.CheckStateRole
        )
        # Update the mda_mvc selection
        if self.mda_mvc is not None:
            self.mda_mvc.setSelectionField()
        # Refresh background highlighting for I0 column if I0 selection changed
        if had_i0:
            self.layoutChanged.emit()

    def applySelectionRules(self, index, changes=False):
        """Apply selection rules 2-4."""
        row = index.row()
        column_name = self.columnName(index.column())
        current_column_number = self.columnNumber(column_name)

        logger.debug(f"applySelectionRules - row={row}, column_name={column_name}")
        logger.debug(f"applySelectionRules - current selections={self.selections}")

        # Handle "Un" column special rules
        if column_name == "Un":
            logger.debug("applySelectionRules - handling Un column")
            # Rule 1: Cannot be same as X
            if isinstance(
                self.selections.get(row), list
            ) and "X" in self.selections.get(row, []):
                if "Un" in self.selections.get(row, []):
                    logger.debug(
                        "applySelectionRules - removing Un because X is selected"
                    )
                    self.selections[row].remove("Un")
                    changes = True
            elif self.selections.get(row) == "X":
                if "Un" in self.selections.get(row, []):
                    logger.debug("applySelectionRules - keeping only X, removing Un")
                    self.selections[row] = "X"  # Keep only X
                    changes = True
            # Rule 2: Cannot be same as I0
            if isinstance(
                self.selections.get(row), list
            ) and "I0" in self.selections.get(row, []):
                if "Un" in self.selections.get(row, []):
                    logger.debug(
                        "applySelectionRules - removing Un because I0 is selected"
                    )
                    self.selections[row].remove("Un")
                    changes = True
            elif self.selections.get(row) == "I0":
                if "Un" in self.selections.get(row, []):
                    logger.debug("applySelectionRules - keeping only I0, removing Un")
                    self.selections[row] = "I0"  # Keep only I0
                    changes = True
            # Rule 3: Requires Y selection (handled in data2Plot)
            # Rule 4: Multiple allowed (no special handling needed)
        else:
            # Handle unique selection columns (X, I0)
            if current_column_number in self.uniqueSelectionColumns:
                for r, v in sorted(self.selections.items()):
                    if v is not None:
                        # Handle both single selection (string) and multiple selection (list)
                        if isinstance(v, list):
                            # For multiple selections, check if any of them conflict
                            for single_v in v:
                                if single_v in ["X", "I0"]:
                                    v_column_number = self.columnNumber(single_v)
                                    if (
                                        v_column_number in self.uniqueSelectionColumns
                                        and current_column_number
                                        in self.uniqueSelectionColumns
                                        and single_v
                                        == column_name  # Only conflict if same column type
                                    ):
                                        if r != row:
                                            logger.debug(
                                                f"applySelectionRules - removing {single_v} from row {r} because {column_name} selected"
                                            )
                                            # Remove the conflicting selection from the list
                                            v.remove(single_v)
                                            if not v:  # If list is empty, set to None
                                                self.selections[r] = None
                                            else:
                                                self.selections[r] = v
                                            changes = True
                            # Also check for conflicts within the same row (e.g., X and Un, I0 and Un)
                            if r == row and isinstance(v, list):
                                # Remove "Un" if "X" is also selected
                                if "X" in v and "Un" in v:
                                    logger.debug(
                                        "applySelectionRules - removing Un because X is selected on same row"
                                    )
                                    v.remove("Un")
                                    changes = True
                                # Remove "Un" if "I0" is also selected
                                if "I0" in v and "Un" in v:
                                    logger.debug(
                                        "applySelectionRules - removing Un because I0 is selected on same row"
                                    )
                                    v.remove("Un")
                                    changes = True
                        else:
                            # Handle single selection (backward compatibility)
                            v_column_number = self.columnNumber(v)
                            if (
                                v_column_number in self.uniqueSelectionColumns
                                and current_column_number in self.uniqueSelectionColumns
                            ):
                                if r != row and column_name == v:
                                    logger.debug(
                                        f"applySelectionRules - removing {v} from row {r} because {column_name} selected"
                                    )
                                    self.selections[r] = None
                                    changes = True

        logger.debug(
            f"applySelectionRules - final selections={self.selections}, changes={changes}"
        )
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
        if new_selection is None or self.mda_mvc is None:
            return
        new_selection = ftm2mda(new_selection)
        self.mda_mvc.setSelectionField(new_selection)

    def logCheckboxSelections(self):
        logger.info("Checkbox selections:")
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
            logger.info(text)

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
        choices = dict(Y=[], Un=[])
        for row, selection in self.selections.items():
            if selection is None:
                continue

            # Handle both single selections (str) and multiple selections (list)
            if isinstance(selection, list):
                for column_name in selection:
                    column_number = self.columnNumber(column_name)
                    if column_number in self.uniqueSelectionColumns:
                        choices[column_name] = row
                    elif column_number in self.multipleSelectionColumns:
                        choices[column_name].append(row)
            else:
                # Handle single selection (backward compatibility)
                column_number = self.columnNumber(selection)
                if column_number in self.uniqueSelectionColumns:
                    choices[selection] = row
                elif column_number in self.multipleSelectionColumns:
                    choices[selection].append(row)
        return choices

    def setStatus(self, text):
        if self.mda_mvc is not None:
            self.mda_mvc.setStatus(text)

    def setData(self, index, value, role):
        """Set the data for the given index and role."""
        if not index.isValid():
            return False

        if role == Qt.ItemDataRole.CheckStateRole:
            # Handle checkbox state changes
            if index.column() in self.checkboxColumns:
                # PyQt6 checkbox behavior fix: toggle the state
                current_state = self.data(index, Qt.ItemDataRole.CheckStateRole)
                if current_state == Qt.CheckState.Checked:
                    new_state = Qt.CheckState.Unchecked
                else:
                    new_state = Qt.CheckState.Checked
                self.setCheckbox(index, new_state)
                return True

        elif role == Qt.ItemDataRole.EditRole:
            # Handle data editing if needed
            return True

        return False
