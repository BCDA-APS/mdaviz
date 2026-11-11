# Working on mdaviz

Notes for AI coding assistants. Humans: start with
`docs/source/architecture.rst` instead.

## Before changing code

Read `docs/source/architecture.rst`. It has the module map, the data flow, and
the five things that are easy to get wrong (two selection formats, positional
`curveID`, transformed vs. original y data, proxy index mapping on the sorted
folder table, incomplete scans). Most bugs in this project's history come from
those five.

## Environment

Use a conda environment with `pip install -e ".[dev]"`. PyQt6 is a declared
dependency; do not install it separately. There is no `Qt6` package.

```bash
pytest src/tests          # 270 pass, 47 skip
pre-commit run --all-files
./run_mypy.sh
```

## Rules

- **Do not touch `src/mdaviz/synApps_mdalib/`.** It is a copy of the EPICS
  synApps MDA parser, kept in the repo instead of installed as a dependency.
  Nothing works without it, and it is excluded from ruff, mypy and coverage.
  If it genuinely needs a change, that goes to its author in this group — not
  a local patch.
- **A green test run does not mean it works.** Live acquisition — the polling,
  the LIVE indicator, 2D structure detection — has no test coverage at all. It
  is verified by hand against a test IOC. The 47 skipped tests are GUI tests
  blocked by issue #13, so the widget layer is far less covered than 48%
  suggests.
- **Widget layouts live in `src/mdaviz/resources/*.ui`**, loaded at runtime. If
  you cannot find a button in Python, it is in a `.ui` file.
- **Verify before you write it down.** Documentation in this repo has asserted
  things that were not true — test counts, CI behavior, UI columns that had been
  removed. If you add a claim to a doc, check it against the code first.
- **Do not duplicate documentation.** Install instructions live in
  `docs/source/install.rst`, usage in `user_guide.rst`, testing and design in
  `architecture.rst`, releases in `release.rst`. The README is deliberately
  short because it is also the PyPI description. Duplicated text drifts.
