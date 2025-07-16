====================================
User Guide
====================================

.. from gemviz
    .. _fig.mdaviz_gui:

    .. figure:: _static/mdaviz_gui.png
        :alt: fig.mdaviz_gui
        :width: 80%

Getting Started
---------------

mdaviz is a Python Qt6 application for visualizing MDA (Measurement Data Acquisition) data with advanced curve fitting capabilities.

Installation
^^^^^^^^^^^

For installation instructions, see :ref:`install`.

Running the Application
^^^^^^^^^^^^^^^^^^^^^^

After installation, you can run mdaviz in several ways:

**From PyPI installation:**
.. code-block:: bash

    conda activate mdaviz
    mdaviz

**From source installation:**
.. code-block:: bash

    git clone https://github.com/BCDA-APS/mdaviz.git
    cd mdaviz
    pip install -e .[dev]
    python -m mdaviz.app

**With debug logging:**
.. code-block:: bash

    python -m mdaviz.app --log debug

Basic Usage
----------

Opening Data
^^^^^^^^^^^

1. **Auto-Load**: The application automatically loads the first valid folder from your recent folders list
2. **Manual Open**: Use the folder dropdown to select a different folder or click "Open..." to browse
3. **Recent Folders**: The dropdown shows your recently opened folders for quick access

Navigating Files
^^^^^^^^^^^^^^^

1. **File Selection**: Click on any MDA file in the folder view to load it
2. **Navigation**: Use the First/Previous/Next/Last buttons to navigate through files
3. **Refresh**: Click the refresh button to reload the current folder

Data Visualization
^^^^^^^^^^^^^^^^^

1. **Plot Mode**: Choose between Auto-replace, Auto-add, or Auto-off modes
2. **Data Selection**: Check/uncheck detectors and positioners to control what's plotted
3. **Interactive Plot**: Use matplotlib's interactive features for zooming, panning, and data exploration

Curve Fitting
^^^^^^^^^^^^

mdaviz provides advanced curve fitting capabilities with 7 mathematical models:

1. **Select Curve**: Choose the curve to fit from the dropdown
2. **Choose Model**: Select from Gaussian, Lorentzian, Linear, Exponential, Quadratic, Cubic, or Error Function
3. **Set Range** (optional): Use cursors to define a specific x-range for fitting
4. **Perform Fit**: Click "Fit" to analyze the data
5. **View Results**: Examine fit parameters, uncertainties, and quality metrics

**Available Models:**
- **Gaussian**: Peak analysis, spectroscopy data
- **Lorentzian**: Resonance peaks, spectral lines  
- **Linear**: Trend analysis, calibration curves
- **Exponential**: Decay processes, growth curves
- **Quadratic**: Curved trends, parabolic data
- **Cubic**: Complex curved trends
- **Error Function**: Step functions, cumulative distributions

Cursor Utilities
^^^^^^^^^^^^^^^

1. **Cursor 1**: Middle-click to set the first cursor position
2. **Cursor 2**: Right-click to set the second cursor position
3. **Range Selection**: Use cursors to define fitting ranges
4. **Data Analysis**: View mathematical information between cursor positions

Advanced Features
----------------

Lazy Loading
^^^^^^^^^^^

For large datasets, mdaviz uses lazy loading to improve performance:
- Progress indicators show scanning status
- Efficient folder scanning with configurable batch sizes
- Automatic handling of large directories

Data Caching
^^^^^^^^^^^

The application includes an LRU cache system for improved performance:
- Frequently accessed data is cached in memory
- Automatic cache management for large datasets
- Configurable cache size limits

Recent Folders
^^^^^^^^^^^^^

mdaviz remembers your recently opened folders:
- Quick access to frequently used directories
- Automatic folder list management
- Clear recent folders option

Troubleshooting
--------------

Common Issues
^^^^^^^^^^^^

**Application won't start:**
- Ensure PyQt6 is properly installed: `pip install PyQt6 Qt6`
- Check conda environment is activated: `conda activate mdaviz`
- Verify Python version (3.10+ required)

**No data displayed:**
- Check that the selected folder contains MDA files
- Verify file permissions
- Try refreshing the folder view

**Fitting fails:**
- Ensure sufficient data points (at least 3 per parameter)
- Try a different fit model
- Check for invalid data values

**Performance issues:**
- Large datasets may take time to load
- Use lazy loading for directories with many files
- Consider reducing cache size for memory-constrained systems

Command-line Options
-------------------

You can run mdaviz with command-line options:

.. code-block:: bash

    python -m mdaviz.app --log debug

Available options:
- `--log LEVEL`: Set logging level (debug, info, warning, error)

Testing & Development
---------------------

To run all tests:

.. code-block:: bash

    pytest src/tests

To run code quality checks:

.. code-block:: bash

    pre-commit run --all-files

Contributing
------------

- Fork the repository and create a branch for your feature or bugfix.
- Add or update tests for your changes.
- Run pre-commit and pytest to ensure all checks pass.
- Submit a pull request on GitHub.

For detailed contributing guidelines, see the project's GitHub repository.
