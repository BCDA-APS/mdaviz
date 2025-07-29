from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtGui import QFont, QKeySequence
from PyQt6.QtWidgets import QWidget, QDialog, QSizePolicy
from PyQt6.QtGui import QShortcut

from mdaviz import utils
from mdaviz.chartview import ChartView
from mdaviz.data_table_view import DataTableView
from mdaviz.fit_models import get_available_models

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

        # Connect tab change signal
        self.tabWidget.currentChanged.connect(self.onTabChanged)

    def update2DTabVisibility(self, show_2d_tab=False):
        """
        Update 2D tab visibility based on data dimensions.

        Parameters:
            show_2d_tab (bool): Whether to show the 2D tab
        """
        # Find the 2D tab index (should be index 3 after Metadata tab)
        tab_count = self.tabWidget.count()
        if tab_count >= 4:
            # Hide/show 2D tab
            self.tabWidget.setTabVisible(3, show_2d_tab)

            # If hiding 2D tab and it's currently selected, switch to 1D tab
            if not show_2d_tab and self.tabWidget.currentIndex() == 3:
                self.tabWidget.setCurrentIndex(0)

    def set2DData(self, data):
        """
        Set 2D data for plotting.

        Parameters:
            data (dict or None): 2D data dictionary with scanDict2D and metadata, or None to clear
        """
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
        if self.tabWidget.currentIndex() == 1:  # 2D tab
            self.update2DPlot()

    def update2DPlot(self):
        """Update the 2D plot with current data."""
        if not hasattr(self, "_2d_data") or not self._2d_data:
            return

        # TODO: Implement 2D plotting
        # This will be implemented when we add 2D plotting to chartview
        print("2D plotting not yet implemented")

    def onTabChanged(self, index):
        """
        Handle tab changes.

        Parameters:
            index (int): Index of the newly selected tab
        """
        # Get current tab structure
        tab_count = self.tabWidget.count()
        is_2d_visible = tab_count >= 4 and self.tabWidget.isTabVisible(3)

        # Handle 2D plotting
        if is_2d_visible and index == 3:  # 2D tab
            self.update2DPlot()
        elif index == 0:  # 1D tab
            # Update 1D plot if needed
            pass

        # Handle search functionality
        # Enable search only when metadata tab is active
        # Tab indices: 0=1D, 1=Data, 2=Metadata, 3=2D(if visible)
        # Metadata is always at index 2
        is_metadata_tab = index == 2

        # Debug: Print tab information
        print(f"Tab changed to index {index}")
        print(f"Tab count: {tab_count}")
        print(f"2D visible: {is_2d_visible}")
        print(f"Metadata index: 2 (fixed)")
        print(f"Is metadata tab: {is_metadata_tab}")

        if hasattr(self, "search_shortcut"):
            self.search_shortcut.setEnabled(is_metadata_tab)
            print(f"Search shortcut enabled: {self.search_shortcut.isEnabled()}")

        # Close search dialog if switching away from metadata tab
        if (
            hasattr(self, "search_dialog")
            and not is_metadata_tab
            and self.search_dialog
            and self.search_dialog.isVisible()
        ):
            self.search_dialog.close()

    def setupFitUI(self):
        """Setup the fit UI components and connections."""
        # Populate fit model combo box in the desired order
        models = get_available_models()
        ordered_model_names = [
            "Gaussian",
            "Lorentzian",
            "Error Function",
            "Linear",
            "Quadratic",
            "Cubic",
            "Exponential",
        ]
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

    def updateFitControls(self, curve_selected: bool):
        """
        Update fit control states based on curve selection.

        Parameters:
        - curve_selected: Whether a curve is currently selected
        """
        self.fitButton.setEnabled(curve_selected)  # type: ignore[attr-defined]
        self.clearFitsButton.setEnabled(curve_selected)  # type: ignore[attr-defined]
        self.updateCurveStyleControls(curve_selected)

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

        # Setup log scale controls
        self.setupLogScaleUI()

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

    def onCurveStyleChanged(self, style_name: str):
        """Handle curve style change."""
        if hasattr(self, "chart_view") and self.chart_view:
            self.chart_view.updateCurveStyle(style_name)

    def updateCurveStyleControls(self, curve_selected: bool):
        """
        Update curve style control states based on curve selection.

        Parameters:
        - curve_selected: Whether a curve is currently selected
        """
        self.curveStyle.setEnabled(curve_selected)  # type: ignore[attr-defined]
        self.logXCheckBox.setEnabled(curve_selected)  # type: ignore[attr-defined]
        self.logYCheckBox.setEnabled(curve_selected)  # type: ignore[attr-defined]

    def setTableData(self, data):
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
        # tab=self.metadataPage
        self.metadata.setText(text)

    def setPlot(self, plot_widget):
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
        layout = self.plotPageMpl.layout()
        if layout.count() == 0:
            print("NO LAYOUT: blank")
            return True
        plot_widget = layout.itemAt(0).widget()
        # Check if the plot widget is an instance of chartView and has data items
        if isinstance(plot_widget, ChartView):
            print("HAS DATA ITEM")
            return not plot_widget.hasDataItems()
        print("NOT A CHARTVIEW INSTANCE")
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
