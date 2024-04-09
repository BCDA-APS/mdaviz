from PyQt5 import QtWidgets
from PyQt5.QtGui import QFont

from . import utils
from .chartview import ChartView
from .data_table_view import DataTableView

MD_FONT = "Monospace"
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
        # TODO- later: replace removeAllLayoutWidgets with mainWindow.clearContent?
        # or clearContents(plot=True, data=False, metadata=False)
        # why are we removing all the layouts?
        utils.removeAllLayoutWidgets(layout)
        layout.addWidget(plot_widget)

    # # TODO: I do not think we use this:
    # def isPlotBlank(self):
    #     layout = self.plotPageMpl.layout()
    #     if layout.count() == 0:
    #         return True
    #     plot_widget = layout.itemAt(0).widget()
    #     # Check if the plot widget is an instance of chartView and has data items
    #     if isinstance(plot_widget, ChartView):
    #         return not plot_widget.hasDataItems()
    #     return True  # If not a chartView instance, consider it as blank

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
