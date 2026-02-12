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
from typing import Any, Optional, Callable
from PyQt6.QtCore import QObject, QThread, pyqtSignal
from mdaviz.utils import get_file_info_lightweight, get_file_info_full
from dataclasses import dataclass
from mdaviz.logger import get_logger
from mdaviz.progress_dialog import AsyncProgressDialog
from mdaviz.lazy_loading_config import get_config

# Get logger for this module
logger = get_logger("lazy_folder_scanner")


@dataclass
class FolderScanResult:
    """Result of a folder scan operation."""

    file_list: list[str]
    file_info_list: list[dict[str, Any]]
    total_files: int
    scanned_files: int
    is_complete: bool
    error_message: Optional[str] = None
    is_progressive: bool = False  # Whether this is a progressive scan


class LazyFolderScanner(QObject):
    """
    Lazy folder scanner for handling large MDA folders efficiently.

    This class provides methods to scan folders in batches, allowing the UI
    to remain responsive while processing large numbers of files.

    Attributes:
        batch_size (int): Number of files to process in each batch
        max_files (int): Maximum number of files to scan before warning
        use_lightweight_scan (bool): Whether to use lightweight scanning
        progressive_loading (bool): Whether to use progressive loading for large directories
    """

    # Signals
    scan_progress = pyqtSignal(int, int)  # current, total
    scan_complete = pyqtSignal(object)  # FolderScanResult
    scan_error = pyqtSignal(str)  # error message
    progressive_scan_update = pyqtSignal(object)  # FolderScanResult (partial)

    def __init__(
        self,
        batch_size: int = 50,
        max_files: int = 10000,
        use_lightweight_scan: bool = True,
        progressive_loading: bool = True,
    ):
        """
        Initialize the lazy folder scanner.

        Parameters:
            batch_size (int): Number of files to process in each batch
            max_files (int): Maximum number of files to scan before warning
            use_lightweight_scan (bool): Whether to use lightweight scanning
            progressive_loading (bool): Whether to use progressive loading for large directories
        """
        super().__init__()
        self.batch_size = batch_size
        self.max_files = max_files
        self.use_lightweight_scan = use_lightweight_scan
        self.progressive_loading = progressive_loading
        self._scanning = False
        self._current_scan_path: Optional[Path] = None
        self.scanner_thread: Optional[QThread] = None
        self.scanner_worker: Optional[FolderScanWorker] = None
        self._progress_dialog: Optional[AsyncProgressDialog] = None

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

        # For very large directories, use progressive loading
        if total_files > self.max_files and self.progressive_loading:
            return self._progressive_scan(folder_path, mda_files, progress_callback)

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
                    logger.error(f"Error scanning {file_path}: {e}")
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

    def _progressive_scan(
        self,
        folder_path: Path,
        mda_files: list[Path],
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> FolderScanResult:
        """
        Perform progressive scanning for very large directories.

        This method scans files in chunks and provides partial results
        to keep the UI responsive.

        Parameters:
            folder_path (Path): Path to the folder to scan
            mda_files (list[Path]): List of MDA files to scan
            progress_callback (callable, optional): Callback for progress updates

        Returns:
            FolderScanResult: Initial result with first batch of files
        """
        total_files = len(mda_files)

        # For progressive loading, we'll scan the first batch immediately
        # and return a partial result
        initial_batch_size = min(self.batch_size * 2, total_files)

        file_list = []
        file_info_list = []
        scanned_files = 0

        # Scan initial batch
        for i in range(initial_batch_size):
            file_path = mda_files[i]
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
                logger.error(f"Error scanning {file_path}: {e}")
                continue

        # Return partial result
        result = FolderScanResult(
            file_list=file_list,
            file_info_list=file_info_list,
            total_files=total_files,
            scanned_files=scanned_files,
            is_complete=False,  # Not complete yet
            is_progressive=True,
        )

        # Emit progressive update
        self.progressive_scan_update.emit(result)

        # Continue scanning in background
        self._continue_progressive_scan(
            folder_path, mda_files, scanned_files, progress_callback
        )

        return result

    def _continue_progressive_scan(
        self,
        folder_path: Path,
        mda_files: list[Path],
        start_index: int,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> None:
        """
        Continue progressive scanning from a given index.

        Parameters:
            folder_path (Path): Path to the folder to scan
            mda_files (list[Path]): List of MDA files to scan
            start_index (int): Index to start scanning from
            progress_callback (callable, optional): Callback for progress updates
        """
        total_files = len(mda_files)
        file_list = []
        file_info_list = []
        scanned_files = start_index

        # Continue scanning from where we left off
        for i in range(start_index, total_files, self.batch_size):
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
                    logger.error(f"Error scanning {file_path}: {e}")
                    continue

            # Emit progressive update every batch
            if file_list:
                result = FolderScanResult(
                    file_list=file_list,
                    file_info_list=file_info_list,
                    total_files=total_files,
                    scanned_files=scanned_files,
                    is_complete=(scanned_files >= total_files),
                    is_progressive=True,
                )
                self.progressive_scan_update.emit(result)

        # Final completion
        if scanned_files >= total_files:
            final_result = FolderScanResult(
                file_list=file_list,
                file_info_list=file_info_list,
                total_files=total_files,
                scanned_files=scanned_files,
                is_complete=True,
                is_progressive=True,
            )
            self.scan_complete.emit(final_result)

    def scan_folder_async(self, folder_path: Path) -> None:
        """
        Scan a folder asynchronously in a separate thread.

        Parameters:
            folder_path (Path): Path to the folder to scan
        """
        # Ignore duplicate refresh: same folder already scanning
        if self._scanning and self._current_scan_path is not None:
            if self._current_scan_path.resolve() == Path(folder_path).resolve():
                return

        # Cancel any existing scan and wait for the thread to actually finish
        # so we never destroy a QThread while it is still running (avoids crash).
        old_thread = None
        if self._scanning:
            self.cancel_scan()
            old_thread = self.scanner_thread
            self.scanner_thread = None
            self.scanner_worker = None

        if old_thread is not None and old_thread.isRunning():
            max_wait_ms = 10000  # 10 seconds max
            waited_ms = 0
            while old_thread.isRunning() and waited_ms < max_wait_ms:
                old_thread.wait(100)
                waited_ms += 100
            if old_thread.isRunning():
                logger.warning(
                    "Previous scan thread did not finish within %d ms; skipping new scan",
                    max_wait_ms,
                )
                self.scan_error.emit(
                    "Previous scan did not finish in time. Please try again in a moment."
                )
                return

        self._scanning = True
        self._current_scan_path = folder_path

        # Create progress dialog if enabled
        if get_config().enable_progress_dialogs:
            self._progress_dialog = AsyncProgressDialog(
                "Scanning folder...", parent=None
            )
            self._progress_dialog.show()
        else:
            self._progress_dialog = None

        # Create a worker thread for scanning
        self.scanner_thread = QThread()
        self.scanner_worker = FolderScanWorker(
            folder_path,
            self.batch_size,
            self.max_files,
            self.use_lightweight_scan,
            self.progressive_loading,
        )

        # Move worker to thread
        self.scanner_worker.moveToThread(self.scanner_thread)

        # Connect signals
        self.scanner_thread.started.connect(self.scanner_worker.scan)
        self.scanner_worker.progress.connect(self.scan_progress)
        self.scanner_worker.progress.connect(self._update_progress)
        self.scanner_worker.complete.connect(self._on_scan_complete)
        self.scanner_worker.error.connect(self._on_scan_error)
        self.scanner_worker.progressive_update.connect(self.progressive_scan_update)
        self.scanner_worker.finished.connect(self.scanner_thread.quit)
        self.scanner_thread.finished.connect(self.scanner_worker.deleteLater)
        self.scanner_thread.finished.connect(self.scanner_thread.deleteLater)

        # Start scanning
        self.scanner_thread.start()

    def _update_progress(self, current: int, total: int) -> None:
        """Update progress dialog."""
        if hasattr(self, "_progress_dialog") and self._progress_dialog:
            self._progress_dialog.update_progress_async(
                current, total, f"Scanning files: {current}/{total}"
            )

    def _on_scan_complete(self, result: FolderScanResult) -> None:
        """Handle scan completion."""
        self._scanning = False
        self._current_scan_path = None
        # Close progress dialog
        if hasattr(self, "_progress_dialog") and self._progress_dialog:
            self._progress_dialog.complete_async()
        self.scan_complete.emit(result)

    def _on_scan_error(self, error_message: str) -> None:
        """Handle scan error."""
        self._scanning = False
        self._current_scan_path = None
        # Close progress dialog on error
        if hasattr(self, "_progress_dialog") and self._progress_dialog:
            self._progress_dialog.fail_async(error_message)
        self.scan_error.emit(error_message)

    def is_scanning(self) -> bool:
        """Check if a scan is currently in progress."""
        return self._scanning

    def cancel_scan(self) -> None:
        """Cancel the current scan operation."""
        if self.scanner_worker is not None:
            self.scanner_worker.cancel()
        self._scanning = False
        self._current_scan_path = None


class FolderScanWorker(QObject):
    """
    Worker class for performing folder scans in background threads.
    """

    # Signals
    progress = pyqtSignal(int, int)  # current, total
    complete = pyqtSignal(object)  # FolderScanResult
    error = pyqtSignal(str)  # error message
    progressive_update = pyqtSignal(object)  # FolderScanResult (partial)
    finished = pyqtSignal()

    def __init__(
        self,
        folder_path: Path,
        batch_size: int,
        max_files: int,
        use_lightweight_scan: bool,
        progressive_loading: bool = True,
    ):
        """
        Initialize the folder scan worker.

        Parameters:
            folder_path (Path): Path to the folder to scan
            batch_size (int): Number of files to process in each batch
            max_files (int): Maximum number of files to scan before warning
            use_lightweight_scan (bool): Whether to use lightweight scanning
            progressive_loading (bool): Whether to use progressive loading
        """
        super().__init__()
        self.folder_path = folder_path
        self.batch_size = batch_size
        self.max_files = max_files
        self.use_lightweight_scan = use_lightweight_scan
        self.progressive_loading = progressive_loading
        self._cancelled = False

    def scan(self) -> None:
        """Perform the folder scan operation."""
        try:
            if not self.folder_path.exists() or not self.folder_path.is_dir():
                self.error.emit("Folder does not exist")
                return

            # Get all MDA files in the folder
            mda_files = list(self.folder_path.glob("*.mda"))
            total_files = len(mda_files)

            if total_files == 0:
                result = FolderScanResult([], [], 0, 0, True, "No MDA files found")
                self.complete.emit(result)
                return

            # For very large directories, use progressive loading
            if total_files > self.max_files and self.progressive_loading:
                self._progressive_scan(mda_files)
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
                return

            # Regular batch scanning
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
                        logger.error(f"Error scanning {file_path}: {e}")
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
            self.error.emit(f"Scan error: {e}")
        finally:
            self.finished.emit()

    def _progressive_scan(self, mda_files: list[Path]) -> None:
        """
        Perform progressive scanning for very large directories.

        Parameters:
            mda_files (list[Path]): List of MDA files to scan
        """
        total_files = len(mda_files)

        # Initial batch
        initial_batch_size = min(self.batch_size * 2, total_files)
        file_list = []
        file_info_list = []
        scanned_files = 0

        # Scan initial batch
        for i in range(initial_batch_size):
            if self._cancelled:
                break

            file_path = mda_files[i]
            try:
                if self.use_lightweight_scan:
                    file_info = get_file_info_lightweight(file_path)
                else:
                    file_info = get_file_info_full(file_path)

                file_list.append(file_path.name)
                file_info_list.append(file_info)
                scanned_files += 1

                self.progress.emit(scanned_files, total_files)

            except Exception as e:
                logger.error(f"Error scanning {file_path}: {e}")
                continue

        # Emit initial result
        if not self._cancelled:
            result = FolderScanResult(
                file_list=file_list,
                file_info_list=file_info_list,
                total_files=total_files,
                scanned_files=scanned_files,
                is_complete=False,
                is_progressive=True,
            )
            self.progressive_update.emit(result)

        # Continue scanning in background
        if not self._cancelled:
            self._continue_progressive_scan(mda_files, scanned_files)

    def _continue_progressive_scan(
        self, mda_files: list[Path], start_index: int
    ) -> None:
        """
        Continue progressive scanning from a given index.

        Parameters:
            mda_files (list[Path]): List of MDA files to scan
            start_index (int): Index to start scanning from
        """
        total_files = len(mda_files)
        file_list = []
        file_info_list = []
        scanned_files = start_index

        # Continue scanning from where we left off
        for i in range(start_index, total_files, self.batch_size):
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

                    self.progress.emit(scanned_files, total_files)

                except Exception as e:
                    logger.error(f"Error scanning {file_path}: {e}")
                    continue

            # Emit progressive update every batch
            if file_list and not self._cancelled:
                result = FolderScanResult(
                    file_list=file_list,
                    file_info_list=file_info_list,
                    total_files=total_files,
                    scanned_files=scanned_files,
                    is_complete=(scanned_files >= total_files),
                    is_progressive=True,
                )
                self.progressive_update.emit(result)

        # Final completion
        if scanned_files >= total_files and not self._cancelled:
            final_result = FolderScanResult(
                file_list=file_list,
                file_info_list=file_info_list,
                total_files=total_files,
                scanned_files=scanned_files,
                is_complete=True,
                is_progressive=True,
            )
            self.complete.emit(final_result)

    def cancel(self) -> None:
        """Cancel the scan operation."""
        self._cancelled = True
