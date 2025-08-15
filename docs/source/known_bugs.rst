Known Bugs
==========

This page documents known bugs that have been identified but not yet resolved.

Statistics Display Bug After Tab Switching
------------------------------------------

**Description**: After switching from the 2D tab to the 1D tab, basic statistics (min, max, mean, COM) may display "n/a" for curves that were previously working correctly.

**Steps to Reproduce**:

1. Load an MDA file with multiple curves
2. Select a curve in the 1D tab - statistics should display correctly
3. Switch to the 2D tab
4. Switch back to the 1D tab
5. Select a different curve - statistics now show "n/a"
6. The originally selected curve may also show "n/a" after switching curves

**Workaround**:

- Manipulate the curve in any way (change style, offset, factor, or apply a fit)
- This triggers a plot update that restores the statistics display

**Root Cause**: The issue appears to be related to object lifecycle management in the Qt widget hierarchy. After tab switching, the ``ChartView`` object and its ``CurveManager`` are being recreated or reset, causing the curve data to be lost from the manager while the plot objects themselves remain visible.

**Technical Details**:

- The ``CurveManager`` object gets replaced (different memory addresses) between ``onCurveSelected`` calls
- The ``plotObjects`` dictionary also becomes empty in the second call
- The entire ``ChartView`` instance appears to be recreated
- Curve manipulation triggers ``updatePlot()`` which re-synchronizes the state and restores statistics

**Status**: Known issue, low priority. The workaround is simple and the core functionality remains intact.

Plotting Area Vertical Expansion Bug
------------------------------------

**Description**: The plotting area sometimes expands vertically beyond reasonable bounds, taking up excessive screen space.

**Steps to Reproduce**:

1. Open mdaviz and load data
2. Plot many files one after another (typically 50+ files)
3. The plotting area may suddenly expand vertically at each new file, making the interface unusable

**Workaround**:

- Set a maximum height for the plotting area in the preferences (e.g., 500 pixels)
- This prevents the plotting area from expanding beyond the specified limit

**Root Cause**: This appears to be a Qt layout management issue where the plotting widget's size constraints are not properly maintained when opening many files in sequence.

**Technical Details**:

- Related to Qt's automatic layout management
- Triggered by opening many files one after another (typically 50+ files)
- The plotting widget loses its size constraints temporarily during file loading

**Status**: Known issue, low priority. The workaround is effective and prevents the problem.
