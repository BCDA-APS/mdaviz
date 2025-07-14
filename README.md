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

## Quickstart

### Conda environment
It is strongly recommended to use the provided conda environment for development and running the application. This ensures all dependencies (including PyQt5) are available and compatible.

```bash
conda env create -f env.yml
conda activate mdaviz
```

Always activate the environment before running, testing, or using pre-commit hooks.

### Install & run the application

Mdaviz is available on PyPi:
```bash
$ conda activate mdaviz
$ pip install mdaviz
```
Once install, you can run the application at anytime using:
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

## Testing

Run all tests:
```bash
pytest src/tests
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
