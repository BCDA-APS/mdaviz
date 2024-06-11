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

import datetime
import pathlib
import re
import threading
from .synApps_mdalib.mda import readMDA, scanPositioner

HEADERS = "Prefix", "Scan #", "Points", "Dim", "Positioner", "Date", "Size"


def human_readable_size(size, decimal_places=2):
    for unit in ["B", "kB", "MB", "GB", "TB"]:
        if size < 1024.0:
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f} {unit}"


def iso2dt(iso_date_time):
    """Convert ISO8601 time string to datetime object."""
    return datetime.datetime.fromisoformat(iso_date_time)


def iso2ts(iso_date_time):
    """Convert ISO8601 time string to timestamp."""
    return iso2dt(iso_date_time).timestamp()


def ts2dt(timestamp):
    """Convert timestamp to datetime object."""
    return datetime.datetime.fromtimestamp(timestamp)


def ts2iso(timestamp):
    """Convert timestamp to ISO8601 time string."""
    return ts2dt(timestamp).isoformat(sep=" ")


def num2fstr(x):
    """Return a string with the adequate precision and format"""
    return f"{x:.3e}" if abs(x) < 1e-3 else f"{x:.3f}"


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


def get_file_info(file_path):
    file_name = file_path.name
    file_data = readMDA(str(file_path))[1]
    file_metadata = readMDA(str(file_path))[0]
    file_num = file_metadata.get("scan_number", None)
    file_prefix = extract_prefix(file_name, file_num)
    file_size = human_readable_size(file_path.stat().st_size)
    file_date = byte2str(file_data.time).split(".")[0]
    file_pts = file_data.curr_pt
    file_dim = file_data.dim
    pv = byte2str(file_data.p[0].name) if len(file_data.p) else "index"
    desc = byte2str(file_data.p[0].desc) if len(file_data.p) else "index"
    file_pos = desc if desc else pv

    fileInfo = {"Name": file_name}
    values = [
        file_prefix,
        file_num,
        file_pts,
        file_dim,
        file_pos,
        file_date,
        file_size,
    ]
    for k, v in zip(HEADERS, values):
        fileInfo[k] = v
    return fileInfo


def extract_prefix(file_name, scan_number):
    """Create a pattern that matches the prefix followed by an optional separator and the scan number with possible leading zeros
    The separators considered here are underscore (_), hyphen (-), dot (.), and space ( )
    """
    scan_number = str(scan_number)
    pattern = rf"^(.*?)[_\-\. ]?0*{scan_number}\.mda$"
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
    npts = mda_file_data.curr_pt = 0  # number of data points actually acquired

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
    for e, d in enumerate(d_list):
        d[e + 1 + np] = d
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
    p0.fieldName, p0.name, p0.desc = "p0", "Index", "Index"
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


def get_md(mda_file_metadata):
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


def mda2ftm(selection):
    """
    Converts a field selection from MDA_MVC (MVC) format to SelectFieldsTableModel (TM) format.

    The MVC format {'Y': [2, 3], 'X': 1} is transformed into TM format {1: 'X', 2: 'Y', 4: 'Y'}.
    This is used to sync selection states between SelectFieldsTableModel and MDA_MVC.

    Parameters:
        - selection (dict): The selection in MVC format to be converted.

    Returns:
        - dict: The selection converted to TM format.
    """
    if selection is not None:
        ftm_selection = {
            v: "X" if k == "X" else "Y"
            for k, vals in selection.items()
            for v in ([vals] if isinstance(vals, int) else vals)
        }
    else:
        ftm_selection = {}
    return ftm_selection


def ftm2mda(selection):
    """
    Converts a field selection from SelectFieldsTableModel (TM) format to MDA_MVC (MVC) format.

    The TM format {1: 'X', 2: 'Y', 4: 'Y'} is transformed into MVC format {'Y': [2, 3], 'X': 1}.
    Used to update MDA_MVC selection state (self.selectionField()) based on changes in SelectFieldsTableModel.

    Parameters:
        - selection (dict): The selection in TM format to be converted.

    Returns:
        - dict: The selection converted to MVC format.
    """
    mda_selection = {}
    if selection is not None:
        for key, value in selection.items():
            if value == "X":
                # Directly assign the value for 'X' since it's always unique
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


def removeAllLayoutWidgets(layout):
    """Remove all existing widgets from QLayout."""
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


def getUiFileName(py_file_name):
    """UI file name matches the Python file, different extension."""
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
