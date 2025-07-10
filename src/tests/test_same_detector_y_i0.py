"""
Test for same detector Y/I0 selection functionality.

This test verifies that when the same detector is selected for both Y and I0,
the selection is allowed and the plot shows Y/Y = 1.
"""

import unittest
from unittest.mock import Mock

from mdaviz.mda_file_table_model import (
    MDAFileTableModel,
    TableColumn,
    ColumnDataType,
    FieldRuleType,
)


class TestSameDetectorYI0(unittest.TestCase):
    """Test cases for same detector Y/I0 selection functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Create column definitions
        self.columns = [
            TableColumn("Field", ColumnDataType.text, _=None),
            TableColumn(
                "X", ColumnDataType.checkbox, rule=FieldRuleType.unique, _=None
            ),
            TableColumn(
                "Y", ColumnDataType.checkbox, rule=FieldRuleType.multiple, _=None
            ),
            TableColumn(
                "I0", ColumnDataType.checkbox, rule=FieldRuleType.unique, _=None
            ),
            TableColumn("PV", ColumnDataType.text, _=None),
            TableColumn("DESC", ColumnDataType.text, _=None),
            TableColumn("Unit", ColumnDataType.text, _=None),
        ]

        # Create mock fields
        self.fields = [
            Mock(name="P1", pv="P1", desc="Positioner 1", unit="mm"),
            Mock(name="D1", pv="D1", desc="Detector 1", unit="counts"),
            Mock(name="D2", pv="D2", desc="Detector 2", unit="counts"),
        ]

        # Create mock parent
        self.mock_parent = Mock()

        # Create table model
        self.model = MDAFileTableModel(self.columns, self.fields, {}, self.mock_parent)

    def test_same_detector_y_i0_selection(self):
        """Test that same detector can be selected for both Y and I0."""
        # Simulate selecting detector 1 for Y
        y_index = self.model.index(1, 2)  # Row 1, Y column (index 2)
        self.model.setCheckbox(y_index, True)

        # Verify Y selection is recorded
        self.assertIn(1, self.model.selections)
        self.assertEqual(self.model.selections[1], "Y")

        # Simulate selecting the same detector for I0
        i0_index = self.model.index(1, 3)  # Row 1, I0 column (index 3)
        self.model.setCheckbox(i0_index, True)

        # Verify both Y and I0 selections are maintained
        self.assertIn(1, self.model.selections)
        # The last selection should be I0 (it overwrites the previous selection for the same row)
        self.assertEqual(self.model.selections[1], "I0")

        # Check that the plotFields method correctly identifies the selections
        plot_fields = self.model.plotFields()
        self.assertIn("I0", plot_fields)
        self.assertEqual(plot_fields["I0"], 1)

    def test_different_detectors_y_i0_selection(self):
        """Test that different detectors can be selected for Y and I0."""
        # Simulate selecting detector 1 for Y
        y1_index = self.model.index(1, 2)  # Row 1, Y column
        self.model.setCheckbox(y1_index, True)

        # Simulate selecting detector 2 for I0
        i0_index = self.model.index(2, 3)  # Row 2, I0 column
        self.model.setCheckbox(i0_index, True)

        # Verify both selections are maintained
        self.assertIn(1, self.model.selections)
        self.assertIn(2, self.model.selections)
        self.assertEqual(self.model.selections[1], "Y")
        self.assertEqual(self.model.selections[2], "I0")

        # Check that the plotFields method correctly identifies the selections
        plot_fields = self.model.plotFields()
        self.assertIn("Y", plot_fields)
        self.assertIn("I0", plot_fields)
        self.assertIn(1, plot_fields["Y"])
        self.assertEqual(plot_fields["I0"], 2)

    def test_unique_selection_conflict(self):
        """Test that unique selection columns still conflict with each other."""
        # Simulate selecting detector 1 for X
        x_index = self.model.index(1, 1)  # Row 1, X column
        self.model.setCheckbox(x_index, True)

        # Simulate selecting detector 2 for I0
        i0_index = self.model.index(2, 3)  # Row 2, I0 column
        self.model.setCheckbox(i0_index, True)

        # Now try to select detector 1 for I0 (should conflict with X)
        i0_conflict_index = self.model.index(1, 3)  # Row 1, I0 column
        self.model.setCheckbox(i0_conflict_index, True)

        # Verify that the X selection was removed when I0 was selected for the same row
        self.assertNotIn(1, self.model.selections)  # X selection should be removed
        self.assertIn(2, self.model.selections)  # I0 selection should remain
        self.assertEqual(self.model.selections[2], "I0")


if __name__ == "__main__":
    unittest.main()
