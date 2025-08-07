"""
Multi-dimensional data table model for handling 2D, 3D, 4D, and higher dimensional scan data.

This module provides a flexible table model that can display multi-dimensional scan data
in a 2D table format, showing positioner values and detector data in an intuitive way.

.. autosummary::

    ~MultiDimensionalDataTableModel
"""

from typing import Any, Optional, Dict, List, Tuple
import numpy as np
from PyQt6.QtCore import (
    QModelIndex,
    QObject,
    Qt,
    QAbstractTableModel,
    QVariant,
)


class MultiDimensionalDataTableModel(QAbstractTableModel):
    """
    A table model for displaying multi-dimensional data in a flattened format.

    For 2D data, displays:
    X2[0]    X1[0]    DET1    DET2    ...
    X2[0]    X1[1]    DET1    DET2    ...
    X2[0]    X1[2]    DET1    DET2    ...
    ...
    X2[1]    X1[0]    DET1    DET2    ...
    X2[1]    X1[1]    DET1    DET2    ...
    ...

    Currently supports 2D data only.
    """

    def __init__(self, scan_data, x2_points=None, x1_points=None):
        """
        Initialize the model with scan data from get_scan_2d().

        Args:
            scan_data: Dictionary returned by utils.get_scan_2d()
            x2_points: Number of X2 points (from metadata)
            x1_points: Number of X1 points (from metadata)
        """
        super().__init__()
        self._scan_data = scan_data
        self._x2_points = x2_points
        self._x1_points = x1_points
        self._flattened_data = []
        self._column_headers = []

        # Process the data
        self._flatten_2d_data()
        self._generate_2d_headers()

    def _flatten_2d_data(self):
        """Flatten 2D data into rows of [X2, X1, DET1, DET2, ...]."""
        # Find the actual positioners (skip Index)
        x2_data = None
        x1_data = None

        for key, value in self._scan_data.items():
            if value.get("type") == "POS" and value.get("name") != "Index":
                if x2_data is None:
                    x2_data = value.get("data", [])
                elif x1_data is None:
                    x1_data = value.get("data", [])
                    break

        if not x2_data or not x1_data:
            self._flattened_data = []
            return

        # Use metadata dimensions if provided, otherwise use data lengths
        x2_count = self._x2_points if self._x2_points is not None else len(x2_data)
        x1_count = self._x1_points if self._x1_points is not None else len(x1_data)

        flattened_rows = []
        for i in range(x2_count):
            for j in range(x1_count):
                # Get X2 value
                if i < len(x2_data):
                    x2_val = x2_data[i]
                else:
                    x2_val = 0

                # Get X1 value (handle nested structure)
                if i < len(x1_data):
                    x1_inner = x1_data[i]
                    if isinstance(x1_inner, (list, np.ndarray)) and j < len(x1_inner):
                        x1_val = x1_inner[j]
                    else:
                        x1_val = x1_inner if j == 0 else 0
                else:
                    x1_val = 0

                row = [x2_val, x1_val]

                # Add detector values
                for key in range(2, len(self._scan_data)):
                    det_data = self._scan_data.get(key, {})
                    if det_data.get("type") == "DET":
                        det_values = det_data.get("data", [])
                        if isinstance(det_values, (list, np.ndarray)):
                            # Handle nested detector data structure
                            if i < len(det_values):
                                det_inner = det_values[i]
                                if isinstance(
                                    det_inner, (list, np.ndarray)
                                ) and j < len(det_inner):
                                    det_value = det_inner[j]
                                else:
                                    det_value = det_inner if j == 0 else 0
                            else:
                                det_value = 0
                        else:
                            det_value = 0
                        row.append(det_value)

                flattened_rows.append(row)

        self._flattened_data = flattened_rows

    def _generate_2d_headers(self):
        """Generate column headers for 2D data."""
        headers = []

        # Find actual positioners (skip Index)
        x2_name = None
        x1_name = None

        for key, value in self._scan_data.items():
            if value.get("type") == "POS" and value.get("name") != "Index":
                if x2_name is None:  # First non-Index positioner
                    x2_name = value.get("name", "X2")
                else:  # Second non-Index positioner
                    x1_name = value.get("name", "X1")
                    break

        if x2_name:
            headers.append(x2_name)
        if x1_name:
            headers.append(x1_name)

        # Add detector headers
        for key in range(2, len(self._scan_data)):
            det_data = self._scan_data.get(key, {})
            if det_data.get("type") == "DET":
                det_name = det_data.get("name", f"DET{key}")
                det_unit = det_data.get("unit", "")
                if det_unit:
                    headers.append(f"{det_name} ({det_unit})")
                else:
                    headers.append(det_name)

        self._column_headers = headers

    # QAbstractTableModel methods
    def rowCount(self, parent=None):
        return len(self._flattened_data)

    def columnCount(self, parent=None):
        return len(self._column_headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.DisplayRole:
            row = index.row()
            col = index.column()

            if row < len(self._flattened_data) and col < len(self._flattened_data[row]):
                value = self._flattened_data[row][col]
                # Format numeric values
                if isinstance(value, (int, float)):
                    return f"{value:.6g}"
                return str(value)

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                if section < len(self._column_headers):
                    return self._column_headers[section]
            else:
                return str(section)
        return None

    # Getter methods (with defensive copying)
    def get_flattened_data(self):
        """Get the flattened data as a copy."""
        return self._flattened_data.copy()

    def get_column_headers(self):
        """Get the column headers as a copy."""
        return self._column_headers.copy()

    def get_2d_structure(self):
        """Get the 2D structure information for debugging."""
        return {
            "x2_data": self._scan_data.get(0, {}),
            "x1_data": self._scan_data.get(1, {}),
            "detectors": {
                k: v for k, v in self._scan_data.items() if v.get("type") == "DET"
            },
            "flattened_rows": len(self._flattened_data),
            "columns": len(self._column_headers),
        }
