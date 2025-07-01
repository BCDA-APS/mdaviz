# mdaviz

Python Qt5 application to visualize mda data.

GH tag | GH release | PyPI
--- | --- | ---
[![tag](https://img.shields.io/github/tag/BCDA-APS/mdaviz.svg)](https://github.com/BCDA-APS/mdaviz/tags) | [![release](https://img.shields.io/github/release/BCDA-APS/mdaviz.svg)](https://github.com/BCDA-APS/mdaviz/releases) | [![PyPi](https://img.shields.io/pypi/v/mdaviz.svg)](https://pypi.python.org/pypi/mdaviz)

Python version(s) | Unit Tests | Code Coverage | License
--- | --- | --- | ---
[![Python version](https://img.shields.io/pypi/pyversions/mdaviz.svg)](https://pypi.python.org/pypi/mdaviz) | [![Unit Tests](https://github.com/BCDA-APS/mdaviz/workflows/Unit%20Tests%20%26%20Code%20Coverage/badge.svg)](https://github.com/BCDA-APS/mdaviz/actions/workflows/unit_tests.yml) | [![Coverage Status](https://coveralls.io/repos/github/BCDA-APS/mdaviz/badge.svg?branch=main)](https://coveralls.io/github/BCDA-APS/mdaviz?branch=main) | [![license: ANL](https://img.shields.io/badge/license-ANL-brightgreen)](LICENSE.txt)

## Features

- **Auto-Load Folders**: The application automatically loads the first valid folder from your recent folders list when it starts, providing a seamless experience without requiring manual folder selection.
- **Lazy Loading**: Efficient folder scanning with progress indicators for large datasets.
- **Interactive Plotting**: Real-time data visualization with matplotlib integration.
- **Recent Folders**: Remembers your recently opened folders for quick access.
- **Configurable Settings**: User preferences are saved and restored between sessions.

## Auto-Load Feature

The auto-load feature automatically loads the first valid folder from your recent folders list when the application starts. This provides a better user experience by eliminating the need to manually select a folder each time you open the application.

### Controlling Auto-Load

You can control the auto-load behavior through the application menu:

- **File → Toggle Auto-Load**: Check/uncheck this menu item to enable or disable auto-loading
- The setting is automatically saved and will be remembered for future sessions
- When disabled, the application will start without loading any folder, requiring manual folder selection

### How It Works

1. When the application starts, it checks if auto-loading is enabled (default: enabled)
2. If enabled, it looks for the first folder in your recent folders list
3. If the folder exists and is valid, it automatically loads and scans that folder
4. If no valid folders are found, the application starts normally without loading any folder

## Quickstart

```bash
# Clone the repo
$ git clone https://github.com/BCDA-APS/mdaviz.git
$ cd mdaviz

# Install with development dependencies
$ pip install -e .[dev]

# Run the application
$ python -m mdaviz.app
```

## Testing

Run all tests:
```bash
pytest src/tests
```

## Pre-commit hooks

To ensure code quality, install and run pre-commit:
```bash
pre-commit install
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
