"""
License dialog functionality.

This module provides a dialog for displaying license information.

.. autosummary::

    ~LicenseDialog
"""

from pathlib import Path
from typing import Optional
from PyQt6.QtWidgets import QDialog, QTextEdit, QVBoxLayout, QWidget

from mdaviz import utils


class LicenseDialog(QDialog):
    """
    Show license text in a GUI window.

    This dialog displays the project license in a readable format.
    """

    # UI file name matches this module, different extension
    ui_file = utils.getUiFileName(__file__)

    def __init__(self, parent: Optional[QWidget]) -> None:
        """
        Initialize the license dialog.

        Parameters:
            parent (Optional[QWidget]): Parent widget for the dialog
        """
        self.parent = parent

        super().__init__(parent)

        # Try to load UI file, with fallback to programmatic creation
        try:
            utils.myLoadUi(self.ui_file, baseinstance=self)
        except Exception as e:
            print(f"Warning: Could not load UI file {self.ui_file}: {e}")
            self._create_fallback_ui()

        self.setup()

    def _create_fallback_ui(self) -> None:
        """
        Create UI programmatically if UI file loading fails.

        This provides a fallback when running tests or if the UI file is not available.
        """
        self.setWindowTitle("License")
        self.resize(600, 400)

        layout = QVBoxLayout()
        self.license = QTextEdit()
        self.license.setReadOnly(True)
        layout.addWidget(self.license)
        self.setLayout(layout)

    def setup(self) -> None:
        """
        Set up the license dialog with license text.

        This method loads the license file and displays it in the dialog.
        """
        try:
            # Find the LICENSE.txt file relative to the project root
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent
            license_file = project_root / "LICENSE.txt"

            self.setModal(True)

            # Read license file with proper error handling
            if license_file.exists():
                with open(license_file, "r", encoding="utf-8") as f:
                    license_text = f.read()
            else:
                license_text = "License file not found."

            # Ensure license widget exists before setting text
            if hasattr(self, "license") and self.license is not None:
                self.license.setText(license_text)
            else:
                print("Warning: License widget not available")

        except Exception as e:
            print(f"Error setting up license dialog: {e}")
            # Fallback text
            if hasattr(self, "license") and self.license is not None:
                self.license.setText("Error loading license information.")
