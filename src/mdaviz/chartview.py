"""
Charting and visualization module for MDA data analysis.

.. Summary::
    This module provides comprehensive plotting capabilities for 1D and 2D scientific data
    from MDA files. It includes interactive plotting widgets,
    curve management, fitting capabilities, and cursor-based analysis tools.

Classes:
    ChartView: Main 1D plotting widget with interactive features
    CurveManager: Manages curve data, properties, and persistence
    ChartView2D: 2D plotting widget for heatmaps and contour plots

Key Features:
    - Interactive 1D and 2D plotting with Matplotlib backend
    - Curve management with persistent properties (style, offset, factor)
    - Real-time data fitting with multiple model support
    - Interactive cursors for data analysis
    - Logarithmic scale support for both 1D and 2D plots
    - Legend management and curve selection
    - Integration with MDA file data structures

Dependencies:
    - PyQt6: GUI framework
    - Matplotlib: Plotting backend
    - NumPy: Numerical computations
    - mdaviz.fit_manager: Curve fitting functionality
    - mdaviz.user_settings: User preferences management

Usage:
    The ChartView widgets are typically instantiated by the main application
    and integrated into the MDA data visualization workflow. They handle
    the display and interaction with scientific data plots.

.. autosummary::

    ~ChartView
    ~ChartView2D
    ~CurveManager
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
from mdaviz.logger import get_logger

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


# Initialize logger for this module
logger = get_logger("chartview")


class ChartView(QWidget):
    """
    Main 1D plotting widget for MDA data visualization.

    This widget provides interactive plotting capabilities for 1D MDA data
    with features including curve management, data fitting, cursor analysis,
    and real-time data manipulation.

    Attributes:
        mda_mvc: Reference to the parent MDA MVC object
        figure: Matplotlib Figure object
        canvas: Matplotlib canvas for Qt integration
        main_axes: Primary matplotlib axes for plotting
        toolbar: Navigation toolbar for plot interactions
        plotObjects: Dictionary mapping curve IDs to plot objects
        fitObjects: Dictionary mapping curve IDs to fit plot objects
        curveManager: CurveManager instance for data management
        fitManager: FitManager instance for curve fitting
        cursors: Dictionary storing cursor positions and information

    Signals:
        fitAdded: Emitted when a fit is added (curveID, fitID)
        fitUpdated: Emitted when a fit is updated (curveID, fitID)
        fitRemoved: Emitted when a fit is removed (curveID, fitID)

    Key Features:
        - Interactive plotting with Matplotlib backend
        - Curve selection and management via combo box
        - Real-time offset and factor adjustments
        - Interactive cursors for data analysis
        - Logarithmic scale support
        - Curve style customization
        - Integration with MDA file data structures
        - Persistent curve properties across sessions

    .. autosummary::

        ~ChartView.calculateCursors
        ~ChartView.clearAllFits
        ~ChartView.clearCursors
        ~ChartView.clearPlot
        ~ChartView.closeEvent
        ~ChartView.configPlot
        ~ChartView.getCursorRange
        ~ChartView.getSelectedCurveID
        ~ChartView.hasDataItems
        ~ChartView.performFit
        ~ChartView.plot
        ~ChartView.setBottomAxisText
        ~ChartView.setLeftAxisText
        ~ChartView.setLogScales
        ~ChartView.setMaximumPlotHeight
        ~ChartView.setPlotTitle
        ~ChartView.setTitle
        ~ChartView.setXlabel
        ~ChartView.setYlabel
        ~ChartView.title
        ~ChartView.updateCurveStyle
        ~ChartView.updateLegend
        ~ChartView.updatePlot
        ~ChartView.xlabel
        ~ChartView.ylabel
    """

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
        """
        Get the ID of the currently selected curve from the combo box.

        This method retrieves the curve ID that corresponds to the currently
        selected item in the curve selection combo box. It uses the UserRole
        data stored with each combo box item rather than parsing the display text,
        ensuring reliable curve identification even when display labels change.

        Returns:
            str or None: The curve ID of the selected curve if valid, None otherwise.
                        Returns None if no item is selected or if the selected
                        curve ID is not found in the curve manager.

        Note:
            The curve ID is a unique identifier generated from the file path,
            row number, and X2 index (for 2D data). This method validates that
            the retrieved curve ID actually exists in the curve manager before
            returning it, ensuring data consistency.
        """
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
            logger.error(f"Error setting log scales: {exc}")
            # If setting log scale fails (e.g., negative values), revert to linear
            self._log_x = False
            self._log_y = False
            self.main_axes.set_xscale("linear")
            self.main_axes.set_yscale("linear")
            self.canvas.draw()

    ########################################## Slot methods:

    def onCurveAdded(self, curveID):
        """
        Handle the addition of a new curve to the plot.

        This slot method is called when a new curve is added to the curve manager.
        It performs the complete setup for displaying a curve on the plot, including
        data processing, styling, plotting, and UI updates.

        Parameters:
            curveID (str): The unique identifier of the curve to be added.

        Process:
            1. Retrieves curve data from the curve manager
            2. Applies curve styling (line style, markers) based on stored preferences
            3. Applies offset and factor transformations to the data
            4. Creates the matplotlib plot object and stores it for later reference
            5. Updates the plot display (axes, legend, title)
            6. Adds the curve to the combo box for user selection
            7. Sets up the first curve as selected if it's the only curve
            8. Updates existing combo box items to maintain consistency

        Styling Support:
            - Line styles: "-", "--", ":", "-."
            - Markers: "o" (circles), "s" (squares), "^" (triangles), "D" (diamonds), "." (points)
            - Combined styles: "o-" (line with circles), "s--" (dashed line with squares), etc.

        Data Transformations:
            - Applies factor multiplication: y_new = y * factor
            - Applies offset addition: y_new = y + offset
            - These transformations are applied before plotting

        UI Integration:
            - Adds curve to combo box with display label and tooltip
            - Stores curve ID as UserRole data for reliable identification
            - Automatically selects the first curve added
            - Updates plot title and legend
        """
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
        logger.debug(
            f"onCurveAdded - curve {curveID}: style={style}, offset={offset}, factor={factor}"
        )
        if factor != 1 or offset != 0:
            new_y = numpy.multiply(ds[1], factor) + offset
            ds = [ds[0], new_y]

        # Plot and store the plot object associated with curveID:
        try:
            plot_obj = self.main_axes.plot(*ds, **ds_options)[0]
            self.plotObjects[curveID] = plot_obj
        except Exception as exc:
            logger.error(str(exc))
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
        """
        Handle updates to an existing curve on the plot.

        Parameters:
            curveID (str): The unique identifier of the curve to be updated.
            recompute_y (bool): If True, update Y-data with current offset/factor.
            update_x (bool): If True, recreate plot object for X-data changes.
        """
        logger.debug(
            f"onCurveUpdated called for {curveID}, recompute_y={recompute_y}, update_x={update_x}"
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
                logger.error(str(exc))

        self.updatePlot(update_title=False)

    def onRemoveButtonClicked(self):
        """
        Handle the remove button click event.

        Removes the currently selected curve from the plot. If it's the last curve,
        removes all curves and clears checkboxes.
        """
        curveID = self.getSelectedCurveID()
        if curveID in self.curveManager.curves():
            if len(self.curveManager.curves()) == 1:
                self.curveManager.removeAllCurves(doNotClearCheckboxes=False)
            else:
                self.curveManager.removeCurve(curveID)

    def onCurveRemoved(self, *arg):
        """
        Handle the removal of a curve from the plot.

        This slot method is called when a curve is removed from the curve manager.
        It performs cleanup operations including plot object removal, UI updates,
        and checkbox management based on data type.

        Parameters:
            *arg: Tuple containing (curveID, curveData, count)
                - curveID (str): The unique identifier of the removed curve
                - curveData (dict): The curve data dictionary
                - count (int): Number of curves remaining for the file

        Process:
            1. Removes the plot object from the matplotlib axes
            2. Manages checkbox state based on data type (1D vs 2D)
            3. Removes curve from the combo box selection
            4. Updates plot display (labels, legend)
            5. Removes file tab if no curves remain (Auto-add mode)

        Checkbox Logic:
            - 1D data: Always uncheck the detector checkbox
            - 2D data: Only uncheck if no curves remain for that detector
                       (allows multiple curves per detector for 2D data)

        UI Synchronization:
            - Updates combo box to remove the curve option
            - Updates plot labels and legend
            - Removes file tab if it was the last curve for that file
        """
        curveID, curveData, count = arg
        # Remove curve from graph & plotObject dict
        if curveID in self.plotObjects:
            curve_obj = self.plotObjects[curveID]
            curve_obj.remove()
            del self.plotObjects[curveID]

        # Check if we should uncheck the checkbox
        row = curveData["row"]
        file_path = curveData["file_path"]
        tableview = self.mda_mvc.mda_file.tabPath2Tableview(file_path)

        if tableview and tableview.tableView.model():
            # Get file info to check if this is 2D data
            file_info = tableview.mda_file.data()
            is_2d_data = file_info.get("isMultidimensional", False)

            if is_2d_data:
                # For 2D data, check if there are still other curves with the same file_path and row
                remaining_curves_for_det = 0
                for (
                    existing_curve_id,
                    existing_data,
                ) in self.curveManager.curves().items():
                    if (
                        existing_data["file_path"] == file_path
                        and existing_data["row"] == row
                    ):
                        remaining_curves_for_det += 1

                # Only uncheck if no curves remain for this detector
                if remaining_curves_for_det == 0:
                    tableview.tableView.model().uncheckCheckBox(row)
                    logger.debug(
                        f"Unchecked DET {row} - no curves remaining for this detector"
                    )
                else:
                    logger.debug(
                        f"Kept DET {row} checked - {remaining_curves_for_det} curves still exist for this detector"
                    )
            else:
                # For 1D data, always uncheck (original behavior)
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
                logger.error(str(exc))
                logger.error("highlightRowInTab failed; ignoring exception.")
        else:
            self.offset_value.setText("0")
            self.factor_value.setText("1")
            self.curveBox.setToolTip("Selected curve")

        # Update basic math info:
        self.updateBasicMathInfo(curveID)

        # Update plot controls
        has_curve = curveID in self.curveManager.curves()
        self.mda_mvc.mda_file_viz.updatePlotControls(has_curve)

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
                logger.error(str(exc))
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
    """
    Manages curve data, properties, and persistence for ChartView.

    This class handles the storage and management of curve data including
    plotting properties, persistent settings, and curve identification.
    It provides signals for curve lifecycle events and maintains
    persistent properties across plotting sessions.

    Attributes:
        _curves: Dictionary storing curve data with curve IDs as keys
        _persistent_properties: Dictionary for storing curve properties across sessions

    Signals:
        curveAdded: Emitted when a curve is added (curveID)
        curveRemoved: Emitted when a curve is removed (curveID, curveData, count)
        curveUpdated: Emitted when a curve is updated (curveID, recompute_y, update_x)
        allCurvesRemoved: Emitted when all curves are removed (doNotClearCheckboxes)

    Key Features:
        - Unique curve ID generation based on file path, row, and X2 index
        - Persistent storage of curve properties (style, offset, factor)
        - Curve data management with automatic property restoration
        - Integration with MDA file data structures
        - Support for 2D data with X2 index tracking

    .. autosummary::

        ~CurveManager.addCurve
        ~CurveManager.curves
        ~CurveManager.findCurveID
        ~CurveManager.generateCurveID
        ~CurveManager.getCurveData
        ~CurveManager.removeAllCurves
        ~CurveManager.removeCurve
        ~CurveManager.updateCurve
        ~CurveManager.updateCurveFactor
        ~CurveManager.updateCurveOffset
    """

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
        """Add a new curve to the manager if not already present on the graph.

        This method handles curve creation with automatic property restoration from
        persistent storage. It generates unique curve IDs and manages curve lifecycle.

        Parameters:
            row: The row number in the file tableview associated with the curve
            *ds: Dataset containing x_data and y_data arrays
            **options: Additional options including:
                plot_options: Plot metadata (filePath, fileName, title, x-axis label, y-axis label, x-axis unit, y-axis unit, i0_name, is_normalized, x2 index, x2-axis unit, x2-axis label, color palette)
                ds_options: Plotting options (label, line style, marker, etc.)
                x2_index: X2 slice index for 2D data (optional)

        Returns:
            None: Emits curveAdded signal when a new curve is successfully added
        """
        # Extract info:
        plot_options = options.get("plot_options", {})
        ds_options = options.get("ds_options", {})
        label = ds_options.get("label", "unknown label")
        file_path = plot_options.get("filePath", "unknown path")
        x2_index = options.get("x2_index")  # Extract X2 index from options
        logger.debug(f"addCurve - Received x2_index: {x2_index}")
        # Generate unique curve ID & update options:
        curveID = self.generateCurveID(label, file_path, row, x2_index)
        ds_options["label"] = label  # Keep the original label for display purposes
        logger.debug(
            f"Adding curve with ID: {curveID}, label: {label}, file_path: {file_path}"
        )
        logger.debug(f"Current curves in manager: {list(self._curves.keys())}")
        x_data = ds[0]
        if curveID in self._curves:
            logger.debug(f"Curve {curveID} already exists")
            # Check if x_data is the same
            existing_x_data = self._curves[curveID]["ds"][0]
            existing_label = (
                self._curves[curveID].get("ds_options", {}).get("label", "")
            )

            # Update the curve if x_data is different OR if the label has changed (I0 normalization)
            if numpy.array_equal(x_data, existing_x_data) and label == existing_label:
                logger.debug(
                    " x_data and label are the same, do not add or update the curve"
                )
                # x_data and label are the same, do not add or update the curve
                return
            else:
                logger.debug(
                    " x_data is different OR label has changed, update the curve"
                )
                # x_data is different or label has changed, update the curve:
                # Get existing curve data and preserve all properties
                existing_curve_data = self._curves[curveID]
                existing_curve_data["ds"] = ds
                existing_curve_data["plot_options"] = plot_options
                existing_curve_data["ds_options"] = ds_options  # Update the label
                # Preserve existing style, offset, factor, and other properties
                self.updateCurve(curveID, existing_curve_data, recompute_y=True)
                return
        else:
            logger.debug(f"Curve {curveID} does NOT exist, creating new curve")
            # Check if this might be a re-creation after removeAllCurves was called
            # Look for any existing curve with the same file_path, row, and x2_index
            for existing_curve_id, existing_data in self._curves.items():
                if (
                    existing_data["file_path"] == file_path
                    and existing_data["row"] == row
                    and existing_data.get("x2_index") == x2_index
                ):
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
                    logger.debug(f"Transferred properties to new curve ID: {curveID}")
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
        logger.debug(
            f"Created curve {curveID} with persistent properties: {persistent_props}"
        )
        self.curveAdded.emit(curveID)

    def updateCurve(self, curveID, curveData, recompute_y=False, update_x=False):
        """Update an existing curve.

        Parameters:
            curveID: The unique identifier of the curve to update
            curveData: Complete curve data dictionary containing ds, plot_options, ds_options, etc.
            recompute_y: If True, recalculate Y data with current offset/factor
            update_x: If True, update X data (requires plot object recreation)

        Returns:
            None: Emits curveUpdated signal when curve is successfully updated
        """
        if curveID in self._curves:
            logger.debug(f"Emits curveUpdated {curveID=}, {recompute_y=}, {update_x=}")
            self._curves[curveID] = curveData
            self.curveUpdated.emit(curveID, recompute_y, update_x)

    def removeCurve(self, curveID):
        """Remove a curve from the manager.

        Removes the specified curve from the internal storage and emits a signal
        with the curve data and count of remaining curves for the same file.

        Parameters:
            curveID: The unique identifier of the curve to remove

        Returns:
            None: Emits curveRemoved signal with curveID, curveData, and remaining count
        """
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
        """Remove all curves from the manager.

        Clears all curves from internal storage and emits a signal indicating
        whether checkboxes should be cleared in the UI.

        Parameters:
            doNotClearCheckboxes: If True, preserves checkbox states in the UI

        Returns:
            None: Emits allCurvesRemoved signal with doNotClearCheckboxes parameter
        """
        self._curves.clear()
        self.allCurvesRemoved.emit(doNotClearCheckboxes)

    def getCurveData(self, curveID):
        """Get curve data by ID.

        Retrieves the complete data dictionary for a specific curve including
        dataset, properties, and metadata.

        Parameters:
            curveID: The unique identifier of the curve

        Returns:
            dict or None: Complete curve data dictionary if found, None otherwise
        """
        return self._curves.get(curveID, None)

    def curves(self):
        """Returns a copy of the currently managed curves.

        Provides access to all curves currently stored in the manager by
        returning a copy of the internal dictionary to prevent direct
        modification of the manager's state.

        Returns:
            dict: Copy of the curves dictionary with curveID as keys
        """
        return dict(self._curves)

    def updateCurveOffset(self, curveID, new_offset):
        """Update the offset value for a specific curve.

        Updates the curve's offset value and saves it to persistent storage
        for restoration across sessions.

        Parameters:
            curveID: The unique identifier of the curve
            new_offset: The new offset value to apply to the curve

        Returns:
            None: Updates curve data and emits curveUpdated signal if changed
        """
        curve_data = self.getCurveData(curveID)
        if curve_data:
            offset = curve_data["offset"]
            if offset != new_offset:
                logger.debug(
                    f"Updating offset for curve {curveID}: {offset} -> {new_offset}"
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
                logger.debug(
                    f"Saved offset to persistent storage: {persistent_key} -> {new_offset}"
                )
                self.updateCurve(curveID, curve_data, recompute_y=True)

    def updateCurveFactor(self, curveID, new_factor):
        """Update the factor value for a specific curve.

        Updates the curve's factor value and saves it to persistent storage
        for restoration across sessions.

        Parameters:
            curveID: The unique identifier of the curve
            new_factor: The new factor value to apply to the curve

        Returns:
            None: Updates curve data and emits curveUpdated signal if changed
        """
        curve_data = self.getCurveData(curveID)
        if curve_data:
            factor = curve_data["factor"]
            if factor != new_factor:
                logger.debug(
                    f"Updating factor for curve {curveID}: {factor} -> {new_factor}"
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
                logger.debug(
                    f"Saved factor to persistent storage: {persistent_key} -> {new_factor}"
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

        logger.debug(f"generateCurveID - curve_id={curve_id}")

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


class ChartView2D(ChartView):
    """
    2D plotting widget for heatmaps and contour plots.

    Extends ChartView to provide 2D visualization capabilities for MDA data.
    Supports both heatmap and contour plot types with interactive features
    and color scale management.

    Attributes:
        _2d_data: Storage for 2D data arrays
        _plot_type: Current plot type ("heatmap" or "contour")
        _current_colorbar: Reference to the current colorbar object
        _log_y_2d: Boolean flag for logarithmic color scale

    Key Features:
        - Heatmap visualization using imshow
        - Contour plot visualization with customizable levels
        - Logarithmic color scale support
        - Automatic axis scaling and labeling
        - Color palette customization
        - Integration with MDA 2D data structures
        - Message display for empty plots

    Plot Types:
        - heatmap: 2D data displayed as a color-coded image
        - contour: 2D data displayed as filled contour lines

    .. autosummary::

        ~ChartView2D.plot2D
        ~ChartView2D.set_plot_type
        ~ChartView2D.get_plot_type
        ~ChartView2D.setLogScales2D
        ~ChartView2D.showMessage
        ~ChartView2D._plot_heatmap
        ~ChartView2D._plot_contour
        ~ChartView2D._set_2d_labels
    """

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._2d_data = None
        self._plot_type = "heatmap"  # "heatmap" or "contour"
        self._current_colorbar = None  # Store reference to current colorbar

    def plot2D(self, y_data, x_data, x2_data, plot_options=None):
        """
        Plot 2D data as heatmap or contour.

        Parameters:
            y_data: 2D array of detector data
            x_data: 1D array of X positioner data
            x2_data: 1D array of X2 positioner data
            plot_options: Dictionary containing plot options including color_palette
        """
        if plot_options is None:
            plot_options = {}

        logger.debug("ChartView2D.plot2D - Plotting 2D data")
        logger.debug(f"  Y data shape: {y_data.shape}")
        logger.debug(f"  X data shape: {x_data.shape}")
        logger.debug(f"  X2 data shape: {x2_data.shape}")
        logger.debug(f"  Plot type: {self._plot_type}")
        logger.debug(f"  Canvas exists: {self.canvas is not None}")
        logger.debug(f"  Main axes exists: {self.main_axes is not None}")

        # Clear the previous plot
        self.figure.clear()
        self.main_axes = self.figure.add_subplot(111)
        # Reset to default subplot parameters
        self.figure.subplots_adjust(bottom=0.1, top=0.9, right=0.92)

        # Get color palette from plot options
        color_palette = plot_options.get("color_palette", "viridis")

        # Validate color palette - ensure it's not empty and is a valid colormap
        if not color_palette or color_palette.strip() == "":
            color_palette = "viridis"

        # Create the 2D plot
        if self._plot_type == "heatmap":
            self._plot_heatmap(y_data, x_data, x2_data, plot_options, color_palette)
        elif self._plot_type == "contour":
            self._plot_contour(y_data, x_data, x2_data, plot_options, color_palette)
        else:
            logger.error(f"Unknown plot type: {self._plot_type}")
            return

        # Set labels and title
        self._set_2d_labels(plot_options)

        # Update the plot

        self.canvas.draw()

        # Force a repaint
        self.canvas.flush_events()

    def _plot_heatmap(self, y_data, x_data, x2_data, plot_options, color_palette):
        """Plot 2D data as heatmap using imshow.

        Creates a heatmap visualization of 2D data with automatic orientation
        correction and logarithmic scaling support.

        Parameters:
            y_data: 2D array of detector data
            x_data: 1D array of X positioner data
            x2_data: 1D array of X2 positioner data
            plot_options: Dictionary containing plot options and metadata
            color_palette: Matplotlib colormap name for the heatmap

        Returns:
            None: Updates the main axes with the heatmap plot
        """
        # Check if X2 data is in descending order (reverse scan direction)
        # If so, flip the Y data vertically to match the expected orientation
        if len(x2_data) > 1 and x2_data[0] > x2_data[-1]:
            y_data = y_data[::-1, :]  # Flip vertically

        # Create meshgrid for proper axis scaling
        X, Y = numpy.meshgrid(x_data, x2_data)

        # Apply log scale normalization if enabled
        norm = None
        if hasattr(self, "_log_y_2d") and self._log_y_2d:
            from matplotlib.colors import LogNorm

            # Use LogNorm for proper log color scaling
            norm = LogNorm(vmin=y_data.min(), vmax=y_data.max())

        # Plot heatmap
        im = self.main_axes.imshow(
            y_data,
            extent=[x_data.min(), x_data.max(), x2_data.min(), x2_data.max()],
            aspect="auto",
            origin="lower",
            cmap=color_palette,
            norm=norm,
        )

        # Add colorbar
        self._current_colorbar = self.figure.colorbar(
            im, ax=self.main_axes, label=plot_options.get("y_unit", "")
        )

    def _plot_contour(self, y_data, x_data, x2_data, plot_options, color_palette):
        """Plot 2D data as contour plot.

        Creates a filled contour plot visualization of 2D data with
        fixed levels (20) and logarithmic scaling support.

        Parameters:
            y_data: 2D array of detector data
            x_data: 1D array of X positioner data
            x2_data: 1D array of X2 positioner data
            plot_options: Dictionary containing plot options and metadata
            color_palette: Matplotlib colormap name for the contour plot

        Returns:
            None: Updates the main axes with the contour plot
        """
        # Create meshgrid for contour plotting
        X, Y = numpy.meshgrid(x_data, x2_data)

        # Apply log scale normalization if enabled
        norm = None
        levels = 20
        if hasattr(self, "_log_y_2d") and self._log_y_2d:
            # For contour plots with log scale, use LogNorm for color normalization
            vmin, vmax = y_data.min(), y_data.max()
            if vmin > 0:  # Only apply log if all values are positive
                from matplotlib.colors import LogNorm

                norm = LogNorm(vmin=vmin, vmax=vmax)

        # Plot contour
        contour = self.main_axes.contourf(
            X, Y, y_data, levels=levels, cmap=color_palette, norm=norm
        )

        # Add colorbar
        self._current_colorbar = self.figure.colorbar(
            contour, ax=self.main_axes, label=plot_options.get("y_unit", "")
        )

    def _set_2d_labels(self, plot_options):
        """Set axis labels and title for 2D plot.

        Configures the plot axes with appropriate labels and title based on
        the plot options metadata.

        Parameters:
            plot_options: Dictionary containing label and title information
                - x: X-axis label
                - x_unit: X-axis unit
                - x2: Y-axis label (X2 positioner)
                - x2_unit: Y-axis unit
                - title: Plot title

        Returns:
            None: Updates the main axes labels and title
        """
        # Set axis labels
        x_label = plot_options.get("x", "X")
        x_unit = plot_options.get("x_unit", "")
        x2_label = plot_options.get("x2", "X2")
        x2_unit = plot_options.get("x2_unit", "")

        if x_unit:
            self.main_axes.set_xlabel(f"{x_label} ({x_unit})")
        else:
            self.main_axes.set_xlabel(x_label)

        if x2_unit:
            self.main_axes.set_ylabel(f"{x2_label} ({x2_unit})")
        else:
            self.main_axes.set_ylabel(x2_label)

        # Set title
        title = plot_options.get("title", "2D Plot")
        self.main_axes.set_title(title)

    def set_plot_type(self, plot_type):
        """Set the type of 2D plot (heatmap or contour).

        Parameters:
            plot_type: String specifying the plot type

        Returns:
            None: Updates the internal plot type setting
        """
        if plot_type in ["heatmap", "contour"]:
            self._plot_type = plot_type

        else:
            logger.error(
                f"Invalid plot type: {plot_type}. Must be 'heatmap' or 'contour'"
            )

    def get_plot_type(self):
        """Get the current plot type.

        Retrieves the currently configured 2D plot visualization type.

        Returns:
            str: Current plot type ("heatmap" or "contour")
        """
        return self._plot_type

    def setLogScales2D(self, log_y: bool):
        """
        Set logarithmic scale for 2D plots (Y-axis color scale).

        Parameters:
        - log_y (bool): Whether to use logarithmic scale for Y-axis (color scale)
        """
        try:
            # Store the log scale state
            self._log_y_2d = log_y

            # For 2D plots, log_y affects the color scale normalization
            # This would need to be handled in the plotting methods
            # For now, we'll store the state for potential future use
            self._log_y_2d = log_y

            # Redraw the canvas to apply changes
            self.canvas.draw()

        except Exception as exc:
            logger.error(f"Error setting 2D log scales: {exc}")
            # If setting log scale fails (e.g., negative values), revert to linear
            self._log_y_2d = False
            self.canvas.draw()

    def showMessage(self, message: str):
        """
        Display a message in the 2D plot area when there's nothing to plot.

        Parameters:
            message (str): The message to display
        """
        # Clear the previous plot
        self.figure.clear()
        self.main_axes = self.figure.add_subplot(111)

        # Remove all axes elements and show only the message
        self.main_axes.set_xticks([])
        self.main_axes.set_yticks([])
        self.main_axes.set_frame_on(False)

        # Add the message text
        self.main_axes.text(
            0.5,
            0.5,
            message,
            horizontalalignment="center",
            verticalalignment="center",
            transform=self.main_axes.transAxes,
            fontsize=16,
            color="#666666",
            bbox=dict(
                boxstyle="round,pad=0.5",
                facecolor="#f5f5f5",
                edgecolor="#cccccc",
                alpha=0.8,
            ),
        )

        # Update the plot
        self.canvas.draw()
        logger.debug(f"ChartView2D.showMessage - Displayed message: {message}")
