"""
Defines MainWindow class.

.. autosummary::

    ~MainWindow
"""

from pathlib import Path
from typing import Optional, List
from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QMainWindow, QSizePolicy, QApplication

# QAction import removed - no longer needed

from mdaviz import APP_TITLE
from mdaviz.mda_folder import MDA_MVC
from mdaviz import utils
from mdaviz.user_settings import settings
from mdaviz.opendialog import DIR_SETTINGS_KEY
from mdaviz.lazy_folder_scanner import LazyFolderScanner, FolderScanResult
from mdaviz.logger import get_logger

# Get logger for this module
logger = get_logger("mainwindow")

UI_FILE = utils.getUiFileName(__file__)
MAX_FILES = 500
MAX_RECENT_DIRS = 10


class MainWindow(QMainWindow):
    """The main window of the app, built in Qt designer.

    .. autosummary::

        ~connect
        ~status
        ~setStatus
        ~doAboutDialog
        ~closeEvent
        ~doClose
        ~doOpen
        ~reset_mainwindow
        ~dataPath
        ~setDataPath
        ~mdaFileList
        ~setMdaFileList
        ~mdaInfoList
        ~setMdaInfoList
        ~folderList
        ~setFolderList
        ~onFolderSelected
        ~onRefresh
        ~_buildFolderList
        ~_updateRecentFolders
    """

    def __init__(self):
        super().__init__()
        utils.myLoadUi(UI_FILE, baseinstance=self)
        self.setWindowTitle(APP_TITLE)

        # Set proper window flags for macOS resizing
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowMaximizeButtonHint
            | Qt.WindowType.WindowCloseButtonHint
        )

        # Additional macOS-specific properties for proper resizing
        self.setAttribute(Qt.WidgetAttribute.WA_MacShowFocusRect, False)
        self.setAttribute(Qt.WidgetAttribute.WA_MacNormalSize, True)

        # Ensure the window can be resized
        self.setMinimumSize(400, 300)
        self.resize(720, 400)  # More reasonable initial size

        # Ensure the window is resizable
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Ensure central widget and main content area are resizable
        self._setup_resizable_layout()

        # self.directory = directory
        self.mvc_folder = None
        self.setDataPath()  # the combined data path obj
        self.setFolderList()  # the list of recent folders in folder QComboBox
        self.setMdaFileList()  # the list of mda file NAME str (name only)
        self.setMdaInfoList()  # the list of mda file Info (all the data necessary to fill the table view)

        # Initialize lazy folder scanner
        self.lazy_scanner = LazyFolderScanner(
            batch_size=50, max_files=10000, use_lightweight_scan=True
        )
        self.lazy_scanner.scan_progress.connect(self._on_scan_progress)
        self.lazy_scanner.scan_complete.connect(self._on_scan_complete)
        self.lazy_scanner.scan_error.connect(self._on_scan_error)

        self.connect()

        # Restore window geometry from settings
        geometry_restored = settings.restoreWindowGeometry(self, "mainwindow_geometry")
        logger.info(f"Settings are saved in: {settings.fileName()}")

        # Calculate screen size constraints
        screen = QApplication.primaryScreen().geometry()
        max_width = screen.width() * 0.8  # Max 80% of screen width
        max_height = screen.height() * 0.8  # Max 80% of screen height

        # Only apply size constraints and centering if no geometry was previously saved
        if not geometry_restored:
            # Ensure the window size is reasonable (not too large)
            if self.width() > max_width or self.height() > max_height:
                self.resize(
                    int(min(self.width(), max_width)),
                    int(min(self.height(), max_height)),
                )
            elif self.width() < 400 or self.height() < 300:
                self.resize(720, 500)  # Reasonable default size

            # Center the window on the screen only if no geometry was restored
            self._center_window()
        else:
            # If geometry was restored, only apply size constraints if window is unreasonably large
            if self.width() > max_width or self.height() > max_height:
                self.resize(
                    int(min(self.width(), max_width)),
                    int(min(self.height(), max_height)),
                )

        # Auto-load the first valid folder from recent folders (delayed to preserve startup message)
        QTimer.singleShot(100, self._auto_load_first_folder)

    def connect(self):
        self.actionOpen.triggered.connect(self.doOpen)
        self.actionAbout.triggered.connect(self.doAboutDialog)
        self.actionPreferences.triggered.connect(self.doPreferences)
        self.actionExit.triggered.connect(self.doClose)
        utils.reconnect(self.open.released, self.doOpen)
        utils.reconnect(self.refresh.released, self.onRefresh)
        self.folder.currentTextChanged.connect(self.onFolderSelected)

        # Auto-load menu removed - now handled in preferences dialog

        # Create tab widget and fit data components if they don't exist
        self._setup_fit_data_tab()

    # Auto-load menu methods removed - now handled in preferences dialog

    @property
    def status(self):
        return self.statusbar.currentMessage()

    def setStatus(self, text, timeout=0):
        """Write new status to the main window and terminal output."""
        # Avoid logging duplicate consecutive messages
        if not hasattr(self, "_last_status") or self._last_status != text:
            logger.info(text)
            self._last_status = text
        self.statusbar.showMessage(str(text), msecs=timeout)

    def doAboutDialog(self, *args, **kw):
        """
        Show the "About ..." dialog
        """
        from mdaviz.aboutdialog import AboutDialog

        about = AboutDialog(self)
        about.open()

    def doPreferences(self, *args, **kw):
        """
        Show the Preferences dialog
        """
        from PyQt6.QtWidgets import (
            QDialog,
            QVBoxLayout,
            QLabel,
            QSpinBox,
            QDialogButtonBox,
            QCheckBox,
        )

        # Create preferences dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Preferences")
        dialog.setModal(True)
        dialog.resize(400, 200)

        layout = QVBoxLayout(dialog)

        # Auto-load setting (first)
        auto_load_checkbox = QCheckBox("Auto-load first folder on startup")
        auto_load_val = settings.getKey("auto_load_folder")
        if auto_load_val is None:
            auto_load_val = True
        elif isinstance(auto_load_val, str):
            auto_load_val = auto_load_val.lower() in ("true", "1", "yes", "on")
        auto_load_checkbox.setChecked(bool(auto_load_val))
        layout.addWidget(auto_load_checkbox)

        # Add some spacing
        layout.addStretch()

        # Plot height setting (second)
        plot_label = QLabel("Maximum Plot Height (pixels):")
        plot_spinbox = QSpinBox()
        plot_spinbox.setRange(200, 2000)
        plot_spinbox.setSingleStep(100)  # Change step size to 100 pixels
        plot_height_val = settings.getKey("plot_max_height")
        try:
            plot_height_val = int(plot_height_val)
        except (TypeError, ValueError):
            plot_height_val = 800
        plot_spinbox.setValue(plot_height_val)
        plot_spinbox.setSuffix(" px")
        layout.addWidget(plot_label)
        layout.addWidget(plot_spinbox)

        # Add helpful caption for plot height setting
        plot_caption = QLabel(
            "Use this setting if plot areas expand vertically unexpectedly due to UI bugs."
        )
        plot_caption.setWordWrap(True)
        plot_caption.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(plot_caption)

        # Add some spacing
        layout.addStretch()

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        # Show dialog
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Save the new plot height setting
            new_height = plot_spinbox.value()
            settings.setKey("plot_max_height", new_height)

            # Save the new auto-load setting
            new_auto_load = auto_load_checkbox.isChecked()
            settings.setKey("auto_load_folder", new_auto_load)

            # Update any existing ChartView widgets
            if hasattr(self, "mvc_folder") and self.mvc_folder:
                if (
                    hasattr(self.mvc_folder, "mda_file_viz")
                    and self.mvc_folder.mda_file_viz
                ):
                    if (
                        hasattr(self.mvc_folder.mda_file_viz, "chart_view")
                        and self.mvc_folder.mda_file_viz.chart_view
                    ):
                        self.mvc_folder.mda_file_viz.chart_view.setMaximumPlotHeight(
                            new_height
                        )

                    # Update tab widget max height to match
                    if hasattr(
                        self.mvc_folder.mda_file_viz, "_updateTabWidgetMaxHeight"
                    ):
                        self.mvc_folder.mda_file_viz._updateTabWidgetMaxHeight()

            self.setStatus(
                f"Settings updated: plot height {new_height}px, auto-load {'enabled' if new_auto_load else 'disabled'}"
            )

    def closeEvent(self, event):
        """
        User clicked the big [X] to quit.
        """
        self.doClose()
        event.accept()  # let the window close

    def doClose(self, *args, **kw):
        """
        User chose exit (or quit), or closeEvent() was called.
        """
        self.setStatus("Application quitting ...")

        # Cancel any ongoing scan operations
        if hasattr(self, "lazy_scanner"):
            self.lazy_scanner.cancel_scan()

        settings.saveWindowGeometry(self, "mainwindow_geometry")
        self.close()

    def doOpen(self, *args, **kw):
        """
        User chose to open a file or folder dialog.
        """
        from mdaviz.opendialog import OpenDialog
        from PyQt6.QtWidgets import QFileDialog

        self.setStatus("Please select a file...")
        open_dialog = OpenDialog(self)
        open_dialog.setWindowTitle("Select a File")

        # Use exec() to show the dialog and get the result
        if open_dialog.exec() == QFileDialog.DialogCode.Accepted:
            # Get the selected files
            selected_files = open_dialog.selectedFiles()
            if selected_files:
                selected_path = selected_files[0]
                if selected_path:
                    # Convert file selection to folder selection
                    path_obj = Path(selected_path)

                    if path_obj.is_file():
                        # If a file was selected, get its parent directory
                        folder_path = path_obj.parent
                        selected_file_name = path_obj.name
                        self.setStatus(
                            f"Selected file: {selected_file_name}, loading folder: {folder_path}"
                        )
                    else:
                        # If a directory was selected, use it directly
                        folder_path = path_obj
                        selected_file_name = None
                        self.setStatus(f"Selected folder: {folder_path}")

                    # Store the selected file name for highlighting
                    self._selected_file_name = selected_file_name

                    # Add to folder list and load
                    folder_list = self.folderList()
                    folder_list.insert(0, str(folder_path))
                    self.setFolderList(folder_list)

                    # Set the combobox selection to the new folder
                    self.folder.setCurrentText(str(folder_path))

    def doPopUp(self, message):
        """
        User chose to show a popup dialog with a message.
        """
        from mdaviz.popup import PopUp

        popup = PopUp(self, message)
        return popup.exec() == QtWidgets.QDialog.accepted

    def proceed(self):
        """Handle the logic when the user clicks 'OK'."""
        return True

    def cancel(self):
        """Handle the logic when the user clicks 'Cancel'."""
        return False

    def reset_mainwindow(self):
        self.setDataPath()
        self.setMdaInfoList()
        self.setMdaFileList()
        if self.mvc_folder is not None:
            self.mvc_folder.mda_folder_tableview.clearContents()

    def dataPath(self):
        """
        Full path object for the selected folder
        """
        return self._dataPath

    def setDataPath(self, path=None):
        self._dataPath = path

    def mdaFileList(self):
        """List of mda file (name only) in the selected folder."""
        return self._mdaFileList

    def setMdaFileList(self, mda_file_list=None):
        self._mdaFileList = mda_file_list if mda_file_list else []

    def mdaInfoList(self):
        return self._mdaInfoList

    def setMdaInfoList(self, infoList=None):
        self._mdaInfoList = infoList if infoList else []

    def folderList(self):
        return self._folderList

    def setFolderList(self, folder_list=None):
        """Set the folder path list & populating the folder QComboBox.

        - If folder_list is not None, it will remove its duplicates.
        - If folder_list is None, the call to buildFolderList will take care of building the list
          based on the recent list of folder saved in the app settings.

        Args:
            folder_list (list, optional): the current list of recent folders. Defaults to None.
        """
        if folder_list != "":
            folder_list = self._buildFolderList(folder_list)
        self._fillFolderBox(folder_list)
        self._folderList = folder_list

    def onFolderSelected(self, folder_name):
        """A folder was selected (from the open dialog or pull down menu)."""
        if folder_name in [".", "", "Select a folder...", "Please select a folder..."]:
            pass
        elif folder_name == "Clear Recently Open...":
            settings.setKey(DIR_SETTINGS_KEY, "")
            folder_list = [str(self.dataPath())] if self.dataPath() else []
            self.setFolderList(folder_list)
        else:
            folder_path = Path(folder_name)
            if folder_path.exists() and folder_path.is_dir():  # folder exists
                # Use lazy folder scanner for better performance
                self.setStatus(f"Scanning folder: {folder_name}")
                self.lazy_scanner.scan_folder_async(folder_path)
            else:
                self.reset_mainwindow()
                self.setStatus(f"{folder_name} does not exist or is not a directory")

    def onRefresh(self):
        """
        Refreshes the file list in the currently selected folder
        - Re-fetch the list of MDA files in the current folder.
        - Display the updated file list in the MDA folder table view.
        - Invalidate cache for files in the current folder to ensure fresh data.
        - Preserve the currently selected file after refresh.
        """
        self.setStatus("Refreshing folder...")
        current_folder = self.dataPath()
        if current_folder:
            # Preserve the currently selected file
            selected_file_name = None
            if (
                self.mvc_folder
                and hasattr(self.mvc_folder, "mda_folder_tableview")
                and self.mvc_folder.selectionModel()
            ):
                current_index = self.mvc_folder.selectionModel().currentIndex()
                if current_index.isValid():
                    current_file_list = self.mdaFileList()
                    if current_index.row() < len(current_file_list):
                        selected_file_name = current_file_list[current_index.row()]
                        self._selected_file_name = selected_file_name

            # Invalidate cache for all files in the current folder
            from mdaviz.data_cache import get_global_cache

            cache = get_global_cache()
            invalidated_count = cache.invalidate_folder(str(current_folder))
            if invalidated_count > 0:
                self.setStatus(f"Invalidated cache for {invalidated_count} files")

            current_mdaFileList = self.mdaFileList()
            self.onFolderSelected(current_folder)
            new_mdaFileList = self.mdaFileList()
            if new_mdaFileList:
                difference = [
                    item for item in new_mdaFileList if item not in current_mdaFileList
                ]
                if difference:
                    self.setStatus(f"Loading new files: {difference}")
                else:
                    self.setStatus("No new files.")
        else:
            self.setStatus("Nothing to update.")

    def _buildFolderList(self, folder_list=None):
        """Build the list of recent folders and remove duplicates from the folder list.

        - If folder_list arg is not None (after a doOpen call), it just removes duplicates.
        - If folder_list arg is None, it grabs the list of recent folder from the app settings.
          The directory loaded at start-up will be added at index 0.

        Args:
            folder_list (list, optional): a list folders. Defaults to None.

        Returns:
            list: list of folders to be populated in the QComboBox
        """
        unique_paths = set()
        candidate_paths = []
        if not folder_list:
            recent_dirs = self._getRecentFolders()
            if recent_dirs:
                candidate_paths.extend([d for d in recent_dirs if d and d != "."])
        else:
            candidate_paths.extend([d for d in folder_list if d and d != "."])
        new_path_list = [
            p
            for p in candidate_paths
            if p not in unique_paths and (unique_paths.add(p) or True)
        ]
        return new_path_list

    def _getRecentFolders(self) -> List[str]:
        recent_dirs = (
            settings.getKey(DIR_SETTINGS_KEY).split(",")
            if settings.getKey(DIR_SETTINGS_KEY)
            else []
        )
        return recent_dirs

    def _addToRecentFolders(self, folder_path: str) -> None:
        """Add a new folder path to the list of recent folders in the app settings.

        Args:
            folder_path (str): The path of the folder to be added.
        """
        recent_dirs = self._getRecentFolders()
        if folder_path in recent_dirs:
            recent_dirs.remove(folder_path)
        recent_dirs.insert(0, str(folder_path))
        recent_dirs = [dir for dir in recent_dirs if dir != "."]
        settings.setKey(DIR_SETTINGS_KEY, ",".join(recent_dirs[:MAX_RECENT_DIRS]))

    def _fillFolderBox(self, folder_list: Optional[List[str]] = None) -> None:
        """Fill the Folder ComboBox; Clear Recently Open... is added at the end by default.

        Args:
            folder_list (list, optional): The list of folders to be displayed in the ComboBox. Defaults to [].
        """
        if folder_list is None:
            folder_list = []
        self.folder.clear()  # type: ignore[attr-defined]

        # If no folders and auto-load is disabled, show "Please select a folder..."
        if not folder_list and not self.get_auto_load_setting():
            folder_list = ["Please select a folder..."]
        else:
            # If we have folders and auto-load is disabled, add "Please select a folder..." at the beginning
            if not self.get_auto_load_setting():
                folder_list = ["Please select a folder..."] + folder_list

        self.folder.addItems(folder_list)  # type: ignore[attr-defined]
        self.folder.addItems(["Clear Recently Open..."])  # type: ignore[attr-defined]
        count = self.folder.count()  # type: ignore[attr-defined]
        self.folder.insertSeparator(count - 1)  # type: ignore[attr-defined]

    def _on_scan_progress(self, current: int, total: int) -> None:
        """Handle scan progress updates."""
        progress_percent = (current / total * 100) if total > 0 else 0
        self.setStatus(f"Scanning files: {current}/{total} ({progress_percent:.1f}%)")

    def _on_scan_complete(self, result: FolderScanResult) -> None:
        """Handle scan completion."""
        if result.is_complete and result.file_list:
            # Sort the file list
            sorted_files = sorted(result.file_list)
            sorted_info = sorted(result.file_info_list, key=lambda x: x["Name"])

            # Set the data - extract folder path from the first file
            if sorted_info and "folderPath" in sorted_info[0]:
                folder_path = Path(sorted_info[0]["folderPath"])
            else:
                # Fallback: construct folder path from file path
                folder_path = Path(sorted_files[0]).parent if sorted_files else None  # type: ignore[assignment]

            if folder_path is not None:
                self.setDataPath(folder_path)
                self.setMdaInfoList(sorted_info)
                self.setMdaFileList(sorted_files)
                self._addToRecentFolders(str(folder_path))
                self.info.setText(f"{len(sorted_files)} mda files")  # type: ignore[attr-defined]

                # Create or update the folder view
                layout = self.groupbox.layout()  # type: ignore[attr-defined]
                if self.mvc_folder is None:
                    self.mvc_folder = MDA_MVC(self)
                    layout.addWidget(self.mvc_folder)
                else:
                    # Always update the folder view since it is a new folder
                    self.mvc_folder.updateFolderView()

                # Highlight the selected file if one was specified, otherwise select the first file
                if hasattr(self, "_selected_file_name") and self._selected_file_name:
                    try:
                        # Find the index of the selected file
                        selected_index = sorted_files.index(self._selected_file_name)
                        # Select and highlight the file in the folder view
                        if self.mvc_folder and hasattr(
                            self.mvc_folder, "mda_folder_tableview"
                        ):
                            model = (
                                self.mvc_folder.mda_folder_tableview.tableView.model()
                            )
                            if model and selected_index < model.rowCount():
                                index = model.index(selected_index, 0)
                                self.mvc_folder.selectAndShowIndex(index)
                                self.setStatus(
                                    f"Highlighted selected file: {self._selected_file_name}"
                                )
                    except ValueError:
                        # File not found in the list, ignore
                        pass
                    finally:
                        # Clear the selected file name
                        self._selected_file_name = None
                else:
                    # Auto-select the first file if no specific file was selected
                    if self.mvc_folder and hasattr(
                        self.mvc_folder, "mda_folder_tableview"
                    ):
                        model = self.mvc_folder.mda_folder_tableview.tableView.model()
                        if model and model.rowCount() > 0:
                            first_index = model.index(0, 0)
                            self.mvc_folder.selectAndShowIndex(first_index)
                            self.setStatus(
                                f"Auto-selected first file: {sorted_files[0]}"
                            )

                self.setStatus(
                    f"Loaded {len(sorted_files)} MDA files from {folder_path}"
                )
            else:
                error_msg = "Could not determine folder path from scan results"
                self.info.setText("No mda files")  # type: ignore[attr-defined]
                self.doPopUp(error_msg)
                self.reset_mainwindow()
                self.setStatus(f"Scan failed: {error_msg}")
        else:
            error_msg = result.error_message or "No MDA files found"
            self.info.setText("No mda files")  # type: ignore[attr-defined]
            self.doPopUp(error_msg)
            self.reset_mainwindow()
            self.setStatus(f"Scan failed: {error_msg}")

    def _on_scan_error(self, error_message: str) -> None:
        """Handle scan errors."""
        self.reset_mainwindow()
        self.setStatus(f"Scan error: {error_message}")
        self.doPopUp(f"Error scanning folder: {error_message}")

    def _setup_resizable_layout(self) -> None:
        """Set up proper size policies for resizable layout."""
        # Ensure central widget is resizable
        if hasattr(self, "centralwidget"):
            self.centralwidget.setSizePolicy(
                QtWidgets.QSizePolicy.Policy.Expanding,
                QtWidgets.QSizePolicy.Policy.Expanding,
            )

        # Ensure the main content area (groupbox) is resizable
        if hasattr(self, "groupbox"):
            self.groupbox.setSizePolicy(
                QtWidgets.QSizePolicy.Policy.Expanding,
                QtWidgets.QSizePolicy.Policy.Expanding,
            )

        # Ensure the tab widget is resizable
        if hasattr(self, "mainTabWidget"):
            self.mainTabWidget.setSizePolicy(
                QtWidgets.QSizePolicy.Policy.Expanding,
                QtWidgets.QSizePolicy.Policy.Expanding,
            )

        # Ensure the fit data tab is resizable
        if hasattr(self, "fitDataTab"):
            self.fitDataTab.setSizePolicy(
                QtWidgets.QSizePolicy.Policy.Expanding,
                QtWidgets.QSizePolicy.Policy.Expanding,
            )

        # Ensure the fit data text widget is resizable
        if hasattr(self, "fitDataText"):
            self.fitDataText.setSizePolicy(
                QtWidgets.QSizePolicy.Policy.Expanding,
                QtWidgets.QSizePolicy.Policy.Expanding,
            )

    def _auto_load_first_folder(self) -> None:
        """
        Auto-load the first valid folder from recent folders.

        This method attempts to automatically load the first folder from the recent
        folders list if it exists and is valid. This provides a better user experience
        by not requiring manual folder selection on startup.

        The auto-loading can be disabled by setting the 'auto_load_folder' setting to False.
        """
        # Check if auto-loading is enabled using the proper boolean conversion
        auto_load_enabled = self.get_auto_load_setting()

        if not auto_load_enabled:
            self.setStatus("Auto-loading disabled by user preference")
            return

        recent_dirs = self._getRecentFolders()
        if recent_dirs:
            first_folder = recent_dirs[0]
            if first_folder and first_folder.strip():
                folder_path = Path(first_folder.strip())
                if folder_path.exists() and folder_path.is_dir():
                    self.setStatus(f"Auto-loading folder: {first_folder}")
                    # Use lazy folder scanner for better performance
                    self.lazy_scanner.scan_folder_async(folder_path)
                else:
                    self.setStatus(
                        f"Auto-load failed: {first_folder} does not exist or is not a directory"
                    )
            else:
                self.setStatus("No valid recent folders to auto-load")
        else:
            self.setStatus("No recent folders available for auto-loading")

    def toggle_auto_load(self) -> bool:
        """
        Toggle the auto-load folder setting.

        Returns:
            bool: The new state of the auto-load setting (True if enabled, False if disabled)
        """
        current_setting = settings.getKey("auto_load_folder")
        if current_setting is None:
            current_setting = True

        new_setting = not current_setting
        settings.setKey("auto_load_folder", new_setting)

        status_text = "Auto-loading enabled" if new_setting else "Auto-loading disabled"
        self.setStatus(status_text)

        return new_setting

    def get_auto_load_setting(self) -> bool:
        """
        Get the current auto-load folder setting.

        Returns:
            bool: True if auto-loading is enabled, False if disabled
        """
        setting = settings.getKey("auto_load_folder")
        if setting is None:
            # Default to True if not set
            setting = True
            settings.setKey("auto_load_folder", True)
        elif isinstance(setting, str):
            # Convert string to boolean
            setting = setting.lower() in ("true", "1", "yes", "on")
        return bool(setting)

    def _center_window(self):
        """Center the window on the screen."""
        screen = QtWidgets.QApplication.primaryScreen().geometry()
        window_geometry = self.geometry()
        x = (screen.width() - window_geometry.width()) // 2
        y = (screen.height() - window_geometry.height()) // 2
        self.move(x, y)

    def showFitDataTab(self):
        """Show the fit data tab and switch to it."""
        self.mainTabWidget.setTabVisible(0, True)  # Show fit data tab
        self.mainTabWidget.setCurrentIndex(0)  # Switch to fit data tab

    def updateFitData(self, fit_data: str):
        """
        Update the fit data tab with new fit information.

        Parameters:
        - fit_data: String containing formatted fit data to display
        """
        self.fitDataText.setPlainText(fit_data)
        self.fitDataLabel.setText("Fit Data Available")
        self.showFitDataTab()

    def connectToFitSignals(self, chart_view):
        """
        Connect to fit signals from a chart view.

        Parameters:
        - chart_view: ChartView instance that emits fit signals
        """
        if hasattr(chart_view, "fitAdded"):
            chart_view.fitAdded.connect(self._on_fit_added)
        if hasattr(chart_view, "fitUpdated"):
            chart_view.fitUpdated.connect(self._on_fit_updated)

    def _on_fit_added(self, curve_id: str, fit_id: str):
        """Handle when a new fit is added."""
        if hasattr(self, "mvc_folder") and self.mvc_folder:
            # Get fit data from the fit manager
            fit_manager = getattr(self.mvc_folder, "fit_manager", None)
            if fit_manager:
                fit_data = fit_manager.getFitData(curve_id)
                if fit_data:
                    self._display_fit_data(fit_data, curve_id)

    def _on_fit_updated(self, curve_id: str, fit_id: str):
        """Handle when a fit is updated."""
        self._on_fit_added(curve_id, fit_id)

    def _display_fit_data(self, fit_data, curve_id: str):
        """Display fit data in the fit data tab."""
        try:
            # Format the fit data for display
            formatted_data = f"Curve ID: {curve_id}\n"
            formatted_data += f"Model: {fit_data.model_name}\n"
            formatted_data += f"Fit Range: {fit_data.x_range}\n\n"

            # Add fit parameters
            if fit_data.fit_result and hasattr(fit_data.fit_result, "parameters"):
                formatted_data += "Parameters:\n"
                for param, value in fit_data.fit_result.parameters.items():
                    formatted_data += f"  {param}: {value:.6f}\n"

            # Add fit quality metrics if available
            if fit_data.fit_result and hasattr(fit_data.fit_result, "quality_metrics"):
                formatted_data += "\nQuality Metrics:\n"
                for metric, value in fit_data.fit_result.quality_metrics.items():
                    formatted_data += f"  {metric}: {value:.6f}\n"

            self.updateFitData(formatted_data)

        except Exception as e:
            error_msg = f"Error displaying fit data: {str(e)}"
            self.updateFitData(error_msg)

    def _setup_fit_data_tab(self):
        """Set up the fit data tab widget and components."""
        # Check if mainTabWidget exists, if not create it
        if not hasattr(self, "mainTabWidget"):
            # Create a tab widget and add it to the groupbox layout
            self.mainTabWidget = QtWidgets.QTabWidget()

            # Create fit data tab
            self.fitDataTab = QtWidgets.QWidget()
            fit_layout = QtWidgets.QVBoxLayout(self.fitDataTab)

            # Create fit data label
            self.fitDataLabel = QtWidgets.QLabel("No Fit Data Available")
            fit_layout.addWidget(self.fitDataLabel)

            # Create fit data text widget
            self.fitDataText = QtWidgets.QTextEdit()
            self.fitDataText.setReadOnly(True)
            fit_layout.addWidget(self.fitDataText)

            # Add fit data tab to main tab widget
            self.mainTabWidget.addTab(self.fitDataTab, "Fit Data")

            # Add the tab widget to the groupbox layout
            if hasattr(self, "groupbox") and self.groupbox.layout():
                self.groupbox.layout().addWidget(self.mainTabWidget)

            # Initially hide the fit data tab until a fit is performed
            self.mainTabWidget.setTabVisible(0, False)
        else:
            # If mainTabWidget exists, ensure fit data components exist
            if not hasattr(self, "fitDataTab"):
                self.fitDataTab = QtWidgets.QWidget()
                fit_layout = QtWidgets.QVBoxLayout(self.fitDataTab)
                self.fitDataLabel = QtWidgets.QLabel("No Fit Data Available")
                fit_layout.addWidget(self.fitDataLabel)
                self.fitDataText = QtWidgets.QTextEdit()
                self.fitDataText.setReadOnly(True)
                fit_layout.addWidget(self.fitDataText)
                self.mainTabWidget.addTab(self.fitDataTab, "Fit Data")

            # Initially hide the fit data tab until a fit is performed
            self.mainTabWidget.setTabVisible(0, False)
