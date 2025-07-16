from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QFont, QKeySequence
from PyQt5.QtWidgets import QShortcut, QWidget, QDialog, QSizePolicy

from . import utils
from .chartview import ChartView
from .data_table_view import DataTableView
from .fit_models import get_available_models

MD_FONT = "Arial"
MD_FONT_SIZE = 12


class MDAFileVisualization(QWidget):
    """The panel to show the contents of a file."""

    # UI file name matches this module, different extension
    ui_file = utils.getUiFileName(__file__)

    def __init__(self, parent):
        """
        Create the vizualization widget and connect with its parent.

        PARAMETERS

        parent object:
            Instance of mdaviz.mda_folder.MDAMVC
        """
        self.mda_mvc = parent
        super().__init__()
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()

    def setup(self):
        font = QFont(MD_FONT)
        font.setPointSize(MD_FONT_SIZE)
        self.metadata.setFont(font)

        # Set size policy for the main visualization widget to prevent unwanted expansion
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Set size policy for the plot page to prevent vertical expansion
        self.plotPageMpl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Set size policy for the tab widget to prevent vertical expansion
        self.tabWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # Get maximum height from user settings with default fallback
        from .user_settings import settings

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
        self.fitButton.setEnabled(curve_selected)
        self.clearFitsButton.setEnabled(curve_selected)
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
            self.curveStyle.addItem(style_name)

        # Set default style
        self.curveStyle.setCurrentText("Line")

        # Connect the combo box signal
        self.curveStyle.currentTextChanged.connect(self.onCurveStyleChanged)

        # Initially disable until a curve is selected
        self.curveStyle.setEnabled(False)

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
        self.curveStyle.setEnabled(curve_selected)

    def setTableData(self, data):
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
        plot_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # Don't override the ChartView's own height constraints
        # The ChartView already has proper max height constraints set

        layout.addWidget(plot_widget)

        # Store reference to chart view for fit functionality
        self.chart_view = plot_widget

        # Update tab widget max height to match the chart view
        self._updateTabWidgetMaxHeight()

    def _updateTabWidgetMaxHeight(self):
        """Update the tab widget's maximum height to match the plot height setting."""
        from .user_settings import settings

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

    def onTabChanged(self, index):
        """Handle tab changes to enable/disable search functionality."""
        # Enable search only when metadata tab is active
        # The metadata tab is at index 2 (0=Plot, 1=Data, 2=Metadata)
        is_metadata_tab = index == 2
        self.search_shortcut.setEnabled(is_metadata_tab)

        # Close search dialog if switching away from metadata tab
        if (
            not is_metadata_tab
            and self.search_dialog
            and self.search_dialog.isVisible()
        ):
            self.search_dialog.close()


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
            cursor.movePosition(cursor.Start)
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
        found = self.text_widget.find(search_text, QtWidgets.QTextDocument.FindBackward)
        if not found:
            # If not found, start from end
            cursor = self.text_widget.textCursor()
            cursor.movePosition(cursor.End)
            self.text_widget.setTextCursor(cursor)
            found = self.text_widget.find(
                search_text, QtWidgets.QTextDocument.FindBackward
            )

        if found:
            self.text_widget.setFocus()

    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == QtCore.Qt.Key_Return or event.key() == QtCore.Qt.Key_Enter:
            # Enter key finds next
            self.findNext()
        elif event.key() == QtCore.Qt.Key_Escape:
            # Escape key closes dialog
            self.close()
        else:
            super().keyPressEvent(event)
