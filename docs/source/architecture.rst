.. _architecture:

Architecture
============

Orientation for developers working on mdaviz for the first time. It assumes
Python fluency but no prior knowledge of this codebase. Read this before
the :ref:`API reference <api>`, which is generated per-module and does not
explain how the pieces fit together.

The short version
-----------------

mdaviz is a PyQt6 desktop application, roughly 14,000 lines across 31 modules
in ``src/mdaviz/``. It reads EPICS synApps MDA files from a folder and plots
them with matplotlib. There is no server, no database, and no network access —
everything is local files and Qt widgets.

The design is Qt Model/View throughout. Widget layouts come from Qt Designer
``.ui`` files in ``src/mdaviz/resources/``, loaded at runtime with ``loadUi``.
If you are looking for where a button lives and cannot find it in Python, it
is in a ``.ui`` file.

Three objects carry most of the state:

``MDA_MVC`` (``mda_folder.py``)
    The central coordinator. Owns the current folder, the current selection,
    the live-update polling timer, and the wiring between every other widget.
    When you do not know where something happens, it probably happens here.

``CurveManager`` (``curve_manager.py``)
    The single source of truth for plotted curves. Holds curve data, per-curve
    styling, offsets, factors, derivatives, and unscaling. Emits signals that
    the chart view listens to. Plot state lives here, not in the chart.

``DataCache`` (``data_cache.py``)
    An LRU, memory-bounded cache of parsed MDA files, keyed by file path and
    validated against mtime. Holds ``CachedFileData`` records, so a file is
    parsed once even if you revisit it.

Module map
----------

**Entry point and shell**

``app.py``
    ``main()``: argument parsing (``--log``), logging setup, the
    ``sys.excepthook`` that writes unhandled tracebacks to the log, then
    ``gui()``.
``mainwindow.py``
    ``MainWindow``. Menus, folder selection, recent-folders list, preferences,
    window geometry, and kicking off folder scans. Owns the
    ``LazyFolderScanner``.
``preferences_dialog.py``, ``aboutdialog.py``, ``licensedialog.py``,
``opendialog.py``, ``popup.py``
    Small dialogs. Self-explanatory.

**Coordination**

``mda_folder.py``
    ``MDA_MVC``, the coordinator described above. The largest concentration of
    application logic. Its module docstring contains a flow chart worth reading
    alongside this page.
``mda_file.py``
    ``MDAFile`` (the tab widget holding one tab per open file) and
    ``TabManager`` (bookkeeping for which files are open).

**Reading files**

``synApps_mdalib/``
    The MDA format parser (``mda.py``, plus ``f_xdrlib.py``, a local stand-in
    for the ``xdrlib`` module removed from the Python standard library in 3.13).
    A copy of EPICS synApps ``mdaPythonUtils`` (version 2022.post9), kept in the
    repo instead of installed as a dependency. Written by Tim Mooney in this
    group, with later fixes by Pete Jemian. **Do not touch this directory.** It
    is excluded from ruff, mypy and coverage, and nothing works without it.
``lazy_folder_scanner.py``
    ``LazyFolderScanner`` and ``FolderScanWorker``. Scans a folder for ``.mda``
    files on a ``QThread``, emitting progress so the UI stays responsive on
    large folders. Supports progressive (partial) results and cancellation.
``data_cache.py``
    ``DataCache`` and ``CachedFileData``. LRU cache with a memory ceiling
    (uses ``psutil``).
``utils.py``
    File reading helpers, scan extraction, number formatting, and the
    selection-format converters described below.

**Table models and views**

``mda_folder_table_model.py`` / ``mda_folder_table_view.py``
    The folder listing: one row per file, sortable by scan number, name,
    dimension, date, and optionally positioners.
``mda_file_table_model.py`` / ``mda_file_table_view.py``
    The per-file field table with the X / Y / I0 checkboxes. This is where
    checkbox exclusivity rules and duplicate-selection prevention live.
``virtual_table_model.py``
    Row-virtualized model for very large folders.
``data_table_model.py`` / ``data_table_view.py`` /
``multidimensional_data_table_model.py`` / ``empty_table_model.py``
    The raw-data tab beneath the plot.

**Plotting**

``chartview.py``
    ``ChartView`` (1D) and ``ChartView2D`` (2D mesh scans), wrapping matplotlib
    canvases. The largest single file. Cursors, basic statistics, log scales,
    and the matplotlib toolbar live here.
``mda_file_viz.py``
    ``MDAFileVisualization``: the tab container around the charts, the curve
    and cursor panels, 2D controls (palette, VMIN/VMAX, X2 slice), and
    ``MetadataSearchDialog``.
``curve_manager.py``
    ``CurveManager``, described above.
``fit_manager.py`` / ``fit_models.py``
    Curve fitting via lmfit. Each curve can carry its own independent fit.

**Support**

``logger.py``
    ``get_logger(name)``, level control, rotating file handler writing to
    ``~/.mdaviz/logs/``.
``user_settings.py``
    ``ApplicationQSettings``: persisted preferences, recent folders, window
    geometry, splitter positions.
``lazy_loading_config.py``
    Thresholds and tuning for lazy scanning and caching.
``progress_dialog.py``
    Non-modal progress dialog used during folder scans.

How data flows
--------------

**Opening a folder**

.. code-block:: text

    MainWindow.doOpen / onFolderSelected
      └─> LazyFolderScanner (QThread)
            ├─ scan_progress ──> progress dialog
            └─ scan_complete ──> MainWindow._on_scan_complete
                                   └─> MDA_MVC.setup / updateFolderView
                                         └─> folder table model populated

**Selecting a file**

.. code-block:: text

    user clicks a row in the folder table
      └─> MDA_MVC.onFileSelected
            ├─> DataCache lookup (parse via synApps_mdalib on miss)
            ├─> MDAFile.addFileTab  ──> new tab, field table, metadata
            └─> MDA_MVC.doPlot
                  └─> CurveManager.addCurve
                        └─ curveAdded ──> ChartView redraws

**Changing a checkbox**

.. code-block:: text

    checkbox toggled in the field table
      └─> MDA_MVC.onCheckboxStateChanged
            └─> handlePlotBasedOnMode   (Auto-add / Auto-replace / Auto-off)
                  └─> doPlot ──> CurveManager ──> ChartView

**Live acquisition**

A ``QTimer`` in ``MDA_MVC`` polls the current file's mtime
(``_pollForChanges``). When the file grows, ``_doLiveUpdate`` re-reads it and
replaces only the active file's curve, leaving curves from other files intact.
The same poll checks the folder for newly created ``.mda`` files. The title bar
shows a red ``LIVE`` indicator while watching. 2D scans take a separate path
(``_check2DStructure``) because the inner scan structure does not exist until
the first outer scan point completes.

Concepts that will trip you up
------------------------------

**Two selection formats.** The same selection is represented two ways, and
``utils.mda2ftm`` / ``utils.ftm2mda`` convert between them:

- MVC format, used by ``MDA_MVC.selectionField()``:
  ``{'X': 1, 'Y': [2, 3], 'I0': 4}``
- Table-model format, used by the field table's checkboxes:
  ``{1: 'X', 2: 'Y', 3: 'Y', 4: 'I0'}``

Passing one where the other is expected fails quietly rather than loudly.

**curveID is positional, not label-based.** ``CurveManager.generateCurveID``
builds ``f"{file_path}_{row}"``, or ``f"{file_path}_{row}_x2_{x2_index}"`` for
a 2D slice. It deliberately excludes the label and the I0 state, so toggling
normalization updates a curve in place instead of creating a second one. Do not
key curve state on the display label.

**Original vs. transformed y data.** ``CurveManager`` stores ``original_y`` and
applies offset, factor, derivative, and unscaling on demand through
``getTransformedCurveXYData`` / ``applyTransformations``. Always read through
those accessors; reading the stored array directly gives you untransformed data.

**Sorted views need index mapping.** The folder table is sortable, so view
indices are proxy indices. Converting them to source indices incorrectly is a
recurring bug — it caused the file-selection bug fixed in 1.4.1.

**Incomplete scans.** A scan in progress, or aborted, has fewer acquired points
than its declared dimensions. Plotting code truncates to
``acquired_dimensions``. Code that assumes ``dimensions`` is what is on disk
will crash or plot a trailing ``(0, 0)`` placeholder point.

**Qt object lifetime.** Several fixed bugs came from widgets being recreated
while something still held a reference to the old instance. Two open issues in
:ref:`known_bugs` are suspected to have the same cause.

Where to start reading
----------------------

To understand the application, read in this order:

1. ``app.py`` — 120 lines, the whole startup path.
2. The module docstring at the top of ``mda_folder.py`` — flow chart.
3. ``curve_manager.py`` — small, self-contained, and central.
4. ``MDA_MVC.onFileSelected`` and ``MDA_MVC.doPlot`` in ``mda_folder.py`` —
   the main path through the app.

Avoid starting with ``chartview.py`` or ``mda_file_table_view.py``. They are
the two largest files and make much more sense once the flow above is clear.

Testing
-------

.. code-block:: bash

    pytest src/tests

The suite is 317 tests: 270 pass and 47 skip, at about 48% coverage. The
skips are GUI tests that cannot run in this environment — see
`issue #13 <https://github.com/BCDA-APS/mdaviz/issues/13>`_ (pytest-qt
compatibility with PyQt6). They are not failures, but they do mean the widget
layer is substantially less covered than the numbers suggest: the heavily
interactive modules (``mda_file_table_view``, ``mda_folder``, ``mda_file_viz``)
sit between 7% and 27%.

Live acquisition is not covered by the test suite. It is verified by hand
against a test IOC writing MDA files, which behaves the same as a real
beamline IOC from the application's point of view.

Test data lives in ``src/tests/data/``, with folders covering the awkward
cases: 2D scans, time scans, scans with no positioner, and deeply nested
subfolders.
