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
* **Auto-Load Folders**: Automatically loads the first valid folder from recent folders list (can be disabled in the preferences).
* **Recent Folders**: Remembers recently opened folders for quick access.
* **Lazy Loading**: Efficient folder scanning with progress indicators for large datasets.
* **Curve Management**: Add, remove, and style multiple data curves.
* **Axis Selection**: Select X-axis (positioners), Y-axis (detectors), I0 normalization, and curve unscaling using checkboxes. Axis selection is saved from one file to the next.
* **Curve Unscaling**: Rescale curves to match the range of other Y curves for better comparison.
* **Data Analysis**: Basic statistics, cursor measurements, and curve fitting.
* **Metadata Search**: Searchable metadata to quickly locate specific parameters and settings.
* **Cross-Platform**: Runs on Linux, macOS and Windows.

## Quickstart

### Option 1: Download a standalone executable (no Python needed)

Download the executable for your platform from the
[GitHub Releases](https://github.com/BCDA-APS/mdaviz/releases) page and run it.
It is self-contained and needs no conda environment.

**At the APS**, use the executable on APSshare instead (`/APSshare/bin/mdaviz`);
the GitHub release build targets personal machines and does not run on APS
hosts. See the [Release Process](https://bcda-aps.github.io/mdaviz/release.html)
for why the two builds differ.

### Option 2: Install from PyPI (Recommended for users)

Mdaviz is available on PyPI. We recommend creating a dedicated environment:

```bash
# Create a simple conda environment
conda create -n mdaviz python=3.12
conda activate mdaviz
pip install PyQt6 Qt6

# Install mdaviz
pip install mdaviz
```

Once installed, you can run the application at any time using:
```bash
conda activate mdaviz
mdaviz
```
**Note**:
* PyQt6 and Qt6 are required dependencies that may need to be installed separately via pip as they are not available in conda-forge for all platforms.
* At the APS: PyQt6 requires to install the following library:
```bash
sudo yum install xcb-util-cursor
```


### Option 3: Development setup with conda environment

For development and contributing, it is strongly recommended to use the provided conda environment. This ensures all dependencies (including PyQt6) are available and compatible.

```bash
# Clone the repo first
git clone https://github.com/BCDA-APS/mdaviz.git
cd mdaviz

# Create and activate a conda environment
conda create -n mdaviz python=3.12
conda activate mdaviz

# Install in development mode, with the test and lint tooling
pip install -e ".[dev]"
```

This installs everything mdaviz needs, including PyQt6 and the developer
tools (pytest, pytest-qt, ruff, mypy, pre-commit). Note the `[dev]` extra: a
plain `pip install -e .` omits the tooling, and the test and pre-commit
commands below will not work.

Once installed, you can run the application at any time using:
```bash
cd mdaviz
conda activate mdaviz
mdaviz
```

Always activate the environment before running, testing, or using pre-commit hooks.


**Note**:
* PyQt6 and Qt6 are required dependencies that may need to be installed separately via pip as they are not available in conda-forge for all platforms.
* At the APS: PyQt6 requires to install the following library:
```bash
sudo yum install xcb-util-cursor
```


## Usage

### Basic Operation

1. **Load Data**: Click "Open" (folder icon) and select an MDA file.
2. **Select Axes**: Use the checkboxes in the data table to select:
   - **X**: Positioner for the x-axis (only one can be selected)
   - **Y**: Detectors for the y-axis (multiple can be selected)
   - **I0**: Normalization detector (only one can be selected)
   - **Un**: Unscale curves to match the range of other Y curves (requires Y selection on same row)
3. **Plot Data**: Data will automatically plot based on your selection mode

### Plotting Modes

- **Auto-add**: New curves are added to existing plots
- **Auto-replace**: New curves replace existing plots
- **Auto-off**: Manual plotting using buttons

### Plot Controls

- **Log Scale**: Use the "LogX" and "LogY" checkboxes to switch between linear and logarithmic scales.
- **Curve Styling**: Select different line styles and markers for the selected curve.
- **Data Manipulation**: Apply offset and scaling factors to individual curves.
- **Data Analysis**: Basic statistics, cursor measurements, and curve fitting.



## Development

### Logging and Debugging

**Default Behavior:**
By default, `mdaviz` logs at the WARNING level, showing only warnings, errors and critical messages (quiet mode).

**Command Line Options:**
You can control the logging level using the `--log` argument:

```bash
# Show only errors and critical messages
mdaviz --log error

# Show warnings, errors, critical messages and info (progress messages, file loading status, and important application events).
mdaviz --log info

# Show all messages including debug information
mdaviz --log debug
```
**Log Files:**
Log files are automatically created in `~/.mdaviz/logs/` with timestamps. Old log files (older than 1 day) are automatically cleaned up on startup.


### Testing

Run all tests:
```bash
pytest src/tests
```

Current test status: **317 tests — 270 passing, 47 skipped, ~48% coverage.**

The skipped tests are GUI tests blocked by
[issue #13](https://github.com/BCDA-APS/mdaviz/issues/13) (pytest-qt
compatibility with PyQt6), not failures. They do mean the widget layer is
less covered than the headline number suggests.

Live acquisition is not covered by the suite; it is verified by hand against
a test IOC writing MDA files.


### Code Quality

The project uses pre-commit hooks for code quality. Run them before committing:
```bash
pre-commit run --all-files
```

## Contributing

mdaviz has been maintained by a single developer committing directly to `main`;
there is no enforced branch or review process. Run `pre-commit run --all-files`
and `pytest src/tests` before committing.

New to the codebase? Start with the
[Architecture guide](https://bcda-aps.github.io/mdaviz/architecture.html).
Cutting a release is documented in the
[Release Process](https://bcda-aps.github.io/mdaviz/release.html).

For a complete installation guide, see [https://bcda-aps.github.io/mdaviz/](https://bcda-aps.github.io/mdaviz/).

## Acknowledgements

"This product includes software produced by UChicago Argonne, LLC
under Contract No. DE-AC02-06CH11357 with the Department of Energy."
