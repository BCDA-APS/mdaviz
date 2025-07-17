"""
Enhanced MDA file management with optimized loading and caching.

This module provides advanced MDA file handling with performance optimizations,
asynchronous loading capabilities, and comprehensive error handling.

.. autosummary::

    ~MDAFile
    ~TabManager
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtWidgets import QAbstractItemView, QWidget, QSplitter

from mdaviz.synApps_mdalib.mda import readMDA
from mdaviz.data_cache import get_global_cache, CachedFileData
from mdaviz.mda_file_table_view import MDAFileTableView
from mdaviz.utils import OptimizedFileReader
from mdaviz import utils


class MDAFile(QWidget):
    """
    Enhanced MDA file manager with optimized loading and caching.

    This widget provides advanced MDA file handling with performance optimizations,
    asynchronous loading capabilities, memory management, and comprehensive error handling.

    Attributes:
        enable_async_loading (bool): Whether to use asynchronous file loading
        preload_enabled (bool): Whether to preload adjacent files for faster navigation
        max_preload_files (int): Maximum number of files to preload
        memory_limit_mb (float): Memory limit for file operations
    """

    # Signals for async operations
    file_loading_started = pyqtSignal(str)  # file path
    file_loading_completed = pyqtSignal(str, bool)  # file path, success
    file_loading_progress = pyqtSignal(int, int)  # current, total
    memory_warning = pyqtSignal(float)  # memory usage in MB
    
    # Emit the action when button is pushed:
    buttonPushed = pyqtSignal(str)
    # Emit the new tab index (int), file path (str), data (dict) and selection field (dict):
    tabChanged = pyqtSignal(int, str, dict, dict)

    # UI file name matches this module, different extension
    ui_file = utils.getUiFileName(__file__)

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        enable_async_loading: bool = True,
        preload_enabled: bool = True,
        max_preload_files: int = 3,
        memory_limit_mb: float = 200.0,
    ) -> None:
        """
        Initialize the enhanced MDA file manager.

        Parameters:
            parent (Optional[QWidget]): Parent widget (should be MDA_MVC instance)
            enable_async_loading (bool): Whether to use asynchronous file loading
            preload_enabled (bool): Whether to preload adjacent files
            max_preload_files (int): Maximum number of files to preload
            memory_limit_mb (float): Memory limit for file operations
        """
        super().__init__(parent)

        # Store reference to parent MDA_MVC instance
        self.mda_mvc = parent

        self.enable_async_loading = enable_async_loading
        self.preload_enabled = preload_enabled
        self.max_preload_files = max_preload_files
        self.memory_limit_mb = memory_limit_mb

        # Initialize optimized file reader
        self._file_reader = OptimizedFileReader(
            max_memory_mb=memory_limit_mb,
            enable_parallel=enable_async_loading,
            max_workers=4,
        )

        # Performance tracking
        self._load_times: Dict[str, float] = {}
        self._preloaded_files: Dict[str, CachedFileData] = {}
        self._loading_futures: Dict[str, asyncio.Future] = {}

        # Async loading support
        self._executor = (
            ThreadPoolExecutor(max_workers=2) if enable_async_loading else None
        )
        self._preload_timer = QTimer()
        self._preload_timer.setSingleShot(True)
        self._preload_timer.timeout.connect(self._perform_preload)

        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()

    def setup(self) -> None:
        """
        Set up the MDA file manager with enhanced features.

        This method initializes the UI components, connects signals,
        and sets up performance monitoring.
        """
        try:
            from functools import partial

            # Initialize data structure
            self._data: Dict[str, Any] = {}

            # Initialize attributes
            self.setData()
            self.tabManager = TabManager(self)  # Instantiate TabManager
            self.currentHighlightedRow = None  # To store the current highlighted row
            self.currentHighlightedFilePath = None  # To store the current highlighted row's file path
            self.currentHighlightedModel = None  # To store the current highlighted's row model

            # Buttons handling:
            self.addButton.hide()
            self.replaceButton.hide()
            self.addButton.clicked.connect(partial(self.responder, "add"))
            self.clearButton.clicked.connect(partial(self.responder, "clear"))
            self.replaceButton.clicked.connect(partial(self.responder, "replace"))
            self.clearGraphButton.clicked.connect(self.onClearGraphRequested)

            # Mode handling:
            options = ["Auto-replace", "Auto-add", "Auto-off"]
            self.setMode(options[0])
            self.autoBox.addItems(options)
            self.autoBox.currentTextChanged.connect(self.setMode)
            self.autoBox.currentTextChanged.connect(self.updateButtonVisibility)

            # Connect TabManager signals:
            self.tabManager.tabAdded.connect(self.onTabAdded)
            self.tabManager.tabRemoved.connect(self.onTabRemoved)
            self.tabManager.allTabsRemoved.connect(self.onAllTabsRemoved)

            # Tab handling:
            self.tabWidget.currentChanged.connect(self.updateCurrentTabInfo)
            self.tabWidget.tabCloseRequested.connect(self.onTabCloseRequested)

            # Set up selection behavior
            self.tableView.setSelectionBehavior(
                QAbstractItemView.SelectionBehavior.SelectRows
            )

            # Connect signals for performance monitoring
            self.file_loading_completed.connect(self._on_file_loaded)

            # Set up memory monitoring if available
            try:
                import psutil

                self._memory_timer = QTimer()
                self._memory_timer.timeout.connect(self._check_memory_usage)
                self._memory_timer.start(10000)  # Check every 10 seconds
            except ImportError:
                pass  # Memory monitoring not available

        except Exception as e:
            print(f"Error setting up MDA file manager: {e}")

    def setData(self, index: Optional[int] = None) -> None:
        """
        Enhanced data loading with async support and caching optimization.

        This method loads MDA file data with performance optimizations including
        asynchronous loading, intelligent caching, and memory management.

        Parameters:
            index (Optional[int]): The index of the file in the MDA file list.
                                 If None, clears the data.
        """
        if index is None:
            self._data = {}
            return

        try:
            # Get file information
            folder_path = self.dataPath()
            file_list = self.mdaFileList()

            if not file_list or index >= len(file_list):
                print(f"Invalid file index: {index}")
                self._data = {}
                return

            file_name = file_list[index]
            file_path = folder_path / file_name

            # Emit loading started signal
            self.file_loading_started.emit(str(file_path))

            # Track loading time
            start_time = time.time()

            # Try to load from cache first
            cache = get_global_cache()
            cached_data = cache.get(str(file_path))

            if cached_data:
                # Use cached data for immediate response
                self._populate_data_from_cache(cached_data, index)
                load_time = time.time() - start_time
                self._load_times[str(file_path)] = load_time
                self.file_loading_completed.emit(str(file_path), True)

                # Schedule preloading of adjacent files
                if self.preload_enabled:
                    self._schedule_preload(index)

                return

            # Load file data with optimization
            if self.enable_async_loading:
                self._load_file_async(file_path, index)
            else:
                self._load_file_sync(file_path, index)

        except Exception as e:
            print(f"Error in setData: {e}")
            self._create_fallback_data(index)
            self.file_loading_completed.emit(
                str(file_path) if "file_path" in locals() else "", False
            )

    def _load_file_sync(self, file_path: Path, index: int) -> None:
        """
        Synchronously load file data with optimizations.

        Parameters:
            file_path (Path): Path to the MDA file
            index (int): File index
        """
        try:
            start_time = time.time()

            # Use optimized file reader
            file_info = self._file_reader.read_file_optimized(file_path)
            if not file_info:
                raise ValueError(f"Could not read file: {file_path}")

            # Load full data using cache system
            cache = get_global_cache()
            cached_data = cache.get_or_load(str(file_path))

            if cached_data:
                self._populate_data_from_cache(cached_data, index)
            else:
                # Fallback direct loading
                self._load_direct(file_path, index)

            # Track performance
            load_time = time.time() - start_time
            self._load_times[str(file_path)] = load_time

            self.file_loading_completed.emit(str(file_path), True)

            # Schedule preloading
            if self.preload_enabled:
                self._schedule_preload(index)

        except Exception as e:
            print(f"Error loading file {file_path}: {e}")
            self._create_fallback_data(index)
            self.file_loading_completed.emit(str(file_path), False)

    def _load_file_async(self, file_path: Path, index: int) -> None:
        """
        Asynchronously load file data for better UI responsiveness.

        Parameters:
            file_path (Path): Path to the MDA file
            index (int): File index
        """
        if not self._executor:
            # Fallback to sync loading
            self._load_file_sync(file_path, index)
            return

        def load_worker():
            """Worker function for async loading."""
            try:
                start_time = time.time()

                # Load through cache system
                cache = get_global_cache()
                cached_data = cache.get_or_load(str(file_path))

                load_time = time.time() - start_time
                return cached_data, load_time, None

            except Exception as e:
                return None, 0.0, str(e)

        def on_complete(future):
            """Callback for async loading completion."""
            try:
                cached_data, load_time, error = future.result()

                if error:
                    print(f"Async loading error: {error}")
                    self._create_fallback_data(index)
                    self.file_loading_completed.emit(str(file_path), False)
                    return

                if cached_data:
                    self._populate_data_from_cache(cached_data, index)
                    self._load_times[str(file_path)] = load_time
                    self.file_loading_completed.emit(str(file_path), True)

                    # Schedule preloading
                    if self.preload_enabled:
                        self._schedule_preload(index)
                else:
                    self._create_fallback_data(index)
                    self.file_loading_completed.emit(str(file_path), False)

            except Exception as e:
                print(f"Error in async callback: {e}")
                self._create_fallback_data(index)
                self.file_loading_completed.emit(str(file_path), False)

        # Submit async task
        future = self._executor.submit(load_worker)
        future.add_done_callback(on_complete)

    def _populate_data_from_cache(
        self, cached_data: CachedFileData, index: int
    ) -> None:
        """
        Populate internal data structure from cached data.

        Parameters:
            cached_data (CachedFileData): Cached file data
            index (int): File index
        """
        self._data = {
            "fileName": cached_data.file_name,
            "filePath": cached_data.file_path,
            "folderPath": cached_data.folder_path,
            "metadata": cached_data.metadata,
            "scanDict": cached_data.scan_dict,
            "firstPos": cached_data.first_pos,
            "firstDet": cached_data.first_det,
            "pvList": cached_data.pv_list,
            "index": index,
        }

    def _load_direct(self, file_path: Path, index: int) -> None:
        """
        Direct file loading fallback method.

        Parameters:
            file_path (Path): Path to the MDA file
            index (int): File index
        """
        result = readMDA(str(file_path))
        if result is None:
            raise ValueError(f"Could not read file: {file_path}")

        file_metadata, file_data_dim1, *_ = result

        if file_metadata.get("rank", 0) > 1:
            print("WARNING: Multidimensional data not supported - ignoring ranks > 1.")

        scan_dict, first_pos, first_det = utils.get_scan(file_data_dim1)
        pv_list = [v["name"] for v in scan_dict.values()]

        self._data = {
            "fileName": file_path.stem,
            "filePath": str(file_path),
            "folderPath": str(file_path.parent),
            "metadata": file_metadata,
            "scanDict": scan_dict,
            "firstPos": first_pos,
            "firstDet": first_det,
            "pvList": pv_list,
            "index": index,
        }

    def _create_fallback_data(self, index: int) -> None:
        """
        Create fallback data structure when loading fails.

        Parameters:
            index (int): File index
        """
        try:
            folder_path = self.dataPath()
            file_list = self.mdaFileList()

            if file_list and index < len(file_list):
                file_name = file_list[index]
                file_path = folder_path / file_name
            else:
                file_name = "unknown.mda"
                file_path = folder_path / file_name

            self._data = {
                "fileName": file_path.stem,
                "filePath": str(file_path),
                "folderPath": str(folder_path),
                "metadata": {},
                "scanDict": {},
                "firstPos": "P0",
                "firstDet": "D01",
                "pvList": [],
                "index": index,
            }
        except Exception as e:
            print(f"Error creating fallback data: {e}")
            self._data = {}

    def _schedule_preload(self, current_index: int) -> None:
        """
        Schedule preloading of adjacent files for faster navigation.

        Parameters:
            current_index (int): Current file index
        """
        if not self.preload_enabled:
            return

        # Delay preloading to avoid interfering with current operation
        self._preload_timer.start(500)  # 500ms delay

    def _perform_preload(self) -> None:
        """Perform preloading of adjacent files."""
        try:
            if not self._data or "index" not in self._data:
                return

            current_index = self._data["index"]
            file_list = self.mdaFileList()

            if not file_list:
                return

            folder_path = self.dataPath()
            cache = get_global_cache()

            # Determine files to preload (adjacent files)
            preload_indices = []
            for offset in range(1, self.max_preload_files + 1):
                # Next files
                if current_index + offset < len(file_list):
                    preload_indices.append(current_index + offset)
                # Previous files
                if current_index - offset >= 0:
                    preload_indices.append(current_index - offset)

            # Preload files that aren't already cached
            for idx in preload_indices:
                file_name = file_list[idx]
                file_path = str(folder_path / file_name)

                if not cache.get(file_path):
                    # Preload in background
                    cache.get_or_load(file_path)

        except Exception as e:
            print(f"Error during preloading: {e}")

    def _check_memory_usage(self) -> None:
        """Check memory usage and emit warnings if needed."""
        try:
            import psutil

            process = psutil.Process()
            memory_mb = process.memory_info().rss / (1024 * 1024)

            if memory_mb > self.memory_limit_mb:
                self.memory_warning.emit(memory_mb)
        except:
            pass

    def _on_file_loaded(self, file_path: str, success: bool) -> None:
        """
        Handle file loading completion.

        Parameters:
            file_path (str): Path of the loaded file
            success (bool): Whether loading was successful
        """
        if success and file_path in self._load_times:
            load_time = self._load_times[file_path]
            if load_time > 2.0:  # Slow loading threshold
                print(f"Slow file loading detected: {file_path} took {load_time:.2f}s")

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics for file operations.

        Returns:
            Dict[str, Any]: Performance statistics including load times and cache stats
        """
        stats = {
            "total_files_loaded": len(self._load_times),
            "average_load_time": sum(self._load_times.values()) / len(self._load_times)
            if self._load_times
            else 0.0,
            "slowest_file": max(self._load_times.items(), key=lambda x: x[1])
            if self._load_times
            else None,
            "preloaded_files": len(self._preloaded_files),
            "async_loading_enabled": self.enable_async_loading,
            "preload_enabled": self.preload_enabled,
        }

        return stats

    def cleanup(self) -> None:
        """Clean up resources and stop background operations."""
        try:
            # Stop timers
            if hasattr(self, "_preload_timer"):
                self._preload_timer.stop()
            if hasattr(self, "_memory_timer"):
                self._memory_timer.stop()

            # Shutdown executor
            if self._executor:
                self._executor.shutdown(wait=False)

            # Clear caches
            self._load_times.clear()
            self._preloaded_files.clear()
            self._loading_futures.clear()

        except Exception as e:
            print(f"Error during cleanup: {e}")

    def closeEvent(self, event) -> None:
        """Handle widget close event with proper cleanup."""
        self.cleanup()
        super().closeEvent(event)

    # Existing methods with type annotations added
    def dataPath(self) -> Path:
        """Get the data path for the current folder."""
        if self.mda_mvc is None:
            return Path()
        return self.mda_mvc.dataPath()

    def mdaFileList(self) -> List[str]:
        """Get the list of MDA file names."""
        if self.mda_mvc is None:
            return []
        return self.mda_mvc.mdaFileList()

    def data(self) -> Dict[str, Any]:
        """Get the current file data."""
        return self._data

    def setStatus(self, message: str) -> None:
        """Set status message."""
        if self.mda_mvc is not None:
            self.mda_mvc.setStatus(message)

    # ------ Get & set methods:

    def mode(self) -> str:
        """
        Get the current mode.
        
        Returns:
            str: "Auto-replace", "Auto-add", or "Auto-off"
        """
        return getattr(self, '_mode', 'Auto-replace')

    def setMode(self, mode: str) -> None:
        """
        Set the current mode.
        
        Parameters:
            mode (str): The mode to set ("Auto-replace", "Auto-add", or "Auto-off")
        """
        self._mode = mode

    def getData(self) -> Dict[str, Any]:
        """
        Get the data to display in the table view.
        
        Returns:
            Dict[str, Any]: The current file data
        """
        return self._data

    # ------ Button and tab management methods:

    def responder(self, action: str) -> None:
        """
        Modify the plot with the described action.
        
        Parameters:
            action (str): Action from buttons: add, clear, replace
        """
        print(f"\nResponder: {action=}")
        self.buttonPushed.emit(action)

    def onTabCloseRequested(self, index: int) -> None:
        """
        Handles tab close request by calling the tab manager.
        
        Parameters:
            index (int): Index of the tab to close
        """
        file_path = self.tabIndex2Path(index)
        if file_path:
            self.tabManager.removeTab(file_path)

    def onTabAdded(self, file_path: str) -> None:
        """To be implemented"""
        pass

    def onTabRemoved(self, file_path: str) -> None:
        """
        Removes a tab from the tab widget based on its file_path.
        If it's the last tab, it calls removeAllTabs() to ensure consistent cleanup.
        
        Parameters:
            file_path (str): Path of the file to remove
        """
        index = self.tabPath2Index(file_path)
        if self.tabWidget.count() == 1 and index == 0:
            self.removeAllFileTabs()
        elif index is not None and index < self.tabWidget.count():
            self.tabWidget.removeTab(index)

    def onAllTabsRemoved(self) -> None:
        """To be implemented"""
        pass

    def onClearGraphRequested(self) -> None:
        """Clear only the graph area in the visualization panel."""
        if self.mda_mvc is not None:
            # Get the chart view and clear all curves with checkboxes
            layout = self.mda_mvc.mda_file_viz.plotPageMpl.layout()
            if layout.count() > 0:
                plot_widget = layout.itemAt(0).widget()
                if hasattr(plot_widget, "curveManager"):
                    plot_widget.curveManager.removeAllCurves(doNotClearCheckboxes=False)
        self.setStatus("Graph cleared.")

    def updateCurrentTabInfo(self, new_tab_index: int) -> None:
        """
        When the current tab is changed, sends a signal to the MDA_MVC with the info
        corresponding to the new selected tab:
            new_tab_index, new_file_path, new_tab_data, new_selection_field
        
        Parameters:
            new_tab_index (int): Index of the new tab
        """
        new_file_path = self.tabIndex2Path(new_tab_index)
        if new_file_path is not None:
            new_tab_data = self.tabManager.getTabData(new_file_path) or {}
        else:
            new_tab_data = {}
        new_tab_tableview = self.tabWidget.widget(new_tab_index)
        if new_tab_tableview and new_tab_tableview.tableView.model():
            new_selection_field = new_tab_tableview.tableView.model().plotFields()
        else:
            new_selection_field = {}
        self.tabChanged.emit(
            new_tab_index, new_file_path or "", new_tab_data, new_selection_field
        )

    def updateButtonVisibility(self) -> None:
        """Update button visibility based on current mode."""
        mode = self.mode()
        if mode == "Auto-off":
            self.addButton.show()
            self.replaceButton.show()
        else:
            self.addButton.hide()
            self.replaceButton.hide()

    # ------ Tab management methods:

    def addFileTab(self, index: int, selection_field: dict) -> None:
        """
        Handles adding or activating a file tab within the tab widget.
        - Retrieves data for the selected file based on its index in the MDA file list.
        - Updates display for metadata and table data in the visualization panel.
        - Determines and applies the default selection of fields if necessary.
        - Checks if a tab for the file already exists; if so, activates it.
        - If the file is new, depending on the mode (Auto-add, Auto-replace, Auto-off),
        it creates a new tab or replaces existing tabs with the new file tab.

        Parameters:
            index (int): The index of the file in the MDA file list.
            selection_field (dict): Specifies the fields (positioners/detectors) for display
            and plotting.
        """
        # Get data for the selected file:
        self.setData(index)
        data = self.data()
        file_path = data["filePath"]
        file_name = data["fileName"]
        first_pos = data["firstPos"]
        first_det = data["firstDet"]
        metadata = data["metadata"]
        tabledata = data["scanDict"]

        # Update data, metadata & selection field (if needed):
        self.displayMetadata(metadata)
        self.displayData(tabledata)
        selection_field = self.defaultSelection(first_pos, first_det, selection_field)
        # Update tab widget:
        if self.tabManager.getTabData(file_path):
            tab_index = self.tabPath2Index(file_path)
            self.tabWidget.setCurrentIndex(tab_index)
        else:
            mode = self.mode()
            if mode in ("Auto-add", "Auto-off"):
                # Add this tab to the UI:
                self.createNewTab(file_name, file_path, selection_field)
            elif mode in ("Auto-replace"):
                # Clear all existing tabs:
                while self.tabWidget.count() > 0:
                    self.tabWidget.removeTab(0)
                self.tabManager.removeAllTabs()
                # Add this tab to the UI:
                self.createNewTab(file_name, file_path, selection_field)
            # Add new tab to tabManager:
            self.tabManager.addTab(file_path, metadata, tabledata)

    def createNewTab(self, file_name: str, file_path: str, selection_field: dict) -> None:
        """
        Creates and activates a new tab with a MDAFileTableView for the selected file.
        - Initializes a new MDAFileTableView with data based on the provided file and selection field.
        - Adds a new tab to the tab widget.
        - Labels the new tab with the file's name.
        - Sets the new tab as the current active tab.
        - Updates the file path Qlabel (named filePath) within MDAFileTableView to reflect the selected file's path.

        Parameters:
            file_name (str): The name of the file, used as the tab's label.
            file_path (str): The full path to the file, used to populate the table view and label.
            selection_field (dict): Specifies the data fields (positioners/detectors) for display in the table view.
        """
        tableview = MDAFileTableView(self)
        tab_index = self.tabWidget.addTab(tableview, file_name)
        self.tabWidget.setCurrentIndex(tab_index)
        tableview.displayTable(selection_field)
        tableview.filePath.setText(file_path)
        self.tabWidget.setTabToolTip(tab_index, file_path)

    def removeAllFileTabs(self) -> None:
        """
        Removes all tabs from the tab widget.
        """
        while self.tabWidget.count() > 0:
            self.tabWidget.removeTab(self.tabWidget.count() - 1)
        # Clear all data associated with the tabs from the TabManager.
        self.tabManager.removeAllTabs()
        # Clear all content from the visualization panel except for graph, if no tabs are open.
        self.mda_mvc.mda_file_viz.clearContents(plot=False)
        # Update the status to reflect that all tabs have been closed.
        self.setStatus("All file tabs have been closed.")

    def highlightRowInTab(self, file_path: str, row: int) -> None:
        """
        Switch to the tab corresponding to the given file path and highlight a specific row.

        Parameters:
            file_path (str): Path of the file
            row (int): Row to highlight
        """
        tab_index = self.tabPath2Index(file_path)
        self.tabWidget.setCurrentIndex(tab_index)
        tableview = self.tabWidget.widget(tab_index)
        model = tableview.tableView.model()
        if model is not None:
            # Unhighlight the previous row if it exists
            if (
                self.currentHighlightedRow is not None
                and self.currentHighlightedModel is not None
            ):
                self.currentHighlightedModel.unhighlightRow(self.currentHighlightedRow)

            # Highlight the new row
            self.selectAndShowRow(tab_index, row)

            # Update the current highlighted row, file path, and model
            self.currentHighlightedRow = row
            self.currentHighlightedFilePath = file_path
            self.currentHighlightedModel = model

    def selectAndShowRow(self, tab_index: int, row: int) -> None:
        """
        Selects a field by its row in the file table view and ensures it is visible to the user
        by adjusting scroll position based on the field's position in the list

        Parameters:
            tab_index (int): Index of the tab
            row (int): Row of the selected field.
        """
        tableview = self.tabWidget.widget(tab_index)
        model = tableview.tableView.model()
        model.setHighlightRow(row)
        rowCount = model.rowCount()
        scrollHint = QAbstractItemView.ScrollHint.EnsureVisible
        if row == 0:
            scrollHint = QAbstractItemView.ScrollHint.PositionAtTop
        elif row == rowCount - 1:
            scrollHint = QAbstractItemView.ScrollHint.PositionAtBottom
        # Get the QModelIndex for the specified row
        index = model.index(row, 0)
        tableview.tableView.scrollTo(index, scrollHint)

    # ------ Helper methods:

    def tabIndex2Path(self, index: int) -> Optional[str]:
        """
        Convert tab index to file path.
        
        Parameters:
            index (int): Tab index
            
        Returns:
            Optional[str]: File path or None if not found
        """
        if 0 <= index < self.tabWidget.count():
            tableview = self.tabWidget.widget(index)
            if hasattr(tableview, 'filePath'):
                return tableview.filePath.text()
        return None

    def tabPath2Index(self, file_path: str) -> Optional[int]:
        """
        Convert file path to tab index.
        
        Parameters:
            file_path (str): File path
            
        Returns:
            Optional[int]: Tab index or None if not found
        """
        for i in range(self.tabWidget.count()):
            tableview = self.tabWidget.widget(i)
            if hasattr(tableview, 'filePath') and tableview.filePath.text() == file_path:
                return i
        return None

    def displayMetadata(self, metadata: dict) -> None:
        """
        Display metadata in the visualization panel.
        
        Parameters:
            metadata (dict): Metadata to display
        """
        self.mda_mvc.mda_file_viz.displayMetadata(metadata)

    def displayData(self, tabledata: dict) -> None:
        """
        Display data in the visualization panel.
        
        Parameters:
            tabledata (dict): Data to display
        """
        self.mda_mvc.mda_file_viz.displayData(tabledata)

    def defaultSelection(self, first_pos: int, first_det: int, selection_field: dict) -> dict:
        """
        Determine default selection for fields.
        
        Parameters:
            first_pos (int): First positioner index
            first_det (int): First detector index
            selection_field (dict): Current selection field
            
        Returns:
            dict: Updated selection field
        """
        if not selection_field:
            selection_field = {"X": first_pos, "Y": [first_det], "I0": None}
        return selection_field


class TabManager(QObject):
    """
    Enhanced tab manager with performance optimizations.

    This class manages file tabs with improved memory management,
    lazy loading, and performance monitoring.
    """

    tabAdded = pyqtSignal(str)  # Signal emitting file path of added tab
    tabRemoved = pyqtSignal(str)  # Signal emitting file path of removed tab
    allTabsRemoved = pyqtSignal()  # Signal indicating all tabs have been removed

    def __init__(self, parent: MDAFile) -> None:
        """
        Initialize the enhanced tab manager.

        Parameters:
            parent (MDAFile): Parent MDA file manager
        """
        super().__init__(parent)
        self.mda_file = parent
        self._tab_cache: Dict[str, MDAFileTableView] = {}
        self._max_cached_tabs = 10  # Limit memory usage

    def addTab(self, file_path: str, metadata: dict, tabledata: dict) -> None:
        """
        Add a new tab with specified metadata and table data.

        Parameters:
            file_path (str): Path to the file
            metadata (dict): Metadata for the file
            tabledata (dict): Table data for the file
        """
        if file_path not in self._tab_cache:
            self._tab_cache[file_path] = {"metadata": metadata, "tabledata": tabledata}
            self.tabAdded.emit(file_path)

    def getTabData(self, file_path: str) -> Optional[dict]:
        """
        Returns the metadata & data for the tab associated with the given file path.

        Parameters:
            file_path (str): Path to the file

        Returns:
            Optional[dict]: Tab data or None if not found
        """
        return self._tab_cache.get(file_path)

    def tabs(self) -> dict:
        """
        Get all tabs data.

        Returns:
            dict: All tabs data
        """
        return self._tab_cache.copy()

    def removeTab(self, file_path: str) -> None:
        """
        Remove a tab and clean up resources.

        Parameters:
            file_path (str): Path to the file
        """
        try:
            if file_path in self._tab_cache:
                del self._tab_cache[file_path]

            self.tabRemoved.emit(file_path)

        except Exception as e:
            print(f"Error removing tab for {file_path}: {e}")

    def removeAllTabs(self) -> None:
        """
        Remove all tabs.
        """
        self._tab_cache.clear()
        self.allTabsRemoved.emit()

    def clearCache(self) -> None:
        """Clear all cached tabs."""
        for tab_view in self._tab_cache.values():
            if hasattr(tab_view, "cleanup"):
                tab_view.cleanup()
        self._tab_cache.clear()
