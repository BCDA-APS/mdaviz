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
from matplotlib.gridspec import GridSpec
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

FONTSIZE = 11
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
        self.figure.subplots_adjust(bottom=0.16, top=0.92, right=0.92)

        # Create the info panel subplot (fixed size)
        self.info_panel_axes = self.figure.add_axes([0.1, 0.01, 0.8, 0.1])
        self.info_panel_axes.set_frame_on(False)
        self.info_panel_axes.get_xaxis().set_visible(False)
        self.info_panel_axes.get_yaxis().set_visible(False)

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
        self.cursor_positions = [None, None]
        self.red_cursor = None
        self.blue_cursor = None

        # Plot configuration
        config = {
            "title": self.setPlotTitle,
            "y": self.setLeftAxisText,
            "x": self.setBottomAxisText,
            # Matplotlib handles units differently, might need to adjust this
            # "x_units": self.setBottomAxisUnits,
            # "y_units": self.setLeftAxisUnits,
        }
        for k, func in config.items():
            func(kwargs.get(k))

    def plot(self, *args, **kwargs):
        # Plot data on the axes
        self.main_axes.plot(*args, **kwargs)
        self.main_axes.legend()
        self.main_axes.grid(True, color="#cccccc", linestyle="-", linewidth=0.5)
        self.canvas.draw()

    def setPlotTitle(self, text):
        self.main_axes.set_title(text, fontsize=FONTSIZE, y=1.03)

    def setBottomAxisText(self, text):
        self.main_axes.set_xlabel(text, fontsize=FONTSIZE, labelpad=10)

    def setLeftAxisText(self, text):
        self.main_axes.set_ylabel(text, fontsize=FONTSIZE, labelpad=20)

    def clearPlot(self):
        self.main_axes.clear()
        self.canvas.draw()

    # Additional methods:

    # TODO: use a dictionary to track the cursors
    # TODO: allow a blue cursor to be placed without the presence of a red cursor

    def onclick(self, event):
        # Only place a marker if the click was on the canvas
        if event.inaxes is not None:
            # Middle click for red cursor
            if event.button == 2:
                if self.red_cursor:
                    self.red_cursor.remove()  # Remove existing red cursor
                (self.red_cursor,) = self.main_axes.plot(
                    event.xdata, event.ydata, "r+", markersize=10
                )
                # Update cursor position
                self.cursor_positions[0] = (event.xdata, event.ydata)

            # Right click for blue cursor
            elif event.button == 3:
                if self.blue_cursor:
                    self.blue_cursor.remove()  # Remove existing blue cursor
                (self.blue_cursor,) = self.main_axes.plot(
                    event.xdata, event.ydata, "b+", markersize=10
                )
                if len(self.cursor_positions) > 1:
                    # Update cursor position
                    self.cursor_positions[1] = (event.xdata, event.ydata)
                else:
                    # Add blue cursor position
                    self.cursor_positions.append((event.xdata, event.ydata))

            # Update the info panel with cursor positions
            self.update_info_panel()

            # Redraw the canvas to display the new markers
            self.canvas.draw()

    def update_info_panel(self):
        # Clear the info panel by removing each text artist
        while len(self.info_panel_axes.texts) > 0:
            for text in self.info_panel_axes.texts:
                text.remove()

        # Initialize text variables
        cursor1_text = cursor2_text = diff_text = midpoint_text = ""
        width = 40  # Adjust the width as needed to align the text

        # Check for the first cursor and update text accordingly
        if self.red_cursor and len(self.cursor_positions) >= 1:
            x1, y1 = self.cursor_positions[0]
            cursor1_text = f"Cursor 1: ({x1:.3f}, {y1:.3f})"
            cursor1_text = f"{cursor1_text:<{width}}"  # Left-align and pad with spaces

        # Check for the second cursor and update text accordingly
        if self.blue_cursor and len(self.cursor_positions) >= 2:
            x2, y2 = self.cursor_positions[1]
            cursor2_text = f"Cursor 2: ({x2:.3f}, {y2:.3f})"
            cursor2_text = f"{cursor2_text:<{width}}"  # Left-align and pad with spaces

            # Calculate differences and midpoints only if both cursors are present
            delta_x = x2 - x1
            delta_y = y2 - y1
            average_x = (x1 + x2) / 2
            average_y = (y1 + y2) / 2
            diff_text = f"Difference: ({delta_x:.3f}, {delta_y:.3f})"
            midpoint_text = f"Midpoint: ({average_x:.3f}, {average_y:.3f})"

        # Construct the info panel text and update
        info_text = f"{cursor1_text}{diff_text}\n{cursor2_text}{midpoint_text}"

        # Clear the info panel by removing each text artist
        while len(self.info_panel_axes.texts) > 0:
            for text in self.info_panel_axes.texts:
                text.remove()

        # Add new text at the bottom of the info panel axes
        self.info_panel_axes.text(
            0.5,
            0,
            info_text,
            verticalalignment="bottom",
            horizontalalignment="center",
            transform=self.info_panel_axes.transAxes,
            fontsize=9,
        )

        # Redraw the canvas to update the panel
        self.canvas.draw()
