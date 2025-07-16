====================================
Installation Guide
====================================

The ``mdaviz`` package is available for installation by ``pip`` or from source.
Please [report](https://github.com/BCDA-APS/mdaviz/issues/new) any issues you encounter or feature requests, too.

Quick Install
------------

For most users, the quickest way to get started is:

.. code-block:: bash

    # Create conda environment
    conda env create -f env.yml
    conda activate mdaviz
    
    # Install PyQt6 (not available in conda-forge for all platforms)
    pip install PyQt6 Qt6
    
    # Install mdaviz
    pip install mdaviz

pip Installation
----------------

Released versions of ``mdaviz`` are available on `PyPI
<https://pypi.python.org/pypi/mdaviz>`_.

If you have ``pip`` installed, then you can install::

    $ pip install mdaviz

**Note**: PyQt6 and Qt6 are required dependencies that may need to be installed separately:

.. code-block:: bash

    pip install PyQt6 Qt6

Source Installation
------------------

The latest development versions can be downloaded from the
GitHub repository listed above::

   $ git clone https://github.com/BCDA-APS/mdaviz

To install from the source directory using ``pip`` in editable mode::

    $ cd mdaviz
    $ python -m pip install -e .

For development installation with all dependencies::

    $ cd mdaviz
    $ python -m pip install -e ".[dev]"

Required Libraries
------------------

The repository's ``env.yml`` file lists the additional packages
required by ``mdaviz``. Most packages are available as conda packages
from https://anaconda.org. The others are available on
https://PyPI.python.org.

**Core Dependencies:**
- PyQt6 (6.9.1+) - Qt6 bindings for Python
- Qt6 (6.9.0+) - Qt6 framework
- matplotlib - Plotting library
- scipy - Scientific computing
- lmfit - Curve fitting
- tiled - Data access
- PyYAML - YAML processing

**Development Dependencies:**
- pytest - Testing framework
- ruff - Code linting and formatting
- mypy - Type checking
- pre-commit - Git hooks

Running the Application
======================

For ``pip`` installation, activate the conda environment and start the application::

   $ conda activate mdaviz
   $ mdaviz

For source installation, navigate to the mdaviz directory then use the same commands::

   $ cd mdaviz
   $ conda activate mdaviz
   $ mdaviz

You can also create an alias for convenience; e.g., in bash::

   $ alias start_mdaviz="conda activate mdaviz; mdaviz"

Command-line Options
-------------------

The application supports several command-line options::

   $ mdaviz --log debug    # Enable debug logging
   $ mdaviz --help         # Show help (future enhancement)

Platform-Specific Notes
=======================

Linux
-----

- Most dependencies available via conda-forge
- PyQt6 may need to be installed via pip
- X11 libraries required for GUI

macOS
-----

- Qt6 and PyQt6 available via conda-forge or pip
- May need to handle code signing for distribution
- Tested on macOS 12+

Windows
-------

- Visual Studio Build Tools may be required for some dependencies
- PyQt6 and Qt6 available via pip
- Tested on Windows 10/11

Troubleshooting
==============

Common Installation Issues
-------------------------

**PyQt6 Import Error:**
.. code-block:: bash

    # Ensure PyQt6 is installed
    pip install PyQt6 Qt6
    
    # Verify installation
    python -c "import PyQt6; print('PyQt6 installed successfully')"

**Conda Environment Issues:**
.. code-block:: bash

    # Recreate environment if needed
    conda env remove -n mdaviz
    conda env create -f env.yml
    conda activate mdaviz
    pip install PyQt6 Qt6

**Permission Errors:**
.. code-block:: bash

    # Use user installation if system-wide fails
    pip install --user mdaviz
    pip install --user PyQt6 Qt6

**Missing Dependencies:**
.. code-block:: bash

    # Install all dependencies explicitly
    conda install matplotlib scipy lmfit tiled pyyaml
    pip install PyQt6 Qt6
