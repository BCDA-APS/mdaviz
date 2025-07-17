"""
Enhanced utilities for MDA file processing and data management.

This module provides optimized utilities for handling MDA files, data processing,
and UI operations with enhanced performance, error handling, and type safety.

.. autosummary::

    ~get_file_info_lightweight
    ~get_file_info_full
    ~get_file_info_async
    ~get_scan
    ~extract_file_prefix
    ~human_readable_size
    ~optimized_file_reader
"""

import concurrent.futures
import pathlib
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import warnings

try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from PyQt6 import uic

from mdaviz.synApps_mdalib.mda import readMDA, skimMDA, scanPositioner
from mdaviz import UI_DIR

# Constants for optimized processing
CHUNK_SIZE = 1024 * 1024  # 1MB chunks for file reading
MAX_PARALLEL_FILES = 8  # Maximum files to process in parallel
MEMORY_WARNING_THRESHOLD = 100  # MB

HEADERS = ["Prefix", "Number", "Points", "Dimension", "Date", "Size"]


class OptimizedFileReader:
    """
    High-performance file reader with memory optimization and async support.

    This class provides enhanced file reading capabilities with memory monitoring,
    chunked reading for large files, and parallel processing support.
    """

    def __init__(
        self,
        max_memory_mb: float = 500.0,
        enable_parallel: bool = True,
        max_workers: int = 4,
    ) -> None:
        """
        Initialize the optimized file reader.

        Parameters:
            max_memory_mb (float): Maximum memory usage in megabytes
            enable_parallel (bool): Whether to enable parallel processing
            max_workers (int): Maximum number of worker threads
        """
        self.max_memory_mb = max_memory_mb
        self.enable_parallel = enable_parallel
        self.max_workers = max_workers
        self._memory_usage = 0.0

    def _check_memory(self) -> float:
        """Check current memory usage."""
        if PSUTIL_AVAILABLE:
            try:
                process = psutil.Process()
                return process.memory_info().rss / (1024 * 1024)
            except Exception:
                pass
        return 0.0

    def _should_use_lightweight(self, file_path: Path) -> bool:
        """Determine if lightweight reading should be used."""
        try:
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            current_memory = self._check_memory()

            # Use lightweight for large files or high memory usage
            return file_size_mb > 50 or current_memory > self.max_memory_mb * 0.8
        except Exception:
            return True  # Default to lightweight on error

    def read_file_optimized(
        self, file_path: Path, force_lightweight: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Read an MDA file with optimized performance.

        Parameters:
            file_path (Path): Path to the MDA file
            force_lightweight (bool): Force lightweight reading

        Returns:
            Optional[Dict[str, Any]]: File information or None if failed
        """
        try:
            if force_lightweight or self._should_use_lightweight(file_path):
                return get_file_info_lightweight(file_path)
            else:
                return get_file_info_full(file_path)
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None

    def read_files_parallel(
        self, file_paths: List[Path], lightweight: bool = False
    ) -> List[Optional[Dict[str, Any]]]:
        """
        Read multiple files in parallel for better performance.

        Parameters:
            file_paths (List[Path]): List of file paths to read
            lightweight (bool): Whether to use lightweight reading

        Returns:
            List[Optional[Dict[str, Any]]]: List of file information
        """
        if not self.enable_parallel or len(file_paths) <= 1:
            # Sequential processing
            return [self.read_file_optimized(path, lightweight) for path in file_paths]

        # Parallel processing
        results: list[dict[str, Any] | None] = [None] * len(file_paths)

        with ThreadPoolExecutor(
            max_workers=min(self.max_workers, len(file_paths))
        ) as executor:
            # Submit all tasks
            future_to_index = {
                executor.submit(self.read_file_optimized, path, lightweight): i
                for i, path in enumerate(file_paths)
            }

            # Collect results
            for future in concurrent.futures.as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    results[index] = future.result()
                except Exception as e:
                    print(f"Error processing file {file_paths[index]}: {e}")
                    results[index] = None

        return results


# Global optimized reader instance
_optimized_reader = OptimizedFileReader()


def get_file_info_async(file_paths: List[Path]) -> List[Optional[Dict[str, Any]]]:
    """
    Asynchronously get file information for multiple files.

    This function provides high-performance file processing using parallel
    execution for improved responsiveness with large file sets.

    Parameters:
        file_paths (List[Path]): List of MDA file paths to process

    Returns:
        List[Optional[Dict[str, Any]]]: List of file information dictionaries
    """
    return _optimized_reader.read_files_parallel(file_paths, lightweight=True)


def get_file_info_lightweight(file_path: pathlib.Path) -> Dict[str, Any]:
    """
    Get lightweight file information without loading full MDA data.

    This function extracts only the essential metadata needed for the folder view
    without loading the complete file data, making it much faster for large folders.
    Uses optimized skimMDA for minimal memory footprint.

    Parameters:
        file_path (Path): Path to the MDA file

    Returns:
        Dict[str, Any]: Dictionary containing lightweight file information with keys:
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

    # Initialize default values
    file_num = None
    file_prefix = None
    file_pts = 0
    file_dim = 1
    positioner_name = "n/a"

    # Try to get basic info from skimMDA first (fastest)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # Suppress warnings for corrupted files

            skim_result = skimMDA(str(file_path))
            if skim_result and len(skim_result) > 0:
                # Extract metadata from skim result
                if isinstance(skim_result[0], dict):
                    skim_data = skim_result[0]
                    file_num = skim_data.get("scan_number")
                    file_dim = skim_data.get("rank", 1)
                    acquired_dims = skim_result[0].get("acquired_dimensions", [0])
                    file_pts = acquired_dims[0] if acquired_dims else 0

                    # Try to get positioner name from scan structure
                    if len(skim_result) > 1 and hasattr(skim_result[1], "p"):
                        try:
                            if len(skim_result[1].p) > 0:
                                pos = skim_result[1].p[0]
                                if hasattr(pos, "name") and pos.name:
                                    positioner_name = byte2str(pos.name)
                        except Exception:
                            pass  # Keep default if extraction fails

                # Extract prefix if scan number is available
                if file_num is not None:
                    file_prefix = extract_file_prefix(file_name, file_num)

    except Exception as e:
        print(f"Warning: Error reading {file_path} with skimMDA: {e}")
        # Continue with default values

    # Get file date from modification time
    try:
        file_date = datetime.fromtimestamp(file_path.stat().st_mtime).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    except:
        file_date = "Unknown"

    # Build comprehensive file info
    file_info: Dict[str, Any] = {
        "Name": file_name,
        "folderPath": str(file_path.parent),
        "Positioner": positioner_name,
    }

    # Add standard headers with safe string conversion
    values = [
        str(file_prefix) if file_prefix is not None else "",
        str(file_num) if file_num is not None else "",
        str(file_pts),
        str(file_dim),
        str(file_date),
        str(file_size),
    ]

    for header, value in zip(HEADERS, values):
        file_info[header] = value

    return file_info


def get_file_info_full(file_path: pathlib.Path) -> Dict[str, Any]:
    """
    Get complete file information by loading the full MDA data.

    This function loads the complete MDA file data and extracts detailed
    information. Use this only when detailed file information is needed,
    as it's slower than the lightweight version.

    Parameters:
        file_path (Path): Path to the MDA file

    Returns:
        Dict[str, Any]: Complete file information including all metadata and data
    """
    file_name = file_path.name

    try:
        # Use optimized reading with memory monitoring
        memory_before = _optimized_reader._check_memory()

        # Check if file is too large for full reading
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > MEMORY_WARNING_THRESHOLD:
            print(
                f"Warning: Large file ({file_size_mb:.1f}MB) - consider using lightweight reading"
            )

        result = readMDA(str(file_path))
        if result is None:
            # Return minimal info if file cannot be read
            return _create_minimal_file_info(file_path)

        file_metadata, file_data_dim1, *_ = result

        # Extract file information with error handling
        file_num = file_metadata.get("scan_number")
        file_prefix = extract_file_prefix(file_name, file_num) if file_num else None
        file_size = human_readable_size(file_path.stat().st_size)

        # Safe date extraction
        try:
            raw_time = (
                byte2str(file_data_dim1.time) if hasattr(file_data_dim1, "time") else ""
            )
            file_date = str(raw_time).split(".")[0] if raw_time else "Unknown"
        except:
            file_date = datetime.fromtimestamp(file_path.stat().st_mtime).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        file_pts = getattr(file_data_dim1, "curr_pt", 0)
        file_dim = getattr(file_data_dim1, "dim", 1)

        # Get positioner information
        positioner_name = "n/a"
        try:
            if hasattr(file_data_dim1, "p") and len(file_data_dim1.p) > 0:
                pos = file_data_dim1.p[0]
                if hasattr(pos, "name") and pos.name:
                    positioner_name = byte2str(pos.name)
        except:
            pass

        # Monitor memory usage
        memory_after = _optimized_reader._check_memory()
        memory_used = memory_after - memory_before
        if memory_used > 50:  # More than 50MB used
            print(f"Warning: File {file_name} used {memory_used:.1f}MB memory")

        # Build complete file info
        file_info: Dict[str, Any] = {
            "Name": file_name,
            "folderPath": str(file_path.parent),
            "Positioner": positioner_name,
        }

        values = [
            str(file_prefix) if file_prefix is not None else "",
            str(file_num) if file_num is not None else "",
            str(file_pts),
            str(file_dim),
            str(file_date),
            str(file_size),
        ]

        for header, value in zip(HEADERS, values):
            file_info[header] = value

        return file_info

    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return _create_minimal_file_info(file_path)


def _create_minimal_file_info(file_path: Path) -> Dict[str, Any]:
    """
    Create minimal file information when full reading fails.

    Parameters:
        file_path (Path): Path to the file

    Returns:
        Dict[str, Any]: Minimal file information
    """
    file_name = file_path.name
    minimal_file_info = {
        "Name": file_name,
        "folderPath": str(file_path.parent),
        "Positioner": "n/a",
    }

    try:
        file_date = datetime.fromtimestamp(file_path.stat().st_mtime).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        file_size = human_readable_size(file_path.stat().st_size)
    except:
        file_date = "Unknown"
        file_size = "Unknown"

    values = ["", "", "0", "1", file_date, file_size]
    for header, value in zip(HEADERS, values):
        minimal_file_info[header] = value

    return minimal_file_info


def get_scan(file_data_dim1) -> Tuple[Dict[str, Any], str, str]:
    """
    Extract scan information from MDA file data with enhanced error handling.

    This function processes the scan data structure and extracts positioner
    and detector information in a format suitable for visualization.

    Parameters:
        file_data_dim1: MDA file data structure from readMDA

    Returns:
        Tuple[Dict[str, Any], str, str]: Tuple containing:
            - scan_dict: Dictionary of scan data organized by field
            - first_pos: Name of the first positioner
            - first_det: Name of the first detector
    """
    scan_dict: Dict[str, Any] = {}

    try:
        # Extract positioners with enhanced error handling
        if hasattr(file_data_dim1, "p") and file_data_dim1.p:
            for i, pos in enumerate(file_data_dim1.p):
                try:
                    field_name = byte2str(getattr(pos, "fieldName", f"P{i}"))
                    name = byte2str(getattr(pos, "name", f"Positioner {i}"))
                    desc = byte2str(getattr(pos, "desc", ""))
                    unit = byte2str(getattr(pos, "unit", ""))

                    # Handle data with proper type conversion
                    data = getattr(pos, "data", [])
                    if NUMPY_AVAILABLE and hasattr(data, "__iter__"):
                        try:
                            data = np.asarray(data, dtype=np.float64).tolist()
                        except:
                            data = list(data) if hasattr(data, "__iter__") else []

                    scan_dict[field_name] = {
                        "object": pos,
                        "type": "POS",
                        "data": data,
                        "unit": unit,
                        "name": name,
                        "desc": desc,
                        "fieldName": field_name,
                    }
                except Exception as e:
                    print(f"Warning: Error processing positioner {i}: {e}")
                    continue

        # Extract detectors with enhanced error handling
        if hasattr(file_data_dim1, "d") and file_data_dim1.d:
            for i, det in enumerate(file_data_dim1.d):
                try:
                    field_name = byte2str(getattr(det, "fieldName", f"D{i:02d}"))
                    name = byte2str(getattr(det, "name", f"Detector {i}"))
                    desc = byte2str(getattr(det, "desc", ""))
                    unit = byte2str(getattr(det, "unit", ""))

                    # Handle data with proper type conversion
                    data = getattr(det, "data", [])
                    if NUMPY_AVAILABLE and hasattr(data, "__iter__"):
                        try:
                            data = np.asarray(data, dtype=np.float32).tolist()
                        except:
                            data = list(data) if hasattr(data, "__iter__") else []

                    scan_dict[field_name] = {
                        "object": det,
                        "type": "DET",
                        "data": data,
                        "unit": unit,
                        "name": name,
                        "desc": desc,
                        "fieldName": field_name,
                    }
                except Exception as e:
                    print(f"Warning: Error processing detector {i}: {e}")
                    continue

        # Add index positioner if no positioners found
        if not any(item["type"] == "POS" for item in scan_dict.values()):
            # Create index positioner
            npts = len(next(iter(scan_dict.values()))["data"]) if scan_dict else 0
            scan_dict["P0"] = {
                "object": None,
                "type": "POS",
                "data": list(range(npts)),
                "unit": "a.u",
                "name": "Index",
                "desc": "Index",
                "fieldName": "P0",
            }

        # Determine first positioner and detector
        first_pos = next(
            (key for key, value in scan_dict.items() if value["type"] == "POS"), "P0"
        )
        first_det = next(
            (key for key, value in scan_dict.items() if value["type"] == "DET"),
            next(iter(scan_dict.keys())) if scan_dict else "D01",
        )

        return scan_dict, first_pos, first_det

    except Exception as e:
        print(f"Error processing scan data: {e}")
        # Return minimal scan structure
        return {}, "P0", "D01"


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
