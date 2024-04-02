"""
Charting widget
"""

import datetime
from functools import partial
from itertools import cycle
import numpy
from PyQt5 import QtWidgets
from . import utils

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

FONTSIZE = 10
LEFT_BUTTON = 1
MIDDLE_BUTTON = 2
RIGHT_BUTTON = 3

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
_AUTO_COLOR_CYCLE = cycle(PLOT_COLORS)
_AUTO_SYMBOL_CYCLE = cycle(PLOT_SYMBOLS)


def auto_color():
    """Returns next color for pens and brushes."""
    return next(_AUTO_COLOR_CYCLE)


def auto_symbol():
    """Returns next symbol for scatter plots."""
    return next(_AUTO_SYMBOL_CYCLE)


class ChartView(QtWidgets.QWidget):
    def __init__(self, parent, **kwargs):
        # parent=<mdaviz.mda_folder.MDA_MVC object at 0x10e7ff520>
        self.mda_mvc = parent
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
        # Apply the QVBoxLayout to the ChartView widget
        self.setLayout(layout)

        # Connect the click event to a handler
        self.cid = self.figure.canvas.mpl_connect("button_press_event", self.onclick)
        self.cursors = {
            1: None,
            "pos1": None,
            "text1": "middle click",
            2: None,
            "pos2": None,
            "text2": "right click",
            "diff": "n/a",
            "midpoint": "n/a",
        }

        # Plot configuration
        self._plot_options = kwargs.get("plot_options", {})
        self._title = self.plot_options().get("title", "")
        self._ylabel = self.plot_options().get("y", "")
        self._xlabel = self.plot_options().get("x", "")
        self.setConfigPlot()

        # Track curves and display in QComboBox:
        self.line2D = {}  # all the Line2D on the graph, key = label
        self.curveBox = self.mda_mvc.findChild(QtWidgets.QComboBox, "curveBox")
        self.curveBox.currentTextChanged.connect(self.curveSelected)

        # Remove buttons
        self.removeButton = self.mda_mvc.findChild(QtWidgets.QPushButton, "curveRemove")
        self.removeCursor1 = self.mda_mvc.findChild(
            QtWidgets.QPushButton, "cursor1_remove"
        )
        self.removeCursor2 = self.mda_mvc.findChild(
            QtWidgets.QPushButton, "cursor2_remove"
        )
        # Remove button triggers removeCurve twice: once when pushed, once when released.
        # This try-except solves the problem.
        try:
            self.removeButton.clicked.disconnect()
        except TypeError:
            pass  # No connection exists
        self.removeButton.clicked.connect(self.removeCurve)
        self.removeCursor1.clicked.connect(partial(self.removeCursor, cursor_num=1))
        self.removeCursor2.clicked.connect(partial(self.removeCursor, cursor_num=2))

        # Connect offset & factor QLineEdit:
        self.offset_value = self.mda_mvc.findChild(QtWidgets.QLineEdit, "offset_value")
        self.factor_value = self.mda_mvc.findChild(QtWidgets.QLineEdit, "factor_value")
        self.offset_value.editingFinished.connect(self.applyBasicMathToCurve)
        self.factor_value.editingFinished.connect(self.applyBasicMathToCurve)

    def setPlotTitle(self, text):
        self.main_axes.set_title(text, fontsize=FONTSIZE, y=1.03)

    def setBottomAxisText(self, text):
        self.main_axes.set_xlabel(text, fontsize=FONTSIZE, labelpad=10)

    def setLeftAxisText(self, text):
        self.main_axes.set_ylabel(text, fontsize=FONTSIZE, labelpad=20)

    def setConfigPlot(self, grid=True):
        self.setLeftAxisText(self.ylabel())
        self.setBottomAxisText(self.xlabel())
        self.setPlotTitle(self.title())
        if grid:
            self.main_axes.grid(True, color="#cccccc", linestyle="-", linewidth=0.5)
        else:
            self.main_axes.grid(False)
        self.canvas.draw()

    def title(self):
        return self._title

    def xlabel(self):
        return self._xlabel

    def ylabel(self):
        return self._ylabel

    def plot_options(self):
        return self._plot_options

    def addCurve(self, row, path, *args, **kwargs):
        # Add to graph
        plot_obj = self.main_axes.plot(*args, **kwargs)
        self.updatePlot()
        # Add to the dictionary:
        label = kwargs.get("label", None)
        self.line2D[label] = {
            "line_obj": plot_obj[0],
            "x_data": args[0],
            "y_data": args[1],
            "offset": 0,  # default offset
            "factor": 1,  # default factor
            "row": row,
            "path": path,
        }
        # Add to the comboBox
        self.addIemCurveBox(label)

    def removeCurve(self, *args, **kwargs):
        label = self.curveBox.currentText()
        # If removing the last curve, clear all content from vizualization panel:
        if label in self.line2D:
            if len(self.line2D) == 1:
                self.mda_mvc.mda_file_viz.clearContents()
                self.mda_mvc.currentFileTV().tableView.model().clearAllCheckboxes()
            else:
                # Remove curve from graph
                row = self.line2D[label]["row"]
                line = self.line2D[label]["line_obj"]
                line.remove()
                # Remove curve from dictionary
                del self.line2D[label]
                # Remove curve from comboBox
                self.removeItemCurveBox(label)
                self.mda_mvc.currentFileTV().tableView.model().uncheckCheckBox(row)
                # Update plot labels, legend and title
                self.updatePlot()

    def plot(self, row, *args, **kwargs):
        # Extract label from kwargs, default to None if not present
        self._plot_options = kwargs.get("plot_options", {})
        ds_options = self._ds_options = kwargs.get("ds_options", {})
        path = self._plot_options["folderPath"]
        label = ds_options.get("label", None)
        self.main_axes.axis("on")
        if label:
            if label not in self.line2D:
                self.addCurve(row, path, *args, **ds_options)

    def clearPlot(self):
        self.main_axes.clear()
        self.main_axes.axis("off")
        self.main_axes.set_title("")
        self.clearCursors()
        self.clearCursorInfo()
        self.clearBasicMath()
        self.figure.canvas.draw()
        self.line2D = {}
        self.curveBox.clear()

    def addIemCurveBox(self, label):
        next_index = self.curveBox.count() + 1
        self.curveBox.addItem(label, next_index)

    def removeItemCurveBox(self, label):
        i = self.curveBox.findText(
            label
        )  # Returns the index of the item containing the given text ; otherwise returns -1.
        if i >= 0:
            self.curveBox.removeItem(i)

    def updatePlot(self):
        # Update labels and title:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._title = f"Plot Date & Time: {now}"
        self._xlabel = self._plot_options.get("x", "")
        if self.curveBox.count() <= 0:
            self._ylabel = self._plot_options.get("y", "")
        else:  # New ylabel is the first curve on the pull down menu
            self._ylabel = self.curveBox.currentText().split(" ", 1)[1]
        # Recompute the axes limits and autoscale:
        self.main_axes.relim()
        self.main_axes.autoscale_view()
        self.updateLegend()
        self.setConfigPlot()
        self.canvas.draw()

    def updateLegend(self):
        labels = self.main_axes.get_legend_handles_labels()[1]
        valid_labels = [label for label in labels if not label.startswith("_")]
        if valid_labels:
            self.main_axes.legend()

    def curveSelected(self, label):
        filePathLabel = self.mda_mvc.findChild(QtWidgets.QLabel, "filePath_viz")
        # Update QLineEdit & QLabel widgets with the values for the selected curve
        if label in self.line2D:
            self.offset_value.setText(str(self.line2D[label]["offset"]))
            self.factor_value.setText(str(self.line2D[label]["factor"]))
            filePathLabel.setText(self.line2D[label]["path"])
        else:
            self.offset_value.setText("0")
            self.factor_value.setText("1")
            filePathLabel.setText("")
        # Update basic math info:
        self.updateBasicMathInfo(label)

    def applyBasicMathToCurve(self):
        # Get the current text from the QLineEdit widgets & convert to float:
        try:
            offset = float(self.offset_value.text())
        except ValueError:
            offset = 0
        try:
            factor = float(self.factor_value.text())
        except ValueError:
            factor = 1
        # Get the current curve
        label = self.curveBox.currentText()
        if label in self.line2D:
            # Update the stored parameters for the current curve
            self.line2D[label]["offset"] = offset
            self.line2D[label]["factor"] = factor
            # Apply factor and offset to the selected curve
            curve = self.line2D[label]
            new_y = numpy.multiply(curve["y_data"], factor) + offset
            # Update the Line2D object with the new y-values
            curve["line_obj"].set_ydata(new_y)
            # Refresh the plot
            self.updatePlot()

    def calculateBasicMath(self, x_data, y_data):
        x_array = numpy.array(x_data)
        y_array = numpy.array(y_data)
        # Find y_min and y_max
        y_min = numpy.min(y_array)
        y_max = numpy.max(y_array)
        # Find the indices of the min and max y value
        y_min_index = numpy.argmin(y_array)
        y_max_index = numpy.argmax(y_array)
        # Find the corresponding x values for y_min and y_max
        x_at_y_min = x_array[y_min_index]
        x_at_y_max = x_array[y_max_index]
        # Calculate x_com and y_mean
        x_com = (
            numpy.sum(x_array * y_array) / numpy.sum(y_array)
            if numpy.sum(y_array) != 0
            else None
        )
        y_mean = numpy.mean(y_array)
        return (x_at_y_min, y_min), (x_at_y_max, y_max), x_com, y_mean

    def updateBasicMathInfo(self, label):
        if label and label in self.line2D:
            curve_data = self.line2D[label]
            x = curve_data["x_data"]
            y = curve_data["y_data"]
            stats = self.calculateBasicMath(x, y)
            for i, txt in zip(stats, ["min_text", "max_text", "com_text", "mean_text"]):
                if isinstance(i, tuple):
                    result = f"({utils.num2fstr(i[0])}, {utils.num2fstr(i[1])})"
                else:
                    result = f"{utils.num2fstr(i)}" if i else "n/a"
                self.mda_mvc.findChild(QtWidgets.QLabel, txt).setText(result)
        else:
            for txt in ["min_text", "max_text", "com_text", "mean_text"]:
                self.mda_mvc.findChild(QtWidgets.QLabel, txt).setText("n/a")

    def clearBasicMath(self):
        for txt in ["min_text", "max_text", "com_text", "mean_text"]:
            self.mda_mvc.findChild(QtWidgets.QLabel, txt).setText("n/a")

    def hasDataItems(self):
        # Return whether any artists have been added to the Axes (bool)
        return self.main_axes.has_data()

    ########################################## Cursors methods:

    def removeCursor(self, cursor_num):
        cross = self.cursors.get(cursor_num)
        if cross:
            cross.remove()
            self.cursors[cursor_num] = None
            self.cursors[f"pos{cursor_num}"] = None
            self.cursors[f"text{cursor_num}"] = (
                "middle click" if cursor_num == 1 else "right click"
            )
        self.cursors["diff"] = "n/a"
        self.cursors["midpoint"] = "n/a"
        self.updateCursorInfo()
        # Recompute the axes limits and autoscale:
        self.main_axes.relim()
        self.main_axes.autoscale_view()
        self.canvas.draw()

    def clearCursors(self):
        self.removeCursor(1)
        self.removeCursor(2)

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
            self.calculateCursors()

            # Redraw the canvas to display the new markers
            self.canvas.draw()

    def calculateCursors(self):
        """
        Update cursor information in info panel widget.
        """
        # Check for the first cursor and update text accordingly
        if self.cursors[1]:
            x1, y1 = self.cursors["pos1"]
            self.cursors["text1"] = f"({utils.num2fstr(x1)}, {utils.num2fstr(y1)})"
        # Check for the second cursor and update text accordingly
        if self.cursors[2]:
            x2, y2 = self.cursors["pos2"]
            self.cursors["text2"] = f"({utils.num2fstr(x2)}, {utils.num2fstr(y2)})"
        # Calculate differences and midpoints only if both cursors are present
        if self.cursors[1] and self.cursors[2]:
            delta_x = x2 - x1
            delta_y = y2 - y1
            midpoint_x = (x1 + x2) / 2
            midpoint_y = (y1 + y2) / 2
            self.cursors["diff"] = (
                f"({utils.num2fstr(delta_x)}, {utils.num2fstr(delta_y)})"
            )
            self.cursors["midpoint"] = (
                f"({utils.num2fstr(midpoint_x)}, {utils.num2fstr(midpoint_y)})"
            )
        self.updateCursorInfo()

    def updateCursorInfo(self):
        self.mda_mvc.findChild(QtWidgets.QLabel, "pos1_text").setText(
            self.cursors["text1"]
        )
        self.mda_mvc.findChild(QtWidgets.QLabel, "pos2_text").setText(
            self.cursors["text2"]
        )
        self.mda_mvc.findChild(QtWidgets.QLabel, "diff_text").setText(
            self.cursors["diff"]
        )
        self.mda_mvc.findChild(QtWidgets.QLabel, "midpoint_text").setText(
            self.cursors["midpoint"]
        )

    def clearCursorInfo(self):
        self.mda_mvc.findChild(QtWidgets.QLabel, "pos1_text").setText("middle click")
        self.mda_mvc.findChild(QtWidgets.QLabel, "pos2_text").setText("right click")
        self.mda_mvc.findChild(QtWidgets.QLabel, "diff_text").setText("n/a")
        self.mda_mvc.findChild(QtWidgets.QLabel, "midpoint_text").setText("n/a")
