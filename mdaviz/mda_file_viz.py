from PyQt5 import QtWidgets
from PyQt5.QtGui import QFont

from . import utils
from .chartview import ChartViewQt
from .chartview import ChartViewMpl

MD_FONT = "Monospace"
MD_FONT_SIZE = 12


class MDAFileVisualization(QtWidgets.QWidget):
    """The panel to show the contents of a file."""

    # UI file name matches this module, different extension
    ui_file = utils.getUiFileName(__file__)

    def __init__(self, parent):
        self.parent = parent

        super().__init__()
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()

    def setup(self):
        font = QFont(MD_FONT)
        font.setPointSize(MD_FONT_SIZE)
        self.metadata.setFont(font)

    def setMetadata(self, text, *args, **kwargs):
        # tab=self.metadataPage
        self.metadata.setText(text)

    def setData(self, text, *args, **kwargs):
        self.data.setText(text)

    def setPlot(self, plotPage, plot_widget):
        layout = plotPage.layout()
        utils.removeAllLayoutWidgets(layout)
        layout.addWidget(plot_widget)
        self.tabWidget.setCurrentWidget(plotPage)

    def setPlotQt(self, plot_widget):
        self.setPlot(self.plotPageQt, plot_widget)

    def setPlotMpl(self, plot_widget):
        self.setPlot(self.plotPageMpl, plot_widget)

    def isPlotBlank(self, plotPage, chartView):
        layout = plotPage.layout()
        if layout.count() == 0:
            return True
        plot_widget = layout.itemAt(0).widget()
        # Check if the plot widget is an instance of chartView and has data items
        if isinstance(plot_widget, chartView):
            return not plot_widget.hasDataItems()
        return True  # If not a chartView instance, consider it as blank

    def isPlotBlankQt(self):
        return self.isPlotBlank(self.plotPageQt, ChartViewQt)

    def isPlotBlankMpl(self):
        return self.isPlotBlank(self.plotPageMpl, ChartViewMpl)

    def setStatus(self, text):
        self.parent.setStatus(text)
