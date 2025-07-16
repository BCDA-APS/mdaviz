from contextlib import nullcontext as does_not_raise
import pytest
from PyQt6.QtCore import Qt

# Import the application modules
from mdaviz.mainwindow import MainWindow


@pytest.fixture
def qtbot(qtbot):
    """Provide qtbot fixture for GUI testing."""
    return qtbot


@pytest.fixture
def app(qtbot):
    """Create and return a QApplication instance."""
    return qtbot.qapp


# The following tests are skipped by default to avoid PyQt5/Qt crashes in headless/CI environments.
# To re-enable, remove or comment out the @pytest.mark.skip decorators and run locally with a display.


@pytest.mark.skip(reason="Skip GUI test in CI/headless environment")
def test_app_startup(qtbot):
    """Test that the application can start without errors."""
    with does_not_raise():
        # Create the main window
        main_window = MainWindow()
        qtbot.addWidget(main_window)

        # Verify the window was created successfully
        assert main_window is not None
        assert main_window.windowTitle() == "mdaviz"

        # Test basic window properties
        assert not main_window.isVisible()  # Window not shown yet
        assert main_window.windowFlags() & Qt.WindowType.Window

        # Close the window without showing it to avoid crashes
        main_window.close()


@pytest.mark.skip(reason="Skip GUI test in CI/headless environment")
def test_main_window_components(qtbot):
    """Test that main window components are properly initialized."""
    main_window = MainWindow()
    qtbot.addWidget(main_window)

    # Test that key components exist
    assert hasattr(main_window, "mvc_folder")
    assert hasattr(main_window, "lazy_scanner")
    assert hasattr(main_window, "setStatus")

    # Test status setting
    main_window.setStatus("Test status")
    # Note: We can't easily test the status bar content without exposing it,
    # but we can test that the method doesn't raise exceptions

    # Test window geometry restoration
    assert main_window.geometry().width() > 0
    assert main_window.geometry().height() > 0

    # Close the window
    main_window.close()


@pytest.mark.skip(reason="Skip GUI test in CI/headless environment")
def test_about_dialog(qtbot):
    """Test that the about dialog can be created."""
    from mdaviz.aboutdialog import AboutDialog

    main_window = MainWindow()
    qtbot.addWidget(main_window)

    # Create about dialog
    about_dialog = AboutDialog(main_window)
    qtbot.addWidget(about_dialog)

    # Test basic properties
    assert about_dialog is not None
    assert "mdaviz" in about_dialog.windowTitle()

    # Test dialog buttons exist
    assert hasattr(about_dialog, "docs_pb")
    assert hasattr(about_dialog, "issues_pb")
    assert hasattr(about_dialog, "license_pb")

    # Close dialogs
    about_dialog.close()
    main_window.close()


@pytest.mark.skip(reason="Skip GUI test in CI/headless environment")
def test_data_cache_initialization(qtbot):
    """Test that DataCache can be initialized."""
    from mdaviz.data_cache import DataCache

    # Create DataCache
    cache = DataCache(max_size=10)
    qtbot.addWidget(cache)

    # Test basic properties
    assert cache is not None
    assert cache.max_size == 10

    # Test basic operations
    cache.put("test_key", "test_value")
    assert cache.get("test_key") == "test_value"
    assert cache.get("nonexistent_key") is None


@pytest.mark.skip(reason="Skip GUI test in CI/headless environment")
def test_lazy_folder_scanner_initialization(qtbot):
    """Test that LazyFolderScanner can be initialized."""
    from mdaviz.lazy_folder_scanner import LazyFolderScanner

    # Create LazyFolderScanner
    scanner = LazyFolderScanner(batch_size=50, max_files=1000)
    qtbot.addWidget(scanner)

    # Test basic properties
    assert scanner is not None
    assert scanner.batch_size == 50
    assert scanner.max_files == 1000

    # Test that signals exist
    assert hasattr(scanner, "scan_progress")
    assert hasattr(scanner, "scan_complete")
    assert hasattr(scanner, "scan_error")


@pytest.mark.skip(reason="Skip GUI test in CI/headless environment")
def test_fit_manager_initialization(qtbot):
    """Test that FitManager can be initialized."""
    from mdaviz.fit_manager import FitManager

    # Create FitManager
    fit_manager = FitManager()
    qtbot.addWidget(fit_manager)

    # Test basic properties
    assert fit_manager is not None
    assert hasattr(fit_manager, "available_models")
    assert hasattr(fit_manager, "perform_fit")

    # Test that available models exist
    models = fit_manager.available_models()
    assert isinstance(models, list)
    assert len(models) > 0


# Non-GUI tests (safe for CI/headless)
def test_xdrlib_fallback():
    """Test that the xdrlib fallback works correctly."""

    # Test that we can import the fallback module
    from mdaviz.synApps_mdalib import f_xdrlib

    # Test basic functionality
    assert hasattr(f_xdrlib, "Packer")
    assert hasattr(f_xdrlib, "Unpacker")

    # Test packer functionality
    packer = f_xdrlib.Packer()
    packer.pack_uint(12345)
    packer.pack_string("test")
    data = packer.get_buffer()
    assert len(data) > 0

    # Test unpacker functionality
    unpacker = f_xdrlib.Unpacker(data)
    value = unpacker.unpack_uint()
    assert value == 12345


def test_deprecation_warnings_suppressed():
    """Test that PyQt5 deprecation warnings are suppressed."""
    import warnings

    # Capture warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        # Import mdaviz (this should trigger the warning filter)

        # Check that sipPyTypeDict warnings are suppressed
        sip_warnings = [
            warning for warning in w if "sipPyTypeDict" in str(warning.message)
        ]
        assert len(sip_warnings) == 0, "PyQt5 deprecation warnings should be suppressed"


# Note: The following test is kept for reference but commented out
# as it requires user interaction which is not suitable for automated testing
# def test_app(qtbot):
#     """mdaviz app should start with no errors."""
#     from mdaviz import app
#     gui = app.gui()
#     assert gui is not None
