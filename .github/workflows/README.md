# GitHub Actions Workflows

This directory contains the GitHub Actions workflows for the mdaviz project. The CI/CD pipeline has been simplified and consolidated for better efficiency and maintainability.

## Workflows Overview

### 1. Main CI Workflow (`ci.yml`)
**Purpose**: Primary continuous integration workflow that runs on all Python versions and platforms.

**Triggers**:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches
- Manual workflow dispatch

**Features**:
- **Multi-Python Testing**: Tests on Python 3.10, 3.11, 3.12, and 3.13
- **Cross-Platform Testing**: Tests on Linux and macOS
- **Comprehensive Checks**:
  - PyQt6 installation verification
  - mdaviz import testing
  - Deprecation warning detection
  - xdrlib usage checking
  - Linting (ruff, mypy)
  - Unit tests with coverage
- **Package Building**: Builds and validates packages on main branch pushes

**Matrix Strategy**:
- **Linux**: Python 3.10, 3.11, 3.12, 3.13 (full test suite)
- **Windows**: Python 3.11, 3.12 (basic tests)
- **macOS**: Python 3.11, 3.12 (basic tests)

### 2. Documentation Workflow (`docs.yml`)
**Purpose**: Builds and deploys project documentation.

**Features**:
- Sphinx documentation build
- Automatic deployment to GitHub Pages
- Runs on documentation changes

### 3. Build Executables (`build-executables.yml`)
**Purpose**: Creates standalone executables for distribution.

**Features**:
- Uses cx_Freeze to create platform-specific executables
- Supports Windows, macOS, and Linux builds
- Creates release artifacts

### 4. PyPI Release (`pypi.yml`)
**Purpose**: Publishes packages to PyPI.

**Features**:
- Automatic PyPI publishing on releases
- Package validation and testing
- Secure credential management

### 5. Pre-commit (`pre-commit.yml`)
**Purpose**: Runs pre-commit hooks for code quality.

**Features**:
- Automated code formatting
- Linting checks
- Runs on pull requests

## Simplified Architecture

### Before (Multiple Workflows)
- `ci.yml` - Basic tests
- `python313-test.yml` - Python 3.13 specific tests
- `deprecation-check.yml` - Deprecation warning checks
- `cross-platform-test.yml` - Cross-platform testing

### After (Consolidated)
- `ci.yml` - Comprehensive testing with matrix strategy
- Additional workflows for specific purposes (docs, builds, releases)

## Benefits of Consolidation

1. **Reduced Complexity**: Fewer workflows to maintain
2. **Better Efficiency**: Eliminates duplicate setup steps
3. **Faster Feedback**: Parallel execution within single workflow
4. **Easier Debugging**: All tests in one place
5. **Cost Optimization**: Fewer GitHub Actions minutes used

## Test Script Integration

The main CI workflow includes a comprehensive test script (`scripts/test_checks.py`) that consolidates:
- PyQt6 installation verification
- mdaviz import testing
- Deprecation warning detection
- xdrlib usage checking
- Linting and type checking
- Basic test execution

This script can be run locally for development:
```bash
python scripts/test_checks.py
```

## Environment Variables

### Linux Testing
- `QT_QPA_PLATFORM=offscreen` - Headless Qt testing
- `DISPLAY=:99.0` - Virtual display for GUI tests
- `PYTEST_QT_API=pyqt6` - PyQt6 API for pytest-qt

### Cross-Platform Testing
- Windows and macOS use native Qt installations
- Basic tests only (no GUI tests on non-Linux platforms)

## Coverage and Reporting

- **Code Coverage**: Generated for all Python versions
- **Coverage Reports**: XML and terminal output
- **Codecov Integration**: Automatic coverage upload
- **Test Results**: Detailed output for debugging

## Performance Optimizations

1. **Caching**: pip dependencies cached by Python version
2. **Parallel Execution**: Matrix strategy for concurrent testing
3. **Selective Testing**: Platform-appropriate test suites
4. **Efficient Setup**: Minimal dependency installation

## Troubleshooting

### Common Issues
1. **Qt Installation**: Ensure Qt6 dependencies are installed
2. **GUI Tests**: Use xvfb for headless testing on Linux
3. **Import Errors**: Check PyQt6 installation and version compatibility
4. **Deprecation Warnings**: Monitor for new deprecation warnings

### Local Testing
```bash
# Run the comprehensive test script
python scripts/test_checks.py

# Run specific test suites
pytest src/tests/test_auto_load.py -v
pytest src/tests/test_lazy_loading.py -k "not gui" -v

# Run linting
ruff check src/
ruff format --check src/
mypy src/mdaviz --ignore-missing-imports
```

## Future Enhancements

1. **Performance Monitoring**: Add performance regression testing
2. **Security Scanning**: Integrate security vulnerability scanning
3. **Dependency Updates**: Automated dependency update workflows
4. **Release Automation**: Streamlined release process
