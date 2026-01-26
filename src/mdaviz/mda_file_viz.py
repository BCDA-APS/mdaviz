"""
MDA File Visualization Module

.. Summary::
    This module provides the main visualization interface for MDA (Multi-dimensional Array)
    data files. It manages the display of data tables, metadata, 1D plots, and 2D plots in a
    tabbed interface with integrated controls for data analysis and manipulation.

Classes:
    MDAFileVisualization: Main widget for displaying MDA file contents with tabbed interface
    MetadataSearchDialog: Dialog for searching within metadata text

Key Features:
    - Tabbed interface for Data, Plot, Metadata, and 2D visualization
    - Integrated 1D and 2D plotting with ChartView and ChartView2D
    - Interactive controls for curve fitting, styling, and log scales
    - Metadata search functionality
    - Dynamic tab visibility based on data dimensionality
    - Persistent UI state management

Dependencies:
    - PyQt6: GUI framework
    - mdaviz.chartview: 1D and 2D plotting widgets
    - mdaviz.data_table_view: Data table display
    - mdaviz.fit_models: Curve fitting functionality
    - mdaviz.utils: Utility functions for UI loading

Usage:
    The MDAFileVisualization widget is typically instantiated as part of the main
    application window and receives MDA file data through:
    - setTableData(): Sets the data table content from MDA file
    - setMetadata(): Sets the metadata text content
    - setPlot(): Sets the 1D plotting widget (ChartView) with data from user selections
    - set2DData(): Sets 2D data for multi-dimensional arrays
    - update2DPlot(): Updates 2D plots based on user selections in 2D controls
"""

from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtGui import QFont, QKeySequence
from PyQt6.QtWidgets import QWidget, QDialog, QSizePolicy
from PyQt6.QtGui import QShortcut

from mdaviz import utils
from mdaviz.chartview import ChartView
from mdaviz.data_table_view import DataTableView
from mdaviz.fit_models import get_available_models
from mdaviz.chartview import ChartView2D
from mdaviz.logger import get_logger

# Get logger for this module
logger = get_logger("mda_file_viz")

MD_FONT = "Arial"
MD_FONT_SIZE = 12


class MDAFileVisualization(QWidget):
    """The panel to show the contents of a file."""

    # UI file name matches this module, different extension
    ui_file = utils.getUiFileName(__file__)

    def __init__(self, parent):
        """
        Initialize the MDA file visualization widget.

        Parameters:
        - parent: Parent widget
        """
        super().__init__(parent)
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()

        # Initialize log scale state storage
        self._log_x_state = False
        self._log_y_state = False

        # Initialize control update state
        self._last_control_update = None
        self._last_control_update_value = None
        self._control_update_delay = 100  # milliseconds

    def setup(self):
        """Setup the UI components and connections."""
        font = QFont(MD_FONT)
        font.setPointSize(MD_FONT_SIZE)
        self.metadata.setFont(font)

        # Set size policy for the main visualization widget to prevent unwanted expansion
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Set size policy for the plot page to prevent vertical expansion
        self.plotPageMpl.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        # Set size policy for the tab widget to prevent vertical expansion
        self.tabWidget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )

        # Get maximum height from user settings with default fallback
        from mdaviz.user_settings import settings

        max_height = settings.getKey("plot_max_height")
        try:
            max_height = int(max_height)
        except (TypeError, ValueError):
            max_height = 800  # Default value

        # Set maximum height for the tab widget to prevent vertical growth
        self.tabWidget.setMaximumHeight(
            max_height + 100
        )  # Add some padding for tab headers

        # Setup fit functionality
        self.setupFitUI()

        # Setup log scale controls
        self.setupLogScaleUI()

        # Setup curve style functionality
        self.setupCurveStyleUI()

        # Setup search functionality for metadata
        self.setupSearchFunctionality()

        # Setup 2D functionality
        self.setup2DFunctionality()

    def setup2DFunctionality(self):
        """Setup 2D plotting functionality."""
        # Initially hide 2D tab
        self.update2DTabVisibility(False)
        # Connect mda_file_viz tab change signal (1D, data, 2D...)
        self.tabWidget.currentChanged.connect(self.onTabChanged)

        # Connect to file tab changes to update 2D plot when switching files
        # Use a timer to delay connection until widget is fully initialized
        from PyQt6.QtCore import QTimer

        QTimer.singleShot(100, self.connectToFileTabChanges)

    def connectToFileTabChanges(self):
        """Connect to file tab changes to update 2D plot when needed."""
        try:
            parent = self.parent()  # MDA_MVC
            while parent and not hasattr(parent, "mda_file"):
                parent = parent.parent()
            if parent and hasattr(parent, "mda_file"):
                # Connect to the tabChanged signal from MDAFile
                parent.mda_file.tabChanged.connect(self.onFileTabChanged)
                logger.debug("Connected to file tab changes")
            else:
                logger.warning("Could not find MDA_MVC with mda_file")
        except Exception as e:
            logger.error(f"Error connecting to file tab changes: {e}")

    def onFileTabChanged(self, tab_index, file_path, file_data, selection_field):
        """
        Handle file tab changes and update 2D plot if on 2D tab.

        Parameters:
            tab_index (int): Index of the newly selected file tab
            file_path (str): Path of the file associated with the new tab
            file_data (dict): Contains metadata and table data for the file
            selection_field (dict): Specifies the fields (POS/DET) selected for plotting
        """
        logger.debug(f"File tab changed to {file_path}")

        # Update 2D tab visibility based on the active file's data
        current_tableview = self.getCurrentFileTableview()
        if (
            current_tableview
            and current_tableview.mda_file
            and current_tableview.mda_file.data()
        ):
            active_file_data = current_tableview.mda_file.data()
            is_2d_data = active_file_data.get("isMultidimensional", False)
            logger.debug(f"Active file data isMultidimensional: {is_2d_data}")
            self.update2DTabVisibility(is_2d_data)
        else:
            logger.debug("No current tableview or file data available")
            self.update2DTabVisibility(False)

        # Always update control visibility to ensure correct controls are shown
        current_tab_index = self.tabWidget.currentIndex()
        logger.debug(f"Current viz tab index: {current_tab_index}")
        self.updateControlVisibility(current_tab_index)

        # Update 2D plot if we're currently on the 2D tab
        if current_tab_index == 3:  # 2D tab
            logger.debug("On 2D tab, updating 2D plot")
            self.update2DPlot()

    def update2DTabVisibility(self, show_2d_tab=False):
        """
        Update 2D tab visibility based on data dimensions.

        Parameters:
            show_2d_tab (bool): Whether to show the 2D tab
        """
        # Find the 2D tab index (should be index 3 after Metadata tab)
        tab_count = self.tabWidget.count()
        if tab_count < 4 and not show_2d_tab:
            # Do nothing - tab doesn't exist and we don't want to show it
            pass
        elif tab_count < 4 and show_2d_tab:
            # The 2D tab should exist but might be hidden
            # Try to show it anyway - the tab should be at index 3
            self.tabWidget.setTabVisible(3, show_2d_tab)
            # Update the 2D plot to populate the tab
            self.update2DPlot()
        else:
            # tab_count >= 4, just show/hide as needed
            self.tabWidget.setTabVisible(3, show_2d_tab)

            # If hiding 2D tab and it's currently selected, switch to 1D tab
            if not show_2d_tab and self.tabWidget.currentIndex() == 3:
                self.tabWidget.setCurrentIndex(0)

    def set2DData(self, data):
        """
        Set 2D data for visualization and manage 2D tab visibility.

        Switches to the 1D plot tab (index 0) when called. If data is multidimensional,
        shows the 2D tab and stores the data; otherwise hides the 2D tab and clears stored data.

        Parameters:
            data (dict or None): 2D data dictionary with scanDict2D and metadata, or None to clear
        """
        # Force switch to 1D tab when switching files (for both 2D and 1D files)
        self.tabWidget.setCurrentIndex(0)

        if not data or not data.get("isMultidimensional", False):
            self.update2DTabVisibility(False)
            # Clear 2D data
            if hasattr(self, "_2d_data"):
                delattr(self, "_2d_data")
            return

        # Show 2D tab for multidimensional data
        self.update2DTabVisibility(True)

        # Store 2D data for plotting
        self._2d_data = data

        # Update 2D plot if tab is visible
        if self.tabWidget.currentIndex() == 3:  # 2D tab
            self.update2DPlot()

    def update2DPlot(self):
        """Update the 2D plot with current data."""
        if not hasattr(self, "_2d_data") or not self._2d_data:
            return

        # Get the current table view by traversing up the parent chain to find MDA_MVC
        parent = self.parent()
        while parent and not hasattr(parent, "currentFileTableview"):
            parent = parent.parent()

        if not parent:
            return

        tableview = parent.currentFileTableview()
        if not tableview:
            return

        # Get 2D selections from comboboxes instead of 1D selections from table view
        if hasattr(tableview, "get2DSelections"):
            selection = tableview.get2DSelections()
        else:
            logger.warning("No get2DSelections method available")
            return

        # Convert 2D selection to 1D format for data2Plot2D
        # data2Plot2D expects: {'X': x_index, 'Y': [y_indices], 'I0': i0_index}
        # i.e X1 -> X; could refactor but it is too risky for a small gain
        converted_selection = {
            "X": selection.get("X1"),
            "X2": selection.get("X2"),
            "Y": selection.get("Y", []),
            "I0": selection.get("I0"),
            "log_y": selection.get("log_y", False),
        }
        logger.debug(f"Converted to 1D format: {converted_selection}")

        # Call our data2Plot2D function to extract 2D data
        datasets, plot_options = tableview.data2Plot2D(converted_selection)

        # Create and display 2D plot if we have data
        if datasets:
            logger.debug("Creating 2D plot")

            # Get the 2D plot widget from the 2D tab layout
            layoutMpl2D = self.plotPage2D.layout()
            if layoutMpl2D.count() != 1:
                return

            widgetMpl2D = layoutMpl2D.itemAt(0).widget()

            # Create ChartView2D if needed
            if not isinstance(widgetMpl2D, ChartView2D):
                logger.debug("Creating new ChartView2D widget for 2D tab")

                # Remove the existing widget from the layout
                layoutMpl2D.removeWidget(widgetMpl2D)
                widgetMpl2D.deleteLater()

                # Create new ChartView2D widget with correct parent (MDA_MVC)
                widgetMpl2D = ChartView2D(
                    parent, **plot_options
                )  # Use parent (MDA_MVC) as parent

                # Make the widget visible
                widgetMpl2D.setVisible(True)
                logger.debug(f"Set 2D widget visible: {widgetMpl2D.isVisible()}")

                # Add the widget to the 2D layout
                layoutMpl2D.addWidget(widgetMpl2D)
                logger.debug("Added ChartView2D to 2D layout")

            # Apply 2D log scale state from current selections (for both new and existing widgets)
            log_y = selection.get("log_y", False)
            widgetMpl2D.setLogScales2D(log_y)
            logger.debug(f"Applied log scale: {log_y}")

            # Plot the 2D data; datasets is a list with 1 element (only 1 det selected)
            for dataset in datasets:
                y_data, dataset_options = dataset
                x_data = dataset_options.get("x_data")
                x2_data = dataset_options.get("x2_data")

                if x_data is not None and x2_data is not None:
                    logger.debug("Plotting 2D data in 2D tab")

                    # Set the plot type from current selections
                    plot_type = selection.get("plot_type", "heatmap")
                    widgetMpl2D.set_plot_type(plot_type)
                    logger.debug(f"Set plot type to: {plot_type}")

                    # Add color palette to plot options
                    color_palette = selection.get("color_palette", "viridis")

                    # Validate color palette - ensure it's not empty
                    if not color_palette or color_palette.strip() == "":
                        color_palette = "viridis"
                        logger.debug(
                            f"Empty color palette, using default: {color_palette}"
                        )

                    plot_options["color_palette"] = color_palette
                    logger.debug(f"Set color palette to: {color_palette}")

                    widgetMpl2D.plot2D(y_data, x_data, x2_data, plot_options)
                else:
                    logger.warning("Missing X or X2 data for 2D plotting")

            # Store reference to 2D chart view
            self.chart_view_2d = widgetMpl2D

        else:
            logger.debug("No 2D datasets extracted, showing message")

            # Show "Nothing to plot" message when no datasets are available
            # This happens when validation fails (e.g., only 1 point for X2)
            layoutMpl2D = self.plotPage2D.layout()
            if layoutMpl2D.count() != 1:
                logger.warning("Expected exactly one widget in 2D layout")
                return

            widgetMpl2D = layoutMpl2D.itemAt(0).widget()

            # Use the showMessage method if the widget supports it
            if hasattr(widgetMpl2D, "showMessage"):
                widgetMpl2D.showMessage("Nothing to plot")
                self.chart_view_2d = widgetMpl2D
            else:
                # Create a simple message widget if needed
                # Remove the existing widget from the layout
                layoutMpl2D.removeWidget(widgetMpl2D)
                widgetMpl2D.deleteLater()

                # Create a simple QLabel widget to show the message
                from PyQt6.QtWidgets import QLabel
                from PyQt6.QtCore import Qt

                message_widget = QLabel("Nothing to plot")
                message_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
                message_widget.setStyleSheet(
                    """
                    QLabel {
                        font-size: 16px;
                        color: #666666;
                        background-color: #f5f5f5;
                        border: 1px solid #cccccc;
                        border-radius: 5px;
                        padding: 20px;
                    }
                """
                )

                # Add the message widget to the 2D layout
                layoutMpl2D.addWidget(message_widget)

                # Store reference to message widget
                self.chart_view_2d = message_widget

    def onTabChanged(self, index):
        """
        Handle tab changes.

        Parameters:
            index (int): Index of the newly selected tab
        """
        logger.debug(f"Tab changed to index: {index}")

        # Get current tab structure
        tab_count = self.tabWidget.count()
        is_2d_visible = tab_count >= 4 and self.tabWidget.isTabVisible(3)

        # Handle control visibility based on tab
        self.updateControlVisibility(index)

        # Handle 2D plotting
        if is_2d_visible and index == 3:  # 2D tab
            logger.debug("Switching to 2D tab, calling update2DPlot")
            self.update2DPlot()
        elif index == 0:  # 1D tab
            logger.debug("Switching to 1D tab")
            # Update 1D plot if needed
            pass

        # Handle search functionality
        # Enable search only when metadata tab is active
        # Tab indices: 0=1D, 1=Data, 2=Metadata, 3=2D(if visible)
        # Metadata is always at index 2
        is_metadata_tab = index == 2

        if hasattr(self, "search_shortcut"):
            self.search_shortcut.setEnabled(is_metadata_tab)

        # Close search dialog if switching away from metadata tab
        if (
            hasattr(self, "search_dialog")
            and not is_metadata_tab
            and self.search_dialog
            and self.search_dialog.isVisible()
        ):
            self.search_dialog.close()

    def updateControlVisibility(self, tab_index):
        """
        Update control visibility based on the selected tab (1D vs 2D).

        Parameters:
            tab_index (int): Index of the selected tab
        """
        # Get the current file table view
        current_tableview = self.getCurrentFileTableview()
        if not current_tableview:
            logger.debug("updateControlVisibility No current tableview found")
            return

        # Tab indices: 0=1D, 1=Data, 2=Metadata, 3=2D(if visible)
        if tab_index == 0:  # 1D tab
            # Show table view, hide Y DET controls
            current_tableview.tableView.setVisible(True)
            current_tableview.yDetControls.setVisible(False)

            # Only show X2 controls if the active tab contains 2D data
            if current_tableview.mda_file.data():
                active_file_data = current_tableview.mda_file.data()
                is_2d_data = active_file_data.get("isMultidimensional", False)
                current_tableview.dimensionControls.setVisible(is_2d_data)
            else:
                current_tableview.dimensionControls.setVisible(False)

            # Show mode controls and clear button
            self.showModeControls(True)

            # Show analysis controls (curves, graphInfo, cursorInfo)
            self.showAnalysisControls(True)
        elif tab_index == 3:  # 2D tab
            # Hide table view and X2 controls, show Y DET controls
            current_tableview.tableView.setVisible(False)
            current_tableview.dimensionControls.setVisible(False)
            current_tableview.yDetControls.setVisible(True)

            # Hide mode controls and clear button
            self.showModeControls(False)

            # Hide analysis controls: curve box, graphInfo, cursorInfo
            self.showAnalysisControls(False)

    def showModeControls(self, show: bool):
        """Show or hide mode controls (autoBox, clearButton, etc.)."""
        try:
            # Try to find MDA_MVC first
            parent = self.parent()
            while parent and not hasattr(parent, "mda_file"):
                parent = parent.parent()

            if parent and hasattr(parent, "mda_file"):
                # Found MDA_MVC, access controls through mda_file
                mda_file = parent.mda_file
                if hasattr(mda_file, "autoBox"):
                    mda_file.autoBox.setVisible(show)
                if hasattr(mda_file, "clearButton"):
                    mda_file.clearButton.setVisible(show)
                if hasattr(mda_file, "clearGraphButton"):
                    mda_file.clearGraphButton.setVisible(show)

                # addButton and replaceButton should only be visible in Auto-off mode
                if show and hasattr(mda_file, "mode"):
                    is_auto_off = mda_file.mode() == "Auto-off"
                    if hasattr(mda_file, "addButton"):
                        mda_file.addButton.setVisible(is_auto_off)
                    if hasattr(mda_file, "replaceButton"):
                        mda_file.replaceButton.setVisible(is_auto_off)
                else:
                    # Hide when show=False (switching to 2D tab)
                    if hasattr(mda_file, "addButton"):
                        mda_file.addButton.setVisible(False)
                    if hasattr(mda_file, "replaceButton"):
                        mda_file.replaceButton.setVisible(False)

        except Exception as e:
            logger.error(f"Error in showModeControls: {e}")

    def showAnalysisControls(self, show: bool):
        """Show or hide 1D-specific controls by hiding/showing the entire curves widget."""
        try:
            # Hide/show the entire curves widget (contains curveBox, curveRemove, curveStyle, clearAll, etc.)
            if hasattr(self, "curves"):
                self.curves.setVisible(show)

            # Hide/show graphInfo panel
            if hasattr(self, "graphInfo"):
                self.graphInfo.setVisible(show)

            # Hide/show cursorInfo panel for 2D tab
            if hasattr(self, "cursorInfo"):
                self.cursorInfo.setVisible(show)

            # If showing 1D controls, restore their state based on current curve selection
            if show and hasattr(self, "chart_view") and self.chart_view:
                logger.debug("Restoring control state for 1D tab")

                # Reconnect the curveRemove button signal
                if hasattr(self, "curveRemove") and hasattr(
                    self.chart_view, "onRemoveButtonClicked"
                ):
                    logger.debug("Reconnecting curveRemove signal")
                    from mdaviz import utils

                    utils.reconnect(
                        self.curveRemove.clicked, self.chart_view.onRemoveButtonClicked
                    )

                selected_id = self.chart_view.getSelectedCurveID()
                has_curve = (
                    selected_id and selected_id in self.chart_view.curveManager.curves()
                )
                self.updatePlotControls(has_curve)

        except Exception as e:
            logger.error(f"Error in showAnalysisControls: {e}")

    def getCurrentFileTableview(self):
        """Get the current file table view from the parent."""
        try:
            parent = self.parent()
            while parent and not hasattr(parent, "currentFileTableview"):
                parent = parent.parent()
            if parent and hasattr(parent, "currentFileTableview"):
                return parent.currentFileTableview()
            else:
                logger.warning("No MDA_MVC found")
                return None
        except Exception as e:
            logger.error(f"Error in getCurrentFileTableview: {e}")
            return None

    def setupFitUI(self):
        """Setup the fit UI components and connections."""
        # Populate fit model combo box in the desired order
        models = get_available_models()
        ordered_model_names = list(models)
        for model_name in ordered_model_names:
            if model_name in models:
                self.fitModelCombo.addItem(model_name)

        # Connect fit buttons
        self.fitButton.clicked.connect(self.onFitButtonClicked)
        self.clearFitsButton.clicked.connect(self.onClearFitsButtonClicked)

        # Initially disable fit controls until a curve is selected
        self.fitButton.setEnabled(False)
        self.clearFitsButton.setEnabled(False)

    def onFitButtonClicked(self):
        """Handle fit button click."""
        if hasattr(self, "chart_view") and self.chart_view:
            model_name = self.fitModelCombo.currentText()
            use_range = self.useFitRangeCheck.isChecked()
            self.chart_view.performFit(model_name, use_range)

    def onClearFitsButtonClicked(self):
        """Handle clear fits button click."""
        if hasattr(self, "chart_view") and self.chart_view:
            self.chart_view.clearAllFits()

    def updatePlotControls(self, curve_selected: bool):
        """
        Update plot control states based on curve selection.

        Parameters:
        - curve_selected: Whether a curve is currently selected
        """
        from PyQt6.QtCore import QTimer

        logger.debug(f"updatePlotControls called with curve_selected={curve_selected}")

        # Prevent rapid successive calls that would disable controls
        if (
            hasattr(self, "_last_control_update")
            and self._last_control_update is not None
            and hasattr(self, "_last_control_update_value")
            and self._last_control_update_value is True
            and curve_selected is False
        ):
            # If this is called too soon after enabling controls, and trying to disable them, ignore it
            logger.debug("Skipping rapid disable call")
            return

        # Set a timer to allow the next call after a delay
        self._last_control_update = QTimer()
        self._last_control_update.singleShot(
            self._control_update_delay,
            lambda: setattr(self, "_last_control_update", None),
        )
        self._last_control_update_value = curve_selected

        self.fitButton.setEnabled(curve_selected)  # type: ignore[attr-defined]
        self.clearFitsButton.setEnabled(curve_selected)  # type: ignore[attr-defined]
        self.curveStyle.setEnabled(curve_selected)  # type: ignore[attr-defined]
        self.logXCheckBox.setEnabled(curve_selected)  # type: ignore[attr-defined]
        self.logYCheckBox.setEnabled(curve_selected)  # type: ignore[attr-defined]

    def setupCurveStyleUI(self):
        """Setup the curve style UI components and connections."""
        # Define available curve styles with their matplotlib format strings
        self.curve_styles = {
            "Line": "-",
            "Points": ".",
            "Circle Markers": "o-",
            "Square Markers": "s-",
            "Triangle Markers": "^-",
            "Diamond Markers": "D-",
            "Dashed": "--",
            "Dots": ":",
            "Dash-Dot": "-.",
        }

        # Populate the combo box
        for style_name in self.curve_styles.keys():
            self.curveStyle.addItem(style_name)  # type: ignore[attr-defined]

        # Set default style
        self.curveStyle.setCurrentText("Line")  # type: ignore[attr-defined]

        # Connect the combo box signal
        self.curveStyle.currentTextChanged.connect(self.onCurveStyleChanged)  # type: ignore[attr-defined]

        # Initially disable until a curve is selected
        self.curveStyle.setEnabled(False)  # type: ignore[attr-defined]

    def onCurveStyleChanged(self, style_name: str):
        """Handle curve style change."""
        if hasattr(self, "chart_view") and self.chart_view:
            self.chart_view.updateCurveStyle(style_name)

    def setupLogScaleUI(self):
        """Setup the log scale UI components and connections."""
        # Connect log scale checkboxes
        self.logXCheckBox.toggled.connect(self.onLogScaleChanged)  # type: ignore[attr-defined]
        self.logYCheckBox.toggled.connect(self.onLogScaleChanged)  # type: ignore[attr-defined]

        # Initially disable until a curve is selected
        self.logXCheckBox.setEnabled(False)  # type: ignore[attr-defined]
        self.logYCheckBox.setEnabled(False)  # type: ignore[attr-defined]

    def onLogScaleChanged(self):
        """Handle log scale checkbox changes."""
        # Store the log scale state centrally
        self._log_x_state = self.logXCheckBox.isChecked()  # type: ignore[attr-defined]
        self._log_y_state = self.logYCheckBox.isChecked()  # type: ignore[attr-defined]

        # Apply to chart if available
        if hasattr(self, "chart_view") and self.chart_view:
            self.chart_view.setLogScales(self._log_x_state, self._log_y_state)

    def getLogScaleState(self):
        """Get the current log scale state."""
        return self._log_x_state, self._log_y_state

    def setLogScaleState(self, log_x: bool, log_y: bool):
        """Set the log scale state and update checkboxes."""
        self._log_x_state = log_x
        self._log_y_state = log_y

        # Update checkbox states to match stored state
        self.logXCheckBox.setChecked(log_x)  # type: ignore[attr-defined]
        self.logYCheckBox.setChecked(log_y)  # type: ignore[attr-defined]

        # Apply to chart if available
        if hasattr(self, "chart_view") and self.chart_view:
            self.chart_view.setLogScales(log_x, log_y)

    def syncLogScaleCheckboxes(self):
        """Sync checkbox states with the stored log scale state."""
        self.logXCheckBox.setChecked(self._log_x_state)  # type: ignore[attr-defined]
        self.logYCheckBox.setChecked(self._log_y_state)  # type: ignore[attr-defined]

    def setTableData(self, data):
        """
        Set data for the data table view.

        Parameters:
            data: Data to display in the table
        """
        # Reuse existing data table view if it exists
        if hasattr(self, "data_table_view") and self.data_table_view:
            self.data_table_view.setData(data)
            self.data_table_view.displayTable()
        else:
            # Create new one only if it doesn't exist
            self.data_table_view = DataTableView(data, self)
            layout = self.dataPage.layout()
            layout.addWidget(self.data_table_view)
            self.data_table_view.displayTable()

    def setMetadata(self, text, *args, **kwargs):
        """
        Set text content for the metadata display.

        Parameters:
            text (str): Text content to display
        """
        # tab=self.metadataPage
        self.metadata.setText(text)

    def setPlot(self, plot_widget):
        """
        Set the plot widget for the visualization tab.

        Parameters:
            plot_widget: The plot widget to add to the layout
        """
        layout = self.plotPageMpl.layout()
        utils.removeAllLayoutWidgets(layout)

        # Set size policy to prevent vertical expansion
        plot_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )

        # Don't override the ChartView's own height constraints
        # The ChartView already has proper max height constraints set

        layout.addWidget(plot_widget)

        # Store reference to chart view for fit functionality
        self.chart_view = plot_widget

        # Sync log scale checkbox states with the stored state
        self.syncLogScaleCheckboxes()

        # Update tab widget max height to match the chart view
        self._updateTabWidgetMaxHeight()

        # # Debug output for 2D plotting
        if hasattr(plot_widget, "_plot_type"):
            logger.debug("setPlot - Added ChartView2D widget to layout")
            logger.debug(f"  Widget type: {type(plot_widget)}")
            logger.debug(f"  Widget visible: {plot_widget.isVisible()}")
            logger.debug(f"  Widget size: {plot_widget.size()}")
            logger.debug(f"  Layout count: {layout.count()}")
            logger.debug(f"  Layout item widget: {layout.itemAt(0).widget()}")
        else:
            logger.debug("setPlot - Added regular ChartView widget to layout")
            logger.debug(f"  Widget type: {type(plot_widget)}")
            logger.debug(f"  Widget visible: {plot_widget.isVisible()}")
            logger.debug(f"  Widget size: {plot_widget.size()}")
            logger.debug(f"  Layout count: {layout.count()}")
            logger.debug(f"  Layout item widget: {layout.itemAt(0).widget()}")

    def _updateTabWidgetMaxHeight(self):
        """Update the tab widget's maximum height to match the plot height setting."""
        from mdaviz.user_settings import settings

        max_height = settings.getKey("plot_max_height")
        try:
            max_height = int(max_height)
        except (TypeError, ValueError):
            max_height = 800  # Default value

        # Set maximum height for the tab widget to prevent vertical growth
        self.tabWidget.setMaximumHeight(
            max_height + 100
        )  # Add some padding for tab headers

        # Also update the plot page max height
        self.plotPageMpl.setMaximumHeight(
            max_height + 50
        )  # Add padding for tab content

    def isPlotBlank(self):
        """Check if the plot area is blank (no data displayed)."""
        layout = self.plotPageMpl.layout()
        if layout.count() == 0:
            return True
        plot_widget = layout.itemAt(0).widget()
        # Check if the plot widget is an instance of chartView and has data items
        if isinstance(plot_widget, ChartView):
            return not plot_widget.hasDataItems()
        return True  # If not a chartView instance, consider it as blank

    def clearContents(self, plot=True, data=True, metadata=True):
        """
        Clears content from the specified components of the visualization.

        Parameters:
        - plot (bool, optional): If True, clears the plot content. Defaults to True.
        - data (bool, optional): If True, clears the data table content. Defaults to True.
        - metadata (bool, optional): If True, clears the metadata content. Defaults to True.
        """
        # Clear Plot
        if plot:
            layout = self.plotPageMpl.layout()
            if layout.count() > 0:
                plot_widget = layout.itemAt(0).widget()
                if isinstance(plot_widget, ChartView):
                    plot_widget.clearPlot()
                    plot_widget.curveManager.removeAllCurves()
        # Clear Metadata
        if metadata:
            self.metadata.setText("")
        # Clear Data Table
        if data:
            try:
                self.data_table_view.clearContents()
            except AttributeError:
                pass  # data_table_view does not exist, so do nothing

    def setStatus(self, text):
        """
        Set the status bar text.

        Parameters:
            text (str): Status message to display
        """
        self.mda_mvc.setStatus(text)

    def setupSearchFunctionality(self):
        """Setup search functionality for the metadata widget."""
        # Create a shortcut for Ctrl+F
        self.search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        self.search_shortcut.activated.connect(self.showSearchDialog)

        # Initially disable the shortcut (only enable when metadata tab is active)
        self.search_shortcut.setEnabled(False)

        # Create search dialog (but don't show it yet)
        self.search_dialog = None

        # Connect tab widget signals to enable/disable search
        self.tabWidget.currentChanged.connect(self.onTabChanged)

    def showSearchDialog(self):
        """Show the search dialog for the metadata widget."""
        if not self.search_dialog:
            self.search_dialog = MetadataSearchDialog(self.metadata, self)

        # Show the dialog
        self.search_dialog.show()
        self.search_dialog.raise_()
        self.search_dialog.activateWindow()


class MetadataSearchDialog(QDialog):
    """A simple search dialog for the metadata widget."""

    def __init__(self, text_widget, parent=None):
        super().__init__(parent)
        self.text_widget = text_widget
        self.current_find_index = 0
        self.setupUI()

    def setupUI(self):
        """Setup the search dialog UI."""
        self.setWindowTitle("Search Metadata")
        self.setModal(False)
        self.resize(300, 100)

        layout = QtWidgets.QVBoxLayout(self)

        # Search input
        search_layout = QtWidgets.QHBoxLayout()
        search_layout.addWidget(QtWidgets.QLabel("Find:"))
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.textChanged.connect(self.findText)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Buttons
        button_layout = QtWidgets.QHBoxLayout()

        self.find_next_btn = QtWidgets.QPushButton("Find Next")
        self.find_next_btn.clicked.connect(self.findNext)
        button_layout.addWidget(self.find_next_btn)

        self.find_prev_btn = QtWidgets.QPushButton("Find Previous")
        self.find_prev_btn.clicked.connect(self.findPrevious)
        button_layout.addWidget(self.find_prev_btn)

        self.close_btn = QtWidgets.QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

        # Set focus to search input
        self.search_input.setFocus()

    def findText(self):
        """Find text as user types."""
        search_text = self.search_input.text()
        if search_text:
            self.current_find_index = 0
            self.findNext()

    def findNext(self):
        """Find next occurrence of the search text."""
        search_text = self.search_input.text()
        if not search_text:
            return

        # Use QTextBrowser's find method
        found = self.text_widget.find(search_text)
        if not found:
            # If not found, start from beginning
            cursor = self.text_widget.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            self.text_widget.setTextCursor(cursor)
            found = self.text_widget.find(search_text)

        if found:
            self.text_widget.setFocus()

    def findPrevious(self):
        """Find previous occurrence of the search text."""
        search_text = self.search_input.text()
        if not search_text:
            return

        # Use QTextBrowser's find method with backward search
        found = self.text_widget.find(
            search_text, QtGui.QTextDocument.FindFlag.FindBackward
        )
        if not found:
            # If not found, start from end
            cursor = self.text_widget.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.text_widget.setTextCursor(cursor)
            found = self.text_widget.find(
                search_text, QtGui.QTextDocument.FindFlag.FindBackward
            )

        if found:
            self.text_widget.setFocus()

    def keyPressEvent(self, event):
        """Handle key press events."""
        if (
            event.key() == QtCore.Qt.Key.Key_Return
            or event.key() == QtCore.Qt.Key.Key_Enter
        ):
            # Enter key finds next
            self.findNext()
        elif event.key() == QtCore.Qt.Key.Key_Escape:
            # Escape key closes dialog
            self.close()
        else:
            super().keyPressEvent(event)
