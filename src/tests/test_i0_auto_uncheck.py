"""
Test for I0 auto-unchecking functionality.

This test verifies that when switching between files, if the I0 PV from the previous
file doesn't exist in the new file, the I0 checkbox is automatically unchecked.
"""

import unittest
from unittest.mock import Mock, patch
from PyQt6.QtWidgets import QApplication

from mdaviz.mda_folder import MDA_MVC


def create_mock_settings():
    """Create a mock settings function that returns appropriate values for different keys."""

    def mock_get_key(key: str) -> str | int | None:
        if "width" in key:
            return 800
        elif "height" in key or "plot_max_height" in key:
            return 600
        elif "x" in key:
            return 100
        elif "y" in key:
            return 100
        elif "geometry" in key:
            return "800x600+100+100"
        elif "sizes" in key:
            # Return None for splitter sizes to use defaults
            return None
        else:
            return "default_value"

    return mock_get_key


class TestI0AutoUncheck(unittest.TestCase):
    """Test cases for I0 auto-unchecking functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Ensure QApplication exists (required for QWidget creation)
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication([])

        self.mock_parent = Mock()

        # Mock the mainWindow methods that are called during initialization
        self.mock_parent.mdaFileList.return_value = []
        self.mock_parent.mdaInfoList.return_value = []

        # Mock settings.getKey to prevent QSettings errors
        self.settings_patcher = patch(
            "mdaviz.user_settings.settings.getKey", side_effect=create_mock_settings()
        )
        self.settings_patcher.start()

        self.mda_mvc = MDA_MVC(self.mock_parent)

        # Mock the tableview and its model
        self.mock_tableview = Mock()
        self.mock_model = Mock()
        # plotFields() returns a dict used to check if "I0" is in it
        self.mock_model.plotFields.return_value = {}
        self.mock_tableview.tableView.model.return_value = self.mock_model

        # Mock the currentFileTableview method
        self.mda_mvc.currentFileTableview = Mock(return_value=self.mock_tableview)

    def tearDown(self):
        """Clean up after tests."""
        self.settings_patcher.stop()

    def test_i0_auto_uncheck_when_pv_removed(self):
        """Test that I0 checkbox is unchecked when I0 PV doesn't exist in new file."""
        # Setup old selection with I0
        old_selection = {"X": 0, "Y": [1, 2], "I0": 3}
        old_pv_list = ["P1", "D1", "D2", "I0_old"]
        new_pv_list = ["P1", "D1", "D2", "D3"]  # I0_old is not in new list

        # Make plotFields return I0 so uncheckI0 can find and uncheck it
        self.mock_model.plotFields.return_value = {"I0": 3}

        # Call the method under test
        self.mda_mvc.updateSelectionForNewPVs(
            old_selection, old_pv_list, new_pv_list, verbose=True
        )

        # Verify that uncheckCheckBox was called for the I0 row
        self.mock_model.uncheckCheckBox.assert_called_once_with(3)

    def test_i0_auto_uncheck_when_index_out_of_range(self):
        """Test that I0 checkbox is unchecked when I0 index is out of range."""
        # Setup old selection with invalid I0 index
        old_selection = {"X": 0, "Y": [1, 2], "I0": 10}  # Index 10 doesn't exist
        old_pv_list = ["P1", "D1", "D2"]  # Only 3 items, index 10 is out of range
        new_pv_list = ["P1", "D1", "D2"]

        # Make plotFields return I0 so uncheckI0 can find and uncheck it
        self.mock_model.plotFields.return_value = {"I0": 10}

        # Call the method under test
        self.mda_mvc.updateSelectionForNewPVs(
            old_selection, old_pv_list, new_pv_list, verbose=True
        )

        # Verify that uncheckCheckBox was called for the invalid I0 row
        self.mock_model.uncheckCheckBox.assert_called_once_with(10)

    def test_i0_preserved_when_pv_exists(self):
        """Test that I0 selection is preserved when I0 PV exists in new file."""
        # Setup old selection with I0
        old_selection = {"X": 0, "Y": [1, 2], "I0": 3}
        old_pv_list = ["P1", "D1", "D2", "I0_old"]
        new_pv_list = ["P1", "D1", "D2", "I0_old"]  # I0_old exists in new list

        # Call the method under test
        self.mda_mvc.updateSelectionForNewPVs(
            old_selection, old_pv_list, new_pv_list, verbose=True
        )

        # Verify that the I0 selection is preserved in the selection field
        # Since the I0 index is the same (3), no changes should be made
        # and the selection field should remain None (initial state)
        self.assertIsNone(self.mda_mvc.selectionField())

    def test_no_i0_in_old_selection(self):
        """Test that nothing happens when there's no I0 in old selection."""
        # Setup old selection without I0
        old_selection = {"X": 0, "Y": [1, 2]}  # No I0
        old_pv_list = ["P1", "D1", "D2"]
        new_pv_list = ["P1", "D1", "D2"]

        # Call the method under test
        self.mda_mvc.updateSelectionForNewPVs(
            old_selection, old_pv_list, new_pv_list, verbose=True
        )

        # Verify that uncheckCheckBox was not called
        self.mock_model.uncheckCheckBox.assert_not_called()

    def test_empty_old_selection(self):
        """Test that nothing happens when old selection is empty."""
        # Setup empty old selection
        old_selection = None
        old_pv_list = ["P1", "D1", "D2"]
        new_pv_list = ["P1", "D1", "D2"]

        # Call the method under test
        self.mda_mvc.updateSelectionForNewPVs(
            old_selection, old_pv_list, new_pv_list, verbose=True
        )

        # Verify that uncheckCheckBox was not called
        self.mock_model.uncheckCheckBox.assert_not_called()


if __name__ == "__main__":
    unittest.main()
