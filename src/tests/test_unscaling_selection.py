#!/usr/bin/env python
"""
Tests for MDA file table selection model functionality.

This module tests the selection logic for X, Y, and I0 columns in the MDA file
table model (unique vs multiple selection, plotFields, checkbox display).

.. autosummary::

    ~test_y_selection
    ~test_y_i0_selection_same_row
    ~test_selection_persistence
    ~test_unique_selection_rules
    ~test_checkbox_state_display
    ~test_duplicate_selection_prevention
    ~test_duplicate_selection_prevention_x
"""

import pytest
from unittest.mock import Mock
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from mdaviz.mda_file_table_model import MDAFileTableModel


@pytest.fixture
def table_model(qapp: QApplication) -> MDAFileTableModel:
    """Create a MDAFileTableModel instance for testing."""
    from mdaviz.mda_file_table_model import (
        TableColumn,
        TableField,
        ColumnDataType,
        FieldRuleType,
    )

    # Define columns (same as in mda_file_table_view.py, without Un)
    columns = [
        TableColumn("Field", ColumnDataType.text),
        TableColumn("X", ColumnDataType.checkbox, rule=FieldRuleType.unique),
        TableColumn("Y", ColumnDataType.checkbox, rule=FieldRuleType.multiple),
        TableColumn("I0", ColumnDataType.checkbox, rule=FieldRuleType.unique),
        TableColumn("PV", ColumnDataType.text),
        TableColumn("DESC", ColumnDataType.text),
        TableColumn("Unit", ColumnDataType.text),
    ]

    # Define fields (test data)
    fields = [
        TableField("pos1", pv="Position 1", desc="Position", unit="mm"),
        TableField("det1", pv="Detector 1", desc="Detector", unit="counts"),
        TableField("det2", pv="Detector 2", desc="Detector", unit="counts"),
        TableField("det3", pv="Detector 3", desc="Detector", unit="counts"),
        TableField("det4", pv="Detector 4", desc="Detector", unit="counts"),
    ]

    # Empty selection field (no initial selections)
    selection_field: dict = {}

    # Create mock parent
    mock_parent = Mock()

    model = MDAFileTableModel(columns, fields, selection_field, mock_parent)
    return model


class TestTableSelection:
    """Test cases for table selection functionality (X, Y, I0)."""

    def test_y_selection(self, table_model: MDAFileTableModel) -> None:
        """Test that Y can be selected on a row."""
        y_col = table_model.columnNumber("Y")
        y_index = table_model.index(1, y_col)
        table_model.setCheckbox(y_index, Qt.CheckState.Checked)
        assert table_model.selections[1] == "Y"

    def test_y_i0_selection_same_row(self, table_model: MDAFileTableModel) -> None:
        """Test that Y and I0 can be selected on the same row."""
        # Select Y on row 2
        y_col = table_model.columnNumber("Y")
        y_index = table_model.index(2, y_col)
        table_model.setCheckbox(y_index, Qt.CheckState.Checked)
        assert table_model.selections[2] == "Y"

        # Select I0 on row 2 (should create multiple selection)
        i0_col = table_model.columnNumber("I0")
        i0_index = table_model.index(2, i0_col)
        table_model.setCheckbox(i0_index, Qt.CheckState.Checked)
        assert table_model.selections[2] == ["Y", "I0"]

        assert "Y" in table_model.selections[2]
        assert "I0" in table_model.selections[2]

    def test_selection_persistence(self, table_model: MDAFileTableModel) -> None:
        """Test that selections persist in plotFields output."""
        table_model.selections = {1: "Y", 2: ["Y", "I0"], 3: "X"}

        selections = table_model.plotFields()

        assert "Y" in selections
        assert "I0" in selections
        assert "X" in selections
        assert "Un" not in selections

        assert 1 in selections["Y"]
        assert 2 in selections["Y"]
        assert selections["I0"] == 2
        assert selections["X"] == 3

    def test_unique_selection_rules(self, table_model: MDAFileTableModel) -> None:
        """Test that unique selection rules work for X and I0."""
        x_col = table_model.columnNumber("X")
        table_model.setCheckbox(table_model.index(1, x_col), Qt.CheckState.Checked)
        assert table_model.selections[1] == "X"

        table_model.setCheckbox(table_model.index(2, x_col), Qt.CheckState.Checked)
        assert table_model.selections[2] == "X"
        assert 1 not in table_model.selections

        i0_col = table_model.columnNumber("I0")
        table_model.setCheckbox(table_model.index(3, i0_col), Qt.CheckState.Checked)
        assert table_model.selections[3] == "I0"

        table_model.setCheckbox(table_model.index(4, i0_col), Qt.CheckState.Checked)
        assert table_model.selections[4] == "I0"
        assert 3 not in table_model.selections

    def test_checkbox_state_display(self, table_model: MDAFileTableModel) -> None:
        """Test that checkbox states display correctly."""
        table_model.selections[1] = "Y"

        y_col = table_model.columnNumber("Y")
        y_state = table_model.checkbox(table_model.index(1, y_col))
        assert y_state == Qt.CheckState.Checked

        x_col = table_model.columnNumber("X")
        x_state = table_model.checkbox(table_model.index(1, x_col))
        assert x_state == Qt.CheckState.Unchecked

    def test_duplicate_selection_prevention(
        self, table_model: MDAFileTableModel
    ) -> None:
        """Test that checking an already-checked Y checkbox doesn't create duplicates."""
        y_col = table_model.columnNumber("Y")
        y_index = table_model.index(1, y_col)
        table_model.setCheckbox(y_index, Qt.CheckState.Checked)
        assert table_model.selections[1] == "Y"

        table_model.setCheckbox(y_index, Qt.CheckState.Checked)
        assert table_model.selections[1] == "Y"
        assert not isinstance(table_model.selections[1], list)

    def test_duplicate_selection_prevention_x(
        self, table_model: MDAFileTableModel
    ) -> None:
        """Test that checking an already-checked X checkbox doesn't create duplicates."""
        x_col = table_model.columnNumber("X")
        x_index = table_model.index(2, x_col)
        table_model.setCheckbox(x_index, Qt.CheckState.Checked)
        assert table_model.selections[2] == "X"

        table_model.setCheckbox(x_index, Qt.CheckState.Checked)
        assert table_model.selections[2] == "X"
        assert not isinstance(table_model.selections[2], list)
