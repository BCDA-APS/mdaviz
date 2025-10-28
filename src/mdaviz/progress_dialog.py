"""
Progress dialog for showing operation progress.

This module provides a progress dialog that can be used to show progress
for long-running operations like folder scanning.

.. autosummary::

    ~ProgressDialog
"""

from PyQt6 import QtWidgets, QtCore
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget, QProgressDialog, QApplication
from typing import Optional, Callable


class ProgressDialog(QProgressDialog):
    """
    Progress dialog for showing operation progress.

    This dialog provides a user-friendly way to show progress for
    long-running operations and allows users to cancel the operation.

    Attributes:
        auto_close (bool): Whether to automatically close when complete
        auto_reset (bool): Whether to automatically reset when complete
    """

    def __init__(
        self,
        title: str = "Progress",
        parent: Optional[QWidget] = None,
        auto_close: bool = True,
        auto_reset: bool = True,
    ):
        """
        Initialize the progress dialog.

        Parameters:
            title (str): Dialog title
            parent (QWidget, optional): Parent widget
            auto_close (bool): Whether to automatically close when complete
            auto_reset (bool): Whether to automatically reset when complete
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setAutoClose(auto_close)
        self.setAutoReset(auto_reset)
        self.setMinimumDuration(0)  # Show immediately
        self.setModal(True)

        # Set up the dialog
        self.setLabelText("Initializing...")
        self.setRange(0, 100)
        self.setValue(0)

        # Connect cancel signal
        self.canceled.connect(self._on_canceled)
        self._canceled = False
        self._cancel_callback: Optional[Callable[[], None]] = None

    def set_cancel_callback(self, callback: Callable[[], None]) -> None:
        """
        Set a callback function to be called when the user cancels.

        Parameters:
            callback (callable): Function to call when canceled
        """
        self._cancel_callback = callback

    def update_progress(self, current: int, total: int, message: str = "") -> None:
        """
        Update the progress display.

        Parameters:
            current (int): Current progress value
            total (int): Total progress value
            message (str, optional): Progress message
        """
        if self._canceled:
            return

        # Calculate percentage
        if total > 0:
            percentage = int((current / total) * 100)
        else:
            percentage = 0

        # Update progress bar
        self.setValue(percentage)

        # Update label text
        if message:
            self.setLabelText(message)
        else:
            self.setLabelText(f"Processing: {current}/{total} ({percentage}%)")

        # Process events to keep UI responsive
        QApplication.processEvents()

    def set_message(self, message: str) -> None:
        """
        Set the progress message.

        Parameters:
            message (str): Progress message
        """
        self.setLabelText(message)
        QApplication.processEvents()

    def _on_canceled(self) -> None:
        """Handle cancel button click."""
        self._canceled = True
        if self._cancel_callback:
            self._cancel_callback()

    def is_canceled(self) -> bool:
        """Check if the operation was canceled."""
        return self._canceled

    def reset_cancel_state(self) -> None:
        """Reset the cancel state."""
        self._canceled = False


class AsyncProgressDialog(ProgressDialog):
    """
    Asynchronous progress dialog that can be updated from background threads.

    This dialog uses Qt's signal/slot mechanism to safely update the UI
    from background threads.
    """

    # Signals for thread-safe updates
    progress_updated = pyqtSignal(int, int, str)  # current, total, message
    message_updated = pyqtSignal(str)  # message
    operation_completed = pyqtSignal()
    operation_failed = pyqtSignal(str)  # error message

    def __init__(
        self, title: str = "Progress", parent: Optional[QtWidgets.QWidget] = None
    ):
        """
        Initialize the async progress dialog.

        Parameters:
            title (str): Dialog title
            parent (QWidget, optional): Parent widget
        """
        super().__init__(title, parent)

        # Connect signals to slots
        self.progress_updated.connect(self._update_progress_slot)
        self.message_updated.connect(self._set_message_slot)
        self.operation_completed.connect(self._operation_completed_slot)
        self.operation_failed.connect(self._operation_failed_slot)

    def update_progress_async(
        self, current: int, total: int, message: str = ""
    ) -> None:
        """
        Update progress asynchronously (thread-safe).

        Parameters:
            current (int): Current progress value
            total (int): Total progress value
            message (str, optional): Progress message
        """
        self.progress_updated.emit(current, total, message)

    def set_message_async(self, message: str) -> None:
        """
        Set message asynchronously (thread-safe).

        Parameters:
            message (str): Progress message
        """
        self.message_updated.emit(message)

    def complete_async(self) -> None:
        """Mark operation as completed asynchronously."""
        self.operation_completed.emit()

    def fail_async(self, error_message: str) -> None:
        """
        Mark operation as failed asynchronously.

        Parameters:
            error_message (str): Error message
        """
        self.operation_failed.emit(error_message)

    def _update_progress_slot(self, current: int, total: int, message: str) -> None:
        """Slot for thread-safe progress updates."""
        super().update_progress(current, total, message)

    def _set_message_slot(self, message: str) -> None:
        """Slot for thread-safe message updates."""
        super().set_message(message)

    def _operation_completed_slot(self) -> None:
        """Slot for operation completion."""
        self.setLabelText("Operation completed successfully")
        # Don't set value to 100 to avoid rendering issue
        # Just show the completion message

        # Keep dialog open for a moment to show completion message
        def close_dialog() -> None:
            self.close()

        QtCore.QTimer.singleShot(1000, close_dialog)  # Close after 1 second

    def _operation_failed_slot(self, error_message: str) -> None:
        """Slot for operation failure."""
        self.setLabelText(f"Operation failed: {error_message}")

        # Keep dialog open for a moment to show error
        def close_dialog() -> None:
            self.close()

        QtCore.QTimer.singleShot(2000, close_dialog)
