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

import numpy
from PyQt6.QtCore import QObject, pyqtSignal
from mdaviz.logger import get_logger

# Initialize logger for this module
logger = get_logger("curveManager")


class CurveManager(QObject):
    """Manages curve data, properties, and persistence for ChartView.

    Handles storage and management of curve data including plotting properties,
    persistent settings, and curve identification. Provides signals for curve
    lifecycle events and maintains persistent properties across plotting sessions.

    Signals:
        curveAdded: Emitted when a curve is added (curveID)
        curveRemoved: Emitted when a curve is removed (curveID, curveData, count)
        curveUpdated: Emitted when a curve is updated (curveID, recompute_y, update_x)
        allCurvesRemoved: Emitted when all curves are removed (doNotClearCheckboxes)
    """

    curveAdded = pyqtSignal(str)
    curveRemoved = pyqtSignal(str, dict, int)  # count = nb of curves left for this file
    curveUpdated = pyqtSignal(str, bool, bool)
    allCurvesRemoved = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Store curves with a unique identifier as the key
        self._curves = {}

        # Persistent storage for curve properties across manager clears
        self._persistent_properties = {}  # key: curveID, value: {style}

    def curves(self):
        """Returns a copy of the currently managed curves.

        Provides access to all curves currently stored in the manager by
        returning a copy of the internal dictionary to prevent direct
        modification of the manager's state.

        Returns:
            dict: Copy of the curves dictionary with curveID as keys
        """
        return dict(self._curves)

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

    def getCurveXYData(self, curveID):
        """
        Get the X and Y data arrays for a curve.

        Parameters:
            curveID (str): Unique identifier of the curve

        Returns:
            tuple: (x_data, y_data) or (None, None) if not found
        """
        curve_info = self.getCurveData(curveID)
        if curve_info:
            data = curve_info.get("ds")
            if data and len(data) >= 2:
                return (data[0], data[1])  # (x_data, y_data)
        return (None, None)

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
                # Create updated curve data, preserving existing properties (style, offset, factor, etc.)
                existing_curve_data = self._curves[curveID]
                updated_curve_data = {
                    **existing_curve_data,  # Preserve all existing properties
                    "ds": ds,  # Update with new data
                    "plot_options": plot_options,  # Update plot options
                    "ds_options": ds_options,  # Update label and other ds options
                }
                self.updateCurve(curveID, updated_curve_data, recompute_y=True)
                return

        # Curve does not exist, create new curve
        logger.debug(f"Curve {curveID} does NOT exist, creating new curve")

        # Check for persistent properties first
        persistent_props = self._persistent_properties.get(curveID, {})

        self._curves[curveID] = {
            "ds": ds,  # ds = [x_data, y_data]
            "offset": 0,  # default offset
            "factor": 1,  # default factor
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

    def updateCurveOffset(self, curveID, new_offset):
        """Update the offset value for a specific curve.

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
                self.updateCurve(curveID, curve_data, recompute_y=True)

    def updateCurveFactor(self, curveID, new_factor):
        """Update the factor value for a specific curve.

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
                self.updateCurve(curveID, curve_data, recompute_y=True)
