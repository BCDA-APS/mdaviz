"""
Data table model for displaying MDA scan data.

This module provides a table model for displaying MDA scan data in a Qt table view.

.. autosummary::

    ~DataTableModel
"""

from typing import Any, Optional, Union, Dict, List
from PyQt6.QtCore import QModelIndex, QObject, Qt
from PyQt6.QtCore import QAbstractTableModel
from PyQt6.QtCore import QVariant


class DataTableModel(QAbstractTableModel):
    """
    Table model for displaying MDA scan data.

    This model is designed to handle data represented as a dictionary where keys
    correspond to column labels and values are lists of data points for each column.

    Args:
        scanDict (Dict[str, Dict[str, Any]]): A dictionary where keys are pos/det indexes
            and values are dictionaries containing:
            {index: {'object': scanObject, 'data': [...], 'unit': '...', 'name': '...','type':...}}.
        parent (Optional[QObject]): The parent object for this table model, default is None.

    Methods:
        rowCount: Returns the number of rows in the table model.
        columnCount: Returns the number of columns in the table model.
        data: Returns the data to be displayed for a given index and role.
        headerData: Provides the header labels for the table model.
        columnLabels: Returns a list of column labels.
        setColumnLabels: Sets the column labels based on keys from the input dictionary.
        allData: Returns the current data stored in the model.
        setAllData: Sets the model's data using the input dictionary.

    The model dynamically adjusts to changes in the input data, updating both
    the data displayed and the column headers as necessary.
    """

    def __init__(
        self, scanDict: Dict[str, Dict[str, Any]], parent: Optional[QObject] = None
    ) -> None:
        """
        Initialize the data table model.

        Parameters:
            scanDict (Dict[str, Dict[str, Any]]): A dictionary where keys are pos/det indexes
                and values are dictionaries containing scan data.
            parent (Optional[QObject]): The parent object for this table model.
        """
        super().__init__(parent)

        self.setAllData(scanDict)
        self.setColumnLabels()

    def rowCount(self, parent: Optional[QModelIndex] = None) -> int:
        """
        Returns the number of rows in the table model.

        Parameters:
            parent (Optional[QModelIndex]): Parent index, not used in this implementation

        Returns:
            int: The number of rows, or 0 if no data
        """
        data = self.allData()
        if not data or len(data) == 0:
            return 0

        # Find the maximum length of any column's data
        max_length = 0
        for column_data in data.values():
            if isinstance(column_data, dict) and "data" in column_data:
                data_list = column_data["data"]
                if isinstance(data_list, list):
                    max_length = max(max_length, len(data_list))

        return max_length

    def columnCount(self, parent: Optional[QModelIndex] = None) -> int:
        """
        Returns the number of columns in the table model.

        Parameters:
            parent (Optional[QModelIndex]): Parent index, not used in this implementation

        Returns:
            int: Number of columns is determined by the number of pos(s) & det(s)
        """
        return len(self.columnLabels())

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """
        Returns the data to be displayed for a given index and role.

        Parameters:
            index (QModelIndex): The index of the item to retrieve data for
            role (int): The role of the data (DisplayRole, EditRole, etc.)

        Returns:
            Any: The data for the given index and role, or QVariant() if not found
        """
        if not index.isValid():
            return QVariant()

        if role == Qt.ItemDataRole.DisplayRole:
            row = index.row()
            col = index.column()

            column_labels = self.columnLabels()
            if col >= len(column_labels):
                return QVariant()

            column_key = list(self.allData().keys())[col]
            column_data = self.allData()[column_key]

            if isinstance(column_data, dict) and "data" in column_data:
                data_list = column_data["data"]
                if isinstance(data_list, list) and row < len(data_list):
                    return data_list[row]

        return QVariant()

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Union[str, QVariant]:
        """
        Provides the header labels for the table model.

        Parameters:
            section (int): The section index (column or row number)
            orientation (Qt.Orientation): Whether this is a horizontal or vertical header
            role (int): The role of the data being requested

        Returns:
            Union[str, QVariant]: The header data as a string, or QVariant() if not found
        """
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                # Return column headers
                column_labels = self.columnLabels()
                if 0 <= section < len(column_labels):
                    return column_labels[section]
            else:
                # Return row numbers for vertical headers
                return str(section + 1)

        return QVariant()

    def columnLabels(self) -> List[str]:
        """
        Returns a list of column labels.

        Returns:
            List[str]: List of column labels (names from scan data)
        """
        if not hasattr(self, "_column_labels"):
            self._column_labels: List[str] = []
        return self._column_labels

    def setColumnLabels(self) -> None:
        """
        Sets the column labels based on the 'name' field from the scan data.

        This method extracts the 'name' field from each column's data dictionary
        to use as the column header.
        """
        data = self.allData()
        labels = []

        for key, column_data in data.items():
            if isinstance(column_data, dict):
                # Use the 'name' field if available, otherwise use the key
                name = column_data.get("name", key)
                labels.append(str(name))
            else:
                labels.append(str(key))

        self._column_labels = labels

    def allData(self) -> Dict[str, Any]:
        """
        Returns the current data stored in the model.

        Returns:
            Dict[str, Any]: The complete scan data dictionary
        """
        if not hasattr(self, "_data"):
            self._data: Dict[str, Any] = {}
        return self._data

    def setAllData(self, scanDict: Dict[str, Dict[str, Any]]) -> None:
        """
        Sets the model's data using the input dictionary.

        Parameters:
            scanDict (Dict[str, Dict[str, Any]]): The new scan data to use
        """
        self.beginResetModel()
        self._data = scanDict.copy() if scanDict else {}
        self.endResetModel()
