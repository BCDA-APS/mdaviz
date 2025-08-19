====================================
Installation Guide
====================================

The ``mdaviz`` package is available for installation by ``pip`` or from source.
Please [report](https://github.com/BCDA-APS/mdaviz/issues/new) any issues you encounter or feature requests, too.

Quick Install
-------------

Option 1: Install from PyPI (Recommended for users)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
For most users, the quickest way to get started is to install from `PyPI
<https://pypi.python.org/pypi/mdaviz>`_.

.. code-block:: bash

    # Create a simple conda environment
    conda create -n mdaviz python=3.12
    conda activate mdaviz
    pip install PyQt6 Qt6

    # Install mdaviz
    pip install mdaviz

**Note**:

- PyQt6 and Qt6 are required dependencies that may need to be installed separately.
- At the APS: PyQt6 requires to install the following library:

.. code-block:: bash

    sudo yum install xcb-util-cursor


Option 2: Install from source (Recommended for developers)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For development and contributing, it is strongly recommended to use the provided conda environment. This ensures all dependencies (including PyQt6) are available and compatible.

.. code-block:: bash

    # Clone the github repository
    git clone https://github.com/BCDA-APS/mdaviz.git
    cd mdaviz

    # Create and activate conda environment
    conda env create -f env.yml
    conda activate mdaviz
    pip install PyQt6 Qt6

    # Install in development mode
    pip install -e .

**Note**:

- PyQt6 and Qt6 are required dependencies that may need to be installed separately.
- At the APS: PyQt6 requires to install the following library:

.. code-block:: bash

    sudo yum install xcb-util-cursor


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
- PyYAML - YAML processing

**Development Dependencies:**

- pytest - Testing framework
- ruff - Code linting and formatting
- mypy - Type checking
- pre-commit - Git hooks

Running the Application
-----------------------

For ``pip`` installation, activate the conda environment and start the application:

.. code-block:: bash

    conda activate mdaviz
    mdaviz

For source installation, navigate to the mdaviz directory then use the same commands:

.. code-block:: bash

    # Navigate to the mdaviz directory
    cd mdaviz
    conda activate mdaviz
    mdaviz

You can also create an alias for convenience; e.g., in bash:

.. code-block:: bash

    alias start_mdaviz="conda activate mdaviz; mdaviz"


Platform-Specific Notes
-----------------------

Linux
^^^^^

- X11 libraries required for GUI
- Tested on RHEL 8

macOS
^^^^^

- Tested on macOS 12+

Windows
^^^^^^^

- Visual Studio Build Tools may be required for some dependencies
- Tested on Windows 10/11

Troubleshooting
---------------

Common Installation Issues (Windows)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

**Missing Dependencies:**

.. code-block:: bash

    # Install all dependencies explicitly
    conda install matplotlib scipy lmfit pyyaml
    pip install PyQt6 Qt6



Build Executables
-----------------

Clone the repository and install the dependencies:

.. code-block:: bash

    git clone https://github.com/BCDA-APS/mdaviz.git
    cd mdaviz

    conda env create -f env.yml
    conda activate mdaviz

    pip install -e ".[dev,build]"


To build the executables, install pyinstaller (available via pip) and use the following commands:

.. code-block:: bash

    # Install pyinstaller via conda
    conda install -c conda-forge pyinstaller
    # OR install pyinstaller via pip
    pip install pyinstaller

    # Build the spec file
    pyi-makespec --onefile --windowed --name mdaviz src/mdaviz/app.py --add-data "src/mdaviz/resources:mdaviz/resources"

    # Build the executable
    pyinstaller mdaviz.spec

You can start the application by running the executable:

.. code-block:: bash

    ./dist/mdaviz  # Linux & MacOS

    dist\mdaviz.exe  # Windows; you can also double click on the executable to start the application.

**Notes:**

- The executable can be run without activating the conda environment.
- On MacOS, the application can be **slow to start** when running from the executable, but once loaded, it is as fast as when running from the conda environment.
