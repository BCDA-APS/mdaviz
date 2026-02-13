"""
Tests for DataTableModel and EmptyTableModel.

Covers rowCount, columnCount, data(), headerData(), setAllData, allData, columnLabels.
"""

from PyQt6.QtCore import Qt, QModelIndex

from mdaviz.data_table_model import DataTableModel
from mdaviz.empty_table_model import EmptyTableModel


def _make_scan_dict():
    """scanDict format: {index: {'name': pv_name, 'data': list, ...}}."""
    return {
        0: {"name": "P0", "data": [0, 1, 2, 3], "unit": "a.u.", "desc": "Index"},
        1: {
            "name": "D1",
            "data": [10.0, 20.0, 30.0, 40.0],
            "unit": "counts",
            "desc": "Det1",
        },
        2: {
            "name": "D2",
            "data": [1, 2, 3],
            "unit": "counts",
            "desc": "Det2",
        },  # shorter
    }


class TestDataTableModel:
    """Tests for DataTableModel."""

    def test_init_and_row_count(self):
        """rowCount is max length of any column's data."""
        scan_dict = _make_scan_dict()
        model = DataTableModel(scan_dict)
        assert model.rowCount() == 4  # P0 and D1 have 4 elements

    def test_column_count(self):
        """columnCount equals number of columns (keys in scanDict)."""
        scan_dict = _make_scan_dict()
        model = DataTableModel(scan_dict)
        assert model.columnCount() == 3

    def test_all_data_and_column_labels(self):
        """allData() maps PV name to data list; columnLabels are PV names."""
        scan_dict = _make_scan_dict()
        model = DataTableModel(scan_dict)
        data = model.allData()
        assert "P0" in data
        assert "D1" in data
        assert "D2" in data
        assert data["P0"] == [0, 1, 2, 3]
        assert data["D1"] == [10.0, 20.0, 30.0, 40.0]
        labels = model.columnLabels()
        assert len(labels) == 3
        assert "P0" in labels and "D1" in labels and "D2" in labels

    def test_data_display_role(self):
        """data(index, DisplayRole) returns cell value as string."""
        scan_dict = _make_scan_dict()
        model = DataTableModel(scan_dict)
        idx = model.index(1, 0)  # row 1, first column (P0)
        assert idx.isValid()
        val = model.data(idx, Qt.ItemDataRole.DisplayRole)
        assert val == "1"
        idx_d1 = model.index(2, 1)  # row 2, D1
        assert model.data(idx_d1, Qt.ItemDataRole.DisplayRole) == "30.0"

    def test_data_invalid_index(self):
        """data() returns QVariant() for invalid index."""
        scan_dict = _make_scan_dict()
        model = DataTableModel(scan_dict)
        invalid = QModelIndex()
        from PyQt6.QtCore import QVariant

        assert model.data(invalid) == QVariant()

    def test_header_data_horizontal(self):
        """headerData() returns column label for horizontal header."""
        scan_dict = _make_scan_dict()
        model = DataTableModel(scan_dict)
        h = model.headerData(0, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
        assert h in model.columnLabels()
        h1 = model.headerData(1, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
        assert h1 in model.columnLabels()

    def test_set_all_data_empty(self):
        """setAllData({}) gives rowCount 0 and columnCount 0."""
        model = DataTableModel({})
        assert model.rowCount() == 0
        assert model.columnCount() == 0
        assert model.allData() == {}

    def test_set_all_data_then_update(self):
        """setAllData with new scanDict updates row/column counts and data."""
        model = DataTableModel(_make_scan_dict())
        assert model.rowCount() == 4
        new_scan = {
            0: {"name": "X", "data": [1, 2]},
            1: {"name": "Y", "data": [3, 4]},
        }
        model.setAllData(new_scan)
        model.setColumnLabels()
        assert model.rowCount() == 2
        assert model.columnCount() == 2
        assert model.allData()["X"] == [1, 2]
        assert model.allData()["Y"] == [3, 4]


class TestEmptyTableModel:
    """Tests for EmptyTableModel."""

    def test_row_count_zero(self):
        """EmptyTableModel has 0 rows."""
        model = EmptyTableModel(["A", "B", "C"])
        assert model.rowCount() == 0

    def test_column_count_from_headers(self):
        """columnCount equals len(headers)."""
        model = EmptyTableModel(["X", "Y", "Z"])
        assert model.columnCount() == 3

    def test_data_returns_variant(self):
        """data() returns QVariant (no data)."""
        model = EmptyTableModel(["A", "B"])
        idx = model.index(0, 0)
        from PyQt6.QtCore import QVariant

        assert model.data(idx, Qt.ItemDataRole.DisplayRole) == QVariant()

    def test_header_data_horizontal(self):
        """headerData() returns headers for horizontal orientation (role=DisplayRole, orientation=Horizontal)."""
        headers = ["Col1", "Col2"]
        model = EmptyTableModel(headers)
        # EmptyTableModel checks orientation == 1 (Horizontal) and role == 0 (DisplayRole)
        r0 = model.headerData(0, 1, 0)
        r1 = model.headerData(1, 1, 0)
        v0 = r0.value() if hasattr(r0, "value") else r0
        v1 = r1.value() if hasattr(r1, "value") else r1
        assert v0 == "Col1"
        assert v1 == "Col2"

    def test_clear_all_checkboxes_no_op(self):
        """clearAllCheckboxes() does not raise."""
        model = EmptyTableModel(["A"])
        model.clearAllCheckboxes()

    def test_uncheck_check_box_no_op(self):
        """uncheckCheckBox(row) does not raise."""
        model = EmptyTableModel(["A"])
        model.uncheckCheckBox(0)
