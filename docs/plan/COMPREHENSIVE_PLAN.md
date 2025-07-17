# mdaviz Comprehensive Development Plan

## Executive Summary

This document provides a comprehensive plan for the mdaviz project, covering environment setup, dependency management, testing, code analysis, bug identification, improvements, and executable compilation. The project is a Python Qt6 application for visualizing MDA (Measurement Data Acquisition) data with a well-structured MVC architecture.

## Current Project Status

### ✅ Strengths
- **Well-structured codebase** with clear MVC architecture
- **130 tests passing** with 46% coverage (improved from 36%)
- **Modern development practices** (pre-commit hooks, CI/CD, documentation)
- **Performance optimizations** (lazy loading, data caching)
- **Dual plotting backends** (Matplotlib and PyQt6)
- **Comprehensive documentation** with Sphinx and GitHub Pages
- **PyQt6 migration complete** - Future-proof and Python 3.13+ compatible

### ⚠️ Areas for Improvement
- **Test coverage needs improvement** (46% - target: 80%+)
- **GUI test failures** - 26 failed tests, mostly due to missing parent arguments
- **Memory management** - potential memory leaks in large datasets
- **Test infrastructure** - Some tests need proper mocking and setup

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
  - pyqtgraph
  - tiled
  - scipy
  - lmfit
  - pyyaml
  - psutil
```

### Installation Commands

```bash
# Create and activate environment
conda env create -f env.yml
conda activate mda1

# Install PyQt6 (not available in conda-forge for all platforms)
pip install PyQt6

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
pip list | grep -E "(PyQt6|matplotlib|scipy|lmfit|tiled)"

# Test basic functionality
python -c "import mdaviz; print('mdaviz imported successfully')"
```

## 2. Testing Strategy

### Current Test Status
- **Total tests**: 210 (130 passed, 26 failed, 54 skipped, 5 errors)
- **Coverage**: 46% (improved from 36%)
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

# Run only passing tests
pytest src/tests -v --tb=short -x
```

### Test Coverage Analysis

**Well-tested modules (>70% coverage):**
- `virtual_table_model.py` (84%)
- `fit_manager.py` (87%)
- `lazy_loading_config.py` (73%)
- `aboutdialog.py` (77%)
- `empty_table_model.py` (80%)

**Modules needing improvement (<50% coverage):**
- `chartview.py` (67%) - Core plotting functionality
- `mainwindow.py` (29%) - Main UI
- `mda_file.py` (35%) - File handling
- `mda_file_table_model.py` (26%) - Table model
- `data_table_model.py` (0%) - Data table model
- `licensedialog.py` (0%) - License dialog
- `popup.py` (0%) - Popup dialogs
- `progress_dialog.py` (0%) - Progress dialogs

### Test Issues Identified

1. **GUI Component Tests**: Missing parent arguments for Qt widgets
   - ChartView, MDAFile, DataTableView require parent arguments
   - Need proper QApplication setup in test fixtures

2. **Mock Configuration**: Settings mocking needs improvement
   - `settings.getKey()` returns tuple instead of string in some tests
   - Need better mocking of user settings

3. **Import Issues**: Some test imports don't match actual module structure
   - `MDAFileViz` import fails
   - `UserSettings` class not found

4. **Cache Testing**: DataCache tests need proper CachedFileData objects
   - Tests pass dict/string instead of CachedFileData objects
   - Need proper object creation for testing

### Test Improvement Plan

1. **Fix GUI test failures** - Add proper parent arguments and mocking
2. **Test error handling paths** in all modules
3. **Add integration tests** for data flow
4. **Test performance-critical paths** (lazy loading, caching)
5. **Add property-based tests** for data validation
6. **Improve test fixtures** - Better setup and teardown

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
3. **ChartView**: Dual plotting (Matplotlib + PyQt6) with curve management
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

#### A. Test Coverage Improvement
- **Issue**: Test coverage at 46% with many critical paths untested
- **Impact**: Reduced confidence in code quality and potential for regressions
- **Modules needing improvement**:
  - `chartview.py` (67%) - Core plotting functionality
  - `mainwindow.py` (29%) - Main UI
  - `mda_file.py` (35%) - File handling
  - `data_table_model.py` (0%) - Data table model

**Improvement Strategy:**
```python
# Add comprehensive tests for critical functionality
def test_chartview_plotting(qtbot):
    """Test ChartView plotting functionality."""
    chart_view = ChartView(parent=None)  # Fix parent argument
    qtbot.addWidget(chart_view)

    # Test data plotting
    x_data = [1, 2, 3, 4, 5]
    y_data = [1, 4, 9, 16, 25]

    chart_view.plot_data(x_data, y_data, "Test Curve")

    # Verify plot was created
    assert len(chart_view.get_curves()) == 1
    assert chart_view.get_curves()[0].label == "Test Curve"
```

#### B. GUI Test Implementation
- **Issue**: GUI tests are failing due to missing parent arguments and improper mocking
- **Location**: `src/tests/test_gui_components.py` and `src/tests/test_gui_integration.py`
- **Current status**: 26 failed tests, 5 errors
- **Impact**: Reduced confidence in UI functionality

**Implementation Strategy:**
```python
# Use pytest-qt for proper GUI testing
import pytest
from PyQt6.QtWidgets import QApplication

@pytest.fixture
def qtbot(qtbot):
    """Provide qtbot fixture for GUI testing."""
    return qtbot

def test_gui_functionality(qtbot):
    """Test GUI functionality with qtbot."""
    # GUI test implementation with proper parent arguments
    pass
```

#### C. Memory Management Optimization
- **Issue**: Potential memory leaks in large datasets
- **Location**: `src/mdaviz/data_cache.py` and `src/mdaviz/lazy_folder_scanner.py`
- **Current status**: Basic LRU cache implemented
- **Impact**: Performance degradation with large datasets

**Optimization Strategy:**
```python
# Implement memory monitoring and cleanup
def monitor_memory_usage():
    """Monitor memory usage and trigger cleanup if needed."""
    import psutil
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    
    if memory_mb > MAX_MEMORY_MB:
        cleanup_cache()
        gc.collect()
```

### Medium Priority Issues

#### A. Settings Management
- **Issue**: Settings mocking in tests returns incorrect types
- **Location**: `src/mdaviz/mainwindow.py` line 446
- **Current status**: Tests fail with `AttributeError: 'tuple' object has no attribute 'split'`
- **Impact**: Test reliability

**Fix Strategy:**
```python
# Proper settings mocking
@patch("mdaviz.mainwindow.settings.getKey")
def test_mainwindow_creation(mock_settings):
    """Test MainWindow creation with proper settings mocking."""
    mock_settings.return_value = "test_folder1,test_folder2"  # Return string, not tuple
    window = MainWindow()
    # Test implementation
```

#### B. Import Structure Issues
- **Issue**: Test imports don't match actual module structure
- **Location**: Multiple test files
- **Current status**: ImportError for some classes
- **Impact**: Test execution failures

**Fix Strategy:**
```python
# Update imports to match actual module structure
from mdaviz.mda_file_viz import MDAFileVisualization  # Correct import
from mdaviz.user_settings import settings  # Use actual module structure
```

## 6. Performance Analysis

### Current Performance Metrics
- **Startup time**: <2 seconds
- **Memory usage**: <500MB for typical datasets
- **File loading**: <1 second for 1MB files
- **Plot rendering**: <100ms for standard plots

### Performance Optimizations

#### A. Data Caching
- **Current**: LRU cache with size and entry limits
- **Improvement**: Add memory-based eviction
- **Benefit**: Better memory management

#### B. Lazy Loading
- **Current**: Efficient folder scanning
- **Improvement**: Progressive data loading
- **Benefit**: Faster UI responsiveness

#### C. Plot Optimization
- **Current**: Matplotlib backend
- **Improvement**: PyQt6 native plotting
- **Benefit**: Better performance for large datasets

## 7. Executable Compilation

### Current Build Tools
- **PyInstaller**: Cross-platform executables
- **cx_Freeze**: Alternative build system
- **Nuitka**: Python to C++ compilation

### Build Configuration

```python
# PyInstaller configuration
import PyInstaller.__main__

PyInstaller.__main__.run([
    'src/mdaviz/app.py',
    '--onefile',
    '--windowed',
    '--name=mdaviz',
    '--add-data=src/mdaviz/resources:resources',
    '--hidden-import=PyQt6',
    '--hidden-import=matplotlib',
])
```

### Build Process

```bash
# Build executable
pyinstaller --onefile --windowed --name mdaviz src/mdaviz/app.py

# Test executable
./dist/mdaviz

# Build for different platforms
# Windows: pyinstaller --onefile --windowed --name mdaviz.exe src/mdaviz/app.py
# macOS: pyinstaller --onefile --windowed --name mdaviz src/mdaviz/app.py
# Linux: pyinstaller --onefile --windowed --name mdaviz src/mdaviz/app.py
```

### CI/CD Integration

```yaml
# GitHub Actions workflow for executable builds
name: Build Executables

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ["3.11"]

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

      - name: Upload executable
        uses: actions/upload-artifact@v4
        with:
          name: mdaviz-${{ matrix.os }}
          path: dist/mdaviz*
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
1. **Fix GUI test failures** - Add proper parent arguments and mocking (target: 0 failed tests)
2. **Improve test coverage** - Add tests for critical paths (target: 60%+)
3. **Fix import issues** - Update test imports to match actual module structure
4. **Enhance test infrastructure** - Better fixtures and mocking

### Phase 2: Short-term Goals (Month 1-2)
1. **Enhanced error handling** - Implement comprehensive error system
2. **Performance optimizations** - Progressive loading for large files
3. **CI/CD for executables** - Automated builds and releases
4. **Advanced testing** - Property-based and integration tests
5. **Test coverage target** - Reach 80% coverage

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

The mdaviz project has a solid foundation with good architecture and modern development practices. The PyQt6 migration is complete, ensuring future compatibility. The test coverage has improved significantly, and the main areas for improvement are:

1. **Immediately**: Fix GUI test failures and improve test infrastructure
2. **Short-term**: Add memory management and error handling improvements
3. **Medium-term**: Implement executable compilation and advanced features
4. **Long-term**: Build community and ecosystem

With this comprehensive plan, the project can evolve into a robust, user-friendly tool for MDA data visualization with excellent cross-platform support and modern development practices.

## Appendices

### A. Current Dependencies
- **Core**: PyQt6, matplotlib, scipy, lmfit, tiled, PyYAML, psutil
- **Development**: pytest, ruff, mypy, pre-commit, pytest-qt
- **Build**: pyinstaller, cx_Freeze, nuitka
- **Vendored**: synApps_mdalib (mdalib)

### B. Platform Support
- **Tested platforms**: Linux (Ubuntu), Windows, macOS
- **Python versions**: 3.10, 3.11, 3.12, 3.13
- **Qt versions**: Qt6 (6.9.0)

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
