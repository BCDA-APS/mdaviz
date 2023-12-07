from PyQt5 import QtWidgets
from PyQt5.QtGui import QFont

from . import utils
from .chartview import ChartView

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

    def setPlot(self, plot_widget):
        layout = self.plotPage.layout()
        utils.removeAllLayoutWidgets(layout)
        layout.addWidget(plot_widget)
        self.tabWidget.setCurrentWidget(self.plotPage)

    def isPlotBlank(self):
        layout = self.plotPage.layout()
        if layout.count() == 0:
            return True
        plot_widget = layout.itemAt(0).widget()
        # Check if the plot widget is an instance of ChartView and has data items
        if isinstance(plot_widget, ChartView):
            return not plot_widget.hasDataItems()
        return True  # If not a ChartView instance, consider it as blank

    def setStatus(self, text):
        self.parent.setStatus(text)
