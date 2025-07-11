"""
Support functions for this demo project.

.. autosummary::
    ~byte2str
    ~getUiFileName
    ~human_readable_size
    ~iso2dt
    ~iso2ts
    ~myLoadUi
    ~removeAllLayoutWidgets
    ~run_in_thread
    ~ts2dt
    ~ts2iso
"""

import pathlib
import re
import threading
from datetime import datetime
from typing import Any
from .synApps_mdalib.mda import readMDA, scanPositioner, skimMDA

HEADERS = "Prefix", "Scan #", "Points", "Dim", "Date", "Size"


def human_readable_size(size: float, decimal_places: int = 2) -> str:
    """Convert size in bytes to human readable format.

    Parameters:
        size (float): Size in bytes
        decimal_places (int): Number of decimal places to show

    Returns:
        str: Human readable size string
    """
    for unit in ["B", "kB", "MB", "GB", "TB"]:
        if size < 1024.0:
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f} {unit}"


def iso2dt(iso_date_time: str) -> datetime:
    """Convert ISO8601 time string to datetime object.

    Parameters:
        iso_date_time (str): ISO8601 formatted time string

    Returns:
        datetime: Datetime object
    """
    return datetime.fromisoformat(iso_date_time)


def iso2ts(iso_date_time: str) -> float:
    """Convert ISO8601 time string to timestamp.

    Parameters:
        iso_date_time (str): ISO8601 formatted time string

    Returns:
        float: Unix timestamp
    """
    return iso2dt(iso_date_time).timestamp()


def ts2dt(timestamp: float) -> datetime:
    """Convert timestamp to datetime object.

    Parameters:
        timestamp (float): Unix timestamp

    Returns:
        datetime: Datetime object
    """
    return datetime.fromtimestamp(timestamp)


def ts2iso(timestamp: float) -> str:
    """Convert timestamp to ISO8601 time string.

    Parameters:
        timestamp (float): Unix timestamp

    Returns:
        str: ISO8601 formatted time string
    """
    return ts2dt(timestamp).isoformat(sep=" ")


def num2fstr(x: float) -> str:
    """Return a string with the adequate precision and format.

    Parameters:
        x (float): Number to format

    Returns:
        str: Formatted string
    """
    return f"{x:.2e}" if abs(x) < 1e-3 else f"{x:.2f}"


def byte2str(byte_literal):
    """
    Converts a byte literal to a UTF-8 encoded string. If the input is not a byte literal, it is returned as is without any conversion.

    Parameters:
        - byte_literal (bytes | Any): The byte literal to be decoded or any input to be returned as is if not bytes.

    Returns:
        - str | Any: The decoded string if the input is a byte literal, otherwise the original input.
    """
    return (
        byte_literal.decode("utf-8")
        if isinstance(byte_literal, bytes)
        else byte_literal
    )


def get_file_info_lightweight(file_path: pathlib.Path) -> dict:
    """
    Get lightweight file information without loading full MDA data.

    This function extracts only the essential metadata needed for the folder view
    without loading the complete file data, making it much faster for large folders.

    Parameters:
        file_path (Path): Path to the MDA file

    Returns:
        dict: Dictionary containing lightweight file information with keys:
            - Name: File name
            - Prefix: File prefix (if extractable)
            - Number: Scan number (if available)
            - Points: Number of data points (if available)
            - Dimension: Scan dimension (if available)
            - Positioner: First positioner name (if available)
            - Date: File date (if available)
            - Size: Human readable file size
    """
    file_name = file_path.name
    file_size = human_readable_size(file_path.stat().st_size)

    # Try to get basic info from skimMDA first (fastest)
    try:
        skim_result = skimMDA(str(file_path))
        if skim_result and len(skim_result) > 0:
            # skimMDA returns a list where the first element is a dict with metadata
            skim_data = skim_result[0] if isinstance(skim_result[0], dict) else {}

            file_num = skim_data.get("scan_number", None)
            file_prefix = (
                extract_file_prefix(file_name, file_num)
                if file_num is not None
                else None
            )

            # Get basic scan info from skim data
            if skim_data.get("rank", 0) > 0:
                file_pts = skim_data.get("acquired_dimensions", [0])[0]
                file_dim = skim_data.get("rank", 1)
            else:
                file_pts = 0
                file_dim = 1

            # Try to get date from file modification time as fallback
            file_date = datetime.fromtimestamp(file_path.stat().st_mtime).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        else:
            # Fallback to basic file info only
            file_num = None
            file_prefix = None
            file_pts = 0
            file_dim = 1
            file_date = datetime.fromtimestamp(file_path.stat().st_mtime).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

    except Exception as e:
        # If skimMDA fails, provide minimal info
        print(f"Error reading {file_path}: {e}")
        file_num = None
        file_prefix = None
        file_pts = 0
        file_dim = 1
        file_date = datetime.fromtimestamp(file_path.stat().st_mtime).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    fileInfo: dict[str, Any] = {
        "Name": file_name,
        "folderPath": str(file_path.parent),
    }
    values = [
        str(file_prefix) if file_prefix is not None else "",
        str(file_num) if file_num is not None else "",
        str(file_pts) if file_pts is not None else "",
        str(file_dim) if file_dim is not None else "",
        str(file_date) if file_date is not None else "",
        str(file_size) if file_size is not None else "",
    ]
    for k, v in zip(HEADERS, values):
        fileInfo[k] = v
    return fileInfo


def get_file_info_full(file_path: pathlib.Path) -> dict:
    """
    Get complete file information by loading the full MDA data.

    This is the original get_file_info function, renamed for clarity.
    Use this only when detailed file information is needed.

    Parameters:
        file_path (Path): Path to the MDA file

    Returns:
        dict: Complete file information including all metadata and data
    """
    file_name = file_path.name

    # Check if readMDA returns None
    result = readMDA(str(file_path))
    if result is None:
        # Return minimal info if file cannot be read
        minimal_file_info = {"Name": file_name}
        values = [
            "",
            "",
            "0",
            "1",
            datetime.fromtimestamp(file_path.stat().st_mtime).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            human_readable_size(file_path.stat().st_size),
        ]
        for k, v in zip(HEADERS, values):
            minimal_file_info[k] = v
        return minimal_file_info

    file_metadata, file_data_dim1, *_ = result
    file_num = file_metadata.get("scan_number", None)
    file_prefix = extract_file_prefix(file_name, file_num)
    file_size = human_readable_size(file_path.stat().st_size)
    file_date = str(byte2str(file_data_dim1.time)).split(".")[0]
    file_pts = file_data_dim1.curr_pt
    file_dim = file_data_dim1.dim

    fileInfo: dict[str, Any] = {"Name": file_name}
    values = [
        str(file_prefix) if file_prefix is not None else "",
        str(file_num) if file_num is not None else "",
        str(file_pts) if file_pts is not None else "",
        str(file_dim) if file_dim is not None else "",
        str(file_date) if file_date is not None else "",
        str(file_size) if file_size is not None else "",
    ]
    for k, v in zip(HEADERS, values):
        fileInfo[k] = v
    return fileInfo


# Keep the original function name for backward compatibility
def get_file_info(file_path: pathlib.Path) -> dict:
    """
    Get file information. This is an alias for get_file_info_full for backward compatibility.

    Parameters:
        file_path (Path): Path to the MDA file

    Returns:
        dict: Complete file information
    """
    return get_file_info_full(file_path)


def extract_file_prefix(file_name: str, scan_number: int | None) -> str | None:
    """Create a pattern that matches the prefix followed by an optional separator and the scan number with possible leading zeros.

    The separators considered here are underscore (_), hyphen (-), dot (.), and space ( )

    Parameters:
        file_name (str): Name of the file
        scan_number (int | None): Scan number to extract prefix for

    Returns:
        str | None: Extracted prefix or None if no match
    """
    scan_number_str = str(scan_number) if scan_number is not None else "0"
    pattern = rf"^(.*?)[_\-\. ]?0*{scan_number_str}\.mda$"
    match = re.match(pattern, file_name)
    if match:
        return match.group(1)
    return None


def get_det(mda_file_data):
    """
    Extracts scan positioners and detectors from an MDA file data object.

    This function processes an mda.scanDim object to extract its scanPositioner and scanDetector instances.
    It organizes these instances into a dictionary, with their indexes as keys in the order of ``p0, P1,... Px, D01, D02,... DX``.
    ``p0`` is a default scanPositioner object representing the point index. If additional positioners exist, they follow ``p0`` in sequence.
    The first detector is labeled ``D01`` and subsequent detectors follow in numerical order.

    Parameters:
        - mda_file_data: An instance of an mda.scanDim object, which contains the MDA file data to be processed.

    Returns:
        A tuple containing:
            - A dictionary (d) where keys are indexes, mapping to either scanPositioner or scanDetector objects.
                The dictionary is structured as ``{0: p0, 1: P1, ..., np: D01, np+1: D02, ..., np+nd: DX}``.
            - The index (first_pos) of the first positioner in the returned dictionary. This is 1 if a positioner
                other than the default index positioner exists, otherwise 0.
            - The index (first_det) of the first detector in the returned dictionary, which directly follows the last positioner.

    Notes:
        - p0 is created by default and corresponds to the point index, described as an 'Index' scanPositioner object with predefined properties.
        - np is the total number of positioners, nd the number of detectors, and npts the number of data points actually acquired.
    """

    d = {}
    print(f"\n\n{mda_file_data=}\n\n")

    p_list = mda_file_data.p  # list of scanDetector instances
    d_list = mda_file_data.d  # list of scanPositioner instances
    np = mda_file_data.np  # number of pos
    npts = mda_file_data.curr_pt  # number of data points actually acquired

    first_pos = 1 if np else 0
    first_det = np + 1

    # Defining a default scanPositioner Object for "Index" at for key=0:
    p0 = scanPositioner()
    p0.number = 0  # positioner number in sscan record
    p0.fieldName = "P0"  # name of sscanRecord PV
    p0.name = "Index"  # name of EPICS PV this positioner wrote to
    p0.desc = "Index"  # description of 'name' PV
    p0.step_mode = ""  # 'LINEAR', 'TABLE', or 'FLY'
    p0.unit = ""  # units of 'name' PV
    p0.readback_name = ""  # name of EPICS PV this positioner read from, if any
    p0.readback_desc = ""  # description of 'readback_name' PV
    p0.readback_unit = ""  # units of 'readback_name' PV
    p0.data = list(range(npts))  # list of values written to 'Index' PV.

    # Make the Index scanPositioner the positioner 0 and build d:
    d[0] = p0
    for e, p in enumerate(p_list):
        d[e + 1] = p
    for e, det in enumerate(d_list):
        d[e + 1 + np] = det
    return d, first_pos, first_det


def get_scan(mda_file_data):
    """
    Extracts scan positioners and detectors from an MDA file data object and prepares datasets.

    Processes an mda.scanDim object to extract scanPositioner and scanDetector
    instances, organizing them into a dictionary with additional metadata like
    data, units, and names. A default scanPositioner object representing the
    point index (p0) is included. If additional positioners exist, they follow
    p0 in sequence. The first detector is labeled D01 and subsequent detectors
    follow in numerical order: p0, p1,... px, d01, d02,... dX.

    Parameters:
        - mda_file_data: An instance of an mda.scanDim object to be processed.

    Returns:
        - A tuple containing:
            - A dictionary keyed by index, each mapping to a sub-dictionary containing
              the scan object ('object') along with its 'data', 'unit', 'name' and 'type'.
              Structure:
              {index: {'object': scanObject, 'data': [...], 'unit': '...', 'name': '...','type':...}}.
            - The index (first_pos) of the first positioner in the returned dictionary. This
              is 1 if a positioner other than the default index positioner exists, otherwise 0.
            - The index (first_det) of the first detector in the returned dictionary, which
              directly follows the last positioner.
    """

    d = {}

    p_list = mda_file_data.p  # list of scanDetector instances
    d_list = mda_file_data.d  # list of scanPositioner instances
    np = mda_file_data.np  # number of positioners
    npts = mda_file_data.curr_pt  # number of data points actually acquired

    first_pos_index = 1 if np else 0
    first_det_index = np + 1

    # Defining a default scanPositioner Object for "Index":
    p0 = scanPositioner()
    # Set predefined properties for p0
    p0.number = 0
    p0.fieldName, p0.name, p0.desc = "P0", "Index", "Index"
    p0.step_mode, p0.unit = "", ""
    p0.readback_name, p0.readback_desc, p0.readback_unit = "", "", ""
    p0.data = list(range(npts))

    # Make the Index scanPositioner the positioner 0 and build d:
    d[0] = p0
    for e, pos in enumerate(p_list):
        d[e + 1] = pos
    for e, det in enumerate(d_list):
        d[e + 1 + np] = det

    datasets = {}
    for k, v in d.items():
        datasets[k] = {
            "object": v,
            "type": "POS" if isinstance(v, scanPositioner) else "DET",
            "data": v.data or [],
            "unit": byte2str(v.unit) if v.unit else "",
            "name": byte2str(v.name) if v.name else "n/a",
            "desc": byte2str(v.desc) if v.desc else "",
            "fieldName": byte2str(v.fieldName),
        }

    return datasets, first_pos_index, first_det_index


def get_md(mda_file_metadata: dict) -> dict:
    """Process MDA file metadata to convert bytes to strings and clean up structure.

    Parameters:
        mda_file_metadata (dict): Raw metadata from MDA file

    Returns:
        dict: Processed metadata with string keys and cleaned values
    """
    from collections import OrderedDict

    new_metadata = OrderedDict()
    for key, value in mda_file_metadata.items():
        if isinstance(key, bytes):
            key = key.decode("utf-8", "ignore")

        if isinstance(value, tuple):
            # Exclude unwanted keys like EPICS_type
            new_metadata[key] = {
                k: byte2str(v)
                for k, v in zip(
                    ["description", "unit", "value", "EPICS_type", "count"],
                    value,
                )
                if k not in ["EPICS_type", "count"]
            }
        else:
            new_metadata[key] = value
    return new_metadata


def mda2ftm(selection: dict | None) -> dict:
    """
    Converts a field selection from MDA_MVC (MVC) format to SelectFieldsTableModel (TM) format.

    The MVC format {'Y': [2, 3], 'X': 1, 'I0': 4} is transformed into TM format {1: 'X', 2: 'Y', 4: 'Y', 4: 'I0'}.
    This is used to sync selection states between SelectFieldsTableModel and MDA_MVC.

    Parameters:
        selection (dict | None): The selection in MVC format to be converted.

    Returns:
        dict: The selection converted to TM format.
    """
    if selection is not None:
        ftm_selection = {}
        for k, vals in selection.items():
            if k in ["X", "I0"]:
                # Handle unique selections (X and I0)
                ftm_selection[vals] = k
            else:
                # Handle multiple selections (Y)
                for v in vals:
                    ftm_selection[v] = k
    else:
        ftm_selection = {}
    return ftm_selection


def ftm2mda(selection: dict | None) -> dict:
    """
    Converts a field selection from SelectFieldsTableModel (TM) format to MDA_MVC (MVC) format.

    The TM format {1: 'X', 2: 'Y', 4: 'Y', 4: 'I0'} is transformed into MVC format {'Y': [2, 3], 'X': 1, 'I0': 4}.
    Used to update MDA_MVC selection state (self.selectionField()) based on changes in SelectFieldsTableModel.

    Parameters:
        selection (dict | None): The selection in TM format to be converted.

    Returns:
        dict: The selection converted to MVC format.
    """
    mda_selection = {}
    if selection is not None:
        for key, value in selection.items():
            if value in ["X", "I0"]:
                # Directly assign the value for 'X' and 'I0' since they are always unique
                mda_selection[value] = key
            else:
                # Append to the list for 'Y'
                if value not in mda_selection:
                    mda_selection[value] = []
                mda_selection[value].append(key)
    return mda_selection


def run_in_thread(func):
    """
    (decorator) run ``func`` in thread

    USAGE::

       @run_in_thread
       def progress_reporting():
           logger.debug("progress_reporting is starting")
           # ...

       #...
       progress_reporting()   # runs in separate thread
       #...

    """

    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.start()
        return thread

    return wrapper


def removeAllLayoutWidgets(layout) -> None:
    """Remove all existing widgets from QLayout.

    Parameters:
        layout: QLayout object to clear
    """
    for i in reversed(range(layout.count())):
        layout.itemAt(i).widget().setParent(None)


def myLoadUi(ui_file, baseinstance=None, **kw):
    """
    Load a .ui file for use in building a GUI.

    Wraps `uic.loadUi()` with code that finds our program's
    *resources* directory.

    :see: http://nullege.com/codes/search/PyQt4.uic.loadUi
    :see: http://bitesofcode.blogspot.ca/2011/10/comparison-of-loading-techniques.html

    inspired by:
    http://stackoverflow.com/questions/14892713/how-do-you-load-ui-files-onto-python-classes-with-pyside?lq=1
    """
    from PyQt5 import uic

    from . import UI_DIR

    if isinstance(ui_file, str):
        ui_file = UI_DIR / ui_file

    # print(f"myLoadUi({ui_file=})")
    return uic.loadUi(ui_file, baseinstance=baseinstance, **kw)


def getUiFileName(py_file_name: str) -> str:
    """UI file name matches the Python file, different extension.

    Parameters:
        py_file_name (str): Python file name

    Returns:
        str: Corresponding UI file name
    """
    return f"{pathlib.Path(py_file_name).stem}.ui"


def reconnect(signal, new_slot):
    """
    Disconnects any slots connected to the given signal and then connects the signal to the new_slot.

    Parameters:
        - signal: The signal to disconnect and then reconnect.
        - new_slot: The new slot to connect to the signal.

    Note:
        - this function catches TypeError which occurs if the signal was not connected to any slots.
    """
    try:
        signal.disconnect()
    except TypeError:
        pass
    signal.connect(new_slot)


def debug_signal(*args, **kwargs):
    print("\nSignal emitted with args:", args, "and kwargs:", kwargs)
