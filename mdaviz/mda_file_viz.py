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

    # def setData(self, text, *args, **kwargs):  # TODO: am  I using this at all?
    #     self.data.setText(text)

    def setPlot(self, plot_widget):
        layout = self.plotPageMpl.layout()
        utils.removeAllLayoutWidgets(
            layout
        )  # TODO replace with mainWindow.clearContent? or clearPlotArea below?
        layout.addWidget(plot_widget)
        #self.tabWidget.setCurrentWidget(self.plotPageMpl)

    def isPlotBlank(self):
        layout = self.plotPageMpl.layout()
        if layout.count() == 0:
            return True
        plot_widget = layout.itemAt(0).widget()
        # Check if the plot widget is an instance of chartView and has data items
        if isinstance(plot_widget, ChartView):
            return not plot_widget.hasDataItems()
        return True  # If not a chartView instance, consider it as blank
    
    # def clearPlotArea(self):
    #     """
    #     Clears the plot area by calling the clearPlot method on the ChartView instance.
    #     """
    #     layout = self.plotPageMpl.layout()
    #     if layout.count() > 0:
    #         plot_widget = layout.itemAt(0).widget()
    #         # Check if the plot widget is an instance of ChartView
    #         if isinstance(plot_widget, ChartView):
    #             plot_widget.clearPlot()  # Call clearPlot method of ChartView
                
 
    def clearAllContent(self):
        """
        Clears all content from the plot, metadata, and data tabs.
        """
        # Clear Plot
        layout = self.plotPageMpl.layout()
        if layout.count() > 0:
            plot_widget = layout.itemAt(0).widget()
            if isinstance(plot_widget, ChartView):
                plot_widget.clearPlot()

        # Clear Metadata
        self.metadata.setText("") 

        # Clear Data Table
        layout = self.dataPage.layout()
        utils.removeAllLayoutWidgets(layout)
    

    def setStatus(self, text):
        self.mda_mvc.setStatus(text)
