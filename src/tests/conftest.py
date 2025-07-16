#!/usr/bin/env python
"""
Pytest configuration and fixtures for mdaviz tests.

This module provides common fixtures and configuration for all tests,
especially for GUI testing with pytest-qt.

.. autosummary::

    ~qtbot
    ~qapp
    ~sample_mda_data
    ~mock_chartview_parent
    ~temp_test_files
"""

from typing import TYPE_CHECKING
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
from PyQt6.QtWidgets import QApplication

if TYPE_CHECKING:
    from _pytest.fixtures import FixtureRequest
    from _pytest.capture import CaptureFixture
    from _pytest.logging import LogCaptureFixture
    from pytest_mock.plugin import MockerFixture


@pytest.fixture(scope="session")
def qapp() -> "QApplication":
    """
    Create a QApplication instance for testing.
    
    This fixture ensures that a QApplication exists for all Qt-based tests.
    The application is created once per test session.
    
    Returns:
        QApplication: The Qt application instance
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def sample_mda_data() -> dict:
    """
    Create sample MDA data for testing.
    
    Returns:
        dict: Sample MDA data structure with metadata and scan data
    """
    return {
        "metadata": {
            "rank": 1,
            "dimensions": [100],
            "data_type": "float32",
            "file_name": "test_sample.mda",
            "file_path": "/tmp/test_sample.mda",
            "folder_path": "/tmp",
        },
        "scanDict": {
            "pos1": {
                "name": "Position 1",
                "values": list(range(100)),
                "unit": "mm",
            },
            "det1": {
                "name": "Detector 1", 
                "values": [i * 2.5 for i in range(100)],
                "unit": "counts",
            },
            "det2": {
                "name": "Detector 2",
                "values": [i * 1.5 + 10 for i in range(100)],
                "unit": "counts",
            },
        },
        "firstPos": 0,
        "firstDet": 1,
        "pvList": ["pos1", "det1", "det2"],
        "index": 0,
    }


@pytest.fixture
def mock_chartview_parent() -> MagicMock:
    """
    Create a mock parent for ChartView testing.
    
    Returns:
        MagicMock: Mock parent with all required attributes
    """
    parent = MagicMock()
    
    # Mock mda_file_viz attributes
    parent.mda_file_viz.curveBox = MagicMock()
    parent.mda_file_viz.clearAll = MagicMock()
    parent.mda_file_viz.curveRemove = MagicMock()
    parent.mda_file_viz.cursor1_remove = MagicMock()
    parent.mda_file_viz.cursor2_remove = MagicMock()
    parent.mda_file_viz.offset_value = MagicMock()
    parent.mda_file_viz.factor_value = MagicMock()
    parent.mda_file_viz.curveBox.currentIndexChanged = MagicMock()
    
    # Mock mda_file attributes
    parent.mda_file.tabManager.tabRemoved = MagicMock()
    
    # Mock other required attributes
    parent.detRemoved = MagicMock()
    
    return parent


@pytest.fixture
def temp_test_files(tmp_path: Path) -> Path:
    """
    Create temporary test files for testing.
    
    Args:
        tmp_path: Pytest's temporary path fixture
        
    Returns:
        Path: Path to directory containing test files
    """
    # Create test MDA files
    for i in range(5):
        test_file = tmp_path / f"test_{i:04d}.mda"
        test_file.write_bytes(b"fake mda data")
    
    # Create a subdirectory with more files
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    for i in range(3):
        test_file = subdir / f"sub_test_{i:04d}.mda"
        test_file.write_bytes(b"fake mda data")
    
    return tmp_path


@pytest.fixture
def sample_plot_data() -> tuple[np.ndarray, np.ndarray]:
    """
    Create sample plotting data.
    
    Returns:
        tuple: (x_data, y_data) arrays for plotting
    """
    x = np.linspace(0, 10, 100)
    y = np.sin(x) * np.exp(-x/5)
    return x, y


@pytest.fixture
def mock_settings() -> MagicMock:
    """
    Create a mock settings object for testing.
    
    Returns:
        MagicMock: Mock settings with common configuration values
    """
    settings = MagicMock()
    settings.getKey.return_value = 800  # Default window height
    return settings


@pytest.fixture
def mock_file_dialog(monkeypatch: "MonkeyPatch") -> MagicMock:
    """
    Create a mock file dialog for testing.
    
    Args:
        monkeypatch: Pytest's monkeypatch fixture
        
    Returns:
        MagicMock: Mock file dialog
    """
    mock_dialog = MagicMock()
    mock_dialog.getExistingDirectory.return_value = "/tmp/test"
    return mock_dialog


# Pytest configuration
def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest for Qt testing."""
    # Add markers for Qt tests
    config.addinivalue_line(
        "markers", "qt: mark test as requiring Qt environment"
    )
    config.addinivalue_line(
        "markers", "gui: mark test as GUI test requiring display"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Modify test collection to add markers."""
    for item in items:
        # Add qt marker to tests that import Qt modules
        if "PyQt6" in str(item.fspath) or "qt" in str(item.fspath).lower():
            item.add_marker(pytest.mark.qt)
        
        # Add gui marker to GUI-specific tests
        if "gui" in str(item.fspath).lower() or "gui" in item.name.lower():
            item.add_marker(pytest.mark.gui)


# Skip GUI tests if no display is available
def pytest_runtest_setup(item: pytest.Item) -> None:
    """Skip GUI tests if no display is available."""
    if item.get_closest_marker("gui"):
        # Check if we have a display
        import os
        if not os.environ.get("DISPLAY") and os.name != "nt":
            pytest.skip("GUI tests require a display")


# Cleanup after tests
@pytest.fixture(autouse=True)
def cleanup_after_test() -> None:
    """Clean up after each test."""
    yield
    # Force garbage collection to clean up Qt objects
    import gc
    gc.collect() 