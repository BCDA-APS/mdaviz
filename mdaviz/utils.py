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
import threading
from mda import scanPositioner


def human_readable_size(size, decimal_places=2):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
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
    """Convert byte literals to strings."""
    return (
        byte_literal.decode("utf-8")
        if isinstance(byte_literal, bytes)
        else byte_literal
    )


def get_det(mda_file_data):
    """det_dict = { index: [fieldname, pv, desc, unit]}"""
    D = {}
    p_list = [
        mda_file_data.p[i] for i in range(0, mda_file_data.np)
    ]  # mda_file_data.np = number of positioners
    d_list = [
        mda_file_data.d[i] for i in range(0, mda_file_data.nd)
    ]  # mda_file_data.nd = number of detectors
    first_pos = 1 if mda_file_data.np else 0
    first_det = mda_file_data.np + 1

    P0 = scanPositioner()
    P0.number = 0  # positioner number in sscan record
    P0.fieldName = "P0"  # name of sscanRecord PV
    P0.name = "Index"  # name of EPICS PV this positioner wrote to
    P0.desc = "Index"  # description of 'name' PV
    P0.step_mode = ""  # 'LINEAR', 'TABLE', or 'FLY'
    P0.unit = "a.u"  # units of 'name' PV
    P0.readback_name = ""  # name of EPICS PV this positioner read from, if any
    P0.readback_desc = ""  # description of 'readback_name' PV
    P0.readback_unit = ""  # units of 'readback_name' PV
    P0.data = list(
        range(0, mda_file_data.curr_pt)
    )  # list of values written to 'name' PV.  If rank==2, lists of lists, etc.

    D[0] = P0
    for e, p in enumerate(p_list):
        D[e + 1] = p
    for e, d in enumerate(d_list):
        D[e + 1 + mda_file_data.np] = d
    return D, first_pos, first_det


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
