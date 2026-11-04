# mdaviz

Python Qt6 application to visualize mda data.

## Status Badges

CI/CD | Code Quality | Documentation | Package
--- | --- | --- | ---
[![CI](https://github.com/BCDA-APS/mdaviz/workflows/CI/badge.svg)](https://github.com/BCDA-APS/mdaviz/actions/workflows/ci.yml) | [![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff) | [![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-blue.svg)](https://bcda-aps.github.io/mdaviz/) | [![PyPI version](https://badge.fury.io/py/mdaviz.svg?cache=1)](https://badge.fury.io/py/mdaviz) [![GitHub release](https://img.shields.io/github/release/BCDA-APS/mdaviz.svg)](https://github.com/BCDA-APS/mdaviz/releases)

Coverage | License | Python | Pre-commit
--- | --- | --- | ---
[![codecov](https://codecov.io/gh/BCDA-APS/mdaviz/branch/main/graph/badge.svg)](https://codecov.io/gh/BCDA-APS/mdaviz) | [![License: ANL](https://img.shields.io/badge/License-ANL-brightgreen.svg)](LICENSE.txt) | [![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/) | [![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

## Features

* **Data Visualization**: Visualize MDA data with support for 1-D and 2D plots (mesh scans) with matplotlib integration.
* **Live Updates**: Plots refresh automatically while a scan is acquiring, marked by a red LIVE indicator. Newly created files appear in the folder table with no manual refresh.
* **Multi-Scan Overlay**: Ctrl/Cmd+click to overlay curves from several files on a single plot, including while one of them is still acquiring.
* **2D Visualization**: Heatmap or contour display, with selectable color palette, log scale, VMIN/VMAX limits, I0 normalization, and a slice selector for the outer positioner.
* **Curve Transformations**: Apply an offset, scaling factor, derivative, or unscaling to any individual curve.
* **Auto-Load Folders**: Automatically loads the first valid folder from recent folders list (can be disabled in the preferences).
* **Recent Folders**: Remembers recently opened folders for quick access.
* **Lazy Loading**: Efficient folder scanning with progress indicators for large datasets.
* **Curve Management**: Add, remove, and style multiple data curves.
* **Axis Selection**: Select X-axis (positioners), Y-axis (detectors), and I0 normalization using checkboxes. Axis selection is saved from one file to the next.
* **Data Analysis**: Basic statistics, cursor measurements, and curve fitting, with an independent fit per curve.
* **Metadata Search**: Searchable metadata to quickly locate specific parameters and settings.
* **Cross-Platform**: Runs on Linux, macOS and Windows.

## Installation

**Standalone executable.** Download for your platform from the
[Releases](https://github.com/BCDA-APS/mdaviz/releases) page and run it. It is
self-contained; no Python or conda environment needed.

At the APS, use `/APSshare/bin/mdaviz` instead. The GitHub release build targets
personal machines and does not run on APS hosts; the
[Release Process](https://bcda-aps.github.io/mdaviz/release.html) explains why the
two builds differ.

**From PyPI.**

```bash
conda create -n mdaviz python=3.12
conda activate mdaviz
pip install mdaviz
mdaviz
```

At the APS, PyQt6 additionally requires `sudo yum install xcb-util-cursor`.

**From source**, for development:

```bash
git clone https://github.com/BCDA-APS/mdaviz.git
cd mdaviz
conda create -n mdaviz python=3.12
conda activate mdaviz
pip install -e ".[dev]"
```

The `[dev]` extra brings in pytest, pytest-qt, ruff, mypy and pre-commit; a plain
`pip install -e .` omits them and the commands below will not work.

Full installation guide, including troubleshooting:
<https://bcda-aps.github.io/mdaviz/install.html>

## Usage

See the [User Guide](https://bcda-aps.github.io/mdaviz/user_guide.html) for opening
data, selecting axes, plotting modes, cursors, curve fitting, 2D maps, and logging.

## Development

Start with the [Architecture guide](https://bcda-aps.github.io/mdaviz/architecture.html):
module map, data flow, and the parts of the codebase that are easy to get wrong.

```bash
pytest src/tests
pre-commit run --all-files
```

Test suite status and coverage caveats are in that guide. Cutting a release is
documented in the [Release Process](https://bcda-aps.github.io/mdaviz/release.html).

## Contributing

mdaviz has been maintained by a single developer committing directly to `main`;
there is no enforced branch or review process. Run `pre-commit run --all-files`
and `pytest src/tests` before committing.

## Acknowledgements

"This product includes software produced by UChicago Argonne, LLC
under Contract No. DE-AC02-06CH11357 with the Department of Energy."
