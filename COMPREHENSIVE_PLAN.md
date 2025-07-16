# mdaviz Comprehensive Development Plan

## Executive Summary

This document provides a comprehensive plan for the mdaviz project, covering environment setup, dependency management, testing, code analysis, bug identification, improvements, and executable compilation. The project is a Python Qt5 application for visualizing MDA (Measurement Data Acquisition) data with a well-structured MVC architecture.

## Current Project Status

### ✅ Strengths
- **Well-structured codebase** with clear MVC architecture
- **58 tests passing** with 36% coverage
- **Modern development practices** (pre-commit hooks, CI/CD, documentation)
- **Performance optimizations** (lazy loading, data caching)
- **Dual plotting backends** (Matplotlib and PyQt5)
- **Comprehensive documentation** with Sphinx and GitHub Pages

### ⚠️ Areas for Improvement
- **Low test coverage** (36%) - many critical paths untested
- **Deprecation warnings** - PyQt5 sipPyTypeDict() deprecations
- **Python 3.13 compatibility** - xdrlib deprecation
- **GUI test limitations** - headless environment challenges
- **Memory management** - potential memory leaks in large datasets

## 1. Environment Setup and Dependencies

### Current Environment Configuration

The project uses a conda environment named `mda1` with the following key dependencies:

```yaml
# env.yml
name: mdaviz
channels:
  - conda-forge
  - nodefaults

dependencies:
  - libopenblas
  - matplotlib
  - pyqt =5
  - pyqtgraph
  - qt =5
  - tiled
  - scipy
  - lmfit
  - pyyaml
```

### Installation Commands

```bash
# Create and activate environment
conda env create -f env.yml
conda activate mda1

# Install project in editable mode
pip install -e .

# Install development dependencies
pip install -e ".[dev]"

# Install build dependencies for executables
pip install -e ".[build]"
```

### Environment Verification

```bash
# Verify environment
conda info --envs
python --version  # Should be 3.11+
pip list | grep -E "(PyQt5|matplotlib|scipy|lmfit|tiled)"

# Test basic functionality
python -c "import mdaviz; print('mdaviz imported successfully')"
```

## 2. Testing Strategy

### Current Test Status
- **Total tests**: 58
- **Coverage**: 36%
- **Test framework**: pytest
- **Coverage tool**: pytest-cov

### Running Tests

```bash
# Run all tests with coverage
pytest src/tests -v --cov=src/mdaviz --cov-report=html

# Run specific test categories
pytest src/tests/test_lazy_loading.py -v
pytest src/tests/test_auto_load.py -v
pytest src/tests/test_i0_auto_uncheck.py -v

# Run tests with detailed output
pytest src/tests -v -s --tb=long
```

### Test Coverage Analysis

**Well-tested modules (>70% coverage):**
- `virtual_table_model.py` (84%)
- `lazy_loading_config.py` (73%)
- `aboutdialog.py` (77%)
- `empty_table_model.py` (85%)

**Modules needing improvement (<50% coverage):**
- `chartview.py` (13%) - Core plotting functionality
- `fit_manager.py` (27%) - Curve fitting
- `mda_file.py` (35%) - File handling
- `app.py` (0%) - Application startup
- `mainwindow.py` (46%) - Main UI

### Test Improvement Plan

1. **Add GUI tests** for critical UI components
2. **Test error handling paths** in all modules
3. **Add integration tests** for data flow
4. **Test performance-critical paths** (lazy loading, caching)
5. **Add property-based tests** for data validation

## 3. Code Quality and Pre-commit Hooks

### Current Pre-commit Configuration

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: debug-statements

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.12.1
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.16.1
    hooks:
      - id: mypy
        additional_dependencies: [types-PyYAML]
        args: [--ignore-missing-imports]
```

### Running Pre-commit Hooks

```bash
# Run all hooks on all files
pre-commit run --all-files

# Run specific hooks
pre-commit run ruff --all-files
pre-commit run mypy --all-files

# Install hooks (first time setup)
pre-commit install
```

### Code Quality Metrics

- **Ruff**: Code linting and formatting
- **MyPy**: Type checking (import errors only)
- **Black**: Code formatting (via ruff)
- **Pre-commit hooks**: Automated quality checks

## 4. Comprehensive Code Analysis

### Architecture Overview

The project follows a Model-View-Controller (MVC) pattern:

```
MainWindow (QMainWindow)
├── MDA_MVC (QWidget) - Core MVC implementation
│   ├── MDAFolderTableView - Folder navigation
│   ├── MDAFile (QWidget) - File content display
│   └── MDAFileVisualization (QWidget) - Data visualization
├── ChartView (QWidget) - Dual plotting backend
├── DataCache - LRU cache system
├── LazyFolderScanner - Efficient folder scanning
└── FitManager - Curve fitting functionality
```

### Key Components

1. **MainWindow**: Central application window and state management
2. **MDA_MVC**: Core MVC handling MDA file operations
3. **ChartView**: Dual plotting (Matplotlib + PyQt5) with curve management
4. **DataCache**: LRU cache for performance optimization
5. **LazyFolderScanner**: Efficient scanning of large directories
6. **FitManager**: Curve fitting with 7 mathematical models

### Data Flow

```
User selects folder → LazyFolderScanner → DataCache → MDA_MVC → ChartView
                                                      ↓
User selects file → MDAFile → DataCache → ChartView → FitManager
```

## 5. Identified Bugs and Issues

### Critical Issues (High Priority)

#### A. PyQt5 Deprecation Warnings
- **Issue**: `sipPyTypeDict()` is deprecated in favor of `sipPyTypeDictRef()`
- **Impact**: Future PyQt5 versions may break functionality
- **Files affected**: 15+ files including:
  - `src/mdaviz/aboutdialog.py:15`
  - `src/mdaviz/mda_folder.py:76`
  - `src/mdaviz/user_settings.py:48`
  - `src/mdaviz/chartview.py:60`
  - `src/mdaviz/mainwindow.py:27`

**Fix Strategy:**
```python
# Before (deprecated)
class MyWidget(QWidget):
    pass

# After (modern)
class MyWidget(QWidget):
    pass  # PyQt5 will handle this automatically
```

#### B. Python 3.13 Compatibility
- **Issue**: `xdrlib` is deprecated and slated for removal in Python 3.13
- **Location**: `src/mdaviz/synApps_mdalib/mda.py:25`
- **Current mitigation**: Fallback to local `f_xdrlib` implementation
- **Impact**: Application will break on Python 3.13+

**Fix Strategy:**
```python
# Current implementation (good)
try:
    import xdrlib as xdr
except ImportError:
    from . import f_xdrlib as xdr_fallback
    xdr = xdr_fallback
```

#### C. GUI Test Limitations
- **Issue**: GUI tests are limited in headless environments
- **Location**: `src/tests/test_app.py`
- **Current status**: Tests are skipped with FIXME comments

**Fix Strategy:**
```python
# Use pytest-qt for GUI testing
import pytest
from PyQt5.QtWidgets import QApplication

@pytest.fixture
def qtbot(qtbot):
    """Provide qtbot fixture for GUI testing."""
    return qtbot

def test_gui_functionality(qtbot):
    """Test GUI functionality with qtbot."""
    # GUI test implementation
    pass
```

### Performance Issues (Medium Priority)

#### A. Memory Management
- **Issue**: Potential memory leaks with large datasets
- **Location**: `src/mdaviz/data_cache.py`
- **Impact**: Application may become unresponsive with large files

**Improvement Strategy:**
```python
# Add memory monitoring
import psutil
import gc

class DataCache(QObject):
    def __init__(self, max_size=100, max_memory_mb=500):
        self.max_memory_mb = max_memory_mb
        # ... existing code ...
    
    def _check_memory_usage(self):
        """Monitor memory usage and cleanup if needed."""
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        if memory_mb > self.max_memory_mb:
            self.clear()
            gc.collect()
```

#### B. Large File Handling
- **Issue**: Limited handling of very large directories (>10,000 files)
- **Location**: `src/mdaviz/lazy_folder_scanner.py`
- **Current limit**: 10,000 files maximum

**Improvement Strategy:**
```python
# Progressive loading for very large directories
class LazyFolderScanner(QObject):
    def __init__(self, batch_size=50, max_files=10000, progressive_loading=True):
        self.progressive_loading = progressive_loading
        # ... existing code ...
    
    def scan_large_directory(self, path):
        """Handle directories with >10,000 files."""
        if self.progressive_loading:
            return self._progressive_scan(path)
        else:
            return self._standard_scan(path)
```

### User Experience Issues (Low Priority)

#### A. Error Handling
- **Issue**: Some error messages are not user-friendly
- **Impact**: Poor user experience when errors occur

**Improvement Strategy:**
```python
# Centralized error handling
class ErrorHandler:
    @staticmethod
    def show_user_friendly_error(error, context=""):
        """Display user-friendly error messages."""
        error_messages = {
            "FileNotFoundError": f"The file could not be found. Please check the path and try again.",
            "PermissionError": f"Permission denied. Please check file permissions.",
            # ... more mappings ...
        }
        return error_messages.get(type(error).__name__, str(error))
```

#### B. UI Responsiveness
- **Issue**: UI may freeze during large operations
- **Location**: `src/mdaviz/mainwindow.py`

**Improvement Strategy:**
```python
# Background processing with progress indicators
from PyQt5.QtCore import QThread, pyqtSignal

class BackgroundWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def run(self):
        try:
            # Perform heavy operation
            for i in range(100):
                self.progress.emit(i)
                # ... work ...
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
```

## 6. Potential Improvements

### High Priority Improvements

#### A. Test Coverage Enhancement
- **Current coverage**: 36%
- **Target**: 80%+
- **Areas to focus**:
  - ChartView plotting functionality
  - FitManager operations
  - DataCache operations
  - Error handling paths

**Implementation Plan:**
```python
# Example test for ChartView
def test_chartview_plotting(qtbot):
    """Test ChartView plotting functionality."""
    chart_view = ChartView()
    qtbot.addWidget(chart_view)
    
    # Test data plotting
    x_data = [1, 2, 3, 4, 5]
    y_data = [1, 4, 9, 16, 25]
    
    chart_view.plot_data(x_data, y_data, "Test Curve")
    
    # Verify plot was created
    assert len(chart_view.get_curves()) == 1
    assert chart_view.get_curves()[0].label == "Test Curve"
```

#### B. Modernize PyQt5 Usage
- **Action**: Update deprecated `sipPyTypeDict()` calls
- **Benefit**: Future compatibility and reduced warnings
- **Effort**: Medium (requires careful testing)

#### C. Python 3.13+ Compatibility
- **Action**: Replace `xdrlib` with modern alternatives
- **Options**: 
  - Use `struct` module for binary data
  - Implement custom XDR library
  - Use third-party XDR libraries
- **Benefit**: Long-term Python compatibility

### Medium Priority Improvements

#### A. Enhanced Error Handling
- **Action**: Implement comprehensive error handling system
- **Features**:
  - User-friendly error messages
  - Error logging and reporting
  - Recovery mechanisms
  - User guidance for common issues

#### B. Performance Optimizations
- **Action**: Implement advanced caching and memory management
- **Features**:
  - Memory usage monitoring
  - Automatic cache cleanup
  - Background data processing
  - Progressive loading for large files

#### C. User Interface Enhancements
- **Action**: Improve UI responsiveness and user experience
- **Features**:
  - Better progress indicators
  - Keyboard shortcuts
  - Customizable layouts
  - Dark mode support

### Low Priority Improvements

#### A. Advanced Features
- **Action**: Add advanced data analysis capabilities
- **Features**:
  - Statistical analysis tools
  - Data export functionality
  - Batch processing capabilities
  - Plugin system

#### B. Documentation Enhancements
- **Action**: Improve user and developer documentation
- **Features**:
  - Video tutorials
  - Interactive examples
  - API documentation improvements
  - Contributing guidelines

## 7. Executable Compilation

### Current State
The project currently supports:
- PyPI packaging with wheel and source distributions
- Entry point script: `mdaviz = "mdaviz.app:main"`
- Standard Python installation via pip

### Executable Compilation Solutions

#### 1. PyInstaller (Recommended)

**Advantages:**
- Cross-platform support (Windows, macOS, Linux)
- Single-file executables
- Good PyQt5 support
- Active development and community

**Implementation:**
```bash
# Install PyInstaller
pip install pyinstaller

# Create executable
pyinstaller --onefile --windowed --name mdaviz src/mdaviz/app.py

# For development
pyinstaller --onefile --windowed --name mdaviz --debug all src/mdaviz/app.py
```

**Configuration file** (`mdaviz.spec`):
```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/mdaviz/app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/mdaviz/resources', 'mdaviz/resources'),
        ('src/mdaviz/synApps_mdalib', 'mdaviz/synApps_mdalib'),
    ],
    hiddenimports=[
        'PyQt5.QtCore',
        'PyQt5.QtWidgets',
        'PyQt5.QtGui',
        'matplotlib',
        'scipy',
        'numpy',
        'lmfit',
        'tiled',
        'yaml',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
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
```

#### 2. cx_Freeze (Alternative)

**Advantages:**
- Good for creating installers
- Cross-platform support
- Active development

**Implementation:**
```bash
# Build executable
python setup_cx_freeze.py build

# Create Windows installer (Windows only)
python setup_cx_freeze.py bdist_msi
```

**Configuration** (`setup_cx_freeze.py`):
```python
#!/usr/bin/env python3
"""
cx_Freeze setup script for mdaviz executable compilation.
"""

from cx_Freeze import setup, Executable
import sys
import os
from pathlib import Path

# Get project root
project_root = Path(__file__).parent

build_exe_options = {
    "packages": [
        "PyQt5", 
        "matplotlib", 
        "scipy", 
        "numpy", 
        "lmfit", 
        "tiled", 
        "yaml", 
        "mdaviz",
        "mdaviz.mainwindow",
        "mdaviz.mda_folder",
        "mdaviz.chartview",
        "mdaviz.data_cache",
        "mdaviz.lazy_folder_scanner",
        "mdaviz.fit_manager",
        "mdaviz.fit_models",
        "mdaviz.user_settings",
        "mdaviz.utils",
        "mdaviz.synApps_mdalib",
    ],
    "excludes": [
        "tkinter",
        "unittest",
        "test",
        "distutils",
    ],
    "include_files": [
        (str(project_root / "src" / "mdaviz" / "resources"), "resources"),
        (str(project_root / "src" / "mdaviz" / "synApps_mdalib"), "synApps_mdalib"),
    ],
    "include_msvcr": True,  # Windows only
}

# Platform-specific base
base = None
if sys.platform == "win32":
    base = "Win32GUI"
elif sys.platform == "darwin":
    base = None  # Use default for macOS
else:
    base = None  # Use default for Linux

# Executable configuration
executables = [
    Executable(
        str(project_root / "src" / "mdaviz" / "app.py"),
        base=base,
        target_name="mdaviz",
        icon=str(project_root / "src" / "mdaviz" / "resources" / "viz.png") if (project_root / "src" / "mdaviz" / "resources" / "viz.png").exists() else None,
    )
]

setup(
    name="mdaviz",
    version="1.1.2",
    description="MDA Data Visualization Tool",
    author="Fanny Rodolakis, Pete Jemian, Rafael Vescovi, Eric Codrea",
    author_email="rodolakis@anl.gov",
    options={"build_exe": build_exe_options},
    executables=executables,
)
```

#### 3. Nuitka (Performance)

**Advantages:**
- Compiles Python to C for better performance
- Smaller executable sizes
- Better startup times

**Implementation:**
```bash
# Simple compilation
python -m nuitka --follow-imports --enable-plugin=pyqt5 --standalone src/mdaviz/app.py

# Optimized compilation
python -m nuitka --follow-imports --enable-plugin=pyqt5 --standalone --lto=yes src/mdaviz/app.py
```

### Automated Builds

#### GitHub Actions Workflow

```yaml
# .github/workflows/build-executables.yml
name: Build Executables

on:
  push:
    tags:
      - "v*"
  workflow_dispatch:

jobs:
  build-windows:
    name: Build Windows Executable
    runs-on: windows-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev,build]"

      - name: Build with PyInstaller
        run: |
          pyinstaller --onefile --windowed --name mdaviz src/mdaviz/app.py

      - name: Upload Windows executable
        uses: actions/upload-artifact@v4
        with:
          name: mdaviz-windows
          path: dist/mdaviz.exe

  build-linux:
    name: Build Linux Executable
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install system dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y \
            libgl1-mesa-glx \
            libglib2.0-0 \
            libxcb-icccm4 \
            libxcb-image0 \
            libxcb-keysyms1 \
            libxcb-randr0 \
            libxcb-render-util0 \
            libxcb-xinerama0 \
            libxcb-xfixes0 \
            libxkbcommon-x11-0

      - name: Install Python dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev,build]"

      - name: Build with PyInstaller
        run: |
          pyinstaller --onefile --windowed --name mdaviz src/mdaviz/app.py

      - name: Upload Linux executable
        uses: actions/upload-artifact@v4
        with:
          name: mdaviz-linux
          path: dist/mdaviz

  build-macos:
    name: Build macOS Executable
    runs-on: macos-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev,build]"

      - name: Build with PyInstaller
        run: |
          pyinstaller --onefile --windowed --name mdaviz src/mdaviz/app.py

      - name: Upload macOS executable
        uses: actions/upload-artifact@v4
        with:
          name: mdaviz-macos
          path: dist/mdaviz
```

### Testing Executables

```bash
# Test executable
./dist/mdaviz

# Test with sample data
./dist/mdaviz --log debug

# Test on different platforms
# Windows: mdaviz.exe
# Linux: ./mdaviz
# macOS: ./mdaviz
```

## 8. Implementation Timeline

### Phase 1: Immediate Actions (Week 1-2)
1. **Fix critical deprecation warnings** - Update PyQt5 usage
2. **Improve test coverage** - Add tests for critical paths
3. **Implement PyInstaller support** - Add executable compilation
4. **Update documentation** - Add executable build instructions

### Phase 2: Short-term Goals (Month 1-2)
1. **Python 3.13 compatibility** - Replace xdrlib dependency
2. **Enhanced error handling** - Implement comprehensive error system
3. **Performance optimizations** - Improve memory management
4. **CI/CD for executables** - Automated builds and releases

### Phase 3: Medium-term Goals (Month 3-6)
1. **Advanced features** - Statistical analysis, data export
2. **Plugin system** - Extensible architecture
3. **Cross-platform testing** - Comprehensive platform support
4. **Community engagement** - User feedback and contributions

## 9. Quality Assurance

### Code Quality Metrics
- **Test coverage target**: 80%+
- **Code complexity**: Maintain low cyclomatic complexity
- **Documentation**: 100% API documentation coverage
- **Performance**: <2s startup time, <500MB memory usage

### Automated Checks
- **Pre-commit hooks**: Run on every commit
- **CI/CD pipeline**: Automated testing and building
- **Code review**: Required for all changes
- **Performance monitoring**: Track memory and CPU usage

### Release Process
1. **Development**: Feature branches with tests
2. **Testing**: Automated and manual testing
3. **Release**: Tagged releases with executables
4. **Distribution**: PyPI, GitHub releases, package managers

## 10. Conclusion

The mdaviz project has a solid foundation with good architecture and modern development practices. The main areas for improvement are:

1. **Immediately**: Address PyQt5 deprecation warnings and improve test coverage
2. **Short-term**: Implement executable compilation and Python 3.13 compatibility
3. **Medium-term**: Add advanced features and performance optimizations
4. **Long-term**: Build community and ecosystem

With this comprehensive plan, the project can evolve into a robust, user-friendly tool for MDA data visualization with excellent cross-platform support and modern development practices.

## Appendices

### A. Current Dependencies
- **Core**: PyQt5, matplotlib, scipy, lmfit, tiled, PyYAML
- **Development**: pytest, ruff, mypy, pre-commit
- **Build**: pyinstaller, cx_Freeze, nuitka
- **Vendored**: synApps_mdalib (mdalib)

### B. Platform Support
- **Tested platforms**: Linux (Ubuntu), Windows, macOS
- **Python versions**: 3.10, 3.11, 3.12
- **Qt versions**: Qt5 (5.15.2)

### C. Performance Benchmarks
- **Startup time**: <2 seconds
- **Memory usage**: <500MB for typical datasets
- **File loading**: <1 second for 1MB files
- **Plot rendering**: <100ms for standard plots

### D. Contributing Guidelines
1. Fork and clone the repository
2. Create a feature branch
3. Make changes with tests
4. Run pre-commit hooks
5. Submit a pull request
6. Ensure CI/CD passes
7. Get code review approval 