# GitHub Actions Workflows

What each workflow actually does. Verified against the workflow files at v1.4.2.

## `ci.yml` — CI

**Triggers**: push to `main` or `develop`, pull requests to `main` or `develop`, manual dispatch.

Three jobs:

- **`test`** (ubuntu-latest, Python 3.10 / 3.11 / 3.12 / 3.13) — ruff, mypy, Qt6 and X11
  system dependencies, PyQt6 installation check, compatibility and deprecation checks
  (including `xdrlib` usage), then `pytest` under `xvfb-run` with coverage, uploaded to
  Codecov.
- **`cross-platform`** (windows-latest and macos-latest, Python 3.11 / 3.12) — basic tests
  only. No GUI tests on these platforms.
- **`build`** (ubuntu-latest) — runs only on pushes to `main`, after the other two jobs
  pass. Builds the sdist and wheel and validates them. It does not publish.

## `docs.yml` — Publish Sphinx Docs to GitHub Pages

**Triggers**: push to `main`, any tag, pull requests to `main`, manual dispatch with a
`deploy` boolean input.

The docs are **built** on every trigger and uploaded as the `mdaviz-docs` artifact, but
the `gh-pages` branch is pushed **only when the manual `deploy` input is true**. Merging
to `main` does not update the published site — publishing is always a deliberate manual
run.

## `build-executables.yml` — Build Executables

**Triggers**: tags matching `v*`, manual dispatch.

Three jobs (windows-latest, ubuntu-latest, macos-latest), all on Python 3.11, each running
`pyi-makespec` followed by `pyinstaller`. These use **PyInstaller**, not cx_Freeze.

Two things that surprise people:

- `pyi-makespec` **regenerates** `mdaviz.spec`, so the spec file committed to the
  repository has no effect on these builds. The committed spec exists for the hand-built
  APS executable, which carries GLIBC compatibility handling the generated spec lacks.
  See the Release Process page in the docs.
- The `create-release` job at the bottom of the file is **commented out**. The workflow
  produces downloadable artifacts; it does not create a GitHub release. Attach the
  artifacts to a release by hand.

## `pypi.yml` — Publish to PyPI

**Triggers**: push to `main`, any tag.

Builds the sdist and wheel and runs `twine check` on every trigger, but publishes to PyPI
**only when the ref is a tag** (`startsWith(github.ref, 'refs/tags')`), authenticating with
the `PYPI_API_TOKEN` repository secret. Despite the workflow's name, there is no TestPyPI
step.

## `pre-commit.yml` — Pre-Commit Checks

**Triggers**: every push, on any branch. Not pull requests.

Runs `pre-commit/action` on Python 3.10.

## Test environment

The Linux test job sets:

- `QT_QPA_PLATFORM=offscreen`
- `QT_LOGGING_RULES="qt.qpa.*=false"`
- `DISPLAY=:99.0`
- `PYTEST_QT_API=pyqt6`

and runs pytest through `xvfb-run -a`. The cross-platform job sets `PYTEST_QT_API=pyqt6`
and relies on the native Qt installation.

## Running the same checks locally

```bash
pytest src/tests

ruff check src/
ruff format --check src/
mypy src/mdaviz --ignore-missing-imports

pre-commit run --all-files
```
