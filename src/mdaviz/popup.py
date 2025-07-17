"""
Popup dialog functionality.

This module provides a dialog for displaying popup messages.

.. autosummary::

    ~PopUp
"""

from typing import Optional
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout, QWidget

from mdaviz import utils


class PopUp(QDialog):
    """Load a generic popup Dialog as a .ui file."""

    # UI file name matches this module, different extension
    ui_file = utils.getUiFileName(__file__)

    def __init__(self, parent: Optional[QWidget], message: str) -> None:
        """
        Initialize the popup dialog.

        Parameters:
            parent (Optional[QWidget]): Parent widget for the dialog
            message (str): Message to display in the popup
        """
        self._parent_widget = parent

        super().__init__(parent)

        # Try to load UI file, with fallback to programmatic creation
        try:
            utils.myLoadUi(self.ui_file, baseinstance=self)
        except Exception as e:
            print(f"Warning: Could not load UI file {self.ui_file}: {e}")
            self._create_fallback_ui()

        # Ensure widgets exist (either from UI file or fallback)
        if not hasattr(self, 'message') or not hasattr(self, 'buttonBox'):
            self._create_fallback_ui()

        self.message.setText(message)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def _create_fallback_ui(self) -> None:
        """
        Create UI programmatically if UI file loading fails.

        This provides a fallback when running tests or if the UI file is not available.
        """
        self.setWindowTitle("Dialog")
        self.resize(530, 113)

        layout = QVBoxLayout()
        
        # Create message label
        self.message = QLabel()
        self.message.setText("TextLabel")
        layout.addWidget(self.message)

        # Create button box
        self.buttonBox = QDialogButtonBox()
        self.buttonBox.setStandardButtons(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok
        )
        layout.addWidget(self.buttonBox)

        self.setLayout(layout)

    def accept(self) -> None:
        """OK button was clicked."""
        super().accept()
        if hasattr(self._parent_widget, 'proceed'):
            self._parent_widget.proceed()

    def reject(self) -> None:
        """Cancel button was clicked."""
        super().reject()
        if hasattr(self._parent_widget, 'cancel'):
            self._parent_widget.cancel()
