"""
Charting widget
"""

import datetime
from functools import partial
from itertools import cycle
from typing import Optional
import numpy
from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import QObject, QTimer, Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy, QApplication
from mdaviz import utils
from mdaviz.fit_manager import FitManager
from mdaviz.user_settings import settings

from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar


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


class ChartView(QWidget):
    """TODO: docstrings"""

    # Fit signals for main window connection
    fitAdded = pyqtSignal(str, str)  # curveID, fitID
    fitUpdated = pyqtSignal(str, str)  # curveID, fitID
    fitRemoved = pyqtSignal(str, str)  # curveID, fitID

    def __init__(self, parent, **kwargs):
        # parent=<mdaviz.mda_folder.MDA_MVC object at 0x10e7ff520>
        self.mda_mvc = parent
        super().__init__()

        # Initialize log scale attributes
        self._log_x = False
        self._log_y = False

        ############# UI initialization:

        # Set size policy to prevent unwanted expansion
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Get maximum height from user settings with default fallback
        max_height = settings.getKey("plot_max_height")
        try:
            max_height = int(max_height)
        except (TypeError, ValueError):
            max_height = 800  # Default value
            settings.setKey("plot_max_height", max_height)

        # Set minimum and maximum height to constrain vertical growth
        self.setMinimumHeight(200)  # Minimum reasonable height
        self.setMaximumHeight(max_height)  # Configurable maximum height

        # Create a Matplotlib figure and canvas
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.main_axes = self.figure.add_subplot(111)
        # Adjust margins
        self.figure.subplots_adjust(bottom=0.1, top=0.9, right=0.92)

        # Set size constraints on the canvas to prevent vertical expansion
        canvas_max_height = max_height - 50  # Leave room for toolbar
        self.canvas.setMaximumHeight(canvas_max_height)
        self.canvas.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )

        # Create the navigation toolbar
        self.toolbar = NavigationToolbar(self.canvas, self)

        # Use a QVBoxLayout for stacking the toolbar and canvas vertically
        layout = QVBoxLayout(self)
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
        self.fitObjects = {}  # all the fit Line2D on the graph, key = curveID
        self.curveBox = self.mda_mvc.mda_file_viz.curveBox
        self.curveBox.currentIndexChanged.connect(self.onCurveSelected)

        # Initialize CurveManager
        self.curveManager = CurveManager(self)
        self.curveManager.curveAdded.connect(self.onCurveAdded)
        self.curveManager.curveUpdated.connect(self.onCurveUpdated)
        self.curveManager.curveRemoved.connect(self.onCurveRemoved)
        self.curveManager.allCurvesRemoved.connect(self.onAllCurvesRemoved)

        # Initialize FitManager
        self.fitManager = FitManager(self)
        self.fitManager.fitAdded.connect(self.onFitAdded)
        self.fitManager.fitUpdated.connect(self.onFitUpdated)
        self.fitManager.fitRemoved.connect(self.onFitRemoved)
        self.fitManager.fitVisibilityChanged.connect(self.onFitVisibilityChanged)
        # # Debug signals:
        # self.curveManager.curveAdded.connect(utils.debug_signal)
        # self.curveManager.curveRemoved.connect(utils.debug_signal)
        # self.curveManager.curveUpdated.connect(utils.debug_signal)
        # self.curveManager.allCurvesRemoved.connect(utils.debug_signal)

        # Remove buttons definitions:
        self.clearAll = self.mda_mvc.mda_file_viz.clearAll
        self.removeButton = self.mda_mvc.mda_file_viz.curveRemove
        self.removeCursor1 = self.mda_mvc.mda_file_viz.cursor1_remove
        self.removeCursor2 = self.mda_mvc.mda_file_viz.cursor2_remove

        # Remove button connections:
        utils.reconnect(self.clearAll.clicked, self.curveManager.allCurvesRemoved)
        utils.reconnect(self.removeButton.clicked, self.onRemoveButtonClicked)
        self.removeCursor1.clicked.connect(partial(self.onRemoveCursor, cursor_num=1))
        self.removeCursor2.clicked.connect(partial(self.onRemoveCursor, cursor_num=2))

        # File tableview & graph synchronization:
        self.mda_mvc.mda_file.tabManager.tabRemoved.connect(self.onTabRemoved)
        self.mda_mvc.detRemoved.connect(self.onDetRemoved)
        # self.mda_mvc.detRemoved.connect(utils.debug_signal)

        # Connect offset & factor QLineEdit:
        self.offset_value = self.mda_mvc.mda_file_viz.offset_value
        self.factor_value = self.mda_mvc.mda_file_viz.factor_value
        self.offset_value.editingFinished.connect(self.onOffsetUpdated)
        self.factor_value.editingFinished.connect(self.onFactorUpdated)

        # Connect the click event to a handler
        self.cid = self.figure.canvas.mpl_connect("button_press_event", self.onclick)
        self.alt_pressed = False

        # Set up a timer to check modifier key state
        self.key_check_timer = QTimer()
        self.key_check_timer.timeout.connect(self.check_modifier_keys)
        self.key_check_timer.start(50)  # Check every 50ms

        self.cursors = {
            1: None,
            "pos1": None,
            "text1": "middle click or alt+right click",
            2: None,
            "pos2": None,
            "text2": "right click",
            "diff": "n/a",
            "midpoint": "n/a",
        }

    def check_modifier_keys(self):
        """Check for modifier keys using Qt's global state."""
        try:
            # Get the global keyboard state
            modifiers = QApplication.keyboardModifiers()
            self.alt_pressed = modifiers & Qt.KeyboardModifier.AltModifier
        except Exception:
            # Fallback if Qt method fails
            pass

    def closeEvent(self, event):
        """Clean up resources when the widget is closed."""
        if hasattr(self, "key_check_timer"):
            self.key_check_timer.stop()
        super().closeEvent(event)

    ########################################## Set & get methods:

    def setPlotTitle(self, txt=""):
        self.main_axes.set_title(txt, fontsize=FONTSIZE)

    def setBottomAxisText(self, text):
        self.main_axes.set_xlabel(text, fontsize=FONTSIZE, labelpad=10)

    def setLeftAxisText(self, text):
        self.main_axes.set_ylabel(text, fontsize=FONTSIZE, labelpad=20)

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

    def getSelectedCurveID(self):
        # Get the curve ID from the item data instead of display text
        current_index = self.curveBox.currentIndex()
        if current_index >= 0:
            curve_id = self.curveBox.itemData(
                current_index, QtCore.Qt.ItemDataRole.UserRole
            )

            # Check if the curve ID exists in the curve manager
            if curve_id in self.curveManager.curves():
                return curve_id
            else:
                # If curve_id is None or not found, return None
                return None
        return None

    def setMaximumPlotHeight(self, height: int):
        """
        Set the maximum height for the plot widget and save to user settings.

        Parameters:
        - height (int): Maximum height in pixels
        """
        if height < 200:
            height = 200  # Minimum reasonable height

        # Update the widget maximum height
        self.setMaximumHeight(height)

        # Update the canvas maximum height (leave room for toolbar)
        canvas_max_height = height - 50
        self.canvas.setMaximumHeight(canvas_max_height)

        # Save to user settings
        settings.setKey("plot_max_height", height)

        # Redraw the canvas
        self.canvas.draw()

    def setLogScales(self, log_x: bool, log_y: bool):
        """
        Set logarithmic scales for X and Y axes.

        Parameters:
        - log_x (bool): Whether to use logarithmic scale for X-axis
        - log_y (bool): Whether to use logarithmic scale for Y-axis
        """
        try:
            # Store the log scale state
            self._log_x = log_x
            self._log_y = log_y

            if log_x:
                self.main_axes.set_xscale("log")
            else:
                self.main_axes.set_xscale("linear")

            if log_y:
                self.main_axes.set_yscale("log")
            else:
                self.main_axes.set_yscale("linear")

            # Redraw the canvas to apply changes
            self.canvas.draw()
        except Exception as exc:
            print(f"Error setting log scales: {exc}")
            # If setting log scale fails (e.g., negative values), revert to linear
            self._log_x = False
            self._log_y = False
            self.main_axes.set_xscale("linear")
            self.main_axes.set_yscale("linear")
            self.canvas.draw()

    ########################################## Slot methods:

    def onCurveAdded(self, curveID):
        # Add to graph
        curveData = self.curveManager.getCurveData(curveID)
        ds = curveData["ds"]
        ds_options = curveData["ds_options"].copy()  # Copy to avoid modifying original

        # Apply the curve style
        style = curveData.get("style", "-")
        ds_options["linestyle"] = style

        # Handle marker styles
        if style.startswith("o"):
            ds_options["marker"] = "o"
            ds_options["linestyle"] = "-" if len(style) > 1 else ""
        elif style.startswith("s"):
            ds_options["marker"] = "s"
            ds_options["linestyle"] = "-" if len(style) > 1 else ""
        elif style.startswith("^"):
            ds_options["marker"] = "^"
            ds_options["linestyle"] = "-" if len(style) > 1 else ""
        elif style.startswith("D"):
            ds_options["marker"] = "D"
            ds_options["linestyle"] = "-" if len(style) > 1 else ""
        elif style == ".":
            ds_options["marker"] = "."
            ds_options["linestyle"] = ""
        else:
            ds_options["marker"] = ""

        # Apply offset and factor to the data
        factor = curveData.get("factor", 1)
        offset = curveData.get("offset", 0)
        style = curveData.get("style", "-")
        print(
            f"DEBUG: onCurveAdded - curve {curveID}: style={style}, offset={offset}, factor={factor}"
        )
        if factor != 1 or offset != 0:
            new_y = numpy.multiply(ds[1], factor) + offset
            ds = [ds[0], new_y]

        # Plot and store the plot object associated with curveID:
        try:
            plot_obj = self.main_axes.plot(*ds, **ds_options)[0]
            self.plotObjects[curveID] = plot_obj
        except Exception as exc:
            print(str(exc))
        # Update plot
        self.updatePlot(update_title=True)
        # Add to the comboBox
        index = self.curveBox.count()  # Get the next index
        # Use the user-friendly label for display, but store curveID as data
        display_label = curveData.get("ds_options", {}).get("label", curveID)
        self.curveBox.addItem(display_label)
        # Store the curveID as item data for later retrieval
        self.curveBox.setItemData(index, curveID, QtCore.Qt.ItemDataRole.UserRole)
        file_path = curveData.get("file_path", "No file path available")
        self.curveBox.setItemData(index, file_path, QtCore.Qt.ItemDataRole.ToolTipRole)
        # Only select the new curve if it's the first one
        if self.curveBox.count() == 1:
            self.curveBox.setCurrentIndex(0)
            # Manually trigger curve selection for the first curve
            self.onCurveSelected(0)

        # Update any existing combo box items to use new curve ID format
        self.updateComboBoxCurveIDs()

    def onCurveUpdated(self, curveID, recompute_y=False, update_x=False):
        print(
            f"DEBUG: onCurveUpdated called for {curveID}, recompute_y={recompute_y}, update_x={update_x}"
        )
        curve_data = self.curveManager.getCurveData(curveID)
        if curve_data and recompute_y:
            factor = curve_data.get("factor", 1)
            offset = curve_data.get("offset", 0)
            ds = curve_data["ds"]
            new_y = numpy.multiply(ds[1], factor) + offset
            if curveID in self.plotObjects:
                self.plotObjects[curveID].set_ydata(new_y)
        if curve_data and update_x:
            # For x-data updates, we need to recreate the plot object to maintain style
            if curveID in self.plotObjects:
                # Remove the old plot object
                old_plot_obj = self.plotObjects[curveID]
                old_plot_obj.remove()
                del self.plotObjects[curveID]

            # Recreate the plot object with proper style
            ds = curve_data["ds"]
            ds_options = curve_data["ds_options"].copy()

            # Apply the curve style
            style = curve_data.get("style", "-")
            ds_options["linestyle"] = style

            # Handle marker styles
            if style.startswith("o"):
                ds_options["marker"] = "o"
                ds_options["linestyle"] = "-" if len(style) > 1 else ""
            elif style.startswith("s"):
                ds_options["marker"] = "s"
                ds_options["linestyle"] = "-" if len(style) > 1 else ""
            elif style.startswith("^"):
                ds_options["marker"] = "^"
                ds_options["linestyle"] = "-" if len(style) > 1 else ""
            elif style.startswith("D"):
                ds_options["marker"] = "D"
                ds_options["linestyle"] = "-" if len(style) > 1 else ""
            elif style == ".":
                ds_options["marker"] = "."
                ds_options["linestyle"] = ""
            else:
                ds_options["marker"] = ""

            # Apply offset and factor
            factor = curve_data.get("factor", 1)
            offset = curve_data.get("offset", 0)
            if factor != 1 or offset != 0:
                new_y = numpy.multiply(ds[1], factor) + offset
                ds = [ds[0], new_y]

            # Create new plot object
            try:
                plot_obj = self.main_axes.plot(*ds, **ds_options)[0]
                self.plotObjects[curveID] = plot_obj
            except Exception as exc:
                print(str(exc))

        self.updatePlot(update_title=False)

    def onRemoveButtonClicked(self):
        curveID = self.getSelectedCurveID()
        if curveID in self.curveManager.curves():
            curveID = self.getSelectedCurveID()
        if curveID in self.curveManager.curves():
            if len(self.curveManager.curves()) == 1:
                self.curveManager.removeAllCurves(doNotClearCheckboxes=False)
            else:
                self.curveManager.removeCurve(curveID)

    def onCurveRemoved(self, *arg):
        curveID, curveData, count = arg
        # Remove curve from graph & plotObject dict
        if curveID in self.plotObjects:
            curve_obj = self.plotObjects[curveID]
            curve_obj.remove()
            del self.plotObjects[curveID]
        # Remove checkbox from corresponding tableview
        row = curveData["row"]
        file_path = curveData["file_path"]
        tableview = self.mda_mvc.mda_file.tabPath2Tableview(file_path)
        if tableview and tableview.tableView.model():
            tableview.tableView.model().uncheckCheckBox(row)
        # Remove curve from comboBox
        self.removeItemCurveBox(curveID)
        # Update plot labels, legend and title
        self.updatePlot(update_title=False)
        # If this was the last curve for this file, remove the tab
        if count == 0 and self.mda_mvc.mda_file.mode() == "Auto-add":
            self.mda_mvc.mda_file.tabManager.removeTab(file_path)

    def onAllCurvesRemoved(self, doNotClearCheckboxes=True):
        # Store current log scale state before clearing
        current_log_x = self._log_x
        current_log_y = self._log_y

        # Clears the plot completely, removing all curve representations.
        self.clearPlot()
        for curveID in self.curveManager.curves().keys():
            self.curveManager.removeCurve(curveID)
        if not doNotClearCheckboxes:
            # Iterates over each tab, accessing its associated tableview to clear all checkbox selections.
            for index in range(self.mda_mvc.mda_file.tabWidget.count()):
                tableview = self.mda_mvc.mda_file.tabIndex2Tableview(index)
                if tableview and tableview.tableView.model():
                    tableview.tableView.model().clearAllCheckboxes()
                    tableview.tableView.model().setHighlightRow()

        # Reapply log scale state after clearing
        self.setLogScales(current_log_x, current_log_y)

    def onDetRemoved(self, file_path, row):
        curveID = self.curveManager.findCurveID(file_path, row)
        if curveID:
            self.curveManager.removeCurve(curveID)

    def onTabRemoved(self, file_path):
        if self.mda_mvc.mda_file.mode() in ["Auto-add"]:
            for curveID in self.curveManager.curves().keys():
                if self.curveManager.curves()[curveID]["file_path"] == file_path:
                    self.curveManager.removeCurve(curveID)

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
        # Collect positioner PVs from all curves and update x label:
        x_label_set = set()
        for curveID in self.curveManager.curves():
            plot_options = self.curveManager.getCurveData(curveID).get("plot_options")
            x_label = plot_options.get("x", "")
            if x_label:
                x_label_set.add(x_label)
        self.setXlabel(", ".join(list(x_label_set)))

        # Simple y-axis label logic: match combo box text and add /I0 if I0 is toggled
        curveID = self.getSelectedCurveID()
        if curveID in self.curveManager.curves():
            self.updateBasicMathInfo(curveID)

            # Get the combo box text for the selected curve
            current_index = self.curveBox.currentIndex()
            if current_index >= 0:
                combo_text = self.curveBox.currentText()

                # Extract detector name from combo box text (remove file name)
                if ": " in combo_text:
                    detector_name = combo_text.split(": ", 1)[1]
                else:
                    detector_name = combo_text
                self.setYlabel(detector_name)
            else:
                self.setYlabel("")
        else:
            # No selected curve or curve not in manager, clear y-axis label
            self.setYlabel("")

        # Update title:
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
        # Clear axis labels
        self.setXlabel("")
        self.setYlabel("")
        self.clearCursors()
        self.clearCursorInfo()
        self.clearBasicMath()
        self.figure.canvas.draw()
        self.plotObjects = {}
        self.curveBox.clear()

    def hasDataItems(self):
        # Return whether any artists have been added to the Axes (bool)
        return self.main_axes.has_data()

    ########################################## Interaction with UI elements:

    def onCurveSelected(self, index):
        # Get the curve ID from the combo box item data
        curveID = None
        if index >= 0:
            curveID = self.curveBox.itemData(index, QtCore.Qt.ItemDataRole.UserRole)

        # Update QLineEdit & QLabel widgets with the values for the selected curve
        if (
            curveID
            and curveID in self.plotObjects
            and curveID in self.curveManager.curves()
        ):
            curve_data = self.curveManager.getCurveData(curveID)
            file_path = curve_data["file_path"]
            row = curve_data["row"]
            self.offset_value.setText(str(curve_data["offset"]))
            self.factor_value.setText(str(curve_data["factor"]))
            self.curveBox.setToolTip(file_path)
            try:
                self.mda_mvc.mda_file.highlightRowInTab(file_path, row)
            except Exception as exc:
                print(str(exc))
                print("highlightRowInTab failed; ignoring exception.")
        else:
            self.offset_value.setText("0")
            self.factor_value.setText("1")
            self.curveBox.setToolTip("Selected curve")

        # Update basic math info:
        self.updateBasicMathInfo(curveID)

        # Update fit UI
        self.updateFitUI(curveID)

        # Update plot labels (including y-axis label)
        self.updatePlot(update_title=False)

    def updateFitUI(self, curveID: str) -> None:
        """
        Update fit UI based on curve selection.

        Parameters:
        - curveID: ID of the selected curve
        """
        # Update fit controls state
        has_curve = curveID in self.curveManager.curves()
        self.mda_mvc.mda_file_viz.updateFitControls(has_curve)

        # Update fit list
        self.updateFitList(curveID)

        # Update curve style combo box to show current curve's style
        if has_curve:
            self.updateCurveStyleComboBox(curveID)

        # Clear fit details if no curve selected or if switching to a different curve
        if not has_curve:
            self.mda_mvc.mda_file_viz.fitDetails.clear()
        else:
            # Clear fit when switching to a different curve
            current_fitted_curve = None
            for curve_id in self.curveManager.curves():
                if self.fitManager.hasFits(curve_id):
                    current_fitted_curve = curve_id
                    break

            # If we're switching to a different curve than the one with the fit, clear the fit
            if current_fitted_curve and current_fitted_curve != curveID:
                self.fitManager.removeFit(current_fitted_curve)
                self.mda_mvc.mda_file_viz.fitDetails.clear()

    def removeItemCurveBox(self, curveID):
        # Find the item by curve ID stored in item data
        for i in range(self.curveBox.count()):
            if self.curveBox.itemData(i, QtCore.Qt.ItemDataRole.UserRole) == curveID:
                self.curveBox.removeItem(i)
                break

    def updateComboBoxCurveIDs(self):
        """Update combo box items to use new curve ID format."""
        for i in range(self.curveBox.count()):
            old_curve_id = self.curveBox.itemData(i, QtCore.Qt.ItemDataRole.UserRole)
            display_text = self.curveBox.itemText(i)
            file_path = self.curveBox.itemData(i, QtCore.Qt.ItemDataRole.ToolTipRole)

            # Try to find the corresponding curve in the manager
            for curve_id, curve_data in self.curveManager.curves().items():
                if (
                    curve_data.get("file_path") == file_path
                    and curve_data.get("ds_options", {}).get("label") == display_text
                ):
                    # Found matching curve, update the combo box item
                    if old_curve_id != curve_id:
                        self.curveBox.setItemData(
                            i, curve_id, QtCore.Qt.ItemDataRole.UserRole
                        )
                    break

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
            try:
                curve_data = self.curveManager.getCurveData(curveID)
                x = curve_data["ds"][0]
                y = curve_data["ds"][1]
                stats = self.calculateBasicMath(x, y)
                for i, txt in zip(
                    stats, ["min_text", "max_text", "com_text", "mean_text"]
                ):
                    if isinstance(i, tuple):
                        result = f"({utils.num2fstr(i[0])}, {utils.num2fstr(i[1])})"
                    else:
                        result = f"{utils.num2fstr(i)}" if i else "n/a"
                    self.mda_mvc.findChild(QtWidgets.QLabel, txt).setText(result)
            except Exception as exc:
                print(str(exc))
                self.clearBasicMath()
        else:
            self.clearBasicMath()

    def clearBasicMath(self):
        for txt in ["min_text", "max_text", "com_text", "mean_text"]:
            self.mda_mvc.findChild(QtWidgets.QLabel, txt).setText("n/a")

    def calculateBasicMath(self, x_data, y_data):
        x_array = numpy.array(x_data, dtype=float)
        y_array = numpy.array(y_data, dtype=float)
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

    ########################################## Cursors methods:

    def onRemoveCursor(self, cursor_num):
        cross = self.cursors.get(cursor_num)
        if cross is not None:
            try:
                cross.remove()
            except (NotImplementedError, AttributeError):
                # Handle case where artist cannot be removed
                pass
            self.cursors[cursor_num] = None
            self.cursors[f"pos{cursor_num}"] = None
            self.cursors[f"text{cursor_num}"] = (
                "middle click or alt+right click" if cursor_num == 1 else "right click"
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

    def findNearestPoint(
        self, x_click: float, y_click: float
    ) -> Optional[tuple[float, float]]:
        """
        Find the nearest data point in the selected curve to the given click position.

        Parameters:
        - x_click: X coordinate of the click
        - y_click: Y coordinate of the click

        Returns:
        - Tuple of (x_nearest, y_nearest) if a curve is selected and has data, None otherwise
        """
        curveID = self.getSelectedCurveID()
        if not curveID or curveID not in self.curveManager.curves():
            return None

        curve_data = self.curveManager.getCurveData(curveID)
        if not curve_data:
            return None

        ds = curve_data.get("ds")
        if not ds or len(ds) < 2:
            return None

        x_data = ds[0]
        y_data = ds[1]

        # Ensure data are numpy arrays
        if not isinstance(x_data, numpy.ndarray):
            x_data = numpy.array(x_data, dtype=float)
        if not isinstance(y_data, numpy.ndarray):
            y_data = numpy.array(y_data, dtype=float)

        # Apply offset and factor to y_data to match what's displayed
        factor = curve_data.get("factor", 1)
        offset = curve_data.get("offset", 0)
        y_data = numpy.multiply(y_data, factor) + offset

        # Calculate distances to all points
        distances = numpy.sqrt((x_data - x_click) ** 2 + (y_data - y_click) ** 2)

        # Find the index of the nearest point
        nearest_index = numpy.argmin(distances)

        return (float(x_data[nearest_index]), float(y_data[nearest_index]))

    def onclick(self, event):
        # Check if the click was in the main_axes
        if event.inaxes is self.main_axes:
            # Find the nearest point in the selected curve
            nearest_point = self.findNearestPoint(event.xdata, event.ydata)

            if nearest_point is None:
                # No curve selected or no data available
                return

            x_nearest, y_nearest = nearest_point

            # Middle click or Alt+right click for red cursor (cursor 1)
            if event.button == MIDDLE_BUTTON or (
                event.button == RIGHT_BUTTON and self.alt_pressed
            ):
                if self.cursors[1] is not None:
                    try:
                        self.cursors[1].remove()  # Remove existing red cursor
                    except (NotImplementedError, AttributeError):
                        # Handle case where artist cannot be removed
                        pass
                (self.cursors[1],) = self.main_axes.plot(
                    x_nearest, y_nearest, "r+", markersize=15, linewidth=2
                )
                # Update cursor position to nearest point
                self.cursors["pos1"] = (x_nearest, y_nearest)

            # Right click (without Alt) for blue cursor (cursor 2)
            elif event.button == RIGHT_BUTTON and not self.alt_pressed:
                if self.cursors[2] is not None:
                    try:
                        self.cursors[2].remove()  # Remove existing blue cursor
                    except (NotImplementedError, AttributeError):
                        # Handle case where artist cannot be removed
                        pass
                (self.cursors[2],) = self.main_axes.plot(
                    x_nearest, y_nearest, "b+", markersize=15, linewidth=2
                )

                # Update cursor position to nearest point
                self.cursors["pos2"] = (x_nearest, y_nearest)

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
        self.mda_mvc.mda_file_viz.pos1_text.setText("middle click or alt+right click")
        self.mda_mvc.mda_file_viz.pos2_text.setText("right click")
        self.mda_mvc.mda_file_viz.diff_text.setText("n/a")
        self.mda_mvc.mda_file_viz.midpoint_text.setText("n/a")

    ########################################## Fit methods:

    def onFitAdded(self, curveID: str) -> None:
        """
        Handle when a new fit is added.

        Parameters:
        - curveID: ID of the curve that was fitted
        """
        # Get fit data and plot the fit curve
        fit_data = self.fitManager.getFitCurveData(curveID)
        if fit_data:
            x_fit, y_fit = fit_data
            # Plot fit curve with dashed line style and higher z-order to ensure it's on top
            fit_line = self.main_axes.plot(
                x_fit, y_fit, "--", alpha=0.8, linewidth=2, zorder=10
            )[0]
            self.fitObjects[curveID] = fit_line

            # Update plot
            self.updatePlot(update_title=False)

            # Update fit details display
            self.updateFitDetails(curveID)

            # Emit signal for main window
            self.fitAdded.emit(curveID, "single_fit")

    def onFitUpdated(self, curveID: str) -> None:
        """
        Handle when a fit is updated.

        Parameters:
        - curveID: ID of the curve
        """
        # Remove existing fit line if any
        if curveID in self.fitObjects:
            try:
                self.fitObjects[curveID].remove()
            except (NotImplementedError, AttributeError):
                # Handle case where artist cannot be removed
                pass
            del self.fitObjects[curveID]

        # Add new fit line
        fit_data = self.fitManager.getFitCurveData(curveID)
        if fit_data:
            x_fit, y_fit = fit_data
            # Plot fit curve with dashed line style and higher z-order to ensure it's on top
            fit_line = self.main_axes.plot(
                x_fit, y_fit, "--", alpha=0.8, linewidth=2, zorder=10
            )[0]
            self.fitObjects[curveID] = fit_line

            # Update plot
            self.updatePlot(update_title=False)

            # Update fit details display
            self.updateFitDetails(curveID)

            # Emit signal for main window
            self.fitUpdated.emit(curveID, "single_fit")

    def onFitRemoved(self, curveID: str) -> None:
        """
        Handle when a fit is removed.

        Parameters:
        - curveID: ID of the curve
        """
        # Remove fit line from plot
        if curveID in self.fitObjects:
            try:
                self.fitObjects[curveID].remove()
            except (NotImplementedError, AttributeError):
                # Handle case where artist cannot be removed
                pass
            del self.fitObjects[curveID]

            # Update plot
            self.updatePlot(update_title=False)

            # Clear fit details display
            self.mda_mvc.mda_file_viz.fitDetails.clear()

            # Emit signal for main window
            self.fitRemoved.emit(curveID, "single_fit")

    def onFitVisibilityChanged(self, curveID: str, visible: bool) -> None:
        """
        Handle when fit visibility changes.

        Parameters:
        - curveID: ID of the curve
        - visible: Whether the fit should be visible
        """
        if curveID in self.fitObjects:
            self.fitObjects[curveID].set_visible(visible)
            self.canvas.draw()

    def updateFitList(self, curveID: str) -> None:
        """
        Update the fit list in the UI for a given curve.
        Note: This method is kept for compatibility but no longer needed with single-fit system.

        Parameters:
        - curveID: ID of the curve
        """
        # With single-fit system, we don't need a fit list
        # The fit details are shown directly when a fit exists
        pass

    def getCursorRange(self) -> Optional[tuple[float, float]]:
        """
        Get the range defined by cursors.

        Returns:
        - Tuple of (x_min, x_max) if both cursors are set, None otherwise
        """
        if "pos1" in self.cursors and "pos2" in self.cursors:
            if self.cursors["pos1"] is not None and self.cursors["pos2"] is not None:
                x1, y1 = self.cursors["pos1"]
                x2, y2 = self.cursors["pos2"]
                return (min(x1, x2), max(x1, x2))
        return None

    def performFit(self, model_name: str, use_range: bool = False) -> None:
        """
        Perform a fit on the currently selected curve.

        Parameters:
        - model_name: Name of the fit model to use
        - use_range: Whether to use cursor range for fitting
        """
        curveID = self.getSelectedCurveID()
        if not curveID or curveID not in self.curveManager.curves():
            return

        # Get curve data
        curve_data = self.curveManager.getCurveData(curveID)
        if not curve_data:
            return

        x_data = curve_data["ds"][0]
        y_data = curve_data["ds"][1]

        # Ensure data are numpy arrays with proper types
        if not isinstance(x_data, numpy.ndarray):
            x_data = numpy.array(x_data, dtype=float)
        if not isinstance(y_data, numpy.ndarray):
            y_data = numpy.array(y_data, dtype=float)

        # Check for valid data
        if len(x_data) == 0 or len(y_data) == 0:
            QtWidgets.QMessageBox.warning(
                self, "Fit Error", "No data available for fitting"
            )
            return

        if len(x_data) != len(y_data):
            QtWidgets.QMessageBox.warning(
                self, "Fit Error", "X and Y data have different lengths"
            )
            return

        # Apply offset and factor
        factor = curve_data.get("factor", 1)
        offset = curve_data.get("offset", 0)
        y_data = numpy.multiply(y_data, factor) + offset

        # Determine fit range
        x_range = None
        if use_range:
            x_range = self.getCursorRange()

        try:
            # Clear all existing fits from other curves before performing new fit
            all_curves = list(self.curveManager.curves().keys())
            for other_curve_id in all_curves:
                if other_curve_id != curveID and self.fitManager.hasFits(
                    other_curve_id
                ):
                    self.fitManager.removeFit(other_curve_id)

            # Perform the fit (this will replace any existing fit for the current curve)
            self.fitManager.addFit(curveID, model_name, x_data, y_data, x_range)

        except ValueError as e:
            # Show error message
            QtWidgets.QMessageBox.warning(self, "Fit Error", str(e))

    def updateFitDetails(self, curveID: str) -> None:
        """
        Update the fit details display.

        Parameters:
        - curveID: ID of the curve
        """
        fit_details = self.mda_mvc.mda_file_viz.fitDetails

        # Get fit data
        fit_data = self.fitManager.getFitData(curveID)
        if not fit_data:
            fit_details.clear()
            return

        # Format fit results
        result = fit_data.fit_result
        details_text = ""

        # Parameters
        details_text += "Parameters:\n"
        for param_name, param_value in result.parameters.items():
            details_text += f"  {param_name}: {utils.num2fstr(param_value)}\n"

        # Quality metrics
        details_text += "\nQuality Metrics:\n"
        details_text += f"  R²: {utils.num2fstr(result.r_squared)}\n"
        details_text += f"  χ²: {utils.num2fstr(result.chi_squared)}\n"
        details_text += f"  Reduced χ²: {utils.num2fstr(result.reduced_chi_squared)}\n"

        fit_details.setText(details_text)

    def clearAllFits(self) -> None:
        """Clear the fit from the currently selected curve."""
        curveID = self.getSelectedCurveID()
        if curveID:
            self.fitManager.removeFit(curveID)
            self.mda_mvc.mda_file_viz.fitDetails.clear()

    def updateCurveStyle(self, style_name: str) -> None:
        """
        Update the style of the currently selected curve.

        Parameters:
        - style_name: Name of the style to apply
        """
        curveID = self.getSelectedCurveID()
        if not curveID or curveID not in self.curveManager.curves():
            return

        # Get the matplotlib format string for the style
        style_map = self.mda_mvc.mda_file_viz.curve_styles
        if style_name not in style_map:
            return

        format_string = style_map[style_name]

        # Update the curve data with the new style
        curve_data = self.curveManager.getCurveData(curveID)
        if curve_data:
            old_style = curve_data.get("style", "-")
            print(
                f"DEBUG: Updating style for curve {curveID}: {old_style} -> {format_string}"
            )
            curve_data["style"] = format_string
            # Save to persistent storage
            persistent_key = (
                curve_data["file_path"],
                curve_data["row"],
                curve_data.get("x2_index"),
            )
            if persistent_key not in self.curveManager._persistent_properties:
                self.curveManager._persistent_properties[persistent_key] = {}
            self.curveManager._persistent_properties[persistent_key][
                "style"
            ] = format_string
            print(
                f"DEBUG: Saved style to persistent storage: {persistent_key} -> {format_string}"
            )
            self.curveManager.updateCurve(curveID, curve_data)

            # Update the plot object with the new style
            if curveID in self.plotObjects:
                plot_obj = self.plotObjects[curveID]

                # Handle different style types properly
                if format_string == ".":
                    # Points only - no line
                    plot_obj.set_linestyle("")
                    plot_obj.set_marker(".")
                elif format_string == "o":
                    # Markers only - no line
                    plot_obj.set_linestyle("")
                    plot_obj.set_marker("o")
                elif format_string.startswith("o"):
                    # Line with circle markers
                    plot_obj.set_linestyle("-")
                    plot_obj.set_marker("o")
                elif format_string.startswith("s"):
                    # Line with square markers
                    plot_obj.set_linestyle("-")
                    plot_obj.set_marker("s")
                elif format_string.startswith("^"):
                    # Line with triangle markers
                    plot_obj.set_linestyle("-")
                    plot_obj.set_marker("^")
                elif format_string.startswith("D"):
                    # Line with diamond markers
                    plot_obj.set_linestyle("-")
                    plot_obj.set_marker("D")
                else:
                    # Regular line styles
                    plot_obj.set_linestyle(format_string)
                    plot_obj.set_marker("")

                # Update the plot
                self.updatePlot(update_title=False)

    def updateCurveStyleComboBox(self, curveID: str) -> None:
        """
        Update the curve style combo box to show the current curve's style.

        Parameters:
        - curveID: ID of the curve
        """
        curve_data = self.curveManager.getCurveData(curveID)
        if not curve_data:
            return

        # Get the current style (default to "Line" if not set)
        current_style = curve_data.get("style", "-")

        # Find the style name that matches the format string
        style_map = self.mda_mvc.mda_file_viz.curve_styles
        style_name = "Line"  # Default

        for name, fmt in style_map.items():
            if fmt == current_style:
                style_name = name
                break

        # Update the combo box (block signals to avoid triggering style change)
        self.mda_mvc.mda_file_viz.curveStyle.blockSignals(True)
        self.mda_mvc.mda_file_viz.curveStyle.setCurrentText(style_name)
        self.mda_mvc.mda_file_viz.curveStyle.blockSignals(False)


# ------ Curves management (data):


class CurveManager(QObject):
    curveAdded = pyqtSignal(str)  # Emit curveID when a curve is added
    curveRemoved = pyqtSignal(str, dict, int)
    # Emit curveID & its corresponding data when a curve is removed, plus the
    # number of curves left on the graph for this file
    curveUpdated = pyqtSignal(
        str, bool, bool
    )  # Emit curveID, recompute_y (bool) & update_x (bool) when a curve is updated
    allCurvesRemoved = pyqtSignal(
        bool
    )  # Emit a doNotClearCheckboxes bool when all curve are removed

    def __init__(self, parent=None):
        super().__init__(parent)
        self._curves = {}  # Store curves with a unique identifier as the key
        # Persistent storage for curve properties across manager clears
        self._persistent_properties = (
            {}
        )  # key: (file_path, row), value: {style, offset, factor}

    def addCurve(self, row, *ds, **options):
        """Add a new curve to the manager if not already present on the graph."""
        # Extract info:
        plot_options = options.get("plot_options", {})
        ds_options = options.get("ds_options", {})
        label = ds_options.get("label", "unknown label")
        file_path = plot_options.get("filePath", "unknown path")
        x2_index = options.get("x2_index")  # Extract X2 index from options
        print(f"DEBUG: addCurve - Received x2_index: {x2_index}")
        # Generate unique curve ID & update options:
        curveID = self.generateCurveID(label, file_path, row, x2_index)
        ds_options["label"] = label  # Keep the original label for display purposes
        print(
            f"DEBUG: Adding curve with ID: {curveID}, label: {label}, file_path: {file_path}"
        )
        print(f"DEBUG: Current curves in manager: {list(self._curves.keys())}")
        x_data = ds[0]
        if curveID in self._curves:
            print(f"DEBUG: Curve {curveID} already exists")
            # Check if x_data is the same
            existing_x_data = self._curves[curveID]["ds"][0]
            existing_label = (
                self._curves[curveID].get("ds_options", {}).get("label", "")
            )

            # Update the curve if x_data is different OR if the label has changed (I0 normalization)
            if numpy.array_equal(x_data, existing_x_data) and label == existing_label:
                print(" x_data and label are the same, do not add or update the curve")
                # x_data and label are the same, do not add or update the curve
                return
            else:
                print(" x_data is different OR label has changed, update the curve")
                # x_data is different or label has changed, update the curve:
                # Get existing curve data and preserve all properties
                existing_curve_data = self._curves[curveID]
                print(
                    f"DEBUG: Existing style: {existing_curve_data.get('style')}, offset: {existing_curve_data.get('offset')}, factor: {existing_curve_data.get('factor')}"
                )
                existing_curve_data["ds"] = ds
                existing_curve_data["plot_options"] = plot_options
                existing_curve_data["ds_options"] = ds_options  # Update the label
                # Preserve existing style, offset, factor, and other properties
                self.updateCurve(curveID, existing_curve_data, recompute_y=True)
                return
        else:
            print(f"DEBUG: Curve {curveID} does NOT exist, creating new curve")
            # Check if this might be a re-creation after removeAllCurves was called
            # Look for any existing curve with the same file_path and row
            for existing_curve_id, existing_data in self._curves.items():
                if (
                    existing_data["file_path"] == file_path
                    and existing_data["row"] == row
                ):
                    print(
                        f"DEBUG: Found existing curve with same file_path and row: {existing_curve_id}"
                    )
                    print(
                        f"DEBUG: Transferring properties: style={existing_data.get('style')}, offset={existing_data.get('offset')}, factor={existing_data.get('factor')}"
                    )
                    # Transfer properties from existing curve
                    self._curves[curveID] = {
                        "ds": ds,  # ds = [x_data, y_data]
                        "offset": existing_data.get("offset", 0),  # preserve offset
                        "factor": existing_data.get("factor", 1),  # preserve factor
                        "style": existing_data.get("style", "-"),  # preserve style
                        "row": row,  # DET checkbox row in the file tableview
                        "file_path": file_path,
                        "file_name": plot_options.get("fileName", ""),  # without ext
                        "plot_options": plot_options,
                        "ds_options": ds_options,
                        "x2_index": x2_index,  # Store X2 index for 2D data
                    }
                    # Remove the old curve entry
                    del self._curves[existing_curve_id]
                    print(f"DEBUG: Transferred properties to new curve ID: {curveID}")
                    self.curveAdded.emit(curveID)
                    return
        # Add new curve if not already present on the graph:
        # Check for persistent properties first
        persistent_key = (file_path, row, x2_index)
        persistent_props = self._persistent_properties.get(persistent_key, {})

        self._curves[curveID] = {
            "ds": ds,  # ds = [x_data, y_data]
            "offset": persistent_props.get("offset", 0),  # restore offset
            "factor": persistent_props.get("factor", 1),  # restore factor
            "style": persistent_props.get("style", "-"),  # restore style
            "row": row,  # DET checkbox row in the file tableview
            "file_path": file_path,
            "file_name": plot_options.get("fileName", ""),  # without ext
            "plot_options": plot_options,
            "ds_options": ds_options,
            "x2_index": x2_index,  # Store X2 index for 2D data
        }
        print(
            f"DEBUG: Created curve {curveID} with persistent properties: {persistent_props}"
        )
        self.curveAdded.emit(curveID)

    def updateCurve(self, curveID, curveData, recompute_y=False, update_x=False):
        """Update an existing curve."""
        if curveID in self._curves:
            print(f"Emits curveUpdated {curveID=}, {recompute_y=}, {update_x=}")
            self._curves[curveID] = curveData
            self.curveUpdated.emit(curveID, recompute_y, update_x)

    def removeCurve(self, curveID):
        """Remove a curve from the manager."""
        if curveID in self._curves:
            curveData = self._curves[curveID]
            file_path = curveData["file_path"]
            # Remove curve entry from self.curves & emit signal:
            del self._curves[curveID]
            # How many curves are left for this file:
            count = 0
            for curve_data in self._curves.values():
                if curve_data["file_path"] == file_path:
                    count += 1
            # Emit signal:
            self.curveRemoved.emit(curveID, curveData, count)

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
                print(
                    f"DEBUG: Updating offset for curve {curveID}: {offset} -> {new_offset}"
                )
                curve_data["offset"] = new_offset
                # Save to persistent storage
                persistent_key = (
                    curve_data["file_path"],
                    curve_data["row"],
                    curve_data.get("x2_index"),
                )
                if persistent_key not in self._persistent_properties:
                    self._persistent_properties[persistent_key] = {}
                self._persistent_properties[persistent_key]["offset"] = new_offset
                print(
                    f"DEBUG: Saved offset to persistent storage: {persistent_key} -> {new_offset}"
                )
                self.updateCurve(curveID, curve_data, recompute_y=True)

    def updateCurveFactor(self, curveID, new_factor):
        curve_data = self.getCurveData(curveID)
        if curve_data:
            factor = curve_data["factor"]
            if factor != new_factor:
                print(
                    f"DEBUG: Updating factor for curve {curveID}: {factor} -> {new_factor}"
                )
                curve_data["factor"] = new_factor
                # Save to persistent storage
                persistent_key = (
                    curve_data["file_path"],
                    curve_data["row"],
                    curve_data.get("x2_index"),
                )
                if persistent_key not in self._persistent_properties:
                    self._persistent_properties[persistent_key] = {}
                self._persistent_properties[persistent_key]["factor"] = new_factor
                print(
                    f"DEBUG: Saved factor to persistent storage: {persistent_key} -> {new_factor}"
                )
                self.updateCurve(curveID, curve_data, recompute_y=True)

    def generateCurveID(self, label, file_path, row, x2_index=None):
        """
        Generates a unique curve ID based on file_path, row, and X2 index, ensuring the same detector
        always gets the same curve ID regardless of I0 normalization.

        Parameters:
        - label (str): The original label for the curve (used for display purposes)
        - file_path (str): The file path associated with the curve
        - row (int): The row number in the file tableview associated with the curve
        - x2_index (int, optional): The X2 slice index for 2D data

        Returns:
        - str: A unique curve ID based on file_path, row, and X2 index
        """
        # Generate curve ID based on file_path, row, and X2 index
        if x2_index is not None:
            curve_id = f"{file_path}_{row}_x2_{x2_index}"
        else:
            curve_id = f"{file_path}_{row}"

        print(
            f"DEBUG: generateCurveID - x2_index={x2_index}, generated curve_id={curve_id}"
        )

        # Check if this curve ID already exists
        if curve_id in self._curves:
            # If it exists, return the existing curve ID (this should not happen in normal usage)
            return curve_id
        else:
            return curve_id

    def findCurveID(self, file_path, row, x2_index=None):
        """
        Find the curveID based on the file path, row number, and X2 index.

        Parameters:
        - file_path (str): The path of the file associated with the curve.
        - row (int): The row number in the file tableview associated with the curve.
        - x2_index (int, optional): The X2 slice index for 2D data.

        Returns:
        - str: The curveID if a matching curve is found; otherwise, None.
        """
        for curveID, curveData in self._curves.items():
            if (
                curveData["file_path"] == file_path
                and curveData["row"] == row
                and curveData.get("x2_index") == x2_index
            ):
                return curveID
        return None
