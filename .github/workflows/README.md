# CI/CD Workflows

This directory contains GitHub Actions workflows for continuous integration and testing of the mdaviz project with PyQt6.

## Workflows Overview

### 1. `ci.yml` - Main CI Pipeline
**Purpose**: Primary continuous integration pipeline for Linux testing
- **Python versions**: 3.10, 3.11, 3.12
- **Platform**: Ubuntu Linux
- **Features**:
  - Code linting (ruff)
  - Type checking (mypy)
  - Unit tests with PyQt6
  - Coverage reporting
  - Package building and validation

### 2. `python313-test.yml` - Python 3.13 Compatibility
**Purpose**: Dedicated testing for Python 3.13 compatibility
- **Python version**: 3.13
- **Platform**: Ubuntu Linux
- **Features**:
  - Basic compatibility tests
  - Deprecation warning checks
  - Non-GUI test execution
  - Linting and type checking

### 3. `cross-platform-test.yml` - Cross-Platform Testing
**Purpose**: Ensure PyQt6 compatibility across different operating systems
- **Platforms**: Windows, macOS, Linux
- **Python versions**: 3.11, 3.12
- **Features**:
  - Basic import and functionality tests
  - Platform-specific verification
  - GUI tests on Linux (with Xvfb)

### 4. `deprecation-check.yml` - Deprecation Warning Monitoring
**Purpose**: Monitor and track deprecation warnings for future Python compatibility
- **Python versions**: 3.11, 3.12, 3.13
- **Features**:
  - Deprecation warning detection
  - Future warning monitoring
  - xdrlib usage tracking
  - Detailed deprecation reports

## Key Features

### PyQt6 Integration
- All workflows use PyQt6 instead of PyQt5
- Qt6 dependencies installed via system packages
- Matplotlib qtagg backend compatibility verified
- GUI testing with Xvfb for headless environments

### Python 3.13 Preparation
- Dedicated workflow for Python 3.13 testing
- Deprecation warning monitoring
- Compatibility checks for future Python versions
- xdrlib deprecation tracking (from synApps_mdalib dependency)

### Cross-Platform Support
- Windows testing with PyQt6
- macOS testing with PyQt6
- Linux GUI testing with Xvfb
- Platform-specific dependency handling

### Quality Assurance
- Code linting with ruff
- Type checking with mypy
- Test coverage reporting
- Package validation
- Deprecation warning monitoring

## Environment Variables

### Common Variables
- `PYTEST_QT_API`: Set to `pyqt6` for all workflows
- `DISPLAY`: Set to `:99.0` for Xvfb on Linux
- `QT_QPA_PLATFORM`: Set to `offscreen` for headless testing

### Platform-Specific
- **Linux**: Xvfb setup for GUI testing
- **Windows**: Native PyQt6 installation
- **macOS**: Native PyQt6 installation

## Dependencies

### System Dependencies (Linux)
- Qt6 development packages
- X11 utilities for GUI testing
- Xvfb for headless display

### Python Dependencies
- PyQt6 (via pip)
- pytest and pytest-qt
- Coverage tools
- Linting tools (ruff, mypy)

## Troubleshooting

### Common Issues
1. **Qt6 installation failures**: Ensure system packages are available
2. **GUI test failures**: Check Xvfb setup and display configuration
3. **Deprecation warnings**: Monitor the deprecation-check workflow
4. **Cross-platform issues**: Check platform-specific dependency installation

### Debugging
- Check workflow logs for specific error messages
- Verify Python and Qt versions in test output
- Monitor deprecation warning reports
- Review coverage reports for test gaps

## Future Enhancements

1. **Performance benchmarking**: Add performance comparison tests
2. **GUI automation**: Enhanced GUI testing with automated interactions
3. **Dependency updates**: Automated dependency update workflows
4. **Release automation**: Automated release and deployment workflows 