# Logging System for mdaviz

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
**Default Behavior:**
By default, `mdaviz` logs at the WARNING level, showing only warnings, errors and critical messages (quiet mode).

### Command Line Options

You can control the logging level using the `--log` argument:

```bash
# Show only errors and critical messages
mdaviz --log error

# Show warnings, errors, critical messages and info (progress messages, file loading status, and important application events).
mdaviz --log info

# Show all messages including debug information
mdaviz --log debug
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

## Log Files

Log files are automatically created in `~/.mdaviz/logs/` with timestamps:  `mdaviz_20241201_143022.log` (format: YYYYMMDD_HHMMSS).
 Old log files (older than 1 day) are automatically cleaned up on startup.
