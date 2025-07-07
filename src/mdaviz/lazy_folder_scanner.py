"""
Lazy folder scanning functionality.

This module provides efficient folder scanning capabilities for MDA files
with support for batch processing and progress tracking.

.. autosummary::

    ~LazyFolderScanner
    ~FolderScanResult
    ~FolderScanWorker
"""

from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from PyQt5 import QtCore
from .utils import get_file_info_lightweight, get_file_info_full
from dataclasses import dataclass


@dataclass
class FolderScanResult:
    """Result of a folder scan operation."""

    file_list: List[str]
    file_info_list: List[Dict[str, Any]]
    total_files: int
    scanned_files: int
    is_complete: bool
    error_message: Optional[str] = None


class LazyFolderScanner(QtCore.QObject):
    """
    Lazy folder scanner for handling large MDA folders efficiently.

    This class provides methods to scan folders in batches, allowing the UI
    to remain responsive while processing large numbers of files.

    Attributes:
        batch_size (int): Number of files to process in each batch
        max_files (int): Maximum number of files to scan before warning
        use_lightweight_scan (bool): Whether to use lightweight scanning
    """

    # Signals
    scan_progress = QtCore.pyqtSignal(int, int)  # current, total
    scan_complete = QtCore.pyqtSignal(object)  # FolderScanResult
    scan_error = QtCore.pyqtSignal(str)  # error message

    def __init__(
        self,
        batch_size: int = 50,
        max_files: int = 1000,
        use_lightweight_scan: bool = True,
    ):
        """
        Initialize the lazy folder scanner.

        Parameters:
            batch_size (int): Number of files to process in each batch
            max_files (int): Maximum number of files to scan before warning
            use_lightweight_scan (bool): Whether to use lightweight scanning
        """
        super().__init__()
        self.batch_size = batch_size
        self.max_files = max_files
        self.use_lightweight_scan = use_lightweight_scan
        self._scanning = False
        self._current_scan_path: Optional[Path] = None
        self.scanner_thread: Optional[QtCore.QThread] = None
        self.scanner_worker: Optional[FolderScanWorker] = None

    def scan_folder(
        self,
        folder_path: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> FolderScanResult:
        """
        Scan a folder for MDA files using lazy loading.

        Parameters:
            folder_path (Path): Path to the folder to scan
            progress_callback (callable, optional): Callback for progress updates

        Returns:
            FolderScanResult: Result of the scan operation
        """
        if not folder_path.exists() or not folder_path.is_dir():
            return FolderScanResult([], [], 0, 0, False, "Folder does not exist")

        # Get all MDA files in the folder
        mda_files = list(folder_path.glob("*.mda"))
        total_files = len(mda_files)

        if total_files == 0:
            return FolderScanResult([], [], 0, 0, True, "No MDA files found")

        if total_files > self.max_files:
            return FolderScanResult(
                [],
                [],
                total_files,
                0,
                False,
                f"Too many files ({total_files} > {self.max_files})",
            )

        # Scan files in batches
        file_list = []
        file_info_list = []
        scanned_files = 0

        for i in range(0, total_files, self.batch_size):
            batch_files = mda_files[i : i + self.batch_size]

            for file_path in batch_files:
                try:
                    if self.use_lightweight_scan:
                        file_info = get_file_info_lightweight(file_path)
                    else:
                        file_info = get_file_info_full(file_path)

                    file_list.append(file_path.name)
                    file_info_list.append(file_info)
                    scanned_files += 1

                    # Emit progress signal
                    self.scan_progress.emit(scanned_files, total_files)
                    if progress_callback:
                        progress_callback(scanned_files, total_files)

                except Exception as e:
                    # Continue scanning other files even if one fails
                    print(f"Error scanning {file_path}: {e}")
                    continue

        result = FolderScanResult(
            file_list=file_list,
            file_info_list=file_info_list,
            total_files=total_files,
            scanned_files=scanned_files,
            is_complete=True,
        )

        self.scan_complete.emit(result)
        return result

    def scan_folder_async(self, folder_path: Path) -> None:
        """
        Scan a folder asynchronously in a separate thread.

        Parameters:
            folder_path (Path): Path to the folder to scan
        """
        # Cancel any existing scan and wait for it to finish
        if self._scanning:
            self.cancel_scan()
            # Wait a bit for the thread to finish
            if self.scanner_thread is not None and self.scanner_thread.isRunning():
                self.scanner_thread.wait(1000)  # Wait up to 1 second

        self._scanning = True
        self._current_scan_path = folder_path

        # Create a worker thread for scanning
        self.scanner_thread = QtCore.QThread()
        self.scanner_worker = FolderScanWorker(
            folder_path, self.batch_size, self.max_files, self.use_lightweight_scan
        )

        # Move worker to thread
        self.scanner_worker.moveToThread(self.scanner_thread)

        # Connect signals
        self.scanner_thread.started.connect(self.scanner_worker.scan)
        self.scanner_worker.progress.connect(self.scan_progress)
        self.scanner_worker.complete.connect(self._on_scan_complete)
        self.scanner_worker.error.connect(self._on_scan_error)
        self.scanner_worker.finished.connect(self.scanner_thread.quit)
        self.scanner_thread.finished.connect(self.scanner_worker.deleteLater)
        self.scanner_thread.finished.connect(self.scanner_thread.deleteLater)

        # Start scanning
        self.scanner_thread.start()

    def _on_scan_complete(self, result: FolderScanResult) -> None:
        """Handle scan completion."""
        self._scanning = False
        self._current_scan_path = None
        self.scan_complete.emit(result)

    def _on_scan_error(self, error_message: str) -> None:
        """Handle scan error."""
        self._scanning = False
        self._current_scan_path = None
        self.scan_error.emit(error_message)

    def is_scanning(self) -> bool:
        """Check if a scan is currently in progress."""
        return self._scanning

    def cancel_scan(self) -> None:
        """Cancel the current scan operation."""
        if self._scanning and self.scanner_thread is not None:
            # Cancel the worker first
            if self.scanner_worker is not None:
                self.scanner_worker.cancel()

            # Quit the thread
            self.scanner_thread.quit()

            # Wait for the thread to finish (with timeout)
            if not self.scanner_thread.wait(2000):  # Wait up to 2 seconds
                # Force terminate if it doesn't finish gracefully
                self.scanner_thread.terminate()
                self.scanner_thread.wait(1000)  # Wait a bit more for termination

            self._scanning = False
            self._current_scan_path = None


class FolderScanWorker(QtCore.QObject):
    """
    Worker class for performing folder scans in background threads.
    """

    # Signals
    progress = QtCore.pyqtSignal(int, int)  # current, total
    complete = QtCore.pyqtSignal(object)  # FolderScanResult
    error = QtCore.pyqtSignal(str)  # error message
    finished = QtCore.pyqtSignal()

    def __init__(
        self,
        folder_path: Path,
        batch_size: int,
        max_files: int,
        use_lightweight_scan: bool,
    ):
        """
        Initialize the scan worker.

        Parameters:
            folder_path (Path): Path to the folder to scan
            batch_size (int): Number of files to process in each batch
            max_files (int): Maximum number of files to scan before warning
            use_lightweight_scan (bool): Whether to use lightweight scanning
        """
        super().__init__()
        self.folder_path = folder_path
        self.batch_size = batch_size
        self.max_files = max_files
        self.use_lightweight_scan = use_lightweight_scan
        self._cancelled = False

    def scan(self) -> None:
        """Perform the folder scan."""
        try:
            if not self.folder_path.exists() or not self.folder_path.is_dir():
                self.error.emit("Folder does not exist")
                self.finished.emit()
                return

            # Get all MDA files in the folder
            mda_files = list(self.folder_path.glob("*.mda"))
            total_files = len(mda_files)

            if total_files == 0:
                result = FolderScanResult([], [], 0, 0, True, "No MDA files found")
                self.complete.emit(result)
                self.finished.emit()
                return

            if total_files > self.max_files:
                result = FolderScanResult(
                    [],
                    [],
                    total_files,
                    0,
                    False,
                    f"Too many files ({total_files} > {self.max_files})",
                )
                self.complete.emit(result)
                self.finished.emit()
                return

            # Scan files in batches
            file_list = []
            file_info_list = []
            scanned_files = 0

            for i in range(0, total_files, self.batch_size):
                if self._cancelled:
                    break

                batch_files = mda_files[i : i + self.batch_size]

                for file_path in batch_files:
                    if self._cancelled:
                        break

                    try:
                        if self.use_lightweight_scan:
                            file_info = get_file_info_lightweight(file_path)
                        else:
                            file_info = get_file_info_full(file_path)

                        file_list.append(file_path.name)
                        file_info_list.append(file_info)
                        scanned_files += 1

                        # Emit progress signal
                        self.progress.emit(scanned_files, total_files)

                    except Exception as e:
                        # Continue scanning other files even if one fails
                        print(f"Error scanning {file_path}: {e}")
                        continue

            if not self._cancelled:
                result = FolderScanResult(
                    file_list=file_list,
                    file_info_list=file_info_list,
                    total_files=total_files,
                    scanned_files=scanned_files,
                    is_complete=True,
                )
                self.complete.emit(result)

        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()

    def cancel(self) -> None:
        """Cancel the scan operation."""
        self._cancelled = True
