"""
Charting widget
"""

import datetime
from functools import partial
from itertools import cycle

from PyQt5 import QtWidgets

import pyqtgraph as pg

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

FONTSIZE = 10
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


############################################################################################################


class ChartViewMpl(QtWidgets.QWidget):
    def __init__(self, parent, **kwargs):
        self.parent = parent
        super().__init__()

        # Create a Matplotlib figure and canvas
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
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

        # Track curves
        self.line2D = {}  # all the Line2D on the graph, key = label
        self.curveBox = self.parent.findChild(QtWidgets.QComboBox, "curveBox")
        self.removeButton = self.parent.findChild(QtWidgets.QPushButton, "curveRemove")
        self.removeCursor1 = self.parent.findChild(
            QtWidgets.QPushButton, "cursor1_remove"
        )
        self.removeCursor2 = self.parent.findChild(
            QtWidgets.QPushButton, "cursor2_remove"
        )
        # NOTE: remove button triggers remove_curve twice: once when pushed, once when released.
        # This try-except solves the problem.
        try:
            self.removeButton.clicked.disconnect()
        except TypeError:
            pass  # No connection exists
        self.removeButton.clicked.connect(self.remove_curve)
        self.removeCursor1.clicked.connect(partial(self.remove_cursor, cursor_num=1))
        self.removeCursor2.clicked.connect(partial(self.remove_cursor, cursor_num=2))

    def setPlotTitle(self, text):
        self.main_axes.set_title(text, fontsize=FONTSIZE, y=1.03)

    def setBottomAxisText(self, text):
        self.main_axes.set_xlabel(text, fontsize=FONTSIZE, labelpad=10)

    def setLeftAxisText(self, text):
        self.main_axes.set_ylabel(text, fontsize=FONTSIZE, labelpad=20)

    def add_curve(self, *args, **kwargs):
        label = kwargs.get("label", None)
        plot_obj = self.main_axes.plot(*args, **kwargs)
        self.main_axes.grid(True, color="#cccccc", linestyle="-", linewidth=0.5)
        self.update_cursor_math()
        self.update_plot_and_ui()
        self.line2D[label] = plot_obj
        self.update_curveBox()

    def remove_curve(self, *args, **kwargs):
        label = self.curveBox.currentText()
        if label in self.line2D and len(self.line2D) == 1:
            self.clearPlot()
        if label in self.line2D:
            line = self.line2D[label][0]
            line.remove()
            del self.line2D[label]  # Remove the label/curve pair from the dictionary
            self.update_curveBox()  # Update the pull down menu with new 2Dline list
            self.update_plot_and_ui()

    def plot(self, *args, **kwargs):
        # Extract label from kwargs, default to None if not present
        label = kwargs.get("label", None)
        if label:
            if label not in self.line2D:
                self.add_curve(*args, **kwargs)

    def clearPlot(self):
        self.main_axes.clear()
        self.clear_cursors()
        self.canvas.draw()
        self.clear_cursor_info_panel()
        self.line2D = {}
        self.update_curveBox()

    def update_curveBox(self):
        self.curveBox.clear()
        self.curveBox.addItems(list(self.line2D.keys()))
        # New ylabel is the first curve on the menu
        if len(self.line2D):
            new_ylabel = self.curveBox.currentText().split(" ", 1)[1]
            self.main_axes.set_ylabel(new_ylabel)
            self.canvas.draw()

    def update_plot_and_ui(self):
        self.main_axes.relim()  # Recompute the axes limits
        self.main_axes.autoscale_view()  # Autoscale the view based on the remaining data
        self.add_legend_if_possible()
        self.canvas.draw()

    def add_legend_if_possible(self):
        handles, labels = self.main_axes.get_legend_handles_labels()
        # Filter out labels that start with '_' or are '_nolegend_'
        valid_labels = [
            label
            for label, handle in zip(labels, handles)
            if label and not label.startswith("_")
        ]
        if valid_labels:
            self.main_axes.legend()

    # def update_curve_basic(self)
    #     self.curveMin
    #     self.curveMax
    #     self.curveCom
    #     self.curveMean

    ########################################## Cursors methods:

    def remove_cursor(self, cursor_num):
        cross = self.cursors.get(cursor_num)
        if cross:
            cross.remove()
            self.cursors[cursor_num] = None
            self.cursors[f"pos{cursor_num}"] = None
            self.cursors[f"text{cursor_num}"] = (
                "press middle click" if cursor_num == 1 else "press right click"
            )
        self.cursors["diff"] = "n/a"
        self.cursors["midpoint"] = "n/a"
        self.update_plot_and_ui()
        self.update_cursor_info_panel()

    def clear_cursors(self):
        self.remove_cursor(1)
        self.remove_cursor(2)

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
            self.update_cursor_math()

            # Redraw the canvas to display the new markers
            self.canvas.draw()

    def update_cursor_math(self):
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
        # Calculate differences and midpoints only if both cursors are present
        if self.cursors[1] and self.cursors[2]:
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
