import datetime
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from PyQt5 import QtWidgets


class ChartViewMpl(QtWidgets.QWidget):
    def __init__(self, parent, **kwargs):
        self.parent = parent
        super().__init__()

        # Create a Matplotlib figure and canvas
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.axes = self.figure.add_subplot(111)

        # QWidget Layout
        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)

        # Add the Matplotlib canvas to the layout
        size = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred
        )
        size.setHorizontalStretch(4)
        self.canvas.setSizePolicy(size)
        layout.addWidget(self.canvas)

        # Additional setup (if needed)
        self.configure_chart(**kwargs)

    def configure_chart(self, **kwargs):
        # Set chart title, axis labels, etc.
        title = kwargs.get("title", "")
        x_label = kwargs.get("x", "")
        y_label = kwargs.get("y", "")

        self.setPlotTitle(title)
        self.setBottomAxisText(x_label)
        self.setLeftAxisText(y_label)

    def plot(self, x, y, label=None):
        # Plot data on the axes
        self.axes.plot(x, y, label=label)
        self.canvas.draw()

    def setPlotTitle(self, text):
        self.axes.set_title(text)

    def setBottomAxisText(self, text):
        self.axes.set_xlabel(text)

    def setLeftAxisText(self, text):
        self.axes.set_ylabel(text)

    def clearPlot(self):
        self.axes.clear()
        self.canvas.draw()

    # Additional methods as needed...
