"""
MDA file table view for data field selection and 2D plotting controls.

This module provides the MDAFileTableView widget which displays a table of MDA file
data fields with checkboxes for selection. It supports both 1D and 2D data visualization
with specialized controls for 2D plotting including X2 slice selection, X1/X2 positioner
selection, Y detector selection, and I0 normalization.

For 1D data, users can select X, Y, I0 fields for plotting.
For 2D data, additional controls are available for:
- X2 slice selection (spinbox)
- X1/X2 positioner selection (comboboxes)
- Y detector selection (combobox)
- I0 normalization (combobox)
- Plot type selection (Heatmap/Contour)
- Color palette selection
- Log scale options

Uses :class:`mda_file_table_model.MDAFileTableModel` for data display.

.. autosummary::

    ~MDAFileTableView
    ~HEADERS
    ~COLUMNS
"""

from PyQt6.QtWidgets import QWidget, QHeaderView
import numpy as np

from mdaviz import utils
from mdaviz.mda_file_table_model import ColumnDataType
from mdaviz.mda_file_table_model import FieldRuleType
from mdaviz.mda_file_table_model import TableColumn
from mdaviz.mda_file_table_model import TableField
from mdaviz.logger import get_logger

# Get logger for this module
logger = get_logger("mda_file_table_view")

HEADERS = "Field", "X", "Y", "I0", "PV", "DESC", "Unit"

COLUMNS = [
    TableColumn("Field", ColumnDataType.text),
    TableColumn("X", ColumnDataType.checkbox, rule=FieldRuleType.unique),  # type: ignore[arg-type]
    TableColumn("Y", ColumnDataType.checkbox, rule=FieldRuleType.multiple),  # type: ignore[arg-type]
    TableColumn("I0", ColumnDataType.checkbox, rule=FieldRuleType.unique),  # type: ignore[arg-type]
    TableColumn("PV", ColumnDataType.text),
    TableColumn("DESC", ColumnDataType.text),
    TableColumn("Unit", ColumnDataType.text),
]


class MDAFileTableView(QWidget):
    ui_file = utils.getUiFileName(__file__)

    def __init__(self, parent):
        """
        Create the table view and connect with its parent.

        PARAMETERS

        parent object:
            Instance of mdaviz.mda_file.MDAFile
        """

        self.mda_file = parent
        super().__init__()
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()

    def setup(self):
        self.setData()
        # Configure the horizontal header to resize based on content.
        header = self.tableView.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        # Setup 2D controls
        self.setupX2Controls()

        # Setup Y DET controls after UI is fully loaded
        self.setup2DControls()

    def setupX2Controls(self):
        """Setup 2D data controls (X2 selection for 1D plot/slice)."""
        # Connect X2 spinbox to update function
        self.x2SpinBox.valueChanged.connect(self.onX2ValueChanged)

        # Initially hide 2D controls
        self.dimensionControls.setVisible(False)

    def setup2DControls(self):
        """Setup Y DET selection controls for 2D plotting."""
        logger.debug("setup2DControls - Starting setup")

        # Use QTimer to ensure UI is fully loaded
        from PyQt6.QtCore import QTimer

        QTimer.singleShot(100, self._setup2DControlsDelayed)

    def _setup2DControlsDelayed(self):
        """Setup Y DET controls after UI is fully loaded."""
        # Connect signals for 2D controls
        self.x1ComboBox.currentIndexChanged.connect(self.onX1SelectionChanged)
        self.x2ComboBox.currentIndexChanged.connect(self.onX2SelectionChanged)
        self.yDetComboBox.currentIndexChanged.connect(self.onYDetSelectionChanged)
        self.i0ComboBox.currentIndexChanged.connect(self.onI0SelectionChanged)
        self.plotTypeComboBox.currentIndexChanged.connect(self.onPlotTypeChanged)
        self.colorPaletteComboBox.currentIndexChanged.connect(
            self.onColorPaletteChanged
        )
        self.plotButton.clicked.connect(self.onPlotButtonClicked)

        # Connect log scale controls
        self.logYCheckBox.toggled.connect(self.onLogScaleChanged)

        # Populate plot type combobox
        self.plotTypeComboBox.addItems(["Heatmap", "Contour"])

        # Populate color palette combobox
        self.colorPaletteComboBox.addItems(
            [
                "viridis",
                "plasma",
                "inferno",
                "magma",
                "cividis",
                "coolwarm",
                "RdBu",
                "RdYlBu",
                "Spectral",
                "jet",
                "hot",
                "cool",
                "terrain",
            ]
        )

        # Initially hide Y DET controls
        self.yDetControls.setVisible(False)

    # ==========================================
    # Populate 2D-data comboBoxes
    # ==========================================

    def populateX1ComboBox(self):
        """Populate X1 combobox with available positioners from scanDictInner."""
        if not hasattr(self, "data") or self.data() is None:
            return

        fileInfo = self.data().get("fileInfo", {})
        if not fileInfo.get("isMultidimensional", False):
            return

        scanDictInner = fileInfo.get("scanDictInner", {})

        self.x1ComboBox.clear()

        # Add positioners (fieldName starts with "P")
        for key, value in scanDictInner.items():
            fieldName = value.get("fieldName", "")
            if fieldName.startswith("P"):  # Only positioners
                name = value.get("name", f"PV_{key}")
                unit = value.get("unit", "")
                display_text = f"{name} ({unit})" if unit else name
                self.x1ComboBox.addItem(display_text, key)

        logger.debug(
            f"populateX1ComboBox - Added {self.x1ComboBox.count()} X1 positioners"
        )

        # Set P1 as default (key 1) if available
        if self.x1ComboBox.count() > 0:
            # Find P1 (key 1) and set as default
            for i in range(self.x1ComboBox.count()):
                if self.x1ComboBox.itemData(i) == 1:  # P1 key
                    self.x1ComboBox.setCurrentIndex(i)
                    break

    def populateX2ComboBox(self):
        """Populate X2 combobox with available positioners from scanDict (outer dimension)."""
        if not hasattr(self, "data") or self.data() is None:
            return

        fileInfo = self.data().get("fileInfo", {})
        if not fileInfo.get("isMultidimensional", False):
            return

        scanDict = fileInfo.get("scanDict", {})
        self.x2ComboBox.clear()

        # Add Index option (P0)
        self.x2ComboBox.addItem("Index", 0)

        # Add positioners from scanDict (outer dimension)
        for key, value in scanDict.items():
            fieldName = value.get("fieldName", "")
            if (
                fieldName.startswith("P") and key > 0
            ):  # Only positioners, skip P0 (Index)
                name = value.get("name", f"PV_{key}")
                unit = value.get("unit", "")
                display_text = f"{name} ({unit})" if unit else name
                self.x2ComboBox.addItem(display_text, key)

        logger.debug(
            f"populateX2ComboBox - Added {self.x2ComboBox.count()} X2 positioners"
        )

        # Set P1 as default (key 1) if available
        if self.x2ComboBox.count() > 0:
            # Find P1 (key 1) and set as default
            for i in range(self.x2ComboBox.count()):
                if self.x2ComboBox.itemData(i) == 1:  # P1 key
                    self.x2ComboBox.setCurrentIndex(i)
                    break

    def populateYDetComboBox(self):
        """Populate Y detector combobox with available detectors from scanDict2D."""
        if not hasattr(self, "data") or self.data() is None:
            return

        fileInfo = self.data().get("fileInfo", {})
        if not fileInfo.get("isMultidimensional", False):
            return

        scanDict2D = fileInfo.get("scanDict2D", {})
        self.yDetComboBox.clear()

        # Add detectors (fieldName starts with "D") directly from scanDict2D
        for key, value in scanDict2D.items():
            fieldName = value.get("fieldName", "")
            if fieldName.startswith("D"):  # Only detectors
                name = value.get("name", f"Detector_{key}")
                unit = value.get("unit", "")
                display_text = f"{name} ({unit})" if unit else name
                self.yDetComboBox.addItem(display_text, key)
                logger.debug(
                    f"populateYDetComboBox - Added detector: {name} (key={key})"
                )

        logger.debug(
            f"populateYDetComboBox - Added {self.yDetComboBox.count()} Y detectors"
        )

    def populateI0ComboBox(self):
        """Populate I0 detector combobox with available detectors from scanDict2D."""
        if not hasattr(self, "data") or self.data() is None:
            return

        fileInfo = self.data().get("fileInfo", {})
        if not fileInfo.get("isMultidimensional", False):
            return

        scanDict2D = fileInfo.get("scanDict2D", {})
        self.i0ComboBox.clear()

        # Add "None" option for no normalization
        self.i0ComboBox.addItem("None", None)

        # Add detectors (fieldName starts with "D") directly from scanDict2D
        for key, value in scanDict2D.items():
            fieldName = value.get("fieldName", "")
            if fieldName.startswith("D"):  # Only detectors
                name = value.get("name", f"Detector_{key}")
                unit = value.get("unit", "")
                display_text = f"{name} ({unit})" if unit else name
                self.i0ComboBox.addItem(display_text, key)
                logger.debug(f"populateI0ComboBox - Added detector: {name} (key={key})")

        logger.debug(
            f"populateI0ComboBox - Added {self.i0ComboBox.count()} I0 detectors"
        )

    def populate2DControls(self):
        """Populate all 2D control comboboxes with data from current file."""
        # Populate all comboboxes
        self.populateX1ComboBox()
        self.populateX2ComboBox()
        self.populateYDetComboBox()
        self.populateI0ComboBox()

        logger.debug("populate2DControls - All 2D controls populated")

    # ==========================================
    # x2 controls & spinBox
    # ==========================================

    def update2DControls(
        self,
        is_multidimensional=False,
        dimensions=None,
        acquired_dimensions=None,
        x2_positioner_info=None,
    ):
        """
        Update 2D controls visibility and settings based on data dimensions.

        Parameters:
            is_multidimensional (bool): Whether the data is multidimensional
            dimensions (list): List of intended dimensions [X2_points, X1_points, ...]
            acquired_dimensions (list): List of actual acquired dimensions [X2_points, X1_points, ...]
            x2_positioner_info (dict): Information about the X2 positioner (name, unit, data)
        """
        logger.debug(
            f"update2DControls - is_multidimensional: {is_multidimensional}, dimensions: {dimensions}"
        )
        logger.debug(f"update2DControls - acquired_dimensions: {acquired_dimensions}")
        logger.debug(f"update2DControls - x2_positioner_info: {x2_positioner_info}")
        if is_multidimensional and dimensions and len(dimensions) >= 2:
            # Show 2D controls
            self.dimensionControls.setVisible(True)

            # Update X2 spinbox range
            # Use acquired_dimensions if available, otherwise fall back to intended dimensions
            if acquired_dimensions and len(acquired_dimensions) >= 2:
                x2_max = acquired_dimensions[0] - 1  # Use actual acquired points
                logger.debug(
                    f"update2DControls - using acquired_dimensions, x2_max: {x2_max}"
                )
            elif dimensions and len(dimensions) >= 2:
                x2_max = dimensions[0] - 1  # Fallback to intended dimensions
                logger.debug(
                    f"update2DControls - using intended dimensions, x2_max: {x2_max}"
                )
            else:
                x2_max = 0  # Default fallback
                logger.debug(
                    f"update2DControls - using default fallback, x2_max: {x2_max}"
                )

            self.x2SpinBox.setMaximum(max(0, x2_max))
            self.x2SpinBox.setValue(0)  # Start at first X2 position

            # Store X2 positioner info for later use
            self._x2_positioner_info = x2_positioner_info

            # Update X2 label with PV name
            if x2_positioner_info:
                pv_name = x2_positioner_info.get("name", "X2")
                self.x2Label.setText(f"X2 ({pv_name}):")
                self._updateX2ValueLabel(0, x2_positioner_info)
            else:
                self.x2Label.setText("X2:")
                self.x2ValueLabel.setText("--")

            # Populate 2D control comboboxes
            self.populate2DControls()
        else:
            # Hide 2D controls (X2 spinBox) for 1D data
            self.dimensionControls.setVisible(False)
            # Clear X2 value label
            self.x2ValueLabel.setText("--")
            # Clear stored X2 positioner info
            if hasattr(self, "_x2_positioner_info"):
                delattr(self, "_x2_positioner_info")

    def onX2ValueChanged(self, value):
        """Handle X2 spinbox value changes."""
        # Update the X2 value label if we have X2 positioner info
        if hasattr(self, "_x2_positioner_info") and self._x2_positioner_info:
            self._updateX2ValueLabel(value, self._x2_positioner_info)

        # Emit signal to update 1D plot with new X2 slice
        if hasattr(self.mda_file, "x2ValueChanged"):
            self.mda_file.x2ValueChanged.emit(value)

    def _updateX2ValueLabel(self, x2_index, x2_positioner_info):
        """
        Update the X2 value label with the current positioner value.

        Parameters:
            x2_index (int): The current X2 index
            x2_positioner_info (dict): Information about the X2 positioner
        """
        try:
            # Get the positioner value at the current index
            positioner_data = x2_positioner_info.get("data", [])
            if x2_index < len(positioner_data):
                value = positioner_data[x2_index]
                unit = x2_positioner_info.get("unit", "")

                # Format the value with unit
                if unit:
                    label_text = f"{value:.3f} {unit}"
                else:
                    label_text = f"{value:.3f}"

                self.x2ValueLabel.setText(label_text)
            else:
                self.x2ValueLabel.setText("--")
        except (IndexError, TypeError, ValueError):
            # Fallback if there's an error
            self.x2ValueLabel.setText("--")

    def getX2Value(self):
        """Get the current X2 value from the spinbox."""
        return self.x2SpinBox.value()

    # ==========================================
    # 2D data plot & event handlers
    # ==========================================

    def get2DSelections(self):
        """Get current 2D plotting selections."""
        # Get color palette with validation
        color_palette = self.colorPaletteComboBox.currentText()
        if not color_palette or color_palette.strip() == "":
            color_palette = "viridis"
            logger.debug(
                f"get2DSelections - Empty color palette, using default: {color_palette}"
            )

        plot_type = self.plotTypeComboBox.currentText().lower()
        if not plot_type or plot_type.strip() == "":
            plot_type = "heatmap"

        selections = {
            "X1": self.x1ComboBox.currentData(),
            "X2": self.x2ComboBox.currentData(),
            "Y": (
                [self.yDetComboBox.currentData()]
                if self.yDetComboBox.currentData() is not None
                else []
            ),
            "I0": self.i0ComboBox.currentData(),
            "plot_type": plot_type,
            "color_palette": color_palette,
            "log_y": self.logYCheckBox.isChecked(),
        }
        logger.debug(f"get2DSelections - {selections}")
        return selections

    # Y DET Controls Signal Handlers
    def _trigger2DPlot(self):
        """Helper method to trigger 2D plotting with current selections."""

        # Check if we're on the 2D tab - only trigger 2D plotting when on 2D tab
        try:
            parent = self.parent()
            while parent and not hasattr(parent, "mda_file_viz"):
                parent = parent.parent()

            if parent and hasattr(parent, "mda_file_viz"):
                # Check which tab is currently active
                current_tab_index = parent.mda_file_viz.tabWidget.currentIndex()
                if (
                    current_tab_index != 3
                ):  # 1D tab is index 0, Data tab is index 1, Metadata tab is index 2, 2D tab is index 3
                    return
        except Exception as e:
            logger.debug(f"_trigger2DPlot - Error checking tab: {e}")
            return

        # Get current selections
        selections = self.get2DSelections()

        # Validate selections
        if selections["Y"] is None or len(selections["Y"]) == 0:
            return

        if selections["X1"] is None:
            return

        if selections["X2"] is None:
            return

        # Trigger 2D plotting
        try:
            # Find the parent MDA_MVC to trigger plotting
            parent = self.parent()
            while parent and not hasattr(parent, "doPlot"):
                parent = parent.parent()

            if parent and hasattr(parent, "doPlot"):
                parent.doPlot("replace", selections)
            else:
                logger.debug(
                    "_trigger2DPlot - Could not find parent with doPlot method"
                )
        except Exception as e:
            logger.debug(f"_trigger2DPlot - Error: {e}")

    def onX1SelectionChanged(self, index):
        """Handle X1 positioner selection change."""
        logger.debug(f"onX1SelectionChanged - index: {index}")
        self._trigger2DPlot()

    def onX2SelectionChanged(self, index):
        """Handle X2 positioner selection change."""
        logger.debug(f"onX2SelectionChanged - index: {index}")
        self._trigger2DPlot()

    def onYDetSelectionChanged(self, index):
        """Handle Y detector selection change."""
        logger.debug(f"onYDetSelectionChanged - index: {index}")
        self._trigger2DPlot()

    def onI0SelectionChanged(self, index):
        """Handle I0 detector selection change."""
        logger.debug(f"onI0SelectionChanged - index: {index}")
        self._trigger2DPlot()

    def onPlotTypeChanged(self, index):
        """Handle plot type selection change."""
        plot_type = self.plotTypeComboBox.currentText().lower()
        logger.debug(f"onPlotTypeChanged - plot_type: {plot_type}")
        self._trigger2DPlot()

    def onColorPaletteChanged(self, index):
        """Handle color palette selection change."""
        palette_name = self.colorPaletteComboBox.currentText()
        logger.debug(f"onColorPaletteChanged - palette_name: {palette_name}")
        self._trigger2DPlot()

    def onLogScaleChanged(self, checked):
        """Handle log scale checkbox changes."""
        sender = self.sender()
        if sender == self.logYCheckBox:
            logger.debug(f"onLogScaleChanged - LogY: {checked}")
        self._trigger2DPlot()

    def onPlotButtonClicked(self):
        """Handle plot button click."""
        logger.debug("onPlotButtonClicked - Plot button clicked")
        self._trigger2DPlot()

    # ==========================================
    # Data management & table display
    # ==========================================

    def data(self):
        """Return the data from the table view:
        self.data=  {"fileInfo": fileInfo, "fields": fields}
        """
        return self._data

    def setData(self):
        """
        Populates the `_data` attribute with file information and data extracted
        from a file.

        The populated `_data` dictionary includes:
            - fileInfo (dict): A dictionary of all the file information:
                - fileName (str): The name of the file without its extension.
                - filePath (str): The full path of the file.
                - folderPath (str): The full path of the parent folder.
                - metadata (dict): The extracted metadata from the file.
                - scanDict (dict): A dictionary of positioner & detector dataset for plot.
                - scanDict2D (dict): For 2D data
                - scanDictInner (dict): For 2D data
                - isMultidimensional (bool)
                - firstPos (float): The first positioner (P1, or if no positioner, P0 = index).
                - firstDet (float): The first detector (D01).
                - pvList (list of str): List of detectors PV names as strings.
            - field (list): List of TableField object, one for each det/pos:
                    ([TableField(name='P0', selection=None,...
                    ...desc='Index', pv='Index', unit='a.u'),...])
        """

        self._data = {}
        if self.mda_file.data() != {}:
            fileInfo = self.mda_file.data()

            # For table display, use inner dimension data for 2D files, 1D data for 1D files
            logger.debug(
                f"isMultidimensional: {fileInfo.get('isMultidimensional', False)}"
            )
            logger.debug(f"scanDictInner exists: {'scanDictInner' in fileInfo}")
            if fileInfo.get("isMultidimensional", False) and fileInfo.get(
                "scanDictInner"
            ):
                scanDict = fileInfo["scanDictInner"]
                logger.debug(
                    f"Using scanDictInner for 2D data, keys: {list(scanDict.keys())}"
                )
            else:
                scanDict = fileInfo["scanDict"]
                logger.debug(
                    f"Using scanDict for 1D data, keys: {list(scanDict.keys())}"
                )

            fields = [
                TableField(
                    v["fieldName"],
                    selection=None,
                    pv=v["name"],
                    desc=v["desc"],
                    unit=v["unit"],
                )
                for v in scanDict.values()
            ]
        self._data = {"fileInfo": fileInfo, "fields": fields}

    def displayTable(self, selection_field):
        from mdaviz.mda_file_table_model import MDAFileTableModel
        from mdaviz.empty_table_model import EmptyTableModel

        if self.data() is not None:
            fields = self.data()["fields"]
            data_model = MDAFileTableModel(
                COLUMNS, fields, selection_field, self.mda_file.mda_mvc
            )
            self.tableView.setModel(data_model)
            # Hide Field column (Field = vertical header)
            # Note: I0 column (index 3) is now visible
            for i in [0]:
                self.tableView.hideColumn(i)
        else:
            # No MDA files to display, show an empty table with headers
            empty_model = EmptyTableModel(HEADERS)
            self.tableView.setModel(empty_model)

    def setStatus(self, text):
        self.mda_file.mda_mvc.setStatus(text)

    def clearContents(self):
        self.tableView.model().clearAllCheckboxes()
        self.tableView.setModel(None)

    # ==========================================
    # Data extraction for plotting
    # ==========================================

    def data2Plot2D(self, selections):
        """
        Extracts 2D datasets for plotting from scanDict2D based on user selections.

        Parameters:
            - selections: A dictionary with keys:
                - "X": The index for the x1-axis data
                - "X2": The index for the x2-axis data
                - "Y": A list of indices for the y-axis data (only the 1st element is used)
                - "I0" (optional): The index for normalization data
                - e.g. selections = {"X": 1, "X2": 2 ,"Y": [3], "I0": 4}

        Returns:
            - A tuple of (datasets, plot_options), where datasets contains 2D data arrays,
              and plot_options contains overall plotting configurations.

        """
        datasets, plot_options = [], {}

        if self.data() is not None:
            # ------ extract scan info:
            fileInfo = self.data()["fileInfo"]
            fileName = fileInfo["fileName"]
            filePath = fileInfo["filePath"]
            acquired_dim = fileInfo.get("acquiredDimensions", [])

            # Check if this is 2D data
            if not fileInfo.get("isMultidimensional", False):
                logger.debug("data2Plot2D - Not 2D data, returning empty")
                return datasets, plot_options

            # Use scanDict2D for 2D plotting
            scanDict2D = fileInfo.get("scanDict2D", {})
            scanDictInner = fileInfo.get("scanDictInner", {})

            logger.debug(f"data2Plot2D - scanDict2D keys: {list(scanDict2D.keys())}")
            logger.debug(
                f"data2Plot2D - scanDictInner keys: {list(scanDictInner.keys())}"
            )
            logger.debug(f"data2Plot2D - selections: {selections}")

            # ------ extract x data (from scanDictInner - this is the X positioner):
            x_index = selections.get("X")
            if x_index is not None and x_index in scanDictInner:
                x_data_2d = scanDictInner[x_index].get("data")
                x_name = scanDictInner[x_index].get("name", f"P{x_index}")
                x_unit = scanDictInner[x_index].get("unit", "")

                # For 2D plotting, we need 1D X data - take the first row
                if x_data_2d is not None and len(np.array(x_data_2d).shape) == 2:
                    x_data = np.array(x_data_2d)[0, :]  # Take first row for 1D X data
                else:
                    x_data = x_data_2d

                logger.debug(
                    f"data2Plot2D - X data shape: {np.array(x_data).shape if x_data is not None else 'None'}"
                )
                if acquired_dim and len(acquired_dim) >= 2 and x_data is not None:
                    acquired_x1_points = acquired_dim[1]
                    x_array = np.array(x_data)
                    if len(x_array) > acquired_x1_points:
                        x_data = x_array[:acquired_x1_points]

            else:
                x_data = None
                x_name = "X"
                x_unit = ""

            # ------ extract y data (detector data from scanDict2D):
            y_index = selections.get("Y", [])
            if y_index and len(y_index) > 0:
                y_idx = y_index[0]  # Take first selected detector for 2D plot
                if y_idx in scanDict2D:
                    y_data = scanDict2D[y_idx].get("data")
                    y_name = scanDict2D[y_idx].get("name", f"D{y_idx}")
                    y_unit = scanDict2D[y_idx].get("unit", "")
                    logger.debug(
                        f"data2Plot2D - Y data shape: {np.array(y_data).shape if y_data else 'None'}"
                    )
                else:
                    y_data = None
                    y_name = "Y"
                    y_unit = ""
            else:
                y_data = None
                y_name = "Y"
                y_unit = ""

            # ------ extract I0 data for normalization (from scanDict2D):
            i0_index = selections.get("I0")
            i0_data = None
            i0_name = None
            is_normalized = False

            if i0_index is not None and i0_index in scanDict2D:
                i0_data = scanDict2D[i0_index].get("data")
                i0_name = scanDict2D[i0_index].get("name", f"D{i0_index}")
                logger.debug(
                    f"data2Plot2D - I0 data shape: {np.array(i0_data).shape if i0_data else 'None'}"
                )

                # Perform normalization if both Y and I0 data are available
                if y_data is not None and i0_data is not None:
                    y_array = np.array(y_data)
                    i0_array = np.array(i0_data)

                    # Check if shapes are compatible
                    if y_array.shape == i0_array.shape:
                        # Handle division by zero (same logic as 1D normalization)
                        # Replace zeros in I0 with 1 to avoid division by zero
                        i0_safe = np.where(i0_array == 0, 1, i0_array)

                        # Perform normalization
                        y_data = y_array / i0_safe
                        is_normalized = True
                        logger.debug(
                            f"data2Plot2D - Normalized Y data by I0: {i0_name}"
                        )
                    else:
                        logger.debug(
                            f"data2Plot2D - I0 shape {i0_array.shape} incompatible with Y shape {y_array.shape}"
                        )
                        i0_data = None
                        i0_name = None

            else:
                logger.debug(
                    f"data2Plot2D - No I0 normalization (I0 index: {i0_index})"
                )

            if acquired_dim and len(acquired_dim) >= 2 and y_data is not None:
                acquired_x2_points = acquired_dim[0]
                acquired_x1_points = acquired_dim[1]
                y_array = np.array(y_data)
                if (
                    y_array.shape[0] > acquired_x2_points
                    or y_array.shape[1] > acquired_x1_points
                ):
                    y_data = y_array[:acquired_x2_points, :acquired_x1_points]

            # ------ extract x2 data (from scanDict - this is the X2 positioner):
            x2_data = None
            x2_name = "X2"
            x2_unit = ""

            x2_index = selections.get("X2")
            logger.debug(f"data2Plot2D - Selected X2 index: {x2_index}")

            # Get scanDict for X2 data extraction
            scanDict = fileInfo.get("scanDict", {})

            if x2_index is not None and x2_index in scanDict:
                x2_data_2d = scanDict[x2_index].get("data")
                x2_name = scanDict[x2_index].get("name", f"P{x2_index}")
                x2_unit = scanDict[x2_index].get("unit", "")

                # For 2D plotting, we need 1D X2 data - take the first column
                if x2_data_2d is not None and len(np.array(x2_data_2d).shape) == 2:
                    x2_data = np.array(x2_data_2d)[
                        :, 0
                    ]  # Take first column for 1D X2 data
                else:
                    x2_data = x2_data_2d

                # If we have acquired_dim, slice X2 data to match actual acquired points
                if acquired_dim and len(acquired_dim) >= 2 and x2_data is not None:
                    acquired_x2_points = acquired_dim[0]  # first element = X2 dimension
                    x2_data_array = np.array(x2_data)
                    if len(x2_data_array) > acquired_x2_points:
                        logger.debug(
                            f"data2Plot2D - Truncating X2 data from {len(x2_data_array)} to {acquired_x2_points} points"
                        )
                        x2_data = x2_data_array[:acquired_x2_points]

                logger.debug(
                    f"data2Plot2D - X2 data shape: {np.array(x2_data).shape if x2_data is not None else 'None'}"
                )
            else:
                logger.debug(f"data2Plot2D - X2 index {x2_index} not found in scanDict")
                # Fallback to the original logic for backward compatibility
                for key, value in scanDict2D.items():
                    if value.get("type") == "POS" and key == 0:
                        x2_data_2d = value.get("data")
                        x2_name = value.get("name", "X2")
                        x2_unit = value.get("unit", "")

                        # Apply same slicing logic for fallback
                        if (
                            x2_data_2d is not None
                            and len(np.array(x2_data_2d).shape) == 2
                        ):
                            x2_data = np.array(x2_data_2d)[
                                :, 0
                            ]  # Take first column for 1D X2 data
                        else:
                            x2_data = x2_data_2d

                        logger.debug(
                            f"data2Plot2D - Using fallback X2 (key 0): {x2_name}"
                        )
                        break

            # Create 2D dataset if we have all required data
            if x_data is not None and y_data is not None and x2_data is not None:
                # Validate data shapes and dimensions
                x_array = np.array(x_data)
                y_array = np.array(y_data)
                x2_array = np.array(x2_data)

                logger.debug("data2Plot2D - Validation:")
                logger.debug(f"  X array shape: {x_array.shape}")
                logger.debug(f"  Y array shape: {y_array.shape}")
                logger.debug(f"  X2 array shape: {x2_array.shape}")

                # Check for edge cases
                validation_errors = []

                # Check if Y data is 2D
                if len(y_array.shape) != 2:
                    validation_errors.append(f"Y data is not 2D: shape {y_array.shape}")

                # Check if X data is 1D
                if len(x_array.shape) != 1:
                    validation_errors.append(f"X data is not 1D: shape {x_array.shape}")

                # Check if X2 data is 1D
                if len(x2_array.shape) != 1:
                    validation_errors.append(
                        f"X2 data is not 1D: shape {x2_array.shape}"
                    )

                # Check dimension compatibility
                if len(validation_errors) == 0:
                    if y_array.shape[0] != x2_array.shape[0]:
                        validation_errors.append(
                            f"Y rows ({y_array.shape[0]}) != X2 length ({x2_array.shape[0]})"
                        )

                    if y_array.shape[1] != x_array.shape[0]:
                        validation_errors.append(
                            f"Y cols ({y_array.shape[1]}) != X length ({x_array.shape[0]})"
                        )

                # Check for empty or single-point data
                if len(validation_errors) == 0:
                    if y_array.size == 0:
                        validation_errors.append("Y data is empty")
                    elif y_array.size == 1:
                        validation_errors.append("Y data has only one point")

                    if x_array.size == 0:
                        validation_errors.append("X data is empty")
                    elif x_array.size == 1:
                        validation_errors.append("X data has only one point")

                    if x2_array.size == 0:
                        validation_errors.append("X2 data is empty")
                    elif x2_array.size == 1:
                        validation_errors.append("X2 data has only one point")

                # Check for NaN or infinite values
                if len(validation_errors) == 0:
                    if np.any(np.isnan(y_array)):
                        validation_errors.append("Y data contains NaN values")
                    if np.any(np.isinf(y_array)):
                        validation_errors.append("Y data contains infinite values")

                # If validation passes, create the dataset
                if len(validation_errors) == 0:
                    logger.debug("data2Plot2D - Validation passed")
                    datasets.append(
                        (
                            y_array,
                            {
                                "label": f"{y_name} ({y_unit})",
                                "x_data": x_array,
                                "x2_data": x2_array,
                                "x_name": x_name,
                                "x2_name": x2_name,
                                "x_unit": x_unit,
                                "x2_unit": x2_unit,
                            },
                        )
                    )

                    plot_options = {
                        "x": x_name,
                        "x_unit": x_unit,
                        "y": y_name,
                        "y_unit": y_unit,
                        "x2": x2_name,
                        "x2_unit": x2_unit,
                        "title": f"{fileName}: {y_name} ({y_unit})",
                        "filePath": filePath,
                        "fileName": fileName,
                        "folderPath": fileInfo.get("folderPath", ""),
                        "log_y": selections.get("log_y", False),
                    }

                    # Update title and add normalization info if normalized
                    if is_normalized and i0_name:
                        plot_options["title"] = f"{fileName}: {y_name} [norm]"
                        plot_options["i0_name"] = i0_name
                        plot_options["is_normalized"] = True
                else:
                    logger.debug("data2Plot2D - Validation failed:")
                    for error in validation_errors:
                        logger.debug(f"  ❌ {error}")
                    return datasets, plot_options
            else:
                logger.debug("data2Plot2D - Missing required data:")
                logger.debug(f"  X data: {'✅' if x_data is not None else '❌'}")
                logger.debug(f"  Y data: {'✅' if y_data is not None else '❌'}")
                logger.debug(f"  X2 data: {'✅' if x2_data is not None else '❌'}")

        return datasets, plot_options

    def data2Plot(self, selections):
        """
        Extracts selected datasets for plotting from scanDict based on user selections.
        Slice (if multidimensional) and/or normalize the data as needed.

        Parameters:
            - selections: A dictionary with keys:
                - "X": The index for the x-axis data
                - "Y": A list of indices for the y-axis data
                - "I0" (optional): The index for normalization data
                - e.g. selections = {"X": 1, "Y": [2, 3, 5], "I0": 4}
        Returns:
            - A tuple of (datasets, plot_options), where datasets is a list of tuples containing the
              data and options (label) for each dataset, and plot_options contains overall plotting configurations.

        """

        datasets, plot_options = [], {}

        if self.data() is not None:
            # ------ extract scan info:
            fileInfo = self.data()["fileInfo"]
            fileName = fileInfo["fileName"]
            filePath = fileInfo["filePath"]

            # For 2D data, we need to use the inner dimension data for 1D plotting
            # For 1D data, use scanDict as usual
            if fileInfo.get("isMultidimensional", False) and fileInfo.get(
                "scanDictInner"
            ):
                # Use inner dimension data for 1D plotting (matches table display)
                scanDict = fileInfo["scanDictInner"]
                x2_slice = 0  # Initial value

                # Debug: Print field mappings
                logger.debug(
                    f"Using scanDictInner for 2D plotting, keys: {list(scanDict.keys())}"
                )
                logger.debug(f"selections: {selections}")

                # Debug: Print data shapes for first few fields
                for i in range(min(3, len(scanDict))):
                    if i in scanDict:
                        data = scanDict[i].get("data")
                        logger.debug(
                            f"Field {i} data shape: {np.array(data).shape if data else 'None'}"
                        )
            else:
                # Use 1D data structure
                scanDict = fileInfo["scanDict"]
                x2_slice = 0

            # ------ extract x data:
            x_index = selections.get("X")
            x_data = scanDict[x_index].get("data") if x_index in scanDict else None

            # For 2D data in scanDictInner, slice to get 1D data
            if x_data is not None and len(np.array(x_data).shape) > 1:
                x2_slice = self.getX2Value()  # Get current X2 value from spinbox
                x_data_array = np.array(x_data)
                if x2_slice >= x_data_array.shape[0]:
                    x2_slice = x_data_array.shape[0] - 1  # Use last available slice
                x_data = x_data[x2_slice]  # Take the selected X2 slice

            # ------ extract I0 data for normalization:
            i0_index = selections.get("I0")
            i0_data = scanDict[i0_index].get("data") if i0_index in scanDict else None

            # For 2D data in scanDictInner, slice to get 1D data
            if i0_data is not None and len(np.array(i0_data).shape) > 1:
                x2_slice = self.getX2Value()  # Get current X2 value from spinbox
                i0_data_array = np.array(i0_data)
                if x2_slice >= i0_data_array.shape[0]:
                    x2_slice = i0_data_array.shape[0] - 1  # Use last available slice
                i0_data = i0_data[x2_slice]  # Take the selected X2 slice

            # ------ extract y(s) data:
            y_index = selections.get("Y", [])
            y_first_unit = y_first_name = ""

            # Process all Y curves
            for i, y in enumerate(y_index):
                if y not in scanDict:
                    continue

                y_data = scanDict[y].get("data")
                y_name = scanDict[y].get("name", "n/a")
                y_unit = scanDict[y].get("unit", "")

                # For 2D data in scanDictInner, slice to get 1D data
                if y_data is not None and len(np.array(y_data).shape) > 1:
                    x2_slice = self.getX2Value()  # Get current X2 value from spinbox

                    # Add bounds checking to prevent IndexError
                    y_data_array = np.array(y_data)
                    if x2_slice >= y_data_array.shape[0]:
                        x2_slice = y_data_array.shape[0] - 1  # Use last available slice
                    y_data = y_data[x2_slice]  # Take the selected X2 slice

                # Apply I0 normalization if I0 is selected
                if i0_data is not None:
                    # Avoid division by zero
                    i0_data_safe = np.array(i0_data)
                    i0_data_safe[i0_data_safe == 0] = (
                        1  # Replace zeros with 1 to avoid division by zero
                    )
                    y_data = np.array(y_data) / i0_data_safe
                    # Display label shows base detector name with [norm] suffix for normalized data
                    y_label = f"{fileName}: {y_name} [norm]"
                    y_unit = ""  # Normalized data typically has no units
                else:
                    y_data = np.array(y_data)
                    y_unit = f"({y_unit})" if y_unit else ""
                    y_label = f"{fileName}: {y_name} {y_unit}"

                # Add X2 index to label for 2D data
                if fileInfo.get("isMultidimensional", False):
                    x2_index = self.getX2Value()
                    y_label = f"{y_label} [{x2_index}]"

                if i == 0:
                    y_first_unit = y_unit
                    # y_first_name is used for y-axis label and shows normalization status
                    if i0_data is not None:
                        y_first_name = f"{y_name} [norm]"
                    else:
                        y_first_name = f"{y_name} {y_unit}"

                # append to dataset:
                ds, ds_options = [], {}
                ds_options["label"] = y_label
                ds = [x_data, y_data] if x_data is not None else [y_data]
                datasets.append((ds, ds_options))

            # scanDict = {index: {'object': scanObject, 'data': [...], 'unit': '...', 'name': '...','type':...}}
            plot_options = {
                "x": scanDict[x_index].get("name", "") if x_index in scanDict else "",
                "x_unit": (
                    scanDict[x_index].get("unit", "") if x_index in scanDict else ""
                ),
                "y": y_first_name,
                "y_unit": y_first_unit,
                "title": "",
                "filePath": filePath,
                "fileName": fileName,
            }

            # Add X2 index to plot options for 2D data
            if fileInfo.get("isMultidimensional", False):
                plot_options["x2_index"] = self.getX2Value()
                logger.debug(
                    f"data2Plot - Added x2_index to plot_options: {plot_options['x2_index']}"
                )
            else:
                logger.debug("data2Plot - Not multidimensional, x2_index not added")

        return datasets, plot_options
