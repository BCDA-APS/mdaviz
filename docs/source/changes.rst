.. _changes:

Changes
=======

Version 1.2.0 (Latest)
----------------------

- Add 2D data visualization functionality
- Update documentation


Version 1.1.2
-------------

**Major Features:**

- **PyQt6 Migration**: Complete migration from PyQt5 to PyQt6 for future compatibility
- **Python 3.13+ Support**: Ensured compatibility with Python 3.13 and future versions
- **Curve Unscaling**: New "Un" column for rescaling curves to match the range of other Y curves
- **Multiple Selection Support**: Enhanced table model to support multiple selections per row for data processing
- **Auto-Load Folders**: Toggle auto-load in preferences

**Technical Improvements:**

- **CI/CD Pipeline**: Comprehensive GitHub Actions workflows with cross-platform testing
- **Code Quality**: Pre-commit hooks, ruff linting, mypy type checking
- **Testing**: 244 tests passing with 47% coverage, automated testing on multiple Python versions

**Bug Fixes:**

- Fixed PyQt6 API compatibility issues
- Fixed time scan not displaying plot
- Fixed data table view shrinking vertically


Version 1.1.1
-------------

**Bug Fixes:**

- Fixed Qt flags conversion error in MDAFileTableModel by using proper Qt constants instead of integer values
- Fixed license dialog crashes the app


Version 1.1.0
-------------

**Features:**

- Implement lazy loading for improved performance
- Increase file loading limit to 10,000 files
- Add curve fitting functionality
- Add I0 normalization feature
- Add line style customization options
- Add Ctrl+F search functionality to metadata
- Add comprehensive test suite

**Bug Fixes:**

- Fixed main window layout expansion issues
- Fixed core dump when refresh button is triggered multiple times

Version 1.0.0
-------------

**Features:**

- Basic MDA data visualization
- Interactive plotting with matplotlib
- Folder navigation and file selection
- Basic mathematical analysis tools
- Remembers recently opened folders for quick access

**Initial Release:**

- Core MVC architecture
- Qt5-based user interface
- Basic data loading and display
- Cross-platform support
