"""
Select data fields for plotting: QTableView.

Uses :class:`mda_file_table_model.MDAFileTableModel`.

.. autosummary::

    ~MDAFileTableView
"""

from PyQt6.QtWidgets import QWidget, QHeaderView
import numpy as np

from mdaviz import utils
from mdaviz.mda_file_table_model import ColumnDataType
from mdaviz.mda_file_table_model import FieldRuleType
from mdaviz.mda_file_table_model import TableColumn
from mdaviz.mda_file_table_model import TableField

HEADERS = "Field", "X", "Y", "I0", "Un", "PV", "DESC", "Unit"

COLUMNS = [
    TableColumn("Field", ColumnDataType.text),
    TableColumn("X", ColumnDataType.checkbox, rule=FieldRuleType.unique),  # type: ignore[arg-type]
    TableColumn("Y", ColumnDataType.checkbox, rule=FieldRuleType.multiple),  # type: ignore[arg-type]
    TableColumn("I0", ColumnDataType.checkbox, rule=FieldRuleType.unique),  # type: ignore[arg-type]
    TableColumn("Un", ColumnDataType.checkbox, rule=FieldRuleType.multiple),  # type: ignore[arg-type]
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
        self.setup2DControls()

        # Setup Y DET controls after UI is fully loaded
        self.setupYDetControls()

    def setup2DControls(self):
        """Setup 2D data controls (X2 selection)."""
        # Connect X2 spinbox to update function
        self.x2SpinBox.valueChanged.connect(self.onX2ValueChanged)

        # Initially hide 2D controls
        self.dimensionControls.setVisible(False)

    def setupYDetControls(self):
        """Setup Y DET selection controls for 2D plotting."""
        print("DEBUG: setupYDetControls - Starting setup")

        # Use QTimer to ensure UI is fully loaded
        from PyQt6.QtCore import QTimer

        QTimer.singleShot(100, self._setupYDetControlsDelayed)

    def _setupYDetControlsDelayed(self):
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

        print(
            f"DEBUG: populateX1ComboBox - Added {self.x1ComboBox.count()} X1 positioners"
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

        print(
            f"DEBUG: populateX2ComboBox - Added {self.x2ComboBox.count()} X2 positioners"
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
        scanDictInner = fileInfo.get("scanDictInner", {})
        self.yDetComboBox.clear()

        # Add detectors (fieldName starts with "D")
        for key, value in scanDict2D.items():
            # Find corresponding detector info from scanDictInner
            detector_info = scanDictInner.get(key, {})
            fieldName = detector_info.get("fieldName", "")
            if fieldName.startswith("D"):  # Only detectors
                name = detector_info.get("name", f"Detector_{key}")
                unit = detector_info.get("unit", "")
                display_text = f"{name} ({unit})" if unit else name
                self.yDetComboBox.addItem(display_text, key)

        print(
            f"DEBUG: populateYDetComboBox - Added {self.yDetComboBox.count()} Y detectors"
        )

    def populateI0ComboBox(self):
        """Populate I0 detector combobox with available detectors from scanDict2D."""
        if not hasattr(self, "data") or self.data() is None:
            return

        fileInfo = self.data().get("fileInfo", {})
        if not fileInfo.get("isMultidimensional", False):
            return

        scanDict2D = fileInfo.get("scanDict2D", {})
        scanDictInner = fileInfo.get("scanDictInner", {})
        self.i0ComboBox.clear()

        # Add "None" option for no normalization
        self.i0ComboBox.addItem("None", None)

        # Add detectors (fieldName starts with "D")
        for key, value in scanDict2D.items():
            # Find corresponding detector info from scanDictInner
            detector_info = scanDictInner.get(key, {})
            fieldName = detector_info.get("fieldName", "")
            if fieldName.startswith("D"):  # Only detectors
                name = detector_info.get("name", f"Detector_{key}")
                unit = detector_info.get("unit", "")
                display_text = f"{name} ({unit})" if unit else name
                self.i0ComboBox.addItem(display_text, key)

        print(
            f"DEBUG: populateI0ComboBox - Added {self.i0ComboBox.count()} I0 detectors"
        )

    def populate2DControls(self):
        """Populate all 2D control comboboxes with data from current file."""
        # Populate all comboboxes
        self.populateX1ComboBox()
        self.populateX2ComboBox()
        self.populateYDetComboBox()
        self.populateI0ComboBox()

        print("DEBUG: populate2DControls - All 2D controls populated")

    def update2DControls(
        self, is_multidimensional=False, dimensions=None, x2_positioner_info=None
    ):
        """
        Update 2D controls visibility and settings based on data dimensions.

        Parameters:
            is_multidimensional (bool): Whether the data is multidimensional
            dimensions (list): List of dimensions [X2_points, X1_points, ...]
            x2_positioner_info (dict): Information about the X2 positioner (name, unit, data)
        """
        print(
            f"DEBUG: update2DControls - is_multidimensional: {is_multidimensional}, dimensions: {dimensions}"
        )
        print(f"DEBUG: update2DControls - x2_positioner_info: {x2_positioner_info}")
        if is_multidimensional and dimensions and len(dimensions) >= 2:
            # Show 2D controls
            self.dimensionControls.setVisible(True)

            # Update X2 spinbox range
            # dimensions[0] is X2 dimension, dimensions[1] is X1 dimension
            x2_max = dimensions[0] - 1 if len(dimensions) > 0 else 0
            print(f"DEBUG: update2DControls - x2_max: {x2_max}")
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
            # Hide 2D controls for 1D data
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

    # Y DET Controls Signal Handlers
    def _trigger2DPlot(self):
        """Helper method to trigger 2D plotting with current selections."""
        print("DEBUG: _trigger2DPlot - Triggering 2D plot")

        # Get current selections
        selections = self.get2DSelections()

        # Validate selections
        if selections["Y"] is None or len(selections["Y"]) == 0:
            print("DEBUG: _trigger2DPlot - No Y detector selected")
            return

        if selections["X1"] is None:
            print("DEBUG: _trigger2DPlot - No X1 positioner selected")
            return

        if selections["X2"] is None:
            print("DEBUG: _trigger2DPlot - No X2 positioner selected")
            return

        # Trigger 2D plotting
        try:
            # Find the parent MDA_MVC to trigger plotting
            parent = self.parent()
            while parent and not hasattr(parent, "doPlot"):
                parent = parent.parent()

            if parent and hasattr(parent, "doPlot"):
                print(
                    f"DEBUG: _trigger2DPlot - Calling parent.doPlot with selections: {selections}"
                )
                parent.doPlot("replace", selections)
                print("DEBUG: _trigger2DPlot - doPlot call completed")
            else:
                print(
                    "DEBUG: _trigger2DPlot - Could not find parent with doPlot method"
                )
        except Exception as e:
            print(f"DEBUG: _trigger2DPlot - Error: {e}")

    def onX1SelectionChanged(self, index):
        """Handle X1 positioner selection change."""
        print(f"DEBUG: onX1SelectionChanged - index: {index}")
        self._trigger2DPlot()

    def onX2SelectionChanged(self, index):
        """Handle X2 positioner selection change."""
        print(f"DEBUG: onX2SelectionChanged - index: {index}")
        self._trigger2DPlot()

    def onYDetSelectionChanged(self, index):
        """Handle Y detector selection change."""
        print(f"DEBUG: onYDetSelectionChanged - index: {index}")
        self._trigger2DPlot()

    def onI0SelectionChanged(self, index):
        """Handle I0 detector selection change."""
        print(f"DEBUG: onI0SelectionChanged - index: {index}")
        self._trigger2DPlot()

    def onPlotTypeChanged(self, index):
        """Handle plot type selection change."""
        plot_type = self.plotTypeComboBox.currentText().lower()
        print(f"DEBUG: onPlotTypeChanged - plot_type: {plot_type}")
        self._trigger2DPlot()

    def onColorPaletteChanged(self, index):
        """Handle color palette selection change."""
        palette_name = self.colorPaletteComboBox.currentText()
        print(f"DEBUG: onColorPaletteChanged - palette_name: {palette_name}")
        self._trigger2DPlot()

    def onPlotButtonClicked(self):
        """Handle plot button click."""
        print("DEBUG: onPlotButtonClicked - Plot button clicked")

        # Get current selections
        selections = self.get2DSelections()
        print(f"DEBUG: onPlotButtonClicked - selections: {selections}")

        # Validate selections
        if selections["Y"] is None or len(selections["Y"]) == 0:
            print("DEBUG: onPlotButtonClicked - No Y detector selected")
            return

        if selections["X1"] is None:
            print("DEBUG: onPlotButtonClicked - No X1 positioner selected")
            return

        if selections["X2"] is None:
            print("DEBUG: onPlotButtonClicked - No X2 positioner selected")
            return

        # Trigger 2D plotting by emitting a signal or calling the parent
        try:
            # Find the parent MDA_MVC to trigger plotting
            parent = self.parent()
            while parent and not hasattr(parent, "doPlot"):
                parent = parent.parent()

            if parent and hasattr(parent, "doPlot"):
                print(
                    "DEBUG: onPlotButtonClicked - Calling parent.doPlot with 2D selections"
                )
                print(
                    f"DEBUG: onPlotButtonClicked - About to call doPlot with: action='replace', selections={selections}"
                )
                parent.doPlot("replace", selections)
                print("DEBUG: onPlotButtonClicked - doPlot call completed")
            else:
                print(
                    "DEBUG: onPlotButtonClicked - Could not find parent with doPlot method"
                )
        except Exception as e:
            print(f"DEBUG: onPlotButtonClicked - Error: {e}")

    def get2DSelections(self):
        """Get current 2D plotting selections."""
        # Get color palette with validation
        color_palette = self.colorPaletteComboBox.currentText()
        if not color_palette or color_palette.strip() == "":
            color_palette = "viridis"
            print(
                f"DEBUG: get2DSelections - Empty color palette, using default: {color_palette}"
            )

        selections = {
            "X1": self.x1ComboBox.currentData(),
            "X2": self.x2ComboBox.currentData(),
            "Y": (
                [self.yDetComboBox.currentData()]
                if self.yDetComboBox.currentData() is not None
                else []
            ),
            "I0": self.i0ComboBox.currentData(),
            "plot_type": self.plotTypeComboBox.currentText().lower(),
            "color_palette": color_palette,
        }
        print(f"DEBUG: get2DSelections - {selections}")
        return selections

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
            print(
                f"DEBUG: isMultidimensional: {fileInfo.get('isMultidimensional', False)}"
            )
            print(f"DEBUG: scanDictInner exists: {'scanDictInner' in fileInfo}")
            if fileInfo.get("isMultidimensional", False) and fileInfo.get(
                "scanDictInner"
            ):
                scanDict = fileInfo["scanDictInner"]
                print(
                    f"DEBUG: Using scanDictInner for 2D data, keys: {list(scanDict.keys())}"
                )
            else:
                scanDict = fileInfo["scanDict"]
                print(
                    f"DEBUG: Using scanDict for 1D data, keys: {list(scanDict.keys())}"
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

    def data2Plot2D(self, selections):
        """
        Extracts 2D datasets for plotting from scanDict2D based on user selections.

        Parameters:
            - selections: A dictionary with keys "X", "Y", where "X" is the index for the x-axis data,
              "Y" is a list of indices for the y-axis data.

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

            # Check if this is 2D data
            if not fileInfo.get("isMultidimensional", False):
                print("DEBUG: data2Plot2D - Not 2D data, returning empty")
                return datasets, plot_options

            # Use scanDict2D for 2D plotting
            scanDict2D = fileInfo.get("scanDict2D", {})
            scanDictInner = fileInfo.get("scanDictInner", {})

            print(f"DEBUG: data2Plot2D - scanDict2D keys: {list(scanDict2D.keys())}")
            print(
                f"DEBUG: data2Plot2D - scanDictInner keys: {list(scanDictInner.keys())}"
            )
            print(f"DEBUG: data2Plot2D - selections: {selections}")

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

                print(
                    f"DEBUG: data2Plot2D - X data shape: {np.array(x_data).shape if x_data is not None else 'None'}"
                )
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
                    print(
                        f"DEBUG: data2Plot2D - Y data shape: {np.array(y_data).shape if y_data else 'None'}"
                    )
                else:
                    y_data = None
                    y_name = "Y"
                    y_unit = ""
            else:
                y_data = None
                y_name = "Y"
                y_unit = ""

            # ------ extract x2 data (from scanDict - this is the X2 positioner):
            x2_data = None
            x2_name = "X2"
            x2_unit = ""

            # Get the selected X2 index from the combobox
            x2_index = self.x2ComboBox.currentData()
            print(f"DEBUG: data2Plot2D - Selected X2 index: {x2_index}")

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

                print(
                    f"DEBUG: data2Plot2D - X2 data shape: {np.array(x2_data).shape if x2_data is not None else 'None'}"
                )
            else:
                print(f"DEBUG: data2Plot2D - X2 index {x2_index} not found in scanDict")
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

                        print(
                            f"DEBUG: data2Plot2D - Using fallback X2 (key 0): {x2_name}"
                        )
                        break

            # Create 2D dataset if we have all required data
            if x_data is not None and y_data is not None and x2_data is not None:
                # Validate data shapes and dimensions
                x_array = np.array(x_data)
                y_array = np.array(y_data)
                x2_array = np.array(x2_data)

                print("DEBUG: data2Plot2D - Validation:")
                print(f"  X array shape: {x_array.shape}")
                print(f"  Y array shape: {y_array.shape}")
                print(f"  X2 array shape: {x2_array.shape}")

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
                    print("DEBUG: data2Plot2D - Validation passed")
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
                    }
                else:
                    print("DEBUG: data2Plot2D - Validation failed:")
                    for error in validation_errors:
                        print(f"  ❌ {error}")
                    return datasets, plot_options
            else:
                print("DEBUG: data2Plot2D - Missing required data:")
                print(f"  X data: {'✅' if x_data is not None else '❌'}")
                print(f"  Y data: {'✅' if y_data is not None else '❌'}")
                print(f"  X2 data: {'✅' if x2_data is not None else '❌'}")

        return datasets, plot_options

    def data2Plot(self, selections):
        """
        Extracts selected datasets for plotting from scanDict based on user selections.

        Parameters:
            - selections: A dictionary with keys "X", "Y", and optionally "I0", where "X" is the index for the x-axis data,
              "Y" is a list of indices for the y-axis data, and "I0" is the index for normalization data.

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
                x2_slice = 0  # Not needed since we're using 1D data

                # Debug: Print field mappings
                print(
                    f"DEBUG: Using scanDictInner for 2D plotting, keys: {list(scanDict.keys())}"
                )
                print(f"DEBUG: selections: {selections}")

                # Debug: Print data shapes for first few fields
                for i in range(min(3, len(scanDict))):
                    if i in scanDict:
                        data = scanDict[i].get("data")
                        print(
                            f"DEBUG: Field {i} data shape: {np.array(data).shape if data else 'None'}"
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
                x_data = x_data[x2_slice]  # Take the selected X2 slice

            # ------ extract I0 data for normalization:
            i0_index = selections.get("I0")
            i0_data = scanDict[i0_index].get("data") if i0_index in scanDict else None

            # For 2D data in scanDictInner, slice to get 1D data
            if i0_data is not None and len(np.array(i0_data).shape) > 1:
                x2_slice = self.getX2Value()  # Get current X2 value from spinbox
                i0_data = i0_data[x2_slice]  # Take the selected X2 slice

            # ------ extract y(s) data:
            y_index = selections.get("Y", [])
            un_index = selections.get("Un", [])
            y_first_unit = y_first_name = ""

            # Identify rows that need unscaling (have both Y and Un selected)
            unscaled_rows = set(y_index) & set(un_index)
            regular_y_rows = set(y_index) - unscaled_rows

            # Calculate global min/max for unscaling (from regular Y curves only)
            global_min = float("inf")
            global_max = float("-inf")
            if unscaled_rows and regular_y_rows:
                for y in regular_y_rows:
                    if y in scanDict:
                        y_data = scanDict[y].get("data")
                        if y_data is not None:
                            # Apply I0 normalization if I0 is selected
                            if i0_data is not None:
                                i0_data_safe = np.array(i0_data)
                                i0_data_safe[i0_data_safe == 0] = 1
                                y_data = np.array(y_data) / i0_data_safe
                            else:
                                y_data = np.array(y_data)
                            global_min = min(global_min, np.min(y_data))
                            global_max = max(global_max, np.max(y_data))

            # If no regular Y curves to reference, use 0 to 1 scale for unscaling
            if unscaled_rows and (
                global_min == float("inf") or global_max == float("-inf")
            ):
                global_min = 0.0
                global_max = 1.0

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

                # Apply unscaling if this row has both Y and Un selected
                if (
                    y in unscaled_rows
                    and global_min != float("inf")
                    and global_max != float("-inf")
                ):
                    # Calculate min/max of this curve
                    m1, M1 = np.min(y_data), np.max(y_data)
                    # Apply unscaling formula: g(x) = ((f1(x) - m1) / (M1 - m1)) * (M23 - m23) + m23
                    if M1 != m1:  # Avoid division by zero
                        y_data = ((y_data - m1) / (M1 - m1)) * (
                            global_max - global_min
                        ) + global_min
                        y_label = f"{fileName}: {y_name} [unscaled]"
                        if i0_data is not None:
                            y_label = f"{fileName}: {y_name} [norm, unscaled]"

                        # Add X2 index to unscaled label for 2D data
                        if fileInfo.get("isMultidimensional", False):
                            x2_index = self.getX2Value()
                            y_label = f"{y_label} [{x2_index}]"

                if i == 0:
                    y_first_unit = y_unit
                    # y_first_name is used for y-axis label and shows normalization status
                    y_first_name = (
                        f"{y_name} [norm]"
                        if i0_data is not None
                        else f"{y_name} {y_unit}"
                    )

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
                print(
                    f"DEBUG: data2Plot - Added x2_index to plot_options: {plot_options['x2_index']}"
                )
            else:
                print("DEBUG: data2Plot - Not multidimensional, x2_index not added")

        return datasets, plot_options
