"""
Preferences dialog for application settings.

This module provides a dedicated dialog for managing application preferences,
including auto-load settings and plot height configuration.

.. autosummary::

    ~PreferencesDialog
"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QSpinBox,
    QDialogButtonBox,
    QCheckBox,
)
from mdaviz.user_settings import settings


class PreferencesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.setModal(True)
        self.resize(400, 200)

        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)

        # Auto-load setting
        self.auto_load_checkbox = QCheckBox("Auto-load first folder on startup")
        layout.addWidget(self.auto_load_checkbox)

        # Add spacing
        layout.addStretch()

        # Plot height setting
        plot_label = QLabel("Maximum Plot Height (pixels):")
        self.plot_spinbox = QSpinBox()
        self.plot_spinbox.setRange(200, 2000)
        self.plot_spinbox.setSingleStep(100)
        self.plot_spinbox.setSuffix(" px")

        layout.addWidget(plot_label)
        layout.addWidget(self.plot_spinbox)

        # Helpful caption
        plot_caption = QLabel(
            "Use this setting if plot areas expand vertically unexpectedly due to UI bugs."
        )
        plot_caption.setWordWrap(True)
        plot_caption.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(plot_caption)

        # Add spacing
        layout.addStretch()

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _load_settings(self):
        """Load current settings into the dialog."""
        # Auto-load setting
        auto_load_val = settings.getKey("auto_load_folder")
        if auto_load_val is None:
            auto_load_val = True
        elif isinstance(auto_load_val, str):
            auto_load_val = auto_load_val.lower() in ("true", "1", "yes", "on")
        self.auto_load_checkbox.setChecked(bool(auto_load_val))

        # Plot height setting
        plot_height_val = settings.getKey("plot_max_height")
        try:
            plot_height_val = int(plot_height_val)
        except (TypeError, ValueError):
            plot_height_val = 800
        self.plot_spinbox.setValue(plot_height_val)

    def get_settings(self):
        """Get the current settings from the dialog."""
        return {
            "auto_load_folder": self.auto_load_checkbox.isChecked(),
            "plot_max_height": self.plot_spinbox.value(),
        }
