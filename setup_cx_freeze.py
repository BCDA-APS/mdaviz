#!/usr/bin/env python3
"""
cx_Freeze setup script for mdaviz executable compilation.

Usage:
    python setup_cx_freeze.py build
    python setup_cx_freeze.py bdist_msi  # Windows only
"""

from cx_Freeze import setup, Executable
import sys
from pathlib import Path

# Get project root
project_root = Path(__file__).parent

build_exe_options = {
    "packages": [
        "PyQt5",
        "matplotlib",
        "scipy",
        "numpy",
        "lmfit",
        "tiled",
        "yaml",
        "mdaviz",
        "mdaviz.mainwindow",
        "mdaviz.mda_folder",
        "mdaviz.chartview",
        "mdaviz.data_cache",
        "mdaviz.lazy_folder_scanner",
        "mdaviz.fit_manager",
        "mdaviz.fit_models",
        "mdaviz.user_settings",
        "mdaviz.utils",
        "mdaviz.synApps_mdalib",
    ],
    "excludes": [
        "tkinter",
        "unittest",
        "test",
        "distutils",
    ],
    "include_files": [
        (str(project_root / "src" / "mdaviz" / "resources"), "resources"),
        (str(project_root / "src" / "mdaviz" / "synApps_mdalib"), "synApps_mdalib"),
    ],
    "include_msvcr": True,  # Windows only
}

# Platform-specific base
base = None
if sys.platform == "win32":
    base = "Win32GUI"
elif sys.platform == "darwin":
    base = None  # Use default for macOS
else:
    base = None  # Use default for Linux

# Executable configuration
executables = [
    Executable(
        str(project_root / "src" / "mdaviz" / "app.py"),
        base=base,
        target_name="mdaviz",
        icon=str(project_root / "src" / "mdaviz" / "resources" / "viz.png")
        if (project_root / "src" / "mdaviz" / "resources" / "viz.png").exists()
        else None,
    )
]

setup(
    name="mdaviz",
    version="1.1.2",
    description="MDA Data Visualization Tool",
    author="Fanny Rodolakis, Pete Jemian, Rafael Vescovi, Eric Codrea",
    author_email="rodolakis@anl.gov",
    options={"build_exe": build_exe_options},
    executables=executables,
)
