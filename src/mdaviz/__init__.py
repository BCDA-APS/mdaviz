"""
Define constants used throught the code.
"""

import pathlib
import warnings

# Suppress PyQt6 deprecation warnings for sipPyTypeDict
# These warnings come from PyQt6's internal implementation, not our code
warnings.filterwarnings(
    "ignore", category=DeprecationWarning, message=".*sipPyTypeDict.*"
)

__settings_orgName__ = "BCDA-APS"
__package_name__ = "mdaviz"

def _get_version() -> str:
    """Get the package version with fallbacks for different environments."""
    # Try setuptools_scm first (for development)
    try:
        from setuptools_scm import get_version
        return get_version(root="../..", relative_to=__file__)
    except (LookupError, ModuleNotFoundError):
        pass
    
    # Try importlib.metadata (for installed packages)
    try:
        from importlib.metadata import version
        return version(__package_name__)
    except Exception:
        pass
    
    # Fallback for PyInstaller executables or when package metadata is not available
    # This version should match what's in pyproject.toml or be updated manually
    return "1.1.2"

__version__ = _get_version()

ROOT_DIR = pathlib.Path(__file__).parent
UI_DIR = ROOT_DIR / "resources"

APP_DESC = "Visualize mda files."
APP_TITLE = __package_name__
AUTHOR_LIST = [
    s.strip()
    for s in """
        Fanny Rodolakis
        Pete Jemian
        Rafael Vescovi
        Eric Codrea
    """.strip().splitlines()
]

COPYRIGHT_TEXT = "(c) 2023, UChicago Argonne, LLC, (see LICENSE file for details)"
DOCS_URL = "https://github.com/BCDA-APS/mdaviz/blob/main/README.md"
ISSUES_URL = "https://github.com/BCDA-APS/mdaviz/issues"
LICENSE_FILE = "LICENSE.txt"
