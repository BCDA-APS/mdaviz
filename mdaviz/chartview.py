"""
Charting widget
"""

import datetime
from itertools import cycle

from PyQt5 import QtWidgets

import pyqtgraph as pg

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

FONTSIZE = 11
LEFT_BUTTON = 1
MIDDLE_BUTTON = 2
RIGHT_BUTTON = 3
TIMESTAMP_LIMIT = datetime.datetime.fromisoformat("1990-01-01").timestamp()

# https://pyqtgraph.readthedocs.io/en/latest/api_reference/graphicsItems/scatterplotitem.html#pyqtgraph.ScatterPlotItem.setSymbol
# https://developer.mozilla.org/en-US/docs/Web/CSS/named-color
# Do NOT sort these colors alphabetically!  There should be obvious
# contrast between adjacent colors.
PLOT_COLORS = """
    r g b c m
    goldenrod
    lime
    orange
    blueviolet
    brown
    teal
    olive
    lightcoral
    cornflowerblue
    forestgreen
    salmon
""".split()
PLOT_SYMBOLS = """o + x star s d t t2 t3""".split()

pg.setConfigOption("background", "w")
pg.setConfigOption("foreground", "k")
GRID_OPACITY = 0.1

_AUTO_COLOR_CYCLE = cycle(PLOT_COLORS)
_AUTO_SYMBOL_CYCLE = cycle(PLOT_SYMBOLS)


def auto_color():
    """Returns next color for pens and brushes."""
    return next(_AUTO_COLOR_CYCLE)


def auto_symbol():
    """Returns next symbol for scatter plots."""
    return next(_AUTO_SYMBOL_CYCLE)


class ChartViewQt(QtWidgets.QWidget):
    def __init__(self, parent, **kwargs):
        self.parent = parent

        super().__init__()

        size = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred
        )

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.addLegend()
        self.plot_widget.plotItem.showAxes(True)
        self.plot_widget.plotItem.showGrid(x=True, y=True, alpha=GRID_OPACITY)
        # see: https://stackoverflow.com/a/70200326
        # label = pg.LabelItem(
        #     f"plot: {datetime.datetime.now()}", color="lightgrey", size="8pt"
        # )
        # label.setParentItem(self.plot_widget.plotItem)
        # label.anchor(itemPos=(0, 1), parentPos=(0, 1))

        config = {
            "title": self.setPlotTitle,
            "y": self.setLeftAxisText,
            "x": self.setBottomAxisText,
            "x_units": self.setBottomAxisUnits,
            "y_units": self.setLeftAxisUnits,
            "x_datetime": self.setAxisDateTime,
        }
        for k, func in config.items():
            func(kwargs.get(k))

        # QWidget Layout
        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)

        ## plot
        size.setHorizontalStretch(4)
        self.plot_widget.setSizePolicy(size)
        layout.addWidget(self.plot_widget)

    def plot(self, *args, **kwargs):
        return self.plot_widget.plot(*args, **kwargs)

    def setAxisDateTime(self, choice):
        if choice:
            item = pg.DateAxisItem(orientation="bottom")
            self.plot_widget.setAxisItems({"bottom": item})

    def setAxisLabel(self, axis, text):
        self.plot_widget.plotItem.setLabel(axis, text)

    def setAxisUnits(self, axis, text):
        self.plot_widget.plotItem.axes[axis]["item"].labelUnits = text

    def setBottomAxisText(self, text):
        self.setAxisLabel("bottom", text)

    def setBottomAxisUnits(self, text):
        self.setAxisUnits("bottom", text)

    def setLeftAxisText(self, text):
        self.setAxisLabel("left", text)

    def setLeftAxisUnits(self, text):
        self.setAxisUnits("left", text)

    def setPlotTitle(self, text):
        self.plot_widget.plotItem.setTitle(text)

    def clearPlot(self):
        self.plot_widget.clear()

    def hasDataItems(self):
        # Check if the plot widget has any plot data items
        return len(self.plot_widget.plotItem.items) > 0


######################################################


class ChartViewMpl(QtWidgets.QWidget):
    def __init__(self, parent, **kwargs):
        self.parent = parent
        super().__init__()

        # Create a Matplotlib figure and canvas
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        # Adjust layout to fit the size and position of the axes within the figure
        # self.figure.tight_layout(pad=2.0, w_pad=0.5, h_pad=0.5)
        # Create the main plot subplot (flexible size)
        self.main_axes = self.figure.add_subplot(111)
        # Adjust margins
        self.figure.subplots_adjust(bottom=0.1, top=0.9, right=0.92)

        # Create the navigation toolbar
        self.toolbar = NavigationToolbar(self.canvas, self)

        # Use a QVBoxLayout for stacking the toolbar and canvas vertically
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        # Apply the QVBoxLayout to the ChartViewMpl widget
        self.setLayout(layout)

        # Connect the click event to a handler
        self.cid = self.figure.canvas.mpl_connect("button_press_event", self.onclick)
        self.cursors = {
            1: None,
            "pos1": None,
            "text1": "press middle click",
            2: None,
            "pos2": None,
            "text2": "press right click",
            "diff": "n/a",
            "midpoint": "n/a",
        }

        # Plot configuration
        config = {
            "title": self.setPlotTitle,
            "y": self.setLeftAxisText,
            "x": self.setBottomAxisText,
        }
        for k, func in config.items():
            func(kwargs.get(k))

    def plot(self, *args, **kwargs):
        # Plot data on the axes
        self.main_axes.plot(*args, **kwargs)
        self.main_axes.legend()
        self.main_axes.grid(True, color="#cccccc", linestyle="-", linewidth=0.5)
        self.update_info_panel()
        self.canvas.draw()

    def setPlotTitle(self, text):
        self.main_axes.set_title(text, fontsize=FONTSIZE, y=1.03)

    def setBottomAxisText(self, text):
        self.main_axes.set_xlabel(text, fontsize=FONTSIZE, labelpad=10)

    def setLeftAxisText(self, text):
        self.main_axes.set_ylabel(text, fontsize=FONTSIZE, labelpad=20)

    def clearPlot(self):
        self.main_axes.clear()
        self.cursors[1] = None
        self.cursors[2] = None
        self.cursors["pos1"] = None
        self.cursors["pos2"] = None
        self.cursors["text1"] = "press middle click"
        self.cursors["text2"] = "press right click"
        self.cursors["diff"] = "n/a"
        self.cursors["midpoint"] = "n/a"
        self.canvas.draw()
        self.clear_cursor_info_panel()

    # Additional methods:

    def onclick(self, event):
        # Check if the click was in the main_axes
        if event.inaxes is self.main_axes:
            # Middle click for red cursor
            if event.button == MIDDLE_BUTTON:
                if self.cursors[1]:
                    self.cursors[1].remove()  # Remove existing red cursor
                (self.cursors[1],) = self.main_axes.plot(
                    event.xdata, event.ydata, "r+", markersize=15, linewidth=2
                )
                # Update cursor position
                self.cursors["pos1"] = (event.xdata, event.ydata)

            # Right click for blue cursor
            elif event.button == RIGHT_BUTTON:
                if self.cursors[2]:
                    self.cursors[2].remove()  # Remove existing blue cursor
                (self.cursors[2],) = self.main_axes.plot(
                    event.xdata, event.ydata, "b+", markersize=15, linewidth=2
                )

                # Update cursor position
                self.cursors["pos2"] = (event.xdata, event.ydata)

            # Update the info panel with cursor positions
            self.update_info_panel()

            # Redraw the canvas to display the new markers
            self.canvas.draw()

    def update_info_panel(self):
        """
        Update cursor information in info panel widget.
        """
        # Check for the first cursor and update text accordingly
        if self.cursors[1]:
            x1, y1 = self.cursors["pos1"]
            self.cursors["text1"] = f"({x1:.2f}, {y1:.2f})"

        # Check for the second cursor and update text accordingly
        if self.cursors[2]:
            x2, y2 = self.cursors["pos2"]
            self.cursors["text2"] = f"({x2:.2f}, {y2:.2f})"

        if self.cursors[1] and self.cursors[2]:
            # Calculate differences and midpoints only if both cursors are present
            delta_x = x2 - x1
            delta_y = y2 - y1
            midpoint_x = (x1 + x2) / 2
            midpoint_y = (y1 + y2) / 2
            self.cursors["diff"] = f"({delta_x:.2f}, {delta_y:.2f})"
            self.cursors["midpoint"] = f"({midpoint_x:.2f}, {midpoint_y:.2f})"

        self.update_cursor_info_panel()

    def update_cursor_info_panel(self):
        self.parent.findChild(QtWidgets.QLineEdit, "pos1_text").setText(
            self.cursors["text1"]
        )
        self.parent.findChild(QtWidgets.QLineEdit, "pos2_text").setText(
            self.cursors["text2"]
        )
        self.parent.findChild(QtWidgets.QLineEdit, "diff_text").setText(
            self.cursors["diff"]
        )
        self.parent.findChild(QtWidgets.QLineEdit, "midpoint_text").setText(
            self.cursors["midpoint"]
        )

    def clear_cursor_info_panel(self):
        self.parent.findChild(QtWidgets.QLineEdit, "pos1_text").setText(
            "press middle click"
        )
        self.parent.findChild(QtWidgets.QLineEdit, "pos2_text").setText(
            "press middle click"
        )
        self.parent.findChild(QtWidgets.QLineEdit, "diff_text").setText("n/a")
        self.parent.findChild(QtWidgets.QLineEdit, "midpoint_text").setText("n/a")
