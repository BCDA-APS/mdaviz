from PyQt5 import QtWidgets
from PyQt5.QtGui import QFont

from . import utils
from .chartview import ChartView
from .data_table_view import DataTableView
from .fit_models import get_available_models

MD_FONT = "Arial"
MD_FONT_SIZE = 12


class MDAFileVisualization(QtWidgets.QWidget):
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
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )

        # Set size policy for the plot page to prevent vertical expansion
        self.plotPageMpl.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )

        # Set size policy for the tab widget to prevent expansion
        self.tabWidget.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )

        # Setup fit functionality
        self.setupFitUI()

    def setupFitUI(self):
        """Setup the fit UI components and connections."""
        # Populate fit model combo box
        models = get_available_models()
        for model_name in models.keys():
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
        plot_widget.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )

        # Set minimum and maximum height to constrain vertical growth
        plot_widget.setMinimumHeight(200)  # Minimum reasonable height
        plot_widget.setMaximumHeight(
            16777215
        )  # Allow reasonable expansion but not unlimited

        layout.addWidget(plot_widget)

        # Store reference to chart view for fit functionality
        self.chart_view = plot_widget

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
