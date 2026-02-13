"""
Tests for PreferencesDialog.
"""

from unittest.mock import patch

from mdaviz.preferences_dialog import PreferencesDialog


def test_preferences_dialog_instantiation(qtbot):
    """PreferencesDialog can be instantiated and has expected title."""
    dialog = PreferencesDialog()
    qtbot.addWidget(dialog)
    assert dialog.windowTitle() == "Preferences"
    assert dialog.auto_load_checkbox is not None
    assert dialog.plot_spinbox is not None


def test_preferences_dialog_get_settings(qtbot):
    """get_settings() returns dict with auto_load_folder and plot_max_height."""
    with patch("mdaviz.preferences_dialog.settings") as mock_settings:
        mock_settings.getKey.side_effect = lambda k: (
            True if k == "auto_load_folder" else 800
        )
        dialog = PreferencesDialog()
        qtbot.addWidget(dialog)
    settings_dict = dialog.get_settings()
    assert "auto_load_folder" in settings_dict
    assert "plot_max_height" in settings_dict
    assert isinstance(settings_dict["auto_load_folder"], bool)
    assert isinstance(settings_dict["plot_max_height"], int)


def test_preferences_dialog_load_settings_handles_string_auto_load(qtbot):
    """_load_settings() parses string auto_load_folder (true/yes/1 -> True)."""
    with patch("mdaviz.preferences_dialog.settings") as mock_settings:

        def get_key(k):
            if k == "auto_load_folder":
                return "yes"
            if k == "plot_max_height":
                return 600
            return None

        mock_settings.getKey.side_effect = get_key
        dialog = PreferencesDialog()
        qtbot.addWidget(dialog)
    assert dialog.auto_load_checkbox.isChecked() is True
    assert dialog.plot_spinbox.value() == 600


def test_preferences_dialog_load_settings_handles_invalid_plot_height(qtbot):
    """_load_settings() uses default 800 when plot_max_height is invalid."""
    with patch("mdaviz.preferences_dialog.settings") as mock_settings:

        def get_key(k):
            if k == "auto_load_folder":
                return False
            if k == "plot_max_height":
                return "not_a_number"
            return None

        mock_settings.getKey.side_effect = get_key
        dialog = PreferencesDialog()
        qtbot.addWidget(dialog)
    assert dialog.plot_spinbox.value() == 800
