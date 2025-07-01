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

To install and run mdaviz:

.. code-block:: bash

    git clone https://github.com/BCDA-APS/mdaviz.git
    cd mdaviz
    pip install -e .[dev]
    python -m mdaviz.app

Command-line
------------

You can also run mdaviz with command-line options:

.. code-block:: bash

    python -m mdaviz.app --log debug

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

.. todo:
    Export
    ------

    * data
    * plot script (such as SVG)
    * plot image
