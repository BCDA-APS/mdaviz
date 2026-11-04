.. _release:

Release Process
===============

How a release of mdaviz is cut and deployed. There are two separate
executable builds with different audiences — see
:ref:`two_builds` below, because it is not obvious from the repository.

Versioning
----------

Versions come from git tags via ``setuptools_scm``; there is no version
string in ``pyproject.toml``. There is one hardcoded fallback, in
``src/mdaviz/_get_version()`` in ``src/mdaviz/__init__.py``, used when neither
``setuptools_scm`` nor package metadata is available — which is the case inside
a PyInstaller executable. **That fallback must be bumped by hand**, or the
standalone executables will report the previous version.

Steps
-----

**1. Check the tree is clean**

.. code-block:: bash

    conda activate mda12
    pre-commit run --all-files
    ./run_mypy.sh
    pytest src/tests

Commit anything outstanding before starting the release itself.


**2. Bump the version and changelog**

- Update the fallback version in ``src/mdaviz/__init__.py``.
- Add the new section at the top of ``docs/source/changes.rst``.

**3. Commit and tag**

.. code-block:: bash

    git add src/mdaviz/__init__.py docs/source/changes.rst
    git commit -m "Prepare release v1.4.2"
    git tag -a v1.4.2 -m "Release v1.4.2"
    git push origin main && git push origin v1.4.2

Pushing the tag triggers two workflows: ``pypi.yml`` publishes to PyPI, and
``build-executables.yml`` builds Windows, Linux, and macOS executables as
workflow artifacts.

**4. Create the GitHub release**

Automatic release creation is **disabled** — the ``create-release`` job at the
bottom of ``.github/workflows/build-executables.yml`` is commented out. Download
the three artifacts from the workflow run on the Actions page and attach them to
a manually created GitHub release.

**5. Publish the documentation**

``docs.yml`` builds on every push to main but only deploys on demand. Trigger it
manually from the Actions page with the ``deploy`` input set to true.

**6. Build and deploy the APS executable**

Prerequisites, all of which the spec file depends on silently:

- A **conda** environment containing mdaviz's dependencies and PyInstaller
  (``pip install -e ".[dev,build]"``). A plain virtualenv will not do; the spec
  needs conda-forge's ``libgcc_s.so.1`` and ``libstdc++.so.6``.
- That environment **activated**, so ``CONDA_PREFIX`` points at it.
- ``readelf`` on the PATH (the ``binutils`` package).
- A Linux host. Build-host GLIBC may be newer than the target; the spec filters
  for that.

.. code-block:: bash

    cd workspace/mdaviz
    git pull
    conda activate mda12          # or your own build environment
    rm -rf build/ dist/
    python -m PyInstaller mdaviz.spec
    ./dist/mdaviz                 # smoke-test it before deploying

Then copy it to APSshare as epicsadm.

.. important::

   Use ``python -m PyInstaller``, not bare ``pyinstaller``. Activating the conda
   environment fixes ``python`` but not necessarily ``pyinstaller``: if a
   ``pip install --user`` copy exists in ``~/.local/bin``, and ``~/.local/bin``
   precedes the environment's ``bin`` on your PATH, the bare command silently
   runs the wrong PyInstaller from the wrong interpreter. Going through
   ``python -m`` cannot be shadowed by PATH.

   The two prerequisites above fail the same quiet way. If the environment is not
   activated, ``CONDA_PREFIX`` is wrong, the ``libgcc_s``/``libstdc++``
   substitution in ``mdaviz.spec`` finds nothing and is skipped. If ``readelf``
   is missing, the GLIBC check returns ``(0, 0)`` for every library and excludes
   none of them. Both produce a build that completes without error and then fails
   to start on older APS machines. Always smoke-test on an older host, not just
   on the build machine.

.. _two_builds:

Why there are two executable builds
-----------------------------------

This is the part that is easy to get wrong.

**CI executables** (``build-executables.yml``) are for users installing mdaviz
on a personal computer. Each build job runs:

.. code-block:: bash

    pyi-makespec --onefile --windowed --name mdaviz src/mdaviz/app.py \
        --add-data "src/mdaviz/resources:mdaviz/resources"
    pyinstaller mdaviz.spec

Note that ``pyi-makespec`` **regenerates** ``mdaviz.spec`` before use, so the
version committed to the repository is overwritten and has no effect in CI.
These builds do not work on APS machines.

**The APS executable** is built by hand with the committed ``mdaviz.spec``,
using the ``pyinstaller`` from the ``mda12`` conda environment. The committed
spec adds GLIBC compatibility handling that the generated spec lacks: it
substitutes conda's portable ``libgcc_s.so.1`` and ``libstdc++.so.6``, and drops
any bundled library requiring newer than GLIBC 2.28, so the result runs on the
older RHEL machines at the APS. This is the binary that goes to
``/APSshare/bin``.

So: changes to ``mdaviz.spec`` affect only the hand-built APS executable, never
the CI artifacts. Anyone trying to fix a packaging problem for APS users by
editing the workflow, or a problem for GitHub-release users by editing the spec
file, will be editing the wrong thing.

A possible improvement, not currently implemented: have CI check out and use the
committed spec rather than regenerating it, so one spec serves both. That would
need testing against both targets before being trusted.
