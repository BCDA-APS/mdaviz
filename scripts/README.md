# mdaviz Migration Scripts

This directory contains scripts to help with the migration from PyQt5 to PyQt6 and Python 3.13+ compatibility.

## Scripts Overview

### 1. `migrate_pyqt5_to_pyqt6.py`
Automated migration script to convert PyQt5 code to PyQt6.

**Features:**
- Updates import statements from PyQt5 to PyQt6
- Fixes deprecated API usage (QDesktopWidget, QVariant)
- Updates matplotlib backend imports
- Creates backup files before making changes

**Usage:**
```bash
# Dry run to see what would be changed
python scripts/migrate_pyqt5_to_pyqt6.py --dry-run

# Create backups and apply changes
python scripts/migrate_pyqt5_to_pyqt6.py --backup

# Apply changes without backups
python scripts/migrate_pyqt5_to_pyqt6.py
```

### 2. `update_dependencies.py`
Script to update dependencies to latest stable versions.

**Features:**
- Checks current vs latest versions of all dependencies
- Updates pyproject.toml with latest versions
- Checks Python version compatibility
- Monitors PyQt5 → PyQt6 migration status

**Usage:**
```bash
# Check current dependency status
python scripts/update_dependencies.py --check

# Update dependencies to latest versions
python scripts/update_dependencies.py --update

# Check Python compatibility
python scripts/update_dependencies.py --python-version

# Check PyQt migration status
python scripts/update_dependencies.py --pyqt-status

# Run all checks
python scripts/update_dependencies.py
```

### 3. `setup_test_environment.py`
Script to set up test environments for different Python and Qt versions.

**Features:**
- Creates conda environments with specific Python/Qt combinations
- Tests environment functionality
- Runs tests in different environments
- Manages environment cleanup

**Usage:**
```bash
# List available environments
python scripts/setup_test_environment.py --list

# Create test environment with Python 3.11 and PyQt6
python scripts/setup_test_environment.py --create-env --python-version 3.11 --qt-version 6

# Test an existing environment
python scripts/setup_test_environment.py --test-env mdaviz-test-py311-qt6

# Run tests in an environment
python scripts/setup_test_environment.py --run-tests mdaviz-test-py311-qt6

# Clean up an environment
python scripts/setup_test_environment.py --cleanup mdaviz-test-py311-qt5
```

### 4. `validate_migration.py`
Comprehensive validation script to test the migration.

**Features:**
- Checks all imports and dependencies
- Validates PyQt API compatibility
- Tests Python version compatibility
- Runs unit and GUI tests
- Performance benchmarking
- Generates detailed reports

**Usage:**
```bash
# Basic validation
python scripts/validate_migration.py

# Full validation including GUI tests
python scripts/validate_migration.py --full-test

# Validate specific versions
python scripts/validate_migration.py --pyqt-version 6 --python-version 3.12
```

## Migration Workflow

### Step 1: Preparation
```bash
# Check current status
python scripts/update_dependencies.py --check --pyqt-status

# Create test environment
python scripts/setup_test_environment.py --create-env --python-version 3.11 --qt-version 6
```

### Step 2: Migration
```bash
# Run migration (dry run first)
python scripts/migrate_pyqt5_to_pyqt6.py --dry-run

# Apply migration with backups
python scripts/migrate_pyqt5_to_pyqt6.py --backup

# Update dependencies
python scripts/update_dependencies.py --update
```

### Step 3: Testing
```bash
# Install updated package
pip install -e .

# Run validation
python scripts/validate_migration.py --full-test

# Test in different environments
python scripts/setup_test_environment.py --run-tests mdaviz-test-py311-qt6
```

### Step 4: Verification
```bash
# Run comprehensive tests
pytest src/tests -v

# Check for any remaining PyQt5 references
grep -r "PyQt5" src/

# Test GUI functionality manually
python -m mdaviz.app
```

## Environment Matrix

The following combinations should be tested:

| Python | PyQt | Status | Notes |
|--------|------|--------|-------|
| 3.10   | 5    | ✅     | Current baseline |
| 3.10   | 6    | 🔄     | Migration target |
| 3.11   | 5    | ✅     | Current baseline |
| 3.11   | 6    | 🔄     | Migration target |
| 3.12   | 5    | ✅     | Current baseline |
| 3.12   | 6    | 🔄     | Migration target |
| 3.13   | 6    | ⏳     | Future target |

## Key Migration Changes

### PyQt5 → PyQt6
1. **Import statements:**
   ```python
   # Before
   from PyQt5.QtCore import QObject, pyqtSignal
   
   # After
   from PyQt6.QtCore import QObject, pyqtSignal
   ```

2. **QDesktopWidget replacement:**
   ```python
   # Before
   from PyQt5.QtWidgets import QDesktopWidget
   screen = QDesktopWidget().screenGeometry()
   
   # After
   from PyQt6.QtWidgets import QApplication
   screen = QApplication.primaryScreen().geometry()
   ```

3. **Matplotlib backend:**
   ```python
   # Before
   from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
   
   # After
   from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
   ```

### Python 3.13 Compatibility
1. **xdrlib deprecation:** Already handled with fallback implementation
2. **Type annotations:** Using modern syntax (list[str] instead of List[str])
3. **Built-in types:** Using native types where possible

## Troubleshooting

### Common Issues

1. **Import errors after migration:**
   ```bash
   # Check for remaining PyQt5 references
   grep -r "PyQt5" src/
   
   # Re-run migration script
   python scripts/migrate_pyqt5_to_pyqt6.py
   ```

2. **GUI tests failing:**
   ```bash
   # Skip GUI tests in headless environment
   pytest src/tests -k "not gui and not qt_thread"
   ```

3. **Dependency conflicts:**
   ```bash
   # Clean environment and reinstall
   conda env remove -n mdaviz
   conda env create -f env.yml
   pip install -e .
   ```

4. **Performance issues:**
   ```bash
   # Run performance validation
   python scripts/validate_migration.py
   ```

### Rollback Procedure

If critical issues are discovered:

```bash
# Revert migration
git checkout main
git revert <migration-commit>

# Restore original dependencies
git checkout HEAD~1 -- pyproject.toml env.yml

# Reinstall original environment
conda env remove -n mdaviz
conda env create -f env.yml
pip install -e .
```

## Success Criteria

The migration is considered successful when:

- [ ] All unit tests pass with PyQt6
- [ ] All unit tests pass with Python 3.13 (when available)
- [ ] No PyQt5 imports remain in the codebase
- [ ] GUI functionality works correctly
- [ ] Performance is maintained or improved
- [ ] No new deprecation warnings
- [ ] CI/CD pipeline passes

## Support

For issues with the migration scripts:

1. Check the script help: `python scripts/script_name.py --help`
2. Review the migration plan: `MIGRATION_PLAN.md`
3. Run validation: `python scripts/validate_migration.py`
4. Check the main project documentation

## Contributing

When updating these scripts:

1. Follow the existing code style
2. Add comprehensive error handling
3. Include help text and examples
4. Test with different Python/Qt combinations
5. Update this README if needed 