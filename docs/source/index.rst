=======================
mdaviz: MDA Data Viewer
=======================

A Python Qt6 application for visualizing MDA (Multi-Dimensional Array) data.

Key Features
============

* **Data Visualization**: Visualize MDA data with support for 1-D and 2D plots (mesh scans) with matplotlib integration.
* **Live Updates**: Plots refresh automatically while a scan is acquiring, marked by a red LIVE indicator. Newly created files appear in the folder table with no manual refresh.
* **Multi-Scan Overlay**: Ctrl/Cmd+click to overlay curves from several files on a single plot, including while one of them is still acquiring.
* **2D Visualization**: Heatmap or contour display, with selectable color palette, log scale, VMIN/VMAX limits, I0 normalization, and a slice selector for the outer positioner.
* **Curve Transformations**: Apply an offset, scaling factor, derivative, or unscaling to any individual curve.
* **Auto-Load Folders**: Automatically loads the first valid folder from recent folders list (can be disabled in the preferences).
* **Recent Folders**: Remembers recently opened folders for quick access.
* **Lazy Loading**: Efficient folder scanning with progress indicators for large datasets.
* **Curve Management**: Add, remove, and style multiple data curves.
* **Axis Selection**: Select X-axis (positioners), Y-axis (detectors), and I0 normalization using checkboxes. Axis selection is saved from one file to the next.
* **Data Analysis**: Basic statistics, cursor measurements, and curve fitting, with an independent fit per curve.
* **Metadata Search**: Searchable metadata to quickly locate specific parameters and settings.
* **Cross-Platform**: Runs on Linux, macOS and Windows.

Documentation
=============

.. grid:: 3

    .. grid-item-card:: |material_summarize| User Guide
      :link: user_guide
      :link-type: doc

    .. grid-item-card:: |material_install| Installation
      :link: install
      :link-type: doc

    .. grid-item-card:: |material_api| API
      :link: api
      :link-type: doc

.. |material_summarize| raw:: html

   <span class="material-icons" style="font-size: 4em; vertical-align: middle;">summarize</span>

.. |material_install| raw:: html

   <span class="material-icons" style="font-size: 4em; vertical-align: middle;">install_desktop</span>

.. |material_api| raw:: html

   <span class="material-icons" style="font-size: 4em; vertical-align: middle;">api</span>




Screenshots
-----------

.. figure:: _static/mda1D.jpg
   :alt: fig.mda1D
   :width: 100%
   :align: center
   :figclass: align-center
   :figwidth: 100%

   Screenshot of the mdaviz GUI displaying sample 1D data with curve fitting.

.. figure:: _static/mda2D.jpg
   :alt: fig.mda2D
   :width: 100%
   :align: center
   :figclass: align-center
   :figwidth: 100%

   Screenshot of the mdaviz GUI displaying sample 2D data.

.. toctree::
   :maxdepth: 1
   :glob:
   :caption: Contents:
   :hidden:

   user_guide
   install
   architecture
   release
   known_bugs
   api
   changes
   license

About
=====

:home: https://bcda-aps.github.io/mdaviz/
:bug tracker: https://github.com/BCDA-APS/mdaviz/issues
:source: https://github.com/BCDA-APS/mdaviz
:license: :ref:`license`
:full version: |release|
:published: |today|
:revisions: :ref:`History of code changes <changes>`
:index: :ref:`genindex`
:module: :ref:`modindex`
:search: :ref:`search`

Acknowledgements
================

"This product includes software produced by UChicago Argonne, LLC
under Contract No. DE-AC02-06CH11357 with the Department of Energy."
