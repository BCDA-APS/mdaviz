.. _changes:

Changes
=======

Version 1.3.0 (latest)
----------------------

**Major Features**

- **2D selection persistence**: Remember 2D selection (X1, X2, Y, I0, plot type, color palette, log scale, x2 slice) across file switches; restore when switching back to 2D files.
- **Unscale feature**: Un column removed from table, moved to curve panel; apply to currently selected curve in curve pull-down menu.
- **Derivative support**: Add derivative option for curves in curve panel; apply to currently selected curve in curve pull-down menu.
- **Progress dialog**: Progress dialog during folder scan (throttled updates, non-modal).
- **Folder refresh cache**: Reuse cached file info for unchanged files (mtime) on refresh to speed up repeated scans.
- **Exception logging**: Custom excepthook logs unhandled exceptions to ``~/.mdaviz/logs/`` for debugging.
- **Active scans**: Plot only acquired points; omit the final (0,0) placeholder point.
- **Multi-fit support**: Each curve can have its own fit; the fit panel shows the result for the curve currently selected in the pull down menu.

**Minor Features**

- Preserve visualization tab (1D/2D) when switching files.
- Show cursor info panel in 2D tab.
- Add horizontal splitter between graph and curve/cursor panel (collapsible).
- Fit improvements: display uncertainty and FWHM when available; smooth x array for fit plotting.
- Fit models: add topHat model; negative Gaussian/Lorentzian.
- Curve panel: select last plotted curve on add; restore curve selection after replace and when I0 toggled.
- Reset log scale when graph is cleared.
- Snap-to-curve uses normalized nearest-point.

**Bug Fixes**

- **Crash guards**: Guard ``addCurve`` when ``len(ds) < 2``; guard ``removeAllLayoutWidgets`` when layout item has no widget (spacer); defensive null checks for ``getCurveData()``, plot widgets, and 2D data validation; default X when missing in ``data2Plot``; skip None y_data; validate 2D plot data shape/empty in ``ChartView2D.plot2D``.
- **Excepthook**: Wrap handler flush in try/except so bad logger cannot crash excepthook; ensure ``_folderList`` is never a string in main window (avoids ``insert`` on string).
- **Lazy scan**: Throttle scan progress to every 100 files (avoid RecursionError); clear ``_scanning`` only when scan thread has finished; wait for previous scan thread before starting new one; timeout and error on duplicate refresh.
- **Plot data**: Truncate 1D/2D plot data to ``acquiredDimensions`` for incomplete scans; early return when no acquired points; fix zero-size array crashes; bounds checking for X/I0 slicing.
- **2D UI**: Fix Ydet control panel visibility when switching 2D files; fix 2D control panel sometimes missing (defer retry with QTimer); avoid Ydet flicker; guard 2D selection restore from duplicate plots; fix invalid plot type when combo not yet populated.
- **Curves**: Reset persistent curve props on detector uncheck; refresh unscale when adding/removing det(s) or normalizing; fix I0 checkbox uncheck to use current file model; fix curve combobox selection after replace and I0 toggle.
- **2D plot**: Fix heatmap/contour orientation and log scale handling; fix ``first_det`` for 2D data;
- **Other**: Fix window geometry save/restore for multi-monitor; progress dialog non-modal (fix modalSession warning); ``displayData()`` tabledata optional; fix data truncation and unscaling (constant reference, bounds); duplicate selection prevention (X/Y checkboxes); fix ``has_curve`` boolean in showAnalysisControls; fix progress dialog rendering at 100% (hide bar on completion).

**Refactoring / Code Quality**

- Main window: extract preferences dialog; extract ``doOpen`` into helpers; reorganize sections; center window.
- ``mda_file_viz``: refactor mode control and tab widget; rename 2D control setup methods; simplify ``onPlotButtonClicked``.
- Curve manager: move to ``curve_manager.py``; use curveID for persistent properties; store ``original_y`` and add transformations helper; ``getTransformedCurveXYData``.
- ChartView: use CurveManager transformations; docstrings and section headers.
- ``mda_file_table_model``: duplicate selection fix; docstrings; setData/data order; defensive None checks.
- ``mda_folder``: clean up; ``doPlot2D`` public; remove dead code; null checks for selection.
- Utils: ``get_scan`` reuses ``get_det``; remove code duplication.
- Logging consolidated into ``logger.py``; remove ``logging_config.py`` and unused methods (fit visibility, toggle_auto_load, fit data tab, etc.).

**Testing**

- Tests for crash guards: ``addCurve`` len(ds)<2, ``removeAllLayoutWidgets`` spacer, ``ChartView2D.plot2D`` invalid data.
- Tests for DataTableModel, EmptyTableModel, PreferencesDialog (coverage).
- Fix mypy in tests (conftest qapp, qtbot type, patch mocks).
- Tests for duplicate selection prevention, transformation functionality, log scale reset.


Version 1.2.5
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
