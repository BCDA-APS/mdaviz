"""
Charting and visualization module for MDA data analysis.

.. Summary::
    This module provides comprehensive plotting capabilities for 1D and 2D scientific data
    from MDA files. It includes interactive plotting widgets,
    curve management, fitting capabilities, and cursor-based analysis tools.

Classes:
    ChartView: Main 1D plotting widget with interactive features
    ChartView2D: 2D plotting widget for heatmaps and contour plots

Key Features:
    - Interactive 1D and 2D plotting with Matplotlib backend
    - Curve management with persistent style properties
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

"""

import datetime
from functools import partial
from itertools import cycle
from typing import Optional
import numpy
from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy, QApplication
from mdaviz import utils
from mdaviz.fit_manager import FitManager
from mdaviz.user_settings import settings
from mdaviz.logger import get_logger
from mdaviz.curve_manager import CurveManager

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

    def __init__(self, parent, **kwargs):
        """Build the 1D plot widget and wire it to the MDA MVC.

        Parameters
        ----------
        parent : MDA_MVC
            Parent MVC widget (provides mda_file_viz, mda_file, etc.).
        **kwargs
            Optional plot_options (e.g. title, x/y labels) applied to the axes.
        """

        self.mda_mvc = parent
        super().__init__()

        # Initialize log scale attributes
        self._log_x = False
        self._log_y = False

        # ==========================================
        #   UI initialization
        # ==========================================

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

        # ==========================================
        #   Signals & slots
        # ==========================================

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

        # Remove buttons definitions:
        self.clearAll = self.mda_mvc.mda_file_viz.clearAll
        self.removeButton = self.mda_mvc.mda_file_viz.curveRemove
        self.removeCursor1 = self.mda_mvc.mda_file_viz.cursor1_remove
        self.removeCursor2 = self.mda_mvc.mda_file_viz.cursor2_remove

        # Remove button connections:
        utils.reconnect(self.clearAll.clicked, self.onClearAllClicked)
        utils.reconnect(self.removeButton.clicked, self.onRemoveButtonClicked)
        self.removeCursor1.clicked.connect(partial(self.onRemoveCursor, cursor_num=1))
        self.removeCursor2.clicked.connect(partial(self.onRemoveCursor, cursor_num=2))

        # File tableview & graph synchronization:
        self.mda_mvc.mda_file.tabManager.tabRemoved.connect(self.onTabRemoved)
        self.mda_mvc.detRemoved.connect(self.onDetRemoved)

        # Connect offset & factor QLineEdit:
        self.offset_value = self.mda_mvc.mda_file_viz.offset_value
        self.factor_value = self.mda_mvc.mda_file_viz.factor_value
        self.offset_value.editingFinished.connect(self.onOffsetFactorUpdated)
        self.factor_value.editingFinished.connect(self.onOffsetFactorUpdated)

        # Connect derivative checkbox
        self.derivative = False
        self.derivativeCheckBox = self.mda_mvc.mda_file_viz.derivativeCheckBox
        self.derivativeCheckBox.setChecked(self.derivative)
        self.derivativeCheckBox.toggled.connect(self.onDerivativeToggled)

        # Connect unscale checkbox
        self.unscale = False
        self.unscaleCheckBox = self.mda_mvc.mda_file_viz.unscaleCheckBox
        self.unscaleCheckBox.setChecked(self.unscale)
        self.unscaleCheckBox.toggled.connect(self.onUnscaleToggled)

        # Initialize snap to curve setting (default to False for free cursor placement)
        self._snap_to_curve = False
        self.snapCursors = self.mda_mvc.mda_file_viz.snapCursors
        self.snapCursors.setChecked(self._snap_to_curve)
        self.snapCursors.toggled.connect(self.onSnapCursorsToggled)

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

        # Connect the click event to a handler
        self.cid = self.figure.canvas.mpl_connect("button_press_event", self.onclick)
        self.alt_pressed = False

        # Set up a timer to check modifier key state
        self.key_check_timer = QTimer()
        self.key_check_timer.timeout.connect(self.check_modifier_keys)
        self.key_check_timer.start(50)  # Check every 50ms

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

    # ==========================================
    #   Set & get methods
    # ==========================================

    def setPlotTitle(self, txt=""):
        """Set the axes title text on the plot."""
        self.main_axes.set_title(txt, fontsize=FONTSIZE)

    def setBottomAxisText(self, text):
        """Set the x-axis label on the axes."""
        self.main_axes.set_xlabel(text, fontsize=FONTSIZE, labelpad=10)

    def setLeftAxisText(self, text):
        """Set the y-axis label on the axes."""
        self.main_axes.set_ylabel(text, fontsize=FONTSIZE, labelpad=10)

    def title(self):
        """Return the stored plot title."""
        return self._title

    def xlabel(self):
        """Return the stored x-axis label."""
        return self._xlabel

    def ylabel(self):
        """Return the stored y-axis label."""
        return self._ylabel

    def setTitle(self, txt=""):
        """Store the plot title (use setPlotTitle to draw it)."""
        self._title = txt

    def setXlabel(self, txt=""):
        """Store the x-axis label (use setBottomAxisText to draw it)."""
        self._xlabel = txt

    def setYlabel(self, txt=""):
        """Store the y-axis label (use setLeftAxisText to draw it)."""
        self._ylabel = txt

    def setDerivative(self, checked):
        """Set derivative checkbox and internal state without emitting toggled (for sync, e.g. on curve selection)."""
        self.derivativeCheckBox.blockSignals(True)
        self.derivativeCheckBox.setChecked(checked)
        self.derivative = checked
        self.derivativeCheckBox.blockSignals(False)

    def setUnscale(self, checked):
        """Set unscale checkbox and internal state without emitting toggled (for sync, e.g. on curve selection)."""
        self.unscaleCheckBox.blockSignals(True)
        self.unscaleCheckBox.setChecked(checked)
        self.unscale = checked
        self.unscaleCheckBox.blockSignals(False)

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

    # ==========================================
    #   Slot methods
    # ==========================================

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
        """
        # Add to graph
        curveData = self.curveManager.getCurveData(curveID)
        if curveData is None:
            return
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

        # Apply transformation to the data
        x_data, y_transformed = self.curveManager.getTransformedCurveXYData(curveID)
        if x_data is not None and y_transformed is not None:
            ds = [x_data, y_transformed]

        # Plot and store the plot object associated with curveID:
        try:
            plot_obj = self.main_axes.plot(*ds, **ds_options)[0]
            self.plotObjects[curveID] = plot_obj
        except Exception as exc:
            logger.error(str(exc))

        # Add to the comboBox
        index = self.curveBox.count()  # Get the next index
        # prev_index = self.curveBox.currentIndex()
        # Use the user-friendly label for display, but store curveID as data
        display_label = curveData.get("ds_options", {}).get("label", curveID)
        self.curveBox.addItem(display_label)
        # Store the curveID as item data for later retrieval
        self.curveBox.setItemData(index, curveID, QtCore.Qt.ItemDataRole.UserRole)
        # Add tooltip with file path
        file_path = curveData.get("file_path", "No file path available")
        self.curveBox.setItemData(index, file_path, QtCore.Qt.ItemDataRole.ToolTipRole)

        # Only select the new curve if it's the first one
        if self.curveBox.count() == 1:
            self.curveBox.setCurrentIndex(0)
            # Manually trigger curve selection for the first curve
            self.onCurveSelected(0)

        # Update any existing combo box items to use new curve ID format
        self.updateComboBoxCurveIDs()

        # Refresh unscaled curves with the new global_min/max
        self.refreshAllUnscaledCurves()

        # Refresh axis labels, legend, limits, and redraw the plot:
        self.updatePlot(update_title=True)

        # Select the last plotted curve in the comboBox and syncs UI to the curve selected:
        # derivative, offset/factor, tooltip, basic maths, fits...
        if self.curveBox.count() > 1:
            new_index = self.curveBox.count() - 1
            self.curveBox.blockSignals(True)
            self.curveBox.setCurrentIndex(new_index)
            self.curveBox.blockSignals(False)
            self.onCurveSelected(new_index)

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

        # Apply transformations
        if curve_data and recompute_y:
            if curve_data.get("unscale", False):
                # Defer so bulk I0/Add updates finish first; then reference set is correct
                QTimer.singleShot(0, self.refreshAllUnscaledCurves)
            else:
                x_data, y_transformed = self.curveManager.getTransformedCurveXYData(
                    curveID
                )
                if (
                    x_data is not None
                    and y_transformed is not None
                    and curveID in self.plotObjects
                ):
                    self.plotObjects[curveID].set_ydata(y_transformed)

        # Handle label changes (e.g., I0 normalization)
        # Only if we're not recreating the plot object (i.e. not update_x)
        if curve_data and not update_x:
            new_label = curve_data.get("ds_options", {}).get("label", "")
            if curveID in self.plotObjects:
                plot_obj = self.plotObjects[curveID]
                old_label = (
                    plot_obj.get_label() if hasattr(plot_obj, "get_label") else ""
                )
                if new_label and new_label != old_label:
                    # Update plot object label for legend
                    plot_obj.set_label(new_label)

                    # Update combo box text
                    for i in range(self.curveBox.count()):
                        if (
                            self.curveBox.itemData(i, QtCore.Qt.ItemDataRole.UserRole)
                            == curveID
                        ):
                            self.curveBox.setItemText(i, new_label)
                            break

        # For x-data updates, we need to recreate the plot object to maintain style
        if curve_data and update_x:
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

            # Apply transformations
            x_data, y_transformed = self.curveManager.getTransformedCurveXYData(curveID)
            if x_data is not None and y_transformed is not None:
                ds = [x_data, y_transformed]

            # Plot and store the new plot object associated with curveID:
            try:
                plot_obj = self.main_axes.plot(*ds, **ds_options)[0]
                self.plotObjects[curveID] = plot_obj
            except Exception as exc:
                logger.error(str(exc))

        # Refresh axis labels, legend, limits, and redraw the plot:
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
                self.mda_mvc.mda_file_viz.setLogScaleState(False, False)
                self.curveManager.removeAllCurves(doNotClearCheckboxes=False)
            else:
                self.curveManager.removeCurve(curveID)

    def onCurveRemoved(self, *arg):
        """
        Handle the removal of a curve from the plot.

        This slot method is called when a curve is removed from the curve manager.
        It performs cleanup operations including plot object removal, UI updates,
        and checkbox management based on data type. If no curve remains, reset the
        log scales.

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
            5. Removes file tab if no curves remain for that file (Auto-add mode)

        Checkbox Logic:
            - 1D data: Always uncheck the detector checkbox
            - 2D data: Only uncheck if no curves remain for that detector
                       (allows multiple curves per detector for 2D data)
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
        # Remove curve from fitManager
        self.fitManager.removeFit(curveID)
        # Update plot labels, legend and title
        self.updatePlot(update_title=False)
        if count > 0:
            # Refresh unscaled curves with the new global_min/max
            self.refreshAllUnscaledCurves()
            self.onCurveSelected(self.curveBox.currentIndex())

        # If this was the last curve for this file, remove the tab
        if count == 0 and self.mda_mvc.mda_file.mode() == "Auto-add":
            logger.debug(
                f"Removing tab for file: {file_path}, count: {count}, mode: {self.mda_mvc.mda_file.mode()}"
            )
            self.mda_mvc.mda_file.tabManager.removeTab(file_path)

        # If no curves left on the graph, reset log scale and clear plot
        if len(self.curveManager.curves()) == 0:
            self.mda_mvc.mda_file_viz.setLogScaleState(False, False)
            self.clearPlot()

    def onAllCurvesRemoved(self, doNotClearCheckboxes=True):
        """Clear plot, fits, and curves; optionally clear checkboxes. Preserve log scale.
        onAllCurvesRemoved preserves the log scale because it is called in auto-replace
        (we want to be able to "browse" between files in the same conditions)."""

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
        """Remove curve for a given det & file."""
        curveIDs = self.curveManager.findCurveID(file_path, row)
        for curveID in curveIDs:
            self.curveManager._persistent_properties.pop(curveID, None)
            self.curveManager.removeCurve(curveID)

    def onTabRemoved(self, file_path):
        """Remove curve(s) for a given tab ie file."""
        if self.mda_mvc.mda_file.mode() in ["Auto-add", "Auto-replace"]:
            for curveID in self.curveManager.curves().keys():
                if self.curveManager.curves()[curveID]["file_path"] == file_path:
                    self.curveManager.removeCurve(curveID)

    def onClearAllClicked(self):
        """Clear plot, fits, curves and checkboxes. Reset log scale."""
        self.mda_mvc.mda_file_viz.setLogScaleState(False, False)
        self.curveManager.allCurvesRemoved.emit(False)

    def refreshAllUnscaledCurves(self):
        """Recompute and redraw y-data for all curves with unscale=True using
        the current reference range, then redraw the plot."""
        for cid in self.curveManager.curves():
            curve_data = self.curveManager.getCurveData(cid)
            if curve_data is None:
                continue
            if curve_data.get("unscale", False) and cid in self.plotObjects:
                x_data, y_transformed = self.curveManager.getTransformedCurveXYData(cid)
                if y_transformed is not None:
                    self.plotObjects[cid].set_ydata(y_transformed)
        self.updatePlot(update_title=False)

    # ==========================================
    #   UI methods
    # ==========================================

    def plot(self, row, *ds, **options):
        """The main method called by MDA_MVC"""
        self.main_axes.axis("on")
        self.curveManager.addCurve(row, *ds, **options)

    def configPlot(self, grid=True):
        """Apply axis labels, title, and grid; redraw canvas."""
        self.setLeftAxisText(self.ylabel())
        self.setBottomAxisText(self.xlabel())
        self.setPlotTitle(self.title())
        if grid:
            self.main_axes.grid(True, color="#cccccc", linestyle="-", linewidth=0.5)
        else:
            self.main_axes.grid(False)
        self.canvas.draw()

    def updatePlot(self, update_title=True):
        """Refresh axis labels, legend, limits, selected curve stats and redraw the plot."""

        # Collect positioner PVs from all curves and update x label:
        x_label_set = set()
        for curveID in self.curveManager.curves():
            curve_data = self.curveManager.getCurveData(curveID)
            if curve_data is None:
                continue
            plot_options = curve_data.get("plot_options") or {}
            x_label = plot_options.get("x", "")
            if x_label:
                x_label_set.add(x_label)
        self.setXlabel(", ".join(list(x_label_set)))

        # Y-axis label: use selected curve's combo box text (detector name, minus file prefix)
        selected_curveID = self.getSelectedCurveID()
        if selected_curveID in self.curveManager.curves():
            self.updateBasicMathInfo(selected_curveID)

            # Get the combo box text for the selected curve
            selected_index = self.curveBox.currentIndex()
            if selected_index >= 0:
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
        """Refresh the axes legend from current curve labels (excluding internal ones)."""
        labels = self.main_axes.get_legend_handles_labels()[1]
        valid_labels = [label for label in labels if not label.startswith("_")]
        if valid_labels:
            self.main_axes.legend()

    def clearPlot(self):
        """Clear axes, labels, cursors, plot objects, and curve combo box; redraw canvas."""
        self.main_axes.clear()
        self.main_axes.axis("off")
        self.main_axes.set_title("")
        self.setXlabel("")
        self.setYlabel("")
        self.clearCursors()
        self.clearCursorInfo()
        self.clearBasicMath()
        self.clearAllFits()
        self.figure.canvas.draw()
        self.plotObjects = {}
        self.curveBox.clear()

    # ==========================================
    #   Interaction with UI elements
    # ==========================================

    def onCurveSelected(self, index):
        """Sync UI to the curve selected in the combo box: derivative, offset/factor, tooltip,
        row highlight, basic math, plot controls, fit UI, and plot labels.

        Parameters
        ----------
        index : int
            Current index of the curve combo box (or -1 if none selected).
        """
        # Get the curve ID from the combo box item data
        curveID = None
        if index >= 0:
            curveID = self.curveBox.itemData(index, QtCore.Qt.ItemDataRole.UserRole)

        has_curve = curveID in self.curveManager.curves()
        # Update QLineEdit & QLabel widgets with the values for the selected curve
        if (
            curveID
            and curveID in self.plotObjects
            and curveID in self.curveManager.curves()
        ):
            curve_data = self.curveManager.getCurveData(curveID)
            if curve_data is None:
                self.offset_value.setText("0")
                self.factor_value.setText("1")
                self.setDerivative(False)
                self.setUnscale(False)
                self.curveBox.setToolTip("Selected curve")
            else:
                file_path = curve_data["file_path"]
                row = curve_data["row"]
                # Update derivative and unscale checkbox
                derivative_state = curve_data.get("derivative", False)
                self.setDerivative(derivative_state)
                unscale_state = curve_data.get("unscale", False)
                self.setUnscale(unscale_state)
                # Update offset & factor
                self.offset_value.setText(str(curve_data["offset"]))
                self.factor_value.setText(str(curve_data["factor"]))
                # Update tooltip & highlight row
                self.curveBox.setToolTip(file_path)
                try:
                    self.mda_mvc.mda_file.highlightRowInTab(file_path, row)
                except Exception as exc:
                    logger.error(str(exc))
                    logger.error("highlightRowInTab failed; ignoring exception.")
        else:
            self.offset_value.setText("0")
            self.factor_value.setText("1")
            self.setDerivative(False)
            self.setUnscale(False)
            self.curveBox.setToolTip("Selected curve")

        # Update plot controls
        self.mda_mvc.mda_file_viz.updatePlotControls(has_curve)

        # Update basic math info:
        self.updateBasicMathInfo(curveID)

        # Update curve style combo box to show current curve's style
        self.updateCurveStyleComboBox(curveID)

        # Update fit UI
        self.updateFitUI(curveID)

        # Update axis labels, legend, limits, selected curve stats and redraw the plot
        self.updatePlot(update_title=False)

    def updateFitUI(self, curveID: str) -> None:
        """
        Update fit UI based on curve selection.

        Parameters:
        - curveID: ID of the selected curve
        """
        # Update fit controls state
        has_curve = curveID in self.curveManager.curves()

        # Clear fit details if no curve selected or if switching to a different curve
        if not has_curve:
            self.mda_mvc.mda_file_viz.fitDetails.clear()
        else:
            if curveID and self.fitManager.hasFits(curveID):
                # If we're switching to a curve that has a fit, update fit details in UI
                self.updateFitDetails(curveID)
            else:
                # If we're switching to a curve that does not have a fit, clear fit details
                self.mda_mvc.mda_file_viz.fitDetails.clear()

    def removeItemCurveBox(self, curveID):
        """Remove the combo box item for the given curveID.

        Parameters
        ----------
        curveID : str
            ID of the curve whose combo box entry to remove.
        """
        # Find the item by curve ID stored in item data
        for i in range(self.curveBox.count()):
            if self.curveBox.itemData(i, QtCore.Qt.ItemDataRole.UserRole) == curveID:
                self.curveBox.removeItem(i)
                break

    def updateComboBoxCurveIDs(self):
        """Update combo box items to use new curve ID format. Likely OBSOLETE."""
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

    # ==========================================
    #   Basic maths methods
    # ==========================================

    def onOffsetFactorUpdated(self):
        """Apply offset and factor from the line edits to the selected curve; refresh basic math stats."""
        curveID = self.getSelectedCurveID()
        if curveID is None:
            return
        try:
            offset = float(self.offset_value.text())
            factor = float(self.factor_value.text())
        except ValueError:
            # Reset to default if conversion fails
            offset = 0
            factor = 1
            if self.offset_value:
                self.offset_value.setText(str(offset))
            if self.factor_value:
                self.factor_value.setText(str(factor))
            return
        self.curveManager.updateCurveOffsetFactor(curveID, offset, factor)
        self.updateBasicMathInfo(curveID)

    def onDerivativeToggled(self, checked):
        """Handle derivative checkbox toggle.

        Parameters:
            checked (bool): True if checkbox is checked (derivative enabled), False if unchecked (derivative disabled)
        """
        self.derivative = checked
        curveID = self.getSelectedCurveID()
        if curveID is None:
            return
        self.curveManager.updateCurveDerivative(curveID, derivative=checked)
        self.updateBasicMathInfo(curveID)

    def onUnscaleToggled(self, checked):
        """Handle unscale checkbox toggle.

        Parameters:
            checked (bool): True if checkbox is checked (unscale enabled), False if unchecked (unscale disabled)
        """
        self.unscale = checked
        curveID = self.getSelectedCurveID()
        if curveID is None:
            return
        self.curveManager.updateCurveUnscale(curveID, unscale=checked)
        self.updateBasicMathInfo(curveID)

    def updateBasicMathInfo(self, curveID):
        """Update min/max/COM/mean labels from the curve's transformed data, or clear them if no valid curve."""
        if curveID and curveID in self.curveManager.curves():
            try:
                x, y = self.curveManager.getTransformedCurveXYData(curveID)

                if x is None or y is None:
                    self.clearBasicMath()
                    return

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
        """Clear min/max/COM/mean labels (set to 'n/a')"""
        for txt in ["min_text", "max_text", "com_text", "mean_text"]:
            self.mda_mvc.findChild(QtWidgets.QLabel, txt).setText("n/a")

    def calculateBasicMath(self, x_data, y_data):
        """Compute min/max (x,y), center-of-mass x, and mean y from the curve data.

        Returns
        -------
        tuple
            ((x_at_y_min, y_min), (x_at_y_max, y_max), x_com, y_mean).
        """
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

    # ==========================================
    #   Cursors methods
    # ==========================================

    def onRemoveCursor(self, cursor_num):
        """Remove the cursor from the plot and clear its state; refresh cursor info and redraw.

        Parameters
        ----------
        cursor_num : int
            1 or 2 (cursor 1 or 2).
        """
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
        """Remove both cursors from the plot and clear their state."""
        self.onRemoveCursor(1)
        self.onRemoveCursor(2)

    def onSnapCursorsToggled(self, checked):
        """Handle snap cursors checkbox toggle.

        Parameters:
            checked (bool): True if checkbox is checked (snap enabled), False if unchecked (snap disabled)
        """
        self._snap_to_curve = checked

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

        # Apply transformations
        x_data, y_data = self.curveManager.getTransformedCurveXYData(curveID)
        if x_data is None or y_data is None:
            return None

        # Ensure data are numpy arrays
        if not isinstance(x_data, numpy.ndarray):
            x_data = numpy.array(x_data, dtype=float)
        if not isinstance(y_data, numpy.ndarray):
            y_data = numpy.array(y_data, dtype=float)

        if len(x_data) == 0 or len(y_data) == 0:
            return None

        # Normalize by axis ranges to account for different scales
        x_range = self.main_axes.get_xlim()
        y_range = self.main_axes.get_ylim()
        x_scale = x_range[1] - x_range[0] if x_range[1] != x_range[0] else 1.0
        y_scale = y_range[1] - y_range[0] if y_range[1] != y_range[0] else 1.0

        # Calculate normalized distances
        dx = (x_data - x_click) / x_scale
        dy = (y_data - y_click) / y_scale
        distances = numpy.sqrt(dx**2 + dy**2)

        # Find the index of the nearest point
        nearest_index = numpy.argmin(distances)

        return (float(x_data[nearest_index]), float(y_data[nearest_index]))

    def onclick(self, event):
        """Handle mouse click on the plot: place cursor 1 (middle or Alt+right) or cursor 2 (right)
        at click position or nearest point on curve if snap is on; refresh cursor info and redraw.

        Parameters
        ----------
        event : matplotlib.backend_bases.MouseEvent
            The mouse click event (button, axes, xdata, ydata).
        """
        # Check if the click was in the main_axes
        if event.inaxes is self.main_axes:
            # Determine cursor position based on snap setting
            if self._snap_to_curve:
                # Find the nearest point in the selected curve
                nearest_point = self.findNearestPoint(event.xdata, event.ydata)

                if nearest_point is None:
                    # No curve selected or no data available
                    return

                x_cursor, y_cursor = nearest_point
            else:
                # Use exact click position
                x_cursor, y_cursor = event.xdata, event.ydata

            # Middle click or Alt+right click for red cursor (cursor 1)
            if event.button == MIDDLE_BUTTON or (
                event.button == RIGHT_BUTTON and self.alt_pressed
            ):
                if self.cursors[1] is not None:
                    try:
                        # Remove existing red cursor
                        self.cursors[1].remove()
                    except (NotImplementedError, AttributeError):
                        # Handle case where artist cannot be removed
                        pass
                # Assign artist to self.cursors dictionary (matplotlib returns a 1-element list)
                self.cursors[1] = self.main_axes.plot(
                    x_cursor, y_cursor, "r+", markersize=15, linewidth=2
                )[0]
                # Update cursor position
                self.cursors["pos1"] = (x_cursor, y_cursor)

            # Right click (without Alt) for blue cursor (cursor 2)
            elif event.button == RIGHT_BUTTON and not self.alt_pressed:
                if self.cursors[2] is not None:
                    try:
                        # Remove existing blue cursor
                        self.cursors[2].remove()
                    except (NotImplementedError, AttributeError):
                        # Handle case where artist cannot be removed
                        pass
                self.cursors[2] = self.main_axes.plot(
                    x_cursor, y_cursor, "b+", markersize=15, linewidth=2
                )[0]

                # Update cursor position
                self.cursors["pos2"] = (x_cursor, y_cursor)

            # Update the info panel with cursor positions
            self.calculateCursors()

            # Redraw the canvas to display the new markers
            self.canvas.draw()

    def calculateCursors(self):
        """
        Calculate diff and midpoint, update cursor dictionary and information in info panel widget.
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
        """Update cursor information in info panel widget."""
        self.mda_mvc.mda_file_viz.pos1_text.setText(self.cursors["text1"])
        self.mda_mvc.mda_file_viz.pos2_text.setText(self.cursors["text2"])
        self.mda_mvc.mda_file_viz.diff_text.setText(self.cursors["diff"])
        self.mda_mvc.mda_file_viz.midpoint_text.setText(self.cursors["midpoint"])

    def clearCursorInfo(self):
        """Clear cursor information in info panel widget."""
        self.mda_mvc.mda_file_viz.pos1_text.setText("middle click or alt+right click")
        self.mda_mvc.mda_file_viz.pos2_text.setText("right click")
        self.mda_mvc.mda_file_viz.diff_text.setText("n/a")
        self.mda_mvc.mda_file_viz.midpoint_text.setText("n/a")

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

    # ==========================================
    #   Fit methods
    # ==========================================

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

        self.onFitAdded(curveID)

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

        # Apply transformation
        x_data, y_data = self.curveManager.getTransformedCurveXYData(curveID)

        if x_data is not None and y_data is not None:
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

            # Determine fit range
            x_range = None
            if use_range:
                x_range = self.getCursorRange()
            try:
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
        details_text += "Fitting results:\n"
        for param_name, param_value in result.parameters.items():
            uncertainty = result.uncertainties.get(param_name, 0.0)
            details_text += f"  {param_name}: {utils.num2fstr(param_value, 3)}"
            if uncertainty > 0:
                details_text += f" ± {utils.num2fstr(uncertainty, 3)}"
            details_text += "\n"
            if fit_data.model_name == "Gaussian" and param_name == "sigma":
                details_text += f"  FWHM: {utils.num2fstr(2.35482 * param_value, 3)}"
                details_text += f" ± {utils.num2fstr(2.35482 * uncertainty, 3)}\n"
            if fit_data.model_name == "Lorentzian" and param_name == "gamma":
                details_text += f"  FWHM: {utils.num2fstr(2 * param_value, 3)}"
                details_text += f" ± {utils.num2fstr(2 * uncertainty, 3)}\n"

        # Quality metrics
        details_text += "\nQuality Metrics:\n"
        details_text += f"  R²: {utils.num2fstr(result.r_squared, 3)}\n"
        details_text += f"  χ²: {utils.num2fstr(result.chi_squared, 3)}\n"
        details_text += (
            f"  Reduced χ²: {utils.num2fstr(result.reduced_chi_squared, 3)}\n"
        )

        fit_details.setText(details_text)

    def clearSelectedFit(self) -> None:
        """Clear the fit from the currently selected curve."""
        curveID = self.getSelectedCurveID()
        if curveID:
            self.fitManager.removeFit(curveID)
            self.mda_mvc.mda_file_viz.fitDetails.clear()

    def clearAllFits(self) -> None:
        """Clear all fits from all curves."""
        self.fitManager.clearAllFits()
        self.mda_mvc.mda_file_viz.fitDetails.clear()

    # ======================================================
    #  Curve styling methods
    # ======================================================

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
            if curveID not in self.curveManager._persistent_properties:
                self.curveManager._persistent_properties[curveID] = {}
            self.curveManager._persistent_properties[curveID]["style"] = format_string
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


# ======================================================
#  Chartview 2D
# ======================================================


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

    def configPlot(self, grid=False):
        """Apply axis labels and title; no grid for 2D plots."""
        super().configPlot(grid=grid)

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

        # Validate 2D data and axes
        y_data = numpy.asarray(y_data)
        x_data = numpy.asarray(x_data)
        x2_data = numpy.asarray(x2_data)

        if y_data.ndim != 2 or y_data.size == 0:
            logger.warning("plot2D: y_data must be non-empty 2D array")
            self.showMessage("Invalid or empty 2D data")
            return
        if x_data.size == 0 or x2_data.size == 0:
            logger.warning("plot2D: x_data and x2_data must be non-empty")
            self.showMessage("Invalid or empty X/X2 data")
            return
        if y_data.shape[0] != x2_data.size or y_data.shape[1] != x_data.size:
            logger.warning(
                "plot2D: y_data shape %s does not match x_data len %s, x2_data len %s",
                y_data.shape,
                x_data.size,
                x2_data.size,
            )
            self.showMessage("2D data shape mismatch")
            return

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
        # Check if X data is in descending order; flip horizontally to match
        if len(x_data) > 1 and x_data[0] > x_data[-1]:
            y_data = y_data[:, ::-1]  # Flip horizontally

        # Apply log scale normalization if enabled
        norm = None
        if hasattr(self, "_log_y_2d") and self._log_y_2d:
            # Only apply log if all values are positive
            vmin, vmax = y_data.min(), y_data.max()
            if vmin > 0:
                from matplotlib.colors import LogNorm

                # Use LogNorm for proper log color scaling
                norm = LogNorm(vmin, vmax)

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
            # Only apply log if all values are positive
            vmin, vmax = y_data.min(), y_data.max()
            if vmin > 0:  # Only apply log if all values are positive
                from matplotlib.colors import LogNorm

                # Use LogNorm for proper log color scaling
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
        # Store the log scale state
        self._log_y_2d = log_y

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
