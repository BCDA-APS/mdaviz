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

    # =====================================
    # Lookup & IDs
    # =====================================

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

    # =====================================
    # Add & update curves
    # =====================================

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
        x2_index = options.get("x2_index")

        logger.debug(f"addCurve - Received x2_index: {x2_index}")

        # Generate unique curve ID & update options:
        curveID = self.generateCurveID(label, file_path, row, x2_index)

        ds_options["label"] = label  # Keep the original label for display purposes
        logger.debug(
            f"Adding curve with ID: {curveID}, label: {label}, file_path: {file_path}"
        )
        logger.debug(f"Current curves in manager: {list(self._curves.keys())}")

        x_data = ds[0]
        y_data = ds[1]

        if curveID in self._curves:
            logger.debug(f"Curve {curveID} already exists")
            # Check if x_data is the same
            existing_curve_data = self._curves[curveID]
            existing_x_data = existing_curve_data["ds"][0]
            existing_y_data = existing_curve_data["ds"][1]
            existing_label = existing_curve_data.get("ds_options", {}).get("label", "")

            x_data_equal = numpy.array_equal(x_data, existing_x_data)
            y_data_equal = numpy.array_equal(y_data, existing_y_data)
            label_equal = label == existing_label

            if x_data_equal and y_data_equal and label_equal:
                # All data and metadata are identical - no update needed
                logger.debug(
                    " x_data, y_data, and label are the same, do not add or update the curve"
                )
                return

            else:
                logger.debug(
                    f" x_data changed: {not x_data_equal}, y_data changed: {not y_data_equal}, label changed: {not label_equal}, update the curve"
                )
                # Data or label has changed, update the curve:
                # Create updated curve data, preserving existing properties (style, offset, factor, etc.)
                updated_curve_data = {
                    **existing_curve_data,  # Preserve all existing properties
                    "ds": ds,  # Update with new data
                    "plot_options": plot_options,  # Update plot options
                    "ds_options": ds_options,  # Update label and other ds options
                    "original_y": numpy.array(ds[1]).copy(),
                }
                # Determine what changed to set appropriate update flags
                x_data_changed = not x_data_equal
                y_data_changed = not y_data_equal
                # If update_x=True, recompute_y is redundant (recreation already applies transformations)
                # If only y_data changed (X same), recompute_y ensures transformations are applied to existing plot
                self.updateCurve(
                    curveID,
                    updated_curve_data,
                    recompute_y=y_data_changed and not x_data_changed,
                    update_x=x_data_changed,
                )
                return

        # Curve does not exist, create new curve
        logger.debug(f"Curve {curveID} does NOT exist, creating new curve")

        # Check for persistent properties first
        persistent_props = self._persistent_properties.get(curveID, {})

        self._curves[curveID] = {
            "ds": ds,  # ds = [x_data, y_data]
            "original_y": numpy.array(ds[1]).copy(),
            "offset": persistent_props.get("offset", 0),
            "factor": persistent_props.get("factor", 1),
            "derivative": persistent_props.get("derivative", False),
            "style": persistent_props.get("style", "-"),
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
            recompute_y: If True, recalculate Y data with current transformations
            update_x: If True, update X data (requires plot object recreation)

        Returns:
            bool: True if curve was found and updated, False if curve not found
                  Emits curveUpdated signal when curve is successfully updated
        """
        if curveID not in self._curves:
            logger.debug(f"Curve {curveID} not found in manager for update")
            return False

        if "original_y" not in curveData and "original_y" in self._curves[curveID]:
            curveData["original_y"] = self._curves[curveID]["original_y"]
        self._curves[curveID] = curveData

        self.curveUpdated.emit(curveID, recompute_y, update_x)
        logger.debug(f"Emits curveUpdated {curveID=}, {recompute_y=}, {update_x=}")
        return True

    # =====================================
    # Transformations
    # =====================================

    def getTransformedCurveXYData(self, curveID):
        """Get transformed (x, y) data for plotting.

        Returns the x_data and transformed y_data (with offset/factor/derivative applied).

        Parameters:
            curveID: The unique identifier of the curve

        Returns:
            tuple: (x_data, y_transformed) or (None, None) if curve not found
        """
        curve_data = self.getCurveData(curveID)
        if not curve_data:
            return None, None

        x_data = curve_data["ds"][0]
        original_y = curve_data.get("original_y")

        if original_y is None:
            logger.warning(f"Curve {curveID} missing original_y, cannot transform")
            return None, None

        y_transformed = self.applyTransformations(curveID, x_data, original_y)

        return x_data, y_transformed

    def applyTransformations(self, curveID, x_data, original_y):
        """
        Apply current transformations to original_y data.

        Parameters:
            curveID (str): Curve identifier
            x_data (array-like): X data array (needed for derivative calculation)
            original_y (array-like): Raw y data to transform

        Returns:
            numpy.ndarray: Transformed y data
        """
        curve_data = self._curves.get(curveID)
        if not curve_data:
            return original_y

        offset = curve_data.get("offset", 0.0)
        factor = curve_data.get("factor", 1.0)
        derivative = curve_data.get("derivative", False)

        original_y_array = numpy.array(original_y)

        if derivative:
            grad = numpy.gradient(original_y_array, x_data)
            transformed_y = offset + factor * grad
        else:
            transformed_y = offset + factor * original_y_array

        return transformed_y

    def updateCurveOffsetFactor(self, curveID, offset=None, factor=None):
        """Update offset and/or factor for a curve.

        Parameters:
            curveID: The unique identifier of the curve
            offset: New offset value (None to skip, can be 0)
            factor: New factor value (None to skip, can be 1)
        """
        if offset is not None:
            self.updateCurveOffset(curveID, offset)
        if factor is not None:
            self.updateCurveFactor(curveID, factor)

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

    def updateCurveDerivative(self, curveID, derivative):
        """Update the derivative flag for a specific curve.

        Parameters:
            curveID: The unique identifier of the curve
            derivative: bool

        Returns:
            None: Updates curve data and emits curveUpdated signal if changed
        """
        curve_data = self.getCurveData(curveID)
        if curve_data:
            old_derivative = curve_data.get("derivative", False)
            if old_derivative != derivative:
                curve_data["derivative"] = derivative
                self.updateCurve(curveID, curve_data, recompute_y=True)

    # =====================================
    # Remove curves
    # =====================================

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
            # Remove curve entry from self.curves & persistent props:
            del self._curves[curveID]
            self._persistent_properties.pop(curveID, None)
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
        for curveID in self._curves.keys():
            if doNotClearCheckboxes:
                curve_data = self.getCurveData(curveID)
                props = self._persistent_properties.setdefault(curveID, {})
                props["offset"] = curve_data.get("offset", 0)
                props["factor"] = curve_data.get("factor", 1)
                props["derivative"] = curve_data.get("derivative", False)
            else:
                self._persistent_properties.pop(curveID, None)
        self._curves.clear()
        self.allCurvesRemoved.emit(doNotClearCheckboxes)

    def clearPersistentProperties(self):
        """Clear all persistent curve properties (offset, factor, derivative, style).

        Call when the file we're plotting changes so that when the user
        returns to a file, curves are shown with default properties.
        """
        self._persistent_properties.clear()
