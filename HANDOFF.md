# Handing mdaviz over

## Important files, in this order

1. **`docs/source/architecture.rst`** — the orientation document. Module map,
   data flow diagrams, and a section called "Concepts that will trip you up"
   that is worth reading twice.
2. **`docs/source/release.rst`** — how a release is cut, and why there are two
   different executable builds. Read it before touching anything to do with
   packaging.
3. **`docs/source/known_bugs.rst`** — two open bugs. Both low priority, both
   have workarounds, both are probably Qt object-lifetime issues.

Published at <https://bcda-aps.github.io/mdaviz/>.

## Getting running

```bash
git clone https://github.com/BCDA-APS/mdaviz.git
cd mdaviz
conda create -n mdaviz python=3.12
conda activate mdaviz
pip install -e ".[dev]"

pytest src/tests
mdaviz
```

## Three things that will bite you

**1. There are two different executable builds.** The ones CI produces on a tag
are for personal machines and do not run on APS hosts. The APS binary at
`/APSshare/bin/mdaviz` is built by hand with the committed `mdaviz.spec`, which
carries GLIBC compatibility handling that CI's generated spec does not have.
Changes to `mdaviz.spec` affect only the APS build; changes to the workflow
affect only the CI build. Editing the wrong one is the classic mistake here.

**2. The APS build fails silently.** If the conda environment is not activated,
or `readelf` is missing, the spec skips its library substitution without error
and produces a binary that starts fine on a modern machine and dies on an older
beamline workstation. Use `python -m PyInstaller`, not bare `pyinstaller` — a
stray `~/.local/bin/pyinstaller` will shadow the environment's. Always smoke-test
on an old host. `release.rst` spells all of this out.

**3. Live acquisition has no test coverage.** The suite is 317 tests: 270 pass,
47 skip, about 48% coverage. The skips are GUI tests blocked by
[issue #13](https://github.com/BCDA-APS/mdaviz/issues/13) (pytest-qt with
PyQt6), not failures — but it means the widget layer is far less covered than
that number suggests, and the live-update path is not covered at all. It is
verified by hand against a test IOC writing MDA files. A green run is not
evidence that live plotting works.

## How this project has been run

- **Reactively.** Work happens in response to beamline users reporting problems
  or asking for something. All the features that were meant to be implemented have been implemented at this point. There is no further roadmap.
- **Documentation deploys manually.** `docs.yml` builds on every push and pull
  request but only pushes `gh-pages` when you run it from the Actions page with
  the `deploy` input set to true. Merging does not update the site.
- **Releases are half automatic.** Pushing a `v*` tag publishes to PyPI and builds
  the three CI executables as artifacts. Creating the GitHub release and
  attaching those artifacts is manual — the `create-release` job is commented
  out (it was failing, never managed to fix it). The APS executable is a separate hand build.
- **The version fallback is hand-maintained.** Versions come from git tags via
  `setuptools_scm`, except inside a PyInstaller executable, which falls back to
  a hardcoded string in `src/mdaviz/__init__.py`. Bump it manually or the executables
  report the previous version.

## One open question

`src/mdaviz/synApps_mdalib/README.md` carries a caution copied from upstream:

> Don't use f_xdrlib. It doesn't work for large numbers of data points.

But `mda.py` imports it unconditionally:

```python
from mdaviz.synApps_mdalib import f_xdrlib as xdr  # Always use fallback
```

The comment directly above that line says the fallback exists for when `xdrlib`
is unavailable, which is true on Python 3.13 and later. The import does not
actually check: `f_xdrlib` is used on every Python version, including 3.12,
where the standard library's `xdrlib` is present and works.

So either that caution is stale, or long scans have been read through an
implementation its own author warned against. Nobody has investigated. Worth settling before someone reports wrong or truncated
data from a large scan.
