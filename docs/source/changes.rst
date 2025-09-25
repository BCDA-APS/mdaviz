.. _changes:

Changes
=======

Version 1.2.5 (latest)
----------------------

**Bug Fixes**

- Fix detector selection mismatch in 2D panel

Version 1.2.4
-------------

**Bug Fixes**

- Fixed plot refresh issue where plots would not update when clicking refresh during real-time data acquisition.
- Added file selection preservation to maintain the currently selected file after folder refresh.

Version 1.2.3
-------------

**Bug Fixes**

- Fixed crash when changing X2 spinbox values after clearing the graph
- Fixed issue where X2 spinbox appeared unexpectedly for 1D scans after removing curves or switching between files
- Fixed issue where 2D tab disappeared after switching to a 1D file in auto-add mode

Version 1.2.2
-------------

**Bug Fixes**

- **Incomplete 2D Scan Handling**: Fixed crash and display issues when loading aborted 2D scans


Version 1.2.1
-------------

**Bug Fixes**

- **UI/UX Improvements**: Fixed dark mode contrast issues in data table view
- **Data Visualization**: Fixed X2 spinner control incorrectly appearing for 1D data files

**Infrastructure**

- **Build System**: Commented out automatic release creation and fixed PyInstaller commands to properly include UI resources with `--add-data` flag
- **Documentation**: Enhanced installation and build documentation


Version 1.2.0
-------------

**Major Features**

- **2D Mesh Scan Visualization**: Implemented 2D mesh scan support, enabling visualization of mesh scans in both 2D and 1D slice modes. 2D visualization is available in contour and heatmap modes, with multiple color palettes options.
- **Snap Cursor to Selected Curve**: Added configurable cursor snapping functionality. Users can now toggle between snapping cursors to the nearest data point or placing them at exact mouse click locations.

**Bug Fixes**

- **Tab Switching Responsiveness**: Fixed issue where curve remove button and plot controls became unresponsive after switching between 1D and 2D tabs.
- **2D Mode Auto-Replace Behavior**: Improved user experience in 2D mode by addressing confusing behavior with forceAutoReplaceMode. The interface now provides more intuitive and predictable interactions.

**Infrastructure Improvements**

- **Logging System**: Replaced print statements with proper logging infrastructure.
- **Documentation Updates**: Comprehensive documentation updates including user guides, API documentation, and improved examples to support new features and functionality.
- **Type Safety Enhancements**: Improved code quality with enhanced type annotations, stricter mypy configuration, and better error handling throughout the codebase.

**Technical Notes**

- Enhanced type checking with proper Optional handling
- Improved CI/CD pipeline with stricter quality checks
- Updated dependencies and build configuration


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
