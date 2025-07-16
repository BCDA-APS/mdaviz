"""
Define constants used throught the code.
"""

import pathlib
import warnings

# Suppress PyQt5 deprecation warnings for sipPyTypeDict
# These warnings come from PyQt5's internal implementation, not our code
warnings.filterwarnings(
    "ignore", category=DeprecationWarning, message=".*sipPyTypeDict.*"
)

__settings_orgName__ = "BCDA-APS"
__package_name__ = "mdaviz"

try:
    from setuptools_scm import get_version

    __version__ = get_version(root="../..", relative_to=__file__)
    del get_version
except (LookupError, ModuleNotFoundError):
    from importlib.metadata import version

    __version__ = version(__package_name__)
    del version

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
