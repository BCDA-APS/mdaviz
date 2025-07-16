# mdaviz Migration Plan: PyQt5 → PyQt6, Python 3.13+, and Dependency Updates

## Executive Summary

This document outlines the comprehensive migration strategy for mdaviz to:
1. **Migrate from PyQt5 to PyQt6** (PyQt5 is deprecated)
2. **Ensure Python 3.13+ compatibility** (xdrlib deprecation)
3. **Update dependencies to latest stable versions**

## Current State Analysis

### PyQt5 Usage Inventory

**Core PyQt5 Modules Used:**
- `PyQt5.QtCore` - Signals, slots, threading, timers
- `PyQt5.QtWidgets` - UI components, dialogs, layouts
- `PyQt5.QtGui` - Fonts, colors, key sequences
- `PyQt5.uic` - UI file loading

**Files with PyQt5 Dependencies (25 files):**
```
src/mdaviz/
├── __init__.py (warning filter)
├── app.py (QApplication)
├── mainwindow.py (QMainWindow, QWidget)
├── chartview.py (QWidget, QVBoxLayout, QTimer)
├── mda_folder.py (QWidget, pyqtSignal)
├── mda_file.py (QWidget, QObject)
├── mda_file_viz.py (QWidget, QDialog)
├── mda_file_table_model.py (QAbstractTableModel)
├── mda_file_table_view.py (QWidget, QHeaderView)
├── mda_folder_table_model.py (QAbstractTableModel)
├── mda_folder_table_view.py (QWidget, QStyledItemDelegate)
├── data_table_model.py (QAbstractTableModel)
├── data_table_view.py (QWidget, QHeaderView)
├── empty_table_model.py (QAbstractTableModel)
├── virtual_table_model.py (QAbstractTableModel)
├── aboutdialog.py (QDialog)
├── licensedialog.py (QDialog)
├── popup.py (QDialog)
├── progress_dialog.py (QWidget, QProgressDialog)
├── opendialog.py (QFileDialog)
├── user_settings.py (QSettings, QDesktopWidget)
├── utils.py (uic.loadUi)
├── data_cache.py (QObject, pyqtSignal)
├── lazy_folder_scanner.py (QObject, QThread, pyqtSignal)
├── lazy_loading_config.py (QObject, pyqtSignal)
└── fit_manager.py (QObject, pyqtSignal)

src/tests/
├── test_app.py (Qt imports)
├── test_aboutdialog.py (QtWidgets)
├── test_lazy_loading.py (QtCore)
└── test_mainwindow_resizing.py (QtWidgets)
```

### Current Dependencies

```toml
dependencies = [
  "matplotlib",
  "PyQt5",           # ← DEPRECATED
  "PyYAML",
  "tiled",
  "scipy>=1.9.0",
  "lmfit>=1.2.0",
  "psutil>=5.8.0",
]

requires-python = ">=3.10"  # ← Should support 3.13+
```

## Migration Strategy

### Phase 1: PyQt5 → PyQt6 Migration

#### 1.1 Dependency Updates

**Update `pyproject.toml`:**
```toml
dependencies = [
  "matplotlib",
  "PyQt6",           # ← Updated
  "PyYAML",
  "tiled",
  "scipy>=1.9.0",
  "lmfit>=1.2.0",
  "psutil>=5.8.0",
]

[project.optional-dependencies]
dev = [
  "pytest>=7.0",
  "pytest-cov>=4.0",
  "ruff>=0.1.0",
  "mypy>=1.0",
  "pre-commit>=3.0",
  "types-PyYAML",
  "pytest-qt>=4.2.0",  # ← Supports PyQt6
]
```

**Update `env.yml`:**
```yaml
dependencies:
  - libopenblas
  - matplotlib
  - pyqt =6          # ← Updated
  - pyqtgraph
  - qt =6            # ← Updated
  - tiled
  - scipy
  - lmfit
  - pyyaml
```

#### 1.2 Import Statement Updates

**Systematic replacement pattern:**
```python
# Before (PyQt5)
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QWidget, QDialog
from PyQt5.QtGui import QFont, QKeySequence
from PyQt5 import uic

# After (PyQt6)
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QWidget, QDialog
from PyQt6.QtGui import QFont, QKeySequence
from PyQt6 import uic
```

#### 1.3 API Changes to Address

**Key PyQt6 Breaking Changes:**

1. **Signal/Slot Syntax:**
   ```python
   # PyQt5 (still works in PyQt6)
   self.signal.connect(self.slot)
   
   # PyQt6 (new style, optional)
   self.signal.connect(self.slot)
   ```

2. **QDesktopWidget Deprecation:**
   ```python
   # Before (PyQt5)
   from PyQt5.QtWidgets import QDesktopWidget
   screen = QDesktopWidget().screenGeometry()
   
   # After (PyQt6)
   from PyQt6.QtWidgets import QApplication
   screen = QApplication.primaryScreen().geometry()
   ```

3. **QVariant Changes:**
   ```python
   # Before (PyQt5)
   from PyQt5.QtCore import QVariant
   return QVariant(value)
   
   # After (PyQt6)
   # QVariant is no longer needed for most cases
   return value
   ```

4. **Matplotlib Backend:**
   ```python
   # Before (PyQt5)
   from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
   from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
   
   # After (PyQt6)
   from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
   from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
   ```

#### 1.4 Migration Script

Create a migration script to automate import updates:

```python
#!/usr/bin/env python3
"""
Migration script: PyQt5 → PyQt6
"""

import re
import os
from pathlib import Path

def update_imports(file_path: Path) -> bool:
    """Update PyQt5 imports to PyQt6 in a file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Track if changes were made
    original_content = content
    
    # Update import statements
    content = re.sub(r'from PyQt5\.', 'from PyQt6.', content)
    content = re.sub(r'import PyQt5', 'import PyQt6', content)
    
    # Update matplotlib backend imports
    content = re.sub(
        r'from matplotlib\.backends\.backend_qt5agg',
        'from matplotlib.backends.backend_qtagg',
        content
    )
    
    # Update QDesktopWidget usage
    content = re.sub(
        r'QDesktopWidget\(\)\.screenGeometry\(\)',
        'QApplication.primaryScreen().geometry()',
        content
    )
    
    # Write back if changes were made
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        return True
    
    return False

def migrate_pyqt5_to_pyqt6():
    """Migrate all Python files from PyQt5 to PyQt6."""
    src_dir = Path("src")
    migrated_files = []
    
    for py_file in src_dir.rglob("*.py"):
        if update_imports(py_file):
            migrated_files.append(py_file)
            print(f"Migrated: {py_file}")
    
    print(f"\nTotal files migrated: {len(migrated_files)}")
    return migrated_files

if __name__ == "__main__":
    migrate_pyqt5_to_pyqt6()
```

### Phase 2: Python 3.13+ Compatibility

#### 2.1 xdrlib Replacement Strategy

**Current Status:** ✅ **Already Implemented**
- Fallback `f_xdrlib.py` module exists
- Graceful degradation when `xdrlib` is unavailable

**Future Enhancements:**
```python
# Option 1: Use struct module directly
import struct

def pack_uint(value: int) -> bytes:
    return struct.pack(">I", value)

def unpack_uint(data: bytes) -> int:
    return struct.unpack(">I", data)[0]

# Option 2: Use third-party XDR library
try:
    import xdrlib
except ImportError:
    # Use our fallback implementation
    from . import f_xdrlib as xdrlib
```

#### 2.2 Python Version Support Update

**Update `pyproject.toml`:**
```toml
requires-python = ">=3.10,<3.14"  # Support 3.10-3.13

classifiers = [
    # ... existing classifiers ...
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",  # ← Added
]
```

#### 2.3 Type Annotation Updates

**Update for Python 3.13 compatibility:**
```python
# Before (Python 3.10+)
from typing import List, Dict, Optional

# After (Python 3.13+)
# Use built-in types where possible
list[str]  # instead of List[str]
dict[str, Any]  # instead of Dict[str, Any]
```

### Phase 3: Dependency Updates

#### 3.1 Core Dependencies

**Recommended versions:**
```toml
dependencies = [
  "matplotlib>=3.8.0",    # ← Updated
  "PyQt6>=6.6.0",         # ← Updated
  "PyYAML>=6.0.1",        # ← Updated
  "tiled>=0.1.0a80",      # ← Updated
  "scipy>=1.12.0",        # ← Updated
  "lmfit>=1.3.0",         # ← Updated
  "psutil>=5.9.0",        # ← Updated
]
```

#### 3.2 Development Dependencies

**Updated dev dependencies:**
```toml
[project.optional-dependencies]
dev = [
  "pytest>=8.0.0",        # ← Updated
  "pytest-cov>=5.0.0",    # ← Updated
  "ruff>=0.3.0",          # ← Updated
  "mypy>=1.8.0",          # ← Updated
  "pre-commit>=4.0.0",    # ← Updated
  "types-PyYAML",         # ← Keep current
  "pytest-qt>=4.5.0",     # ← Updated
]
```

#### 3.3 Build Dependencies

**Updated build dependencies:**
```toml
build = [
  "pyinstaller>=6.5.0",   # ← Updated
  "cx_Freeze>=6.15.0",    # ← Keep current
  "nuitka>=1.9.0",        # ← Updated
]
```

## Implementation Timeline

### Week 1-2: Preparation and Testing
1. **Create migration branch:** `migration-pyqt6-python313`
2. **Set up test environment** with PyQt6 and Python 3.13
3. **Run comprehensive tests** to establish baseline
4. **Create migration scripts** for automated updates

### Week 3-4: PyQt5 → PyQt6 Migration
1. **Update dependencies** in `pyproject.toml` and `env.yml`
2. **Run migration script** to update imports
3. **Manual fixes** for API changes (QDesktopWidget, QVariant, etc.)
4. **Update matplotlib backend** imports
5. **Test GUI functionality** thoroughly

### Week 5-6: Python 3.13 Compatibility
1. **Test with Python 3.13** (when available)
2. **Verify xdrlib fallback** works correctly
3. **Update type annotations** for modern Python
4. **Update CI/CD** to test Python 3.13

### Week 7-8: Dependency Updates and Testing
1. **Update all dependencies** to latest stable versions
2. **Comprehensive testing** across all Python versions
3. **Performance testing** to ensure no regressions
4. **Documentation updates**

### Week 9-10: Final Testing and Deployment
1. **Integration testing** with real MDA files
2. **User acceptance testing**
3. **Performance benchmarking**
4. **Documentation finalization**
5. **Release preparation**

## Testing Strategy

### Automated Testing
```bash
# Test matrix
Python versions: 3.10, 3.11, 3.12, 3.13 (when available)
Qt versions: PyQt6 6.6+
Platforms: Linux, macOS, Windows

# Test commands
pytest src/tests -v --cov=src/mdaviz
pre-commit run --all-files
mypy src/mdaviz
```

### Manual Testing Checklist
- [ ] Application starts without errors
- [ ] All GUI dialogs work correctly
- [ ] File loading and visualization
- [ ] Plotting functionality (both backends)
- [ ] Curve fitting
- [ ] Settings persistence
- [ ] Large file handling
- [ ] Memory usage monitoring

### Performance Testing
- [ ] Startup time comparison
- [ ] Memory usage comparison
- [ ] Large file loading performance
- [ ] UI responsiveness

## Risk Assessment and Mitigation

### High Risk Items
1. **PyQt6 API Changes**
   - **Risk:** Breaking changes in signal/slot system
   - **Mitigation:** Comprehensive testing, gradual migration

2. **Matplotlib Backend Compatibility**
   - **Risk:** Plotting functionality may break
   - **Mitigation:** Test both plotting backends thoroughly

3. **Python 3.13 Compatibility**
   - **Risk:** xdrlib removal may cause issues
   - **Mitigation:** Fallback implementation already in place

### Medium Risk Items
1. **Dependency Conflicts**
   - **Risk:** New versions may conflict
   - **Mitigation:** Test in isolated environment first

2. **Performance Regression**
   - **Risk:** PyQt6 may be slower than PyQt5
   - **Mitigation:** Benchmark before and after

### Low Risk Items
1. **Import Statement Updates**
   - **Risk:** Automated script may miss edge cases
   - **Mitigation:** Manual review of all changes

## Rollback Plan

### Emergency Rollback
If critical issues are discovered:

1. **Revert to PyQt5 branch:**
   ```bash
   git checkout main
   git revert <migration-commit>
   ```

2. **Restore original dependencies:**
   ```bash
   # Revert pyproject.toml and env.yml
   git checkout HEAD~1 -- pyproject.toml env.yml
   ```

3. **Reinstall original environment:**
   ```bash
   conda env remove -n mdaviz
   conda env create -f env.yml
   ```

### Gradual Rollback
If only specific components have issues:

1. **Create hybrid approach** with PyQt5 fallback
2. **Feature flags** to enable/disable PyQt6 features
3. **Conditional imports** based on availability

## Success Criteria

### Technical Success Criteria
- [ ] All tests pass with PyQt6
- [ ] All tests pass with Python 3.13
- [ ] No performance regression >5%
- [ ] All GUI functionality works correctly
- [ ] No new deprecation warnings

### User Success Criteria
- [ ] Application starts and runs normally
- [ ] All existing workflows continue to work
- [ ] No user-facing changes in functionality
- [ ] Performance is maintained or improved

### Development Success Criteria
- [ ] CI/CD pipeline updated and working
- [ ] Documentation updated
- [ ] Migration scripts documented
- [ ] Rollback procedures tested

## Post-Migration Tasks

### Immediate (Week 11)
1. **Update documentation** with new requirements
2. **Update CI/CD** configurations
3. **Release notes** preparation
4. **User communication** about changes

### Short-term (Month 3)
1. **Performance monitoring** in production
2. **User feedback** collection
3. **Bug fixes** for any issues discovered
4. **Documentation improvements**

### Long-term (Month 6)
1. **Evaluate PyQt6 benefits** (performance, features)
2. **Plan next major version** features
3. **Consider Qt6-specific features** (if beneficial)
4. **Community feedback** integration

## Conclusion

This migration plan provides a comprehensive roadmap for modernizing mdaviz while maintaining stability and user experience. The phased approach minimizes risk while ensuring all critical functionality is preserved.

The key success factors are:
1. **Thorough testing** at each phase
2. **Clear rollback procedures** for emergencies
3. **User communication** about changes
4. **Performance monitoring** throughout the process

By following this plan, mdaviz will be positioned for long-term sustainability with modern Python and Qt versions. 