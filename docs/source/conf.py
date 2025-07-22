# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

import pathlib
import sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[no-redef]

from importlib.metadata import version as get_version
from typing import List

sys.path.insert(0, str(pathlib.Path().absolute().parent.parent))
import mdaviz  # noqa

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

root_path = pathlib.Path(__file__).parent.parent.parent

with open(root_path / "pyproject.toml", "rb") as fp:
    toml = tomllib.load(fp)
metadata = toml["project"]

gh_org = "BCDA-APS"
project = metadata["name"]
copyright = toml["tool"]["copyright"]["copyright"]
author = "Fanny Rodolakis, Pete Jemian"
description = metadata["description"]
rst_prolog = f".. |author| replace:: {author}"
github_url = f"https://github.com/{gh_org}/{project}"

# -- Special handling for version numbers ------------------------------------
# https://github.com/pypa/setuptools_scm#usage-from-sphinx

release: str = get_version(project)
doc_version: str = ".".join(release.split(".")[:2])

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = """
    sphinx.ext.autodoc
    sphinx.ext.autosummary
    sphinx.ext.coverage
    sphinx.ext.githubpages
    sphinx.ext.inheritance_diagram
    sphinx.ext.mathjax
    sphinx.ext.todo
    sphinx.ext.viewcode
    sphinx_design
""".split()
extensions.append("sphinx_tabs.tabs")  # this must be last

templates_path = ["_templates"]
exclude_patterns: List[str] = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_static_path = ["_static"]
html_theme = "pydata_sphinx_theme"
html_title = f"{project} {doc_version}"

# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#confval-autodoc_mock_imports
autodoc_mock_imports = """
    matplotlib
    mda
    numpy
    PyQt6
    yaml
    mdaviz.aboutdialog
    mdaviz.app
    mdaviz.chartview
    mdaviz.data_table_model
    mdaviz.data_table_view
    mdaviz.empty_table_model
    mdaviz.fit_manager
    mdaviz.fit_models
    mdaviz.licensedialog
    mdaviz.mainwindow
    mdaviz.mda_file
    mdaviz.mda_file_table_model
    mdaviz.mda_file_table_view
    mdaviz.mda_file_viz
    mdaviz.mda_folder
    mdaviz.mda_folder_table_model
    mdaviz.mda_folder_table_view
    mdaviz.opendialog
    mdaviz.popup
    mdaviz.progress_dialog
    mdaviz.user_settings
    mdaviz.utils
    mdaviz.virtual_table_model
""".split()

# Suppress warnings about mocked objects
suppress_warnings = ["autodoc.mocked_object"]
