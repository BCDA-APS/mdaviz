#!/usr/bin/env python
"""
Tests for unscaling selection model functionality.

This module tests the selection logic for the "Un" column and its interactions
with X, Y, and I0 columns in the MDA file table model.

.. autosummary::

    ~test_y_un_selection_same_row
    ~test_y_i0_selection_same_row
    ~test_x_un_prevention_same_row
    ~test_i0_un_prevention_same_row
    ~test_multiple_un_selections
    ~test_selection_persistence
"""

import pytest
from unittest.mock import Mock, patch
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

    # Define columns (same as in mda_file_table_view.py)
    columns = [
        TableColumn("Field", ColumnDataType.text),
        TableColumn("X", ColumnDataType.checkbox, rule=FieldRuleType.unique),
        TableColumn("Y", ColumnDataType.checkbox, rule=FieldRuleType.multiple),
        TableColumn("I0", ColumnDataType.checkbox, rule=FieldRuleType.unique),
        TableColumn("Un", ColumnDataType.checkbox, rule=FieldRuleType.multiple),
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
    selection_field = {}

    # Create mock parent
    mock_parent = Mock()

    model = MDAFileTableModel(columns, fields, selection_field, mock_parent)
    return model


class TestUnscalingSelection:
    """Test cases for unscaling selection functionality."""

    def test_y_un_selection_same_row(self, table_model: MDAFileTableModel) -> None:
        """Test that Y and Un can be selected on the same row."""
        # Select Y on row 1
        y_col = table_model.columnNumber("Y")
        y_index = table_model.index(1, y_col)
        table_model.setCheckbox(y_index, Qt.CheckState.Checked)
        assert table_model.selections[1] == "Y"

        # Select Un on row 1 (should create multiple selection)
        un_col = table_model.columnNumber("Un")
        un_index = table_model.index(1, un_col)
        table_model.setCheckbox(un_index, Qt.CheckState.Checked)
        assert table_model.selections[1] == ["Y", "Un"]

        # Verify both remain selected
        assert "Y" in table_model.selections[1]
        assert "Un" in table_model.selections[1]

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

        # Verify both remain selected
        assert "Y" in table_model.selections[2]
        assert "I0" in table_model.selections[2]

    def test_x_un_prevention_same_row(self, table_model: MDAFileTableModel) -> None:
        """Test that X and Un cannot be selected on the same row."""
        # Select X on row 3
        x_col = table_model.columnNumber("X")
        x_index = table_model.index(3, x_col)
        table_model.setCheckbox(x_index, Qt.CheckState.Checked)
        assert table_model.selections[3] == "X"

        # Try to select Un on row 3 (should be prevented)
        un_col = table_model.columnNumber("Un")
        un_index = table_model.index(3, un_col)
        table_model.setCheckbox(un_index, Qt.CheckState.Checked)
        # Should remain only X, Un should not be added
        assert table_model.selections[3] == ["X"]  # Single item remains as list
        assert "Un" not in table_model.selections[3]

    def test_i0_un_prevention_same_row(self, table_model: MDAFileTableModel) -> None:
        """Test that I0 and Un cannot be selected on the same row."""
        # Select I0 on row 4
        i0_col = table_model.columnNumber("I0")
        i0_index = table_model.index(4, i0_col)
        table_model.setCheckbox(i0_index, Qt.CheckState.Checked)
        assert table_model.selections[4] == "I0"

        # Try to select Un on row 4 (should be prevented)
        un_col = table_model.columnNumber("Un")
        un_index = table_model.index(4, un_col)
        table_model.setCheckbox(un_index, Qt.CheckState.Checked)
        # Should remain only I0, Un should not be added
        assert table_model.selections[4] == ["I0"]  # Single item remains as list
        assert "Un" not in table_model.selections[4]

    def test_multiple_un_selections(self, table_model: MDAFileTableModel) -> None:
        """Test that multiple Un selections across different rows work."""
        # Select Y + Un on row 1
        y_col = table_model.columnNumber("Y")
        un_col = table_model.columnNumber("Un")

        table_model.setCheckbox(table_model.index(1, y_col), Qt.CheckState.Checked)
        table_model.setCheckbox(table_model.index(1, un_col), Qt.CheckState.Checked)
        assert table_model.selections[1] == ["Y", "Un"]

        # Select Y + Un on row 2
        table_model.setCheckbox(table_model.index(2, y_col), Qt.CheckState.Checked)
        table_model.setCheckbox(table_model.index(2, un_col), Qt.CheckState.Checked)
        assert table_model.selections[2] == ["Y", "Un"]

        # Select Y + Un on row 3
        table_model.setCheckbox(table_model.index(3, y_col), Qt.CheckState.Checked)
        table_model.setCheckbox(table_model.index(3, un_col), Qt.CheckState.Checked)
        assert table_model.selections[3] == ["Y", "Un"]

        # Verify all selections are maintained
        assert len([s for s in table_model.selections.values() if "Un" in s]) == 3

    def test_selection_persistence(self, table_model: MDAFileTableModel) -> None:
        """Test that selections persist when switching files."""
        # Set up initial selections
        table_model.selections = {1: ["Y", "Un"], 2: ["Y", "I0"], 3: "X"}

        # Simulate file switch by calling plotFields
        selections = table_model.plotFields()

        # Verify selections are preserved in the expected format
        assert "Y" in selections
        assert "Un" in selections
        assert "I0" in selections
        assert "X" in selections

        # Verify Y selections include both rows
        assert 1 in selections["Y"]
        assert 2 in selections["Y"]

        # Verify Un selections include row 1
        assert 1 in selections["Un"]

        # Verify I0 selection includes row 2 (I0 is unique, so it's a single value)
        assert selections["I0"] == 2

        # Verify X selection includes row 3 (X is unique, so it's a single value)
        assert selections["X"] == 3

    def test_unselection_behavior(self, table_model: MDAFileTableModel) -> None:
        """Test unselecting Y when Un is also selected."""
        # Set up Y + Un selection
        table_model.selections[1] = ["Y", "Un"]

        # Unselect Y
        y_col = table_model.columnNumber("Y")
        y_index = table_model.index(1, y_col)
        table_model.setCheckbox(y_index, Qt.CheckState.Unchecked)

        # Un should remain selected
        assert table_model.selections[1] == ["Un"]  # Single item remains as list

    def test_unselection_behavior_reverse(self, table_model: MDAFileTableModel) -> None:
        """Test unselecting Un when Y is also selected."""
        # Set up Y + Un selection
        table_model.selections[1] = ["Y", "Un"]

        # Unselect Un
        un_col = table_model.columnNumber("Un")
        un_index = table_model.index(1, un_col)
        table_model.setCheckbox(un_index, Qt.CheckState.Unchecked)

        # Y should remain selected
        assert table_model.selections[1] == ["Y"]  # Single item remains as list

    def test_unique_selection_rules(self, table_model: MDAFileTableModel) -> None:
        """Test that unique selection rules still work with Un column."""
        # Select X on row 1
        x_col = table_model.columnNumber("X")
        table_model.setCheckbox(table_model.index(1, x_col), Qt.CheckState.Checked)
        assert table_model.selections[1] == "X"

        # Select X on row 2 (should uncheck row 1)
        table_model.setCheckbox(table_model.index(2, x_col), Qt.CheckState.Checked)
        assert table_model.selections[2] == "X"
        assert 1 not in table_model.selections  # Row 1 should be unchecked

        # Select I0 on row 3
        i0_col = table_model.columnNumber("I0")
        table_model.setCheckbox(table_model.index(3, i0_col), Qt.CheckState.Checked)
        assert table_model.selections[3] == "I0"

        # Select I0 on row 4 (should uncheck row 3)
        table_model.setCheckbox(table_model.index(4, i0_col), Qt.CheckState.Checked)
        assert table_model.selections[4] == "I0"
        assert 3 not in table_model.selections  # Row 3 should be unchecked

    def test_checkbox_state_display(self, table_model: MDAFileTableModel) -> None:
        """Test that checkbox states display correctly for multiple selections."""
        # Set up Y + Un selection
        table_model.selections[1] = ["Y", "Un"]

        # Check that Y checkbox shows as checked
        y_col = table_model.columnNumber("Y")
        y_state = table_model.checkbox(table_model.index(1, y_col))
        assert y_state == Qt.CheckState.Checked

        # Check that Un checkbox shows as checked
        un_col = table_model.columnNumber("Un")
        un_state = table_model.checkbox(table_model.index(1, un_col))
        assert un_state == Qt.CheckState.Checked

        # Check that X checkbox shows as unchecked
        x_col = table_model.columnNumber("X")
        x_state = table_model.checkbox(table_model.index(1, x_col))
        assert x_state == Qt.CheckState.Unchecked
