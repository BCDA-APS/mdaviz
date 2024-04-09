"""
Charting widget
"""

import datetime
from functools import partial
from itertools import cycle
import numpy
from PyQt5 import QtCore, QtWidgets
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

        ############# UI initialization:

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

        # Plot configuration
        plot_options = kwargs.get("plot_options", {})
        self.setTitle(plot_options.get("title", ""))
        self.setXlabel(plot_options.get("y", ""))
        self.setYlabel(plot_options.get("x", ""))
        self.configPlot()

        ############# Signals & slots:

        # Track curves and display in QComboBox:
        self.plotObjects = {}  # all the Line2D on the graph, key = curveID
        self.curveBox = self.mda_mvc.mda_file_viz.curveBox
        self.curveBox.currentTextChanged.connect(self.onCurveSelected)

        # Initialize CurveManager
        self.curveManager = CurveManager(self)
        self.curveManager.curveAdded.connect(self.onCurveAdded)
        self.curveManager.curveUpdated.connect(self.onCurveUpdated)
        self.curveManager.curveRemoved.connect(self.onCurveRemoved)
        self.curveManager.allCurvesRemoved.connect(self.onAllCurvesRemoved)

        self.curveManager.curveAdded.connect(utils.debug_signal)
        self.curveManager.curveRemoved.connect(utils.debug_signal)
        self.curveManager.curveUpdated.connect(utils.debug_signal)
        self.curveManager.allCurvesRemoved.connect(utils.debug_signal)

        # Remove buttons definitions:
        self.clearAll = self.mda_mvc.mda_file_viz.clearAll
        self.removeButton = self.mda_mvc.mda_file_viz.curveRemove
        self.removeCursor1 = self.mda_mvc.mda_file_viz.cursor1_remove
        self.removeCursor2 = self.mda_mvc.mda_file_viz.cursor2_remove
        # Remove buttons connections:
        utils.reconnect(self.clearAll.clicked, self.curveManager.allCurvesRemoved)
        utils.reconnect(self.removeButton.clicked, self.onRemoveButtonClicked)
        self.removeCursor1.clicked.connect(partial(self.onRemoveCursor, cursor_num=1))
        self.removeCursor2.clicked.connect(partial(self.onRemoveCursor, cursor_num=2))

        # Connect offset & factor QLineEdit:
        self.offset_value = self.mda_mvc.mda_file_viz.offset_value
        self.factor_value = self.mda_mvc.mda_file_viz.factor_value
        self.offset_value.editingFinished.connect(self.onOffsetUpdated)
        self.factor_value.editingFinished.connect(self.onFactorUpdated)

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

    ########################################## Set & get methods:

    def setPlotTitle(self, text):
        self.main_axes.set_title(text, fontsize=FONTSIZE, y=1.03)

    def setBottomAxisText(self, text):
        self.main_axes.set_xlabel(text, fontsize=FONTSIZE, labelpad=10)

    def setLeftAxisText(self, text):
        self.main_axes.set_ylabel(text, fontsize=FONTSIZE, labelpad=20)

    def setPathLabelText(self, text):
        self.mda_mvc.mda_file_viz.filePath_viz.setText(text)

    def title(self):
        return self._title

    def xlabel(self):
        return self._xlabel

    def ylabel(self):
        return self._ylabel

    def setTitle(self, txt=""):
        self._title = txt

    def setXlabel(self, txt=""):
        self._xlabel = txt

    def setYlabel(self, txt=""):
        self._ylabel = txt

    def getFullPath(self, path, file):
        return f"{path}/{file}.mda"

    def getSelectedCurveID(self):
        return self.curveBox.currentText()

    ########################################## Slot methods:

    def onCurveAdded(self, curveID):
        # Add to graph
        curveData = self.curveManager.getCurveData(curveID)
        ds = curveData["ds"]
        ds_options = curveData["ds_options"]
        # Plot and store the plot object associated with curveID:
        plot_obj = self.main_axes.plot(*ds, **ds_options)[0]
        self.plotObjects[curveID] = plot_obj
        # Update plot
        self.updatePlot(update_title=True)
        # Add to the comboBox
        self.curveBox.addItem(curveID)

    def onCurveUpdated(self, curveID, recompute_y=False):
        curve_data = self.curveManager.getCurveData(curveID)
        if curve_data and recompute_y:
            factor = curve_data.get("factor", 1)
            offset = curve_data.get("offset", 0)
            ds = curve_data["ds"]
            new_y = numpy.multiply(ds[1], factor) + offset
            if curveID in self.plotObjects:
                self.plotObjects[curveID].set_ydata(new_y)
        self.updatePlot(update_title=False)

    def onRemoveButtonClicked(self):
        curveID = self.getSelectedCurveID()
        if curveID in self.curveManager.curves():
            if len(self.curveManager.curves()) == 1:
                self.curveManager.removeAllCurves(doNotClearCheckboxes=False)
            else:
                self.curveManager.removeCurve(curveID)

    def onCurveRemoved(self, curveID, curveData):
        # Remove curve from graph & plotObject dict
        if curveID in self.plotObjects:
            curve_obj = self.plotObjects[curveID]
            curve_obj.remove()
            del self.plotObjects[curveID]
        # Remove checkbox from corresponding tableview
        row = curveData["row"]
        path = curveData["path"]
        file = curveData["file"]
        full_path = self.getFullPath(path, file)
        tableview = self.mda_mvc.mda_file.tabPath2Tableview(full_path)
        if tableview and tableview.tableView.model():
            tableview.tableView.model().uncheckCheckBox(row)
        # Remove curve from comboBox
        self.removeItemCurveBox(curveID)
        # Update plot labels, legend and title
        self.updatePlot(update_title=False)

    def onAllCurvesRemoved(self, doNotClearCheckboxes=True):
        # Clears the plot completely, removing all curve representations.
        self.clearPlot()
        if not doNotClearCheckboxes:
            # Iterates over each tab, accessing its associated tableview to clear all checkbox selections.
            for index in range(self.mda_mvc.mda_file.tabWidget.count()):
                tableview = self.mda_mvc.mda_file.tabIndex2Tableview(index)
                if tableview and tableview.tableView.model():
                    tableview.tableView.model().clearAllCheckboxes()

    ########################################## UI methods:

    def plot(self, row, *ds, **options):
        """The main method called by MDA_MVC"""
        self.main_axes.axis("on")
        self.curveManager.addCurve(row, *ds, **options)

    def configPlot(self, grid=True):
        self.setLeftAxisText(self.ylabel())
        self.setBottomAxisText(self.xlabel())
        self.setPlotTitle(self.title())
        if grid:
            self.main_axes.grid(True, color="#cccccc", linestyle="-", linewidth=0.5)
        else:
            self.main_axes.grid(False)
        self.canvas.draw()

    def updatePlot(self, update_title=True):
        # Update labels and title:
        curveID = self.getSelectedCurveID()
        if curveID in self.curveManager.curves():
            self.updateBasicMathInfo(curveID)
            plot_options = self.curveManager.getCurveData(curveID).get("plot_options")
            if plot_options:
                self.setXlabel(plot_options.get("x", ""))
                self.setYlabel(plot_options.get("y", ""))
        if update_title:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.setTitle(f"Plot Date & Time: {now}")
        # Recompute the axes limits and autoscale:
        self.main_axes.relim()
        self.main_axes.autoscale_view()
        self.updateLegend()
        self.configPlot()
        self.canvas.draw()

    def updateLegend(self):
        labels = self.main_axes.get_legend_handles_labels()[1]
        valid_labels = [label for label in labels if not label.startswith("_")]
        if valid_labels:
            self.main_axes.legend()

    def clearPlot(self):
        self.main_axes.clear()
        self.main_axes.axis("off")
        self.main_axes.set_title("")
        self.clearCursors()
        self.clearCursorInfo()
        self.clearBasicMath()
        self.figure.canvas.draw()
        self.plotObjects = {}
        self.curveBox.clear()

    ########################################## Interaction with UI elements:

    def onCurveSelected(self, curveID):
        # Update QLineEdit & QLabel widgets with the values for the selected curve
        if curveID in self.plotObjects and curveID in self.curveManager.curves():
            curve_data = self.curveManager.getCurveData(curveID)
            self.offset_value.setText(str(curve_data["offset"]))
            self.factor_value.setText(str(curve_data["factor"]))
            self.setPathLabelText(curve_data["path"])
        else:
            self.offset_value.setText("0")
            self.factor_value.setText("1")
            self.setPathLabelText("")
        # Update basic math info:
        self.updateBasicMathInfo(curveID)

    def removeItemCurveBox(self, curveID):
        # Returns the index of the item containing the given text ; otherwise returns -1.
        i = self.curveBox.findText(curveID)
        if i >= 0:
            self.curveBox.removeItem(i)

    def onOffsetUpdated(self):
        curveID = self.getSelectedCurveID()
        try:
            offset = float(self.offset_value.text())
        except ValueError:
            offset = 0
            # Reset to default if conversion fails
            self.offset_value.setText(str(offset))
            return
        self.curveManager.updateCurveOffset(curveID, offset)

    def onFactorUpdated(self):
        curveID = self.getSelectedCurveID()
        try:
            factor = float(self.factor_value.text())
        except ValueError:
            factor = 1
            # Reset to default if conversion fails or zero
            self.factor_value.setText(str(factor))
            return
        self.curveManager.updateCurveFactor(curveID, factor)

    ########################################## Basic maths methods:

    def updateBasicMathInfo(self, curveID):
        if curveID and curveID in self.curveManager.curves():
            curve_data = self.curveManager.getCurveData(curveID)
            x = curve_data["ds"][0]
            y = curve_data["ds"][1]
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

    # TODO: question: I do not think we use this - used for isPlotBlank that is not used
    # def hasDataItems(self):
    #     # Return whether any artists have been added to the Axes (bool)
    #     return self.main_axes.has_data()

    ########################################## Cursors methods:

    def onRemoveCursor(self, cursor_num):
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
        self.onRemoveCursor(1)
        self.onRemoveCursor(2)

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
        self.mda_mvc.mda_file_viz.pos1_text.setText(self.cursors["text1"])
        self.mda_mvc.mda_file_viz.pos2_text.setText(self.cursors["text2"])
        self.mda_mvc.mda_file_viz.diff_text.setText(self.cursors["diff"])
        self.mda_mvc.mda_file_viz.midpoint_text.setText(self.cursors["midpoint"])

    def clearCursorInfo(self):
        self.mda_mvc.mda_file_viz.pos1_text.setText("middle click")
        self.mda_mvc.mda_file_viz.pos2_text.setText("right click")
        self.mda_mvc.mda_file_viz.diff_text.setText("n/a")
        self.mda_mvc.mda_file_viz.midpoint_text.setText("n/a")


# ------ Curves management (data):


class CurveManager(QtCore.QObject):
    curveAdded = QtCore.pyqtSignal(str)  # Emit curveID when a curve is added
    curveRemoved = QtCore.pyqtSignal(
        str, dict
    )  # Emit curveID & its corresponding data when a curve is removed
    curveUpdated = QtCore.pyqtSignal(
        str, bool
    )  # Emit curveID and recompute_y (bool) when a curve is updated
    allCurvesRemoved = QtCore.pyqtSignal(
        bool
    )  # Emit a doNotClearCheckboxes bool when all curve are removed

    def __init__(self, parent=None):
        super().__init__(parent)
        self._curves = {}  # Store curves with a unique identifier as the key

    def addCurve(self, row, *ds, **options):
        """Add a new curve to the manager if not already present on the graph."""
        # Extract info:
        plot_options = options.get("plot_options", {})
        ds_options = options.get("ds_options", {})
        label = ds_options.get("label", "unknown label")
        path = plot_options.get("folderPath", "unknown path")
        # Generate unique label & update options:
        ds_options["label"] = curveID = self.generateCurveID(label, path)
        # Add new curve if not already present on the graph:
        if curveID not in self._curves:
            self._curves[curveID] = {
                "ds": ds,  # ds = [x_data, y_data]
                "offset": 0,  # default offset
                "factor": 1,  # default factor
                "row": row,  # checkbox row in the file tableview
                "path": plot_options.get("folderPath", "unknown path"),  # file path
                "file": plot_options.get("fileName", "unknown path"),  # without ext
                "plot_options": plot_options,
                "ds_options": ds_options,
            }
            self.curveAdded.emit(curveID)

    def updateCurve(self, curveID, curveData, recompute_y=False):
        """Update an existing curve."""
        if curveID in self._curves:
            self._curves[curveID] = curveData
            self.curveUpdated.emit(curveID, recompute_y)

    def removeCurve(self, curveID):
        """Remove a curve from the manager."""
        if curveID in self._curves:
            curveData = self._curves[curveID]
            del self._curves[curveID]
            self.curveRemoved.emit(curveID, curveData)

    def removeAllCurves(self, doNotClearCheckboxes=True):
        """Remove all curves from the manager."""
        self._curves.clear()
        self.allCurvesRemoved.emit(doNotClearCheckboxes)

    def getCurveData(self, curveID):
        """Get curve data by ID."""
        return self._curves.get(curveID, None)

    def curves(self):
        """Returns a read-only view of the currently managed curves."""
        return dict(self._curves)

    def updateCurveOffset(self, curveID, new_offset):
        curve_data = self.getCurveData(curveID)
        if curve_data:
            offset = curve_data["offset"]
            if offset != new_offset:
                curve_data["offset"] = new_offset
                self.updateCurve(curveID, curve_data, recompute_y=True)

    def updateCurveFactor(self, curveID, new_factor):
        curve_data = self.getCurveData(curveID)
        if curve_data:
            factor = curve_data["factor"]
            if factor != new_factor:
                curve_data["factor"] = new_factor
                self.updateCurve(curveID, curve_data, recompute_y=True)

    def generateCurveID(self, label, path):
        """
        Generates a unique curve label for a given label, considering the file path.

        Parameters:
        - label (str): The original label for the curve:
                "file_name: PV_name (PV_unit)" or "file_name: PV_name" (if no PV_unit)
        - path (str): The file path associated with the curve.

        Returns:
        - str: A unique curve label. If the exact label already exists for different file path,
        a numeric suffix is appended:
                "file_name: PV_name (PV_unit) (1)" or "file_name: PV_name (1)"

        Notes:
        - This method allows each curve to be uniquely identified and selected, even if their base
        labels are identical, by considering their file paths.
        """
        counter = 1
        original_label = label
        # Loop through existing labels:
        while True:
            # Check if the current label exists:
            if label in self._curves:
                existing_path = self._curves[label].get("path")
                if existing_path != path:
                    label = f"{original_label} ({counter})"
                    counter += 1
                else:
                    break  # If path is equal, then the curve is already on the graph.
            else:
                break  # If the label doesn't exist already, it's automatically unique.
        return label
