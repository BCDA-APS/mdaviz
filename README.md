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

- **Auto-Load Folders**: The application automatically loads the first valid folder from your recent folders list when it starts, providing a seamless experience without requiring manual folder selection.
- **Lazy Loading**: Efficient folder scanning with progress indicators for large datasets.
- **Interactive Plotting**: Real-time data visualization with matplotlib integration.
- **Axis Selection**: Select X-axis (positioners), Y-axis (detectors), and I0 normalization using checkboxes.
- **Log Scale Support**: Toggle between linear and logarithmic scales for both X and Y axes.
- **Curve Management**: Add, remove, and style multiple data curves.
- **Data Analysis**: Basic statistics, cursor measurements, and curve fitting.
- **Recent Folders**: Remembers your recently opened folders for quick access.

## Quickstart

### Conda environment
It is strongly recommended to use the provided conda environment for development and running the application. This ensures all dependencies (including PyQt6) are available and compatible.

```bash
conda env create -f env.yml
conda activate mdaviz
pip install PyQt6 Qt6
```

Always activate the environment before running, testing, or using pre-commit hooks.

**Note**: PyQt6 and Qt6 are installed via pip as they are not available in conda-forge for all platforms.

### Install & run the application

Mdaviz is available on PyPI:
```bash
$ conda activate mdaviz
$ pip install mdaviz
```

Once installed, you can run the application at any time using:
```bash
$ conda activate mdaviz
$ mdaviz
```

### Run the application in developer mode

```bash
# Clone the repo
$ git clone https://github.com/BCDA-APS/mdaviz.git
$ cd mdaviz

# Install with development dependencies
$ conda activate mdaviz
$ pip install -e .

# Run the application
$ mdaviz
```

## Usage

### Basic Operation

1. **Load Data**: Select a folder containing MDA files
2. **Select Axes**: Use the checkboxes in the data table to select:
   - **X**: Positioner for the x-axis (only one can be selected)
   - **Y**: Detectors for the y-axis (multiple can be selected)
   - **I0**: Normalization detector (only one can be selected)
3. **Plot Data**: Data will automatically plot based on your selection mode

### Plot Controls

- **Log Scale**: Use the "LogX" and "LogY" checkboxes to switch between linear and logarithmic scales
- **Curve Styling**: Select different line styles and markers for your curves
- **Data Manipulation**: Apply offset and scaling factors to individual curves
- **Cursors**: Use mouse clicks to place measurement cursors on the plot

### Plotting Modes

- **Auto-add**: New curves are added to existing plots
- **Auto-replace**: New curves replace existing plots
- **Auto-off**: Manual plotting using buttons

## Development

### Testing

Run all tests:
```bash
pytest src/tests
```

### Code Quality

The project uses pre-commit hooks for code quality. Run them before committing:
```bash
pre-commit run --all-files
```

## Contributing

1. Fork and clone the repository.
2. Create a new branch for your feature or bugfix.
3. Make your changes and add tests.
4. Run pre-commit and pytest to ensure all checks pass.
5. Submit a pull request.

For a complete installation guide, see [https://bcda-aps.github.io/mdaviz/](https://bcda-aps.github.io/mdaviz/).

## Acknowledgements

"This product includes software produced by UChicago Argonne, LLC
under Contract No. DE-AC02-06CH11357 with the Department of Energy."
