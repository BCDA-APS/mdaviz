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
# Exclude any bundled lib that requires a GLIBC newer than the oldest supported
# target machine (ratchet: GLIBC 2.28). Those libs will come from the system.
# libgcc_s and libstdc++ are replaced with conda's portable versions instead
# of excluded, since they are compiler runtime libs not guaranteed on all systems.
import os
import re
import subprocess

TARGET_GLIBC = (2, 28)

def _max_glibc(path):
    try:
        out = subprocess.check_output(
            ['readelf', '-V', path], stderr=subprocess.DEVNULL
        ).decode()
        versions = re.findall(r'GLIBC_(\d+)\.(\d+)', out)
        return max(((int(a), int(b)) for a, b in versions), default=(0, 0))
    except Exception:
        return (0, 0)

_conda_lib = os.path.join(os.environ.get('CONDA_PREFIX', ''), 'lib')
_replacements = {}
for _lib in ('libgcc_s.so.1', 'libstdc++.so.6'):
    _path = os.path.join(_conda_lib, _lib)
    if os.path.exists(_path):
        _replacements[_lib] = _path

_filtered = []
for n, p, t in a.binaries:
    if n in _replacements:
        _filtered.append((n, _replacements[n], t))
    elif _max_glibc(p) <= TARGET_GLIBC:
        _filtered.append((n, p, t))
a.binaries = _filtered

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
