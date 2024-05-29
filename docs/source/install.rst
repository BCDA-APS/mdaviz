====================================
Installation Guide
====================================

The ``mdaviz`` package is available for installation by ``pip`` or from source.
Please report any issues you encounter (https://github.com/BCDA-APS/mdaviz/issues/new) or feature requests, too.

pip
---

Released versions of ``mdaviz`` are available on `PyPI
<https://pypi.python.org/pypi/mdaviz>`_.

If you have ``pip`` installed, then you can install::

    $ pip install mdaviz

source
------

The latest development versions of apstools can be downloaded from the
GitHub repository listed above::

   $ git clone https://github.com/BCDA-APS/mdaviz

To install from the source directory using ``pip`` in editable mode::

    $ cd mdaviz
    $ python -m pip install -e .

Required Libraries
------------------

The repository's ``env.yml`` file lists the additional packages
required by ``mdaviz``.  Most packages are available as conda packages
from https://anaconda.org.  The others are available on
https://PyPI.python.org.

To Run This Program
===================

For ``pip`` installation, activate the conda environment and start the application::

   $ conda activate mdaviz
   $ mdaviz

For source installation, navigate to the mdaviz directory then use the same commands::

   $ cd mdaviz
   $ conda activate mdaviz
   $ mdaviz

You can also create an alias for convenience; e.g., in bash::

   $ alias start_mdaviz="conda activate mdaviz; mdaviz"
