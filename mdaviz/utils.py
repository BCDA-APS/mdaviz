"""
Support functions for this demo project.

.. autosummary::

    ~connect_tiled_server
    ~get_tiled_runs
    ~getUiFileName
    ~get_md
    ~iso2dt
    ~iso2ts
    ~myLoadUi
    ~QueryTimeSince
    ~QueryTimeUntil
    ~removeAllLayoutWidgets
    ~run_in_thread
    ~run_summary_table
    ~ts2dt
    ~ts2iso
"""

import datetime
import pathlib
import threading

import tiled.queries


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


def byte2str(byte_literal):
    """Convert byte literals to strings."""
    return (
        byte_literal.decode("utf-8")
        if isinstance(byte_literal, bytes)
        else byte_literal
    )


def byte2str_dict(byte_literal_dict):
    """Convert dictionary of byte literals to strings."""
    str_dict = {}
    for key, value in byte_literal_dict.items():
        new_key = key.decode("utf-8") if isinstance(key, bytes) else key
        if isinstance(value, (list, tuple)):
            new_value = tuple(
                elem.decode("utf-8") if isinstance(elem, bytes) else elem
                for elem in value
            )
        else:
            new_value = value.decode("utf-8") if isinstance(value, bytes) else value
        str_dict[new_key] = new_value
    return str_dict


def get_md(parent, doc, key, default=None):
    """Cautiously, get metadata from tiled object by document and key."""
    return (parent.metadata.get(doc) or {}).get(key) or default


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


def run_summary_table(runs):
    import pyRestTable

    table = pyRestTable.Table()
    table.labels = "# uid7 scan# plan #points exit started streams".split()
    for i, uid in enumerate(runs, start=1):
        run = runs[uid]
        md = run.metadata
        t0 = md["start"].get("time")
        table.addRow(
            (
                i,
                uid[:7],
                md["summary"].get("scan_id"),
                md["summary"].get("plan_name"),
                md["start"].get("num_points"),
                (md["stop"] or {}).get("exit_status"),  # if no stop document!
                datetime.datetime.fromtimestamp(t0).isoformat(sep=" "),
                ", ".join(md["summary"].get("stream_names")),
            )
        )
    return table


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
