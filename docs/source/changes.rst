.. _changes:

Changes
=======

Version 1.1.2 (Latest)
----------------------

**Major Features:**
- **PyQt6 Migration**: Complete migration from PyQt5 to PyQt6 for future compatibility
- **Python 3.13+ Support**: Ensured compatibility with Python 3.13 and future versions
- **Advanced Curve Fitting**: Implemented 7 mathematical models (Gaussian, Lorentzian, Linear, Exponential, Quadratic, Cubic, Error Function)
- **Auto-Load Folders**: Application automatically loads the first valid folder from recent folders list
- **Lazy Loading**: Efficient folder scanning with progress indicators for large datasets
- **Recent Folders**: Remembers recently opened folders for quick access
- **Data Caching**: LRU cache system for improved performance with large datasets

**Technical Improvements:**
- **CI/CD Pipeline**: Comprehensive GitHub Actions workflows with cross-platform testing
- **Code Quality**: Pre-commit hooks, ruff linting, mypy type checking
- **Documentation**: Comprehensive Sphinx documentation with API reference
- **Testing**: 58 tests with 36% coverage, automated testing on multiple Python versions
- **Performance**: Optimized memory management and data loading

**Bug Fixes:**
- Fixed matplotlib artist removal crashes
- Improved folder view selection and auto-selection logic
- Enhanced error handling and user feedback
- Fixed PyQt6 API compatibility issues

**API Changes:**
- Updated all Qt constants to use enum-based syntax
- Moved QAction and QShortcut imports to QtGui
- Replaced QDesktopWidget with QApplication.primaryScreen()
- Updated QSettings constants to use enum-based format

Version 1.1.1
-------------

**Features:**
- Initial curve fitting functionality
- Improved folder navigation
- Enhanced data visualization

**Bug Fixes:**
- Fixed file loading issues
- Improved UI responsiveness
- Enhanced error handling

Version 1.1.0
-------------

**Features:**
- Basic MDA data visualization
- Interactive plotting with matplotlib
- Folder navigation and file selection
- Basic mathematical analysis tools

**Initial Release:**
- Core MVC architecture
- Qt5-based user interface
- Basic data loading and display
- Cross-platform support

Future Plans
-----------

**Planned Features:**
- Advanced statistical analysis tools
- Data export functionality
- Plugin system for extensibility
- Enhanced performance optimizations
- Additional fit models and analysis tools

**Technical Roadmap:**
- Improve test coverage to 80%+
- Enhanced GUI testing with pytest-qt
- Performance monitoring and optimization
- Advanced memory management
- Cross-platform executable builds
