"""
Defines MainWindow class.

.. autosummary::

    ~MainWindow
"""

from pathlib import Path
from typing import List, Optional
from PyQt5 import QtWidgets, QtCore

from . import APP_TITLE
from .mda_folder import MDA_MVC
from . import utils
from .user_settings import settings
from .opendialog import DIR_SETTINGS_KEY
from .lazy_folder_scanner import LazyFolderScanner, FolderScanResult

UI_FILE = utils.getUiFileName(__file__)
MAX_FILES = 500
MAX_RECENT_DIRS = 10


class MainWindow(QtWidgets.QMainWindow):
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
            QtCore.Qt.Window
            | QtCore.Qt.WindowMinimizeButtonHint
            | QtCore.Qt.WindowMaximizeButtonHint
            | QtCore.Qt.WindowCloseButtonHint
        )

        # Additional macOS-specific properties for proper resizing
        self.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)
        self.setAttribute(QtCore.Qt.WA_MacNormalSize, True)

        # Ensure the window can be resized
        self.setMinimumSize(400, 300)
        self.resize(720, 400)  # More reasonable initial size

        # Ensure the window is resizable
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )

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

        settings.restoreWindowGeometry(self, "mainwindow_geometry")
        print("Settings are saved in:", settings.fileName())

        # Ensure the window size is reasonable (not too large)
        screen = QtWidgets.QDesktopWidget().screenGeometry()
        max_width = min(screen.width() * 0.8, 1200)  # Max 80% of screen width or 1200px
        max_height = min(
            screen.height() * 0.8, 800
        )  # Max 80% of screen height or 800px

        if self.width() > max_width or self.height() > max_height:
            self.resize(
                int(min(self.width(), max_width)), int(min(self.height(), max_height))
            )
        elif self.width() < 400 or self.height() < 300:
            self.resize(720, 400)  # Reasonable default size

        # Center the window on the screen
        self._center_window()

        # Auto-load the first valid folder from recent folders
        self._auto_load_first_folder()

    def connect(self):
        self.actionOpen.triggered.connect(self.doOpen)
        self.actionAbout.triggered.connect(self.doAboutDialog)
        self.actionPreferences.triggered.connect(self.doPreferences)
        self.actionExit.triggered.connect(self.doClose)
        utils.reconnect(self.open.released, self.doOpen)
        utils.reconnect(self.refresh.released, self.onRefresh)
        self.folder.currentTextChanged.connect(self.onFolderSelected)

        # Add auto-load toggle action to File menu
        self._setup_auto_load_menu()

        # Create tab widget and fit data components if they don't exist
        self._setup_fit_data_tab()

    def _setup_auto_load_menu(self):
        """Set up the auto-load toggle menu action."""
        # Create the auto-load toggle action
        self.actionToggleAutoLoad = QtWidgets.QAction("Toggle Auto-Load", self)
        self.actionToggleAutoLoad.setStatusTip(
            "Toggle automatic folder loading on startup"
        )
        self.actionToggleAutoLoad.setCheckable(True)
        self.actionToggleAutoLoad.setChecked(self.get_auto_load_setting())
        self.actionToggleAutoLoad.triggered.connect(self._on_toggle_auto_load)

        # Add to File menu
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionToggleAutoLoad)

    def _on_toggle_auto_load(self):
        """Handle auto-load toggle menu action."""
        new_setting = self.toggle_auto_load()
        self.actionToggleAutoLoad.setChecked(new_setting)

    @property
    def status(self):
        return self.statusbar.currentMessage()

    def setStatus(self, text, timeout=0):
        """Write new status to the main window and terminal output."""
        print(text)
        self.statusbar.showMessage(str(text), msecs=timeout)

    def doAboutDialog(self, *args, **kw):
        """
        Show the "About ..." dialog
        """
        from .aboutdialog import AboutDialog

        about = AboutDialog(self)
        about.open()

    def doPreferences(self, *args, **kw):
        """
        Show the Preferences dialog
        """
        from PyQt5.QtWidgets import (
            QDialog,
            QVBoxLayout,
            QHBoxLayout,
            QLabel,
            QSpinBox,
            QDialogButtonBox,
        )

        # Create preferences dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Preferences")
        dialog.setModal(True)
        dialog.resize(400, 200)

        layout = QVBoxLayout(dialog)

        # Plot height setting
        plot_layout = QHBoxLayout()
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
        plot_layout.addWidget(plot_label)
        plot_layout.addWidget(plot_spinbox)
        layout.addLayout(plot_layout)

        # Add some spacing
        layout.addStretch()

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        # Show dialog
        if dialog.exec_() == QDialog.Accepted:
            # Save the new plot height setting
            new_height = plot_spinbox.value()
            settings.setKey("plot_max_height", new_height)

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

            self.setStatus(f"Plot height setting updated to {new_height} pixels")

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
        settings.saveWindowGeometry(self, "mainwindow_geometry")
        self.close()

    def doOpen(self, *args, **kw):
        """
        User chose to open (connect with) a tiled server.
        """
        from .opendialog import OpenDialog

        self.setStatus("Please select a folder...")
        open_dialog = OpenDialog(self)
        dir_name = open_dialog.getExistingDirectory(self, "Select a Directory")
        if dir_name:
            folder_list = self.folderList()
            folder_list.insert(0, dir_name)
            self.setFolderList(folder_list)

    def doPopUp(self, message):
        """
        User chose to open (connect with) a tiled server.
        """
        from .popup import PopUp

        popup = PopUp(self, message)
        return popup.exec_() == QtWidgets.QDialog.Accepted

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
        if folder_name in [".", "", "Select a folder..."]:
            pass
        elif folder_name in ["Open..."]:
            self.doOpen()
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
                self.setStatus(f"\n{str(folder_path)!r} - Path does not exist.")

    def onRefresh(self):
        """
        Refreshes the file list in the currently selected folder
        - Re-fetch the list of MDA files in the current folder.
        - Display the updated file list in the MDA folder table view.
        """
        self.setStatus("Refreshing folder...")
        current_folder = self.dataPath()
        if current_folder:
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
        """Fill the Folder ComboBox; Open... and Clear Recently Open... are added at the end by default.

        Args:
            folder_list (list, optional): The list of folders to be displayed in the ComboBox. Defaults to [].
        """
        if folder_list is None:
            folder_list = []
        self.folder.clear()
        if not folder_list:
            folder_list = ["Select a folder..."]
        self.folder.addItems(folder_list)
        self.folder.addItems(["Open...", "Clear Recently Open..."])
        count = self.folder.count()
        self.folder.insertSeparator(count - 1)
        self.folder.insertSeparator(count - 2)

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
                self.info.setText(f"{len(sorted_files)} mda files")

                # Create or update the folder view
                layout = self.groupbox.layout()
                if self.mvc_folder is None:
                    self.mvc_folder = MDA_MVC(self)
                    layout.addWidget(self.mvc_folder)
                else:
                    # Always update the folder view since it is a new folder
                    self.mvc_folder.updateFolderView()

                self.setStatus(
                    f"Loaded {len(sorted_files)} MDA files from {folder_path}"
                )
            else:
                error_msg = "Could not determine folder path from scan results"
                self.info.setText("No mda files")
                self.doPopUp(error_msg)
                self.reset_mainwindow()
                self.setStatus(f"Scan failed: {error_msg}")
        else:
            error_msg = result.error_message or "No MDA files found"
            self.info.setText("No mda files")
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
                QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
            )

        # Ensure the main content area (groupbox) is resizable
        if hasattr(self, "groupbox"):
            self.groupbox.setSizePolicy(
                QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
            )

        # Ensure the tab widget is resizable
        if hasattr(self, "mainTabWidget"):
            self.mainTabWidget.setSizePolicy(
                QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
            )

        # Ensure the fit data tab is resizable
        if hasattr(self, "fitDataTab"):
            self.fitDataTab.setSizePolicy(
                QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
            )

        # Ensure the fit data text widget is resizable
        if hasattr(self, "fitDataText"):
            self.fitDataText.setSizePolicy(
                QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
            )

    def _auto_load_first_folder(self) -> None:
        """
        Auto-load the first valid folder from recent folders.

        This method attempts to automatically load the first folder from the recent
        folders list if it exists and is valid. This provides a better user experience
        by not requiring manual folder selection on startup.

        The auto-loading can be disabled by setting the 'auto_load_folder' setting to False.
        """
        # Check if auto-loading is enabled (default to True)
        auto_load_enabled = settings.getKey("auto_load_folder")
        if auto_load_enabled is None:
            # Default to True if not set
            auto_load_enabled = True
            settings.setKey("auto_load_folder", True)

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
        screen = QtWidgets.QDesktopWidget().screenGeometry()
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
