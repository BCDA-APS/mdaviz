"""
.. autosummary::

    ~DataTableModel

"""

from typing import Any, Optional
from PyQt6.QtCore import QModelIndex, QObject, Qt, QAbstractTableModel, QVariant


class DataTableModel(QAbstractTableModel):
    """This model is designed to handle data represented as a dictionary where keys correspond to column labels and values are lists of data points for each column.


    Args:
        - scanDict (dict): A dictionary where keys are pos/det indexes and values are dictionaries:
          {index: {'object': scanObject, 'data': [...], 'unit': '...', 'name': '...','type':...}}.
        - parent (QObject, optional): The parent object for this table model, default is None.

    Methods:
        - rowCount: Returns the number of rows in the table model.
        - columnCount: Returns the number of columns in the table model.
        - data: Returns the data to be displayed for a given index and role.
        - headerData: Provides the header labels for the table model.
        - columnLabels: Returns a list of column labels.
        - setColumnLabels: Sets the column labels based on keys from the input dictionary.
        - allData: Returns the current data stored in the model.
        - setAllData: Sets the model's data using the input dictionary.

    The model dynamically adjusts to changes in the input data, updating both the data displayed and the column headers as necessary.
    """

    def __init__(
        self, scanDict: dict[str, dict[str, Any]], parent: Optional[QObject] = None
    ) -> None:
        """Initialize the data table model.

        Parameters:
            scanDict (dict[str, dict[str, Any]]): A dictionary where keys are pos/det indexes and values are dictionaries:
              {index: {'object': scanObject, 'data': [...], 'unit': '...', 'name': '...','type':...}}.
            parent (Optional[QObject]): The parent object for this table model, default is None.
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
            if isinstance(column_data, list):
                max_length = max(max_length, len(column_data))

        return max_length

    def columnCount(self, parent: Optional[QModelIndex] = None) -> int:
        """Returns the number of columns in the table model.

        Parameters:
            parent (Optional[QModelIndex]): Parent index, not used in this implementation

        Returns:
            int: Number of columns is determined by the number of pos(s) & det(s)
        """
        return len(self.columnLabels())

    def data(self, index: QModelIndex, role: int = 0) -> Any:  # 0 = Qt.DisplayRole
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

        if role == 0:  # Qt.DisplayRole
            row = index.row()
            col = index.column()

            # Get the column label for this column
            if col < len(self.columnLabels()):
                column_label = self.columnLabels()[col]

                # Get the data for this column
                if column_label in self.allData():
                    column_data = self.allData()[column_label]

                    # Return the data for this row if it exists
                    if row < len(column_data):
                        return str(column_data[row])
                    else:
                        return QVariant()

        return QVariant()

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = 0
    ) -> Any:  # 0 = Qt.DisplayRole
        """
        Provide horizontal header labels only, nothing for vertical headers (Index is always the first column).

        Parameters:
            section (int): Section index
            orientation (int): Header orientation (Horizontal/Vertical)
            role (int): Data role

        Returns:
            Any: Header data or QVariant() if not found
        """
        if (
            role == 0 and orientation == Qt.Orientation.Horizontal
        ):  # Qt.DisplayRole and Qt.Horizontal
            return self.columnLabels()[section]
        return QVariant()

    # # # ------------ get & set methods

    def columnLabels(self) -> list[str]:
        """Get the column labels.

        Returns:
            list[str]: List of column labels
        """
        return self._columnLabels

    def setColumnLabels(self) -> list[str]:
        """Set the column labels based on the data keys.

        Returns:
            list[str]: List of column labels
        """
        self._columnLabels = list(self.allData().keys())
        return self._columnLabels

    def allData(self) -> dict[str, list]:
        """Get all data stored in the model.

        Returns:
            dict[str, list]: Dictionary mapping column names to data lists
        """
        return self._allData

    def setAllData(self, scanDict: dict[str, dict[str, Any]]) -> dict[str, list]:
        """Set the model's data using the input dictionary.

        Parameters:
            scanDict (dict[str, dict[str, Any]]): Input data dictionary

        Returns:
            dict[str, list]: Processed data dictionary
        """
        self._allData = {}
        if scanDict:
            for v in list(scanDict.values()):
                pv = v["name"]
                data = v["data"]
                self._allData[pv] = data
        return self._allData
