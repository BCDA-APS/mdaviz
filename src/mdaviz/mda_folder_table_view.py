"""
Search for mda files.
"""

from PyQt6.QtCore import Qt, QSortFilterProxyModel
from PyQt6.QtWidgets import QWidget, QHeaderView
from mdaviz import utils
from mdaviz.mda_folder_table_model import HEADERS


class FolderSortProxyModel(QSortFilterProxyModel):
    """Proxy model with correct numeric sorting for Scan # and Points columns."""

    NUMERIC_COLUMNS = {1, 2}  # Scan #, Points

    def lessThan(self, left, right):
        if left.column() in self.NUMERIC_COLUMNS:
            try:
                return int(left.data() or 0) < int(right.data() or 0)
            except (ValueError, TypeError):
                pass
        return super().lessThan(left, right)


class MDAFolderTableView(QWidget):
    ui_file = utils.getUiFileName(__file__)

    def __init__(self, parent):
        """
        Create the table view and connect with its parent.

        PARAMETERS

        parent object:
            Instance of mdaviz.mda_folder.MDAMVC
        """

        self.mda_mvc = parent
        super().__init__()
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()

    def setup(self):
        # Configure the horizontal header to resize based on content.
        header = self.tableView.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.proxyModel = None

    def displayTable(self):
        from mdaviz.mda_folder_table_model import MDAFolderTableModel
        from mdaviz.empty_table_model import EmptyTableModel

        data = self.mdaInfoList()
        if len(data) > 0:
            data_model = MDAFolderTableModel(data, self.mda_mvc)
            self.proxyModel = FolderSortProxyModel()
            self.proxyModel.setSourceModel(data_model)
            self.tableView.setModel(self.proxyModel)
            self.tableView.setSortingEnabled(True)
            self.applyDefaultSort()
        else:
            self.proxyModel = None
            empty_model = EmptyTableModel(HEADERS)
            self.tableView.setModel(empty_model)

    def applyDefaultSort(self):
        """Apply the sort order from user preferences (newest first or natural order)."""
        if self.proxyModel is None:
            return
        from mdaviz.user_settings import settings

        sort_newest = settings.getKey("sort_newest_first")
        if isinstance(sort_newest, str):
            sort_newest = sort_newest.lower() in ("true", "1", "yes", "on")
        DATE_COLUMN = 4
        if sort_newest:
            self.proxyModel.sort(DATE_COLUMN, Qt.SortOrder.DescendingOrder)
        else:
            self.proxyModel.sort(-1)  # -1 restores natural (source model) order

    def sourceRow(self, proxy_index):
        """Map a proxy model index to the underlying source model row."""
        if self.proxyModel is not None and proxy_index.isValid():
            return self.proxyModel.mapToSource(proxy_index).row()
        return proxy_index.row()

    def mdaInfoList(self):
        """List of mda file (name only) in the selected folder."""
        return self.mda_mvc.mdaInfoList()

    def setStatus(self, text):
        self.mda_mvc.setStatus(text)

    def clearContents(self):
        # Clear the data model of the table view
        self.tableView.setModel(None)
        self.proxyModel = None
