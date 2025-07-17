# Test Improvement Plan for mdaviz

## Current Status (Updated: January 2025)

### Test Coverage
- **Current Coverage**: 46% (improved from 36%)
- **Tests**: 130 passing, 26 failed, 54 skipped, 5 errors
- **Total Tests**: 215

### Test Data Infrastructure
- **Real Test Data Available**: Comprehensive set of real MDA files in `src/tests/data/`
- **Test Folders**: 
  - `test_folder1/` - 12 MDA files with various naming patterns
  - `test_folder2/` - 16 MDA files 
  - `test_folder3/` - 50 MDA files with nested subfolders
  - `test_no_positioner/` - 28 ARPES MDA files (no positioner data)
- **File Types**: Real MDA files with actual data structures, not mock data

## Priority 1: Fix Failed Tests (26 tests)

### 1.1 Settings Mock Issues (High Priority)
**Problem**: Settings mock returns incorrect data types
**Files**: `test_mainwindow.py`, `test_gui_components.py`, `test_gui_integration.py`

**Solution**: Update settings mock to return appropriate values based on key:
```python
def mock_settings_get_key(key: str) -> str | int:
    """Return appropriate mock values based on settings key."""
    if key == "recentFolders":
        return "test_folder1,test_folder2"
    elif key == "windowGeometry":
        return "800x600+100+100"
    elif key == "windowState":
        return "normal"
    else:
        return "default_value"
```

### 1.2 Qt Widget Parent Issues (High Priority)
**Problem**: Qt widgets missing parent arguments
**Files**: Multiple test files

**Solution**: Add parent arguments to all Qt widget instantiations:
```python
# Before
widget = QWidget()

# After  
widget = QWidget(parent=main_window)
```

### 1.3 Import and Module Issues (Medium Priority)
**Problem**: Incorrect import names and missing modules
**Files**: `test_chartview.py`, `test_fit_manager.py`

**Solution**: Fix import statements and add missing dependencies

### 1.4 Cache Testing Issues (Medium Priority)
**Problem**: Cache tests using incorrect data types
**Files**: `test_data_cache.py`

**Solution**: Update cache tests to use proper data structures

## Priority 2: Leverage Real Test Data Infrastructure

### 2.1 Create Real Test Data Fixtures (High Priority)
**Goal**: Replace mock data with real MDA files from test data directory

**New Fixtures to Create**:
```python
@pytest.fixture
def test_data_path() -> Path:
    """Return path to test data directory."""
    return Path(__file__).parent / "data"

@pytest.fixture
def test_folder1_path(test_data_path: Path) -> Path:
    """Return path to test_folder1 with 12 MDA files."""
    return test_data_path / "test_folder1"

@pytest.fixture
def test_folder2_path(test_data_path: Path) -> Path:
    """Return path to test_folder2 with 16 MDA files."""
    return test_data_path / "test_folder2"

@pytest.fixture
def test_folder3_path(test_data_path: Path) -> Path:
    """Return path to test_folder3 with 50 MDA files and nested structure."""
    return test_data_path / "test_folder3"

@pytest.fixture
def test_no_positioner_path(test_data_path: Path) -> Path:
    """Return path to test_no_positioner with 28 ARPES files."""
    return test_data_path / "test_no_positioner"

@pytest.fixture
def sample_mda_files(test_folder1_path: Path) -> list[Path]:
    """Return list of real MDA files from test_folder1."""
    return list(test_folder1_path.glob("*.mda"))

@pytest.fixture
def nested_mda_files(test_folder3_path: Path) -> list[Path]:
    """Return list of MDA files including nested subfolders."""
    return list(test_folder3_path.rglob("*.mda"))
```

### 2.2 Update Existing Tests to Use Real Data (High Priority)
**Files to Update**:
- `test_mda_file.py` - Use real MDA files instead of mock data
- `test_data_cache.py` - Test with actual file loading
- `test_lazy_loading.py` - Use real folder structures
- `test_gui_integration.py` - Load real files in GUI tests

**Benefits**:
- Tests real file parsing and data structures
- Catches actual file format issues
- Tests performance with real data sizes
- Validates against known good data

### 2.3 Create Data-Driven Tests (Medium Priority)
**Goal**: Test with different file types and structures

**Test Categories**:
- **Standard MDA files**: `test_folder1/`, `test_folder2/`
- **Nested folder structure**: `test_folder3/` with subfolders
- **No positioner data**: `test_no_positioner/` ARPES files
- **Various naming patterns**: Different file prefixes and numbering

## Priority 3: Improve Test Coverage (Target: 70%+)

### 3.1 Core Module Coverage
**Target Modules**:
- `mda_file.py` - File loading and parsing
- `data_cache.py` - Caching and memory management  
- `lazy_folder_scanner.py` - Folder scanning
- `chartview.py` - Plotting and visualization
- `mainwindow.py` - Main application logic

### 3.2 Edge Cases and Error Handling
**Test Scenarios**:
- Corrupted MDA files
- Missing files and directories
- Permission errors
- Memory pressure scenarios
- Large file handling

### 3.3 Integration Testing
**Test Workflows**:
- Complete file loading workflow
- Folder navigation and selection
- Data visualization pipeline
- Settings persistence
- Error recovery

## Priority 4: Test Infrastructure Improvements

### 4.1 Performance Testing
**Goals**:
- Test with large numbers of files (use test_folder3)
- Measure memory usage during operations
- Test lazy loading performance
- Benchmark file loading times

### 4.2 CI/CD Integration
**Improvements**:
- Parallel test execution
- Coverage reporting
- Test result caching
- Automated test data validation

### 4.3 Test Documentation
**Add**:
- Test data documentation
- Test scenario descriptions
- Performance benchmarks
- Troubleshooting guide

## Implementation Timeline

### Week 1: Fix Failed Tests
- [ ] Fix settings mock issues
- [ ] Resolve Qt parent arguments
- [ ] Fix import and module issues
- [ ] Update cache tests

### Week 2: Real Data Integration
- [ ] Create test data fixtures
- [ ] Update core test files to use real data
- [ ] Create data-driven test framework
- [ ] Validate test data integrity

### Week 3: Coverage Improvement
- [ ] Add missing test cases
- [ ] Implement edge case testing
- [ ] Add integration test workflows
- [ ] Performance testing setup

### Week 4: Infrastructure and Documentation
- [ ] CI/CD improvements
- [ ] Test documentation
- [ ] Performance benchmarks
- [ ] Final validation and cleanup

## Success Metrics

### Quantitative Goals
- **Test Coverage**: 70%+ (from current 46%)
- **Failed Tests**: 0 (from current 26)
- **Skipped Tests**: <10 (from current 54)
- **Test Execution Time**: <5 minutes for full suite

### Qualitative Goals
- **Real Data Usage**: 90%+ of tests use real MDA files
- **Test Reliability**: Consistent test results across environments
- **Maintainability**: Clear test structure and documentation
- **Performance**: Tests complete within reasonable time limits

## Risk Mitigation

### Technical Risks
- **Large Test Data**: Monitor disk space and test execution time
- **File Dependencies**: Ensure test data is version controlled and validated
- **Environment Differences**: Use containerized testing environments

### Process Risks
- **Scope Creep**: Focus on core functionality first
- **Test Maintenance**: Document test data and update procedures
- **CI/CD Integration**: Gradual rollout of improvements

## Conclusion

This plan prioritizes leveraging the existing comprehensive test data infrastructure to create more robust and realistic tests. By using real MDA files instead of mock data, we can catch actual issues and improve confidence in the application's reliability. The focus on fixing failed tests first ensures a stable foundation for further improvements. 