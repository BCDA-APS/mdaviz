# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src/mdaviz/app.py'],
    pathex=[],
    binaries=[],
    datas=[('src/mdaviz/resources', 'mdaviz/resources')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
# Replace the system's libgcc_s.so.1 (which may require a newer GLIBC than
# the target machines have) with the conda env's portable version.
import os
_conda_libgcc = os.path.join(os.environ.get('CONDA_PREFIX', ''), 'lib', 'libgcc_s.so.1')
if os.path.exists(_conda_libgcc):
    a.binaries = [
        (n, _conda_libgcc, t) if n == 'libgcc_s.so.1' else (n, p, t)
        for n, p, t in a.binaries
    ]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='mdaviz',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
