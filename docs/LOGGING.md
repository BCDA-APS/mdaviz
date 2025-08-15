# Logging System for mdaviz

This document explains how to use the new logging system in mdaviz, which replaces the previous debug print statements with a proper, configurable logging framework.

## Overview

The logging system provides:
- **Configurable log levels** (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **File and console output** with different formatting
- **Automatic log file rotation** with timestamps
- **Easy enable/disable** without code changes
- **Better performance** (debug statements can be compiled out)

## Quick Start

### Basic Usage

```python
from mdaviz.logger import get_logger

# Get a logger for your module
logger = get_logger('your_module_name')

# Use different log levels
logger.debug("Detailed information for debugging")
logger.info("General information about program execution")
logger.warning("Warning messages for potentially problematic situations")
logger.error("Error messages for serious problems")
logger.critical("Critical messages for fatal errors")
```

### Environment Variables

You can control logging behavior using environment variables:

```bash
# Enable debug mode (shows all debug messages)
export MDAVIZ_DEBUG=1

# Set specific log level
export MDAVIZ_LOG_LEVEL=DEBUG  # or INFO, WARNING, ERROR, CRITICAL

# Run the application
python -m mdaviz
```

### Programmatic Control

```python
from mdaviz.logger import enable_debug_mode, disable_debug_mode, set_log_level

# Enable debug mode
enable_debug_mode()

# Disable debug mode (sets to INFO level)
disable_debug_mode()

# Set specific log level
set_log_level('WARNING')
```

## Log Files

Log files are automatically created in `~/.mdaviz/logs/` with timestamps:
- `mdaviz_20241201_143022.log` (format: YYYYMMDD_HHMMSS)

### Managing Log Files

```python
from mdaviz.logging_config import list_log_files, clear_old_logs

# List all log files
log_files = list_log_files()
for log_file in log_files:
    print(log_file)

# Clear logs older than 7 days
clear_old_logs(keep_days=7)
```

## Converting Existing Debug Prints

If you have existing debug print statements, you can convert them using the provided script:

```bash
# Generate a conversion report
python scripts/convert_debug_to_logger.py src/

# Run the auto-generated conversion script
python convert_debug_prints.py
```

### Manual Conversion Pattern

Replace:
```python
print("DEBUG: Some debug message")
print(f"DEBUG: Variable value: {variable}")
```

With:
```python
logger.debug("Some debug message")
logger.debug(f"Variable value: {variable}")
```

## Configuration

### Log Format

**Console output** (INFO level and above):
```
INFO - mdaviz.app - Starting mdaviz application
WARNING - mdaviz.mda_file_viz - No current tableview found
```

**File output** (DEBUG level and above):
```
2024-12-01 14:30:22,345 - mdaviz.mda_file_viz - DEBUG - connectToFileTabChanges:140 - Starting connection attempt
2024-12-01 14:30:22,346 - mdaviz.mda_file_viz - DEBUG - connectToFileTabChanges:144 - Initial parent: <class 'mdaviz.mainwindow.MainWindow'>
```

### Log Levels

- **DEBUG**: Detailed information for debugging
- **INFO**: General information about program execution
- **WARNING**: Warning messages for potentially problematic situations
- **ERROR**: Error messages for serious problems
- **CRITICAL**: Critical messages for fatal errors

## Best Practices

1. **Use appropriate log levels**:
   - DEBUG: Detailed debugging information
   - INFO: General program flow
   - WARNING: Unexpected but handled situations
   - ERROR: Errors that don't stop execution
   - CRITICAL: Fatal errors

2. **Include context in messages**:
   ```python
   # Good
   logger.debug(f"Processing file: {file_path}")
   logger.error(f"Failed to load data from {file_path}: {e}")
   
   # Avoid
   logger.debug("Processing file")
   logger.error("Failed to load data")
   ```

3. **Use structured logging for complex data**:
   ```python
   logger.debug(f"Selection changed - X: {x_index}, Y: {y_indices}, I0: {i0_index}")
   ```

4. **Don't log sensitive information**:
   ```python
   # Avoid logging passwords, API keys, etc.
   logger.debug(f"API key: {api_key}")  # BAD
   logger.debug("API authentication successful")  # GOOD
   ```

## Migration from Print Statements

The logging system is designed to be a drop-in replacement for debug print statements. The main benefits are:

1. **Configurable**: Enable/disable debug output without code changes
2. **Structured**: Consistent formatting with timestamps and module names
3. **Persistent**: Log files for later analysis
4. **Performance**: Debug statements can be compiled out in production

## Troubleshooting

### Logs not appearing
- Check that the log level is set appropriately
- Verify that the log directory exists and is writable
- Ensure the logger is properly imported and initialized

### Too many log messages
- Increase the log level (e.g., from DEBUG to INFO)
- Use environment variables to control logging at runtime

### Log files too large
- Use `clear_old_logs()` to remove old log files
- Consider implementing log rotation for long-running applications 