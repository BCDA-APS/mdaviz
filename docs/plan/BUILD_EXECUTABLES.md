# Building mdaviz Executables

This guide explains how to build standalone executables for the mdaviz application using different tools.

## Prerequisites

1. **Python Environment**: Ensure you have Python 3.10+ installed
2. **Dependencies**: Install the build dependencies:
   ```bash
   pip install -e ".[build]"
   ```

## Method 1: PyInstaller (Recommended)

PyInstaller is the most popular and reliable tool for creating Python executables.

### Basic Usage

```bash
# Simple build
pyinstaller --onefile --windowed --name mdaviz src/mdaviz/app.py

# Build with spec file (recommended)
pyinstaller mdaviz.spec
```

### Advanced Options

```bash
# Debug build with console
pyinstaller --onefile --name mdaviz --debug all src/mdaviz/app.py

# Build with custom icon
pyinstaller --onefile --windowed --name mdaviz --icon=path/to/icon.ico src/mdaviz/app.py

# Build for specific platform
pyinstaller --onefile --windowed --name mdaviz --target-arch=x86_64 src/mdaviz/app.py
```

### Troubleshooting

**Common Issues:**
1. **Missing modules**: Add to `hiddenimports` in spec file
2. **Missing data files**: Add to `datas` in spec file
3. **Large executable size**: Use `--exclude-module` to remove unused modules

**Debug Mode:**
```bash
# Run with debug output
pyinstaller --debug all mdaviz.spec
```

## Method 2: cx_Freeze

cx_Freeze is good for creating installers and distributions.

### Basic Usage

```bash
# Build executable
python setup_cx_freeze.py build

# Create Windows installer (Windows only)
python setup_cx_freeze.py bdist_msi
```

### Customization

Edit `setup_cx_freeze.py` to:
- Add/remove packages
- Include additional files
- Configure platform-specific options

## Method 3: Nuitka (Performance)

Nuitka compiles Python to C for better performance.

### Basic Usage

```bash
# Simple compilation
python -m nuitka --follow-imports --enable-plugin=pyqt5 --standalone src/mdaviz/app.py

# Optimized compilation
python -m nuitka --follow-imports --enable-plugin=pyqt5 --standalone --lto=yes src/mdaviz/app.py
```

### Advanced Options

```bash
# Include data files
python -m nuitka --follow-imports --enable-plugin=pyqt5 --standalone \
    --include-data-dir=src/mdaviz/resources=resources \
    --include-data-dir=src/mdaviz/synApps_mdalib=synApps_mdalib \
    src/mdaviz/app.py
```

## Platform-Specific Instructions

### Windows

**Requirements:**
- Visual Studio Build Tools (for some dependencies)
- Windows 10/11

**Build Commands:**
```bash
# PyInstaller
pyinstaller --onefile --windowed --name mdaviz src/mdaviz/app.py

# cx_Freeze
python setup_cx_freeze.py build
python setup_cx_freeze.py bdist_msi
```

**Notes:**
- Use `--windowed` flag to hide console window
- Consider code signing for distribution
- Test on clean Windows VM

### macOS

**Requirements:**
- Xcode Command Line Tools
- macOS 10.15+

**Build Commands:**
```bash
# PyInstaller
pyinstaller --onefile --windowed --name mdaviz src/mdaviz/app.py

# Nuitka
python -m nuitka --follow-imports --enable-plugin=pyqt5 --standalone src/mdaviz/app.py
```

**Notes:**
- May need to handle code signing
- Consider notarization for distribution
- Test on different macOS versions

### Linux

**Requirements:**
- GCC and development libraries
- X11 libraries

**Build Commands:**
```bash
# Install dependencies
sudo apt-get install libgl1-mesa-glx libglib2.0-0 libxcb-*

# PyInstaller
pyinstaller --onefile --windowed --name mdaviz src/mdaviz/app.py

# Nuitka
python -m nuitka --follow-imports --enable-plugin=pyqt5 --standalone src/mdaviz/app.py
```

**Notes:**
- Test on different Linux distributions
- Consider AppImage for distribution
- Handle library dependencies carefully

## Automated Builds

### GitHub Actions

The project includes automated builds via GitHub Actions:

1. **Trigger**: Push a tag starting with "v" (e.g., `v1.1.2`)
2. **Platforms**: Windows, Linux, macOS
3. **Output**: Executables uploaded as release assets

### Local Automation

Create a build script:

```bash
#!/bin/bash
# build_all.sh

set -e

echo "Building mdaviz executables..."

# Clean previous builds
rm -rf build dist

# Build for current platform
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "Building for Windows..."
    pyinstaller --onefile --windowed --name mdaviz src/mdaviz/app.py
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Building for macOS..."
    pyinstaller --onefile --windowed --name mdaviz src/mdaviz/app.py
else
    echo "Building for Linux..."
    pyinstaller --onefile --windowed --name mdaviz src/mdaviz/app.py
fi

echo "Build complete! Executable in dist/ directory."
```

## Distribution

### GitHub Releases

1. Create a tag: `git tag v1.1.2`
2. Push tag: `git push origin v1.1.2`
3. GitHub Actions will automatically build and create a release

### Package Managers

**Windows:**
- Chocolatey: `choco install mdaviz`
- Scoop: `scoop install mdaviz`

**macOS:**
- Homebrew: `brew install mdaviz`

**Linux:**
- AppImage: Download and run
- Snap: `snap install mdaviz`
- Flatpak: `flatpak install mdaviz`

### Direct Distribution

1. **Host executables** on project website
2. **Provide checksums** for verification
3. **Include installation instructions**
4. **Offer portable versions**

## Testing Executables

### Basic Testing

```bash
# Test executable
./dist/mdaviz

# Test with sample data
./dist/mdaviz --log debug
```

### Comprehensive Testing

1. **Functionality**: Test all features work
2. **Performance**: Check startup time and memory usage
3. **Compatibility**: Test on different OS versions
4. **Dependencies**: Verify all required files included

### Test Matrix

| Platform | Python | Qt | Status |
|----------|--------|----|--------|
| Windows 10 | 3.11 | 5.15 | ✅ |
| Windows 11 | 3.11 | 5.15 | ✅ |
| macOS 12 | 3.11 | 5.15 | ✅ |
| macOS 13 | 3.11 | 5.15 | ✅ |
| Ubuntu 20.04 | 3.11 | 5.15 | ✅ |
| Ubuntu 22.04 | 3.11 | 5.15 | ✅ |

## Troubleshooting

### Common Issues

1. **"Module not found" errors**
   - Add missing modules to `hiddenimports`
   - Check import paths

2. **Missing data files**
   - Add to `datas` in spec file
   - Verify file paths

3. **Large executable size**
   - Use `--exclude-module` to remove unused modules
   - Consider using `--onedir` instead of `--onefile`

4. **Runtime errors**
   - Test with `--debug all` flag
   - Check console output for errors

### Performance Optimization

1. **Reduce size**:
   ```bash
   pyinstaller --onefile --windowed --strip --upx-dir=/path/to/upx src/mdaviz/app.py
   ```

2. **Improve startup time**:
   ```bash
   pyinstaller --onedir --windowed src/mdaviz/app.py
   ```

3. **Memory optimization**:
   - Use lazy loading
   - Implement proper cleanup

## Best Practices

1. **Always test** on clean systems
2. **Version executables** properly
3. **Document dependencies** and requirements
4. **Provide fallback** installation methods
5. **Monitor file sizes** and performance
6. **Update regularly** with security patches

## Support

For issues with executable builds:

1. Check the [troubleshooting section](#troubleshooting)
2. Review PyInstaller/cx_Freeze/Nuitka documentation
3. Open an issue on GitHub with:
   - Platform and version information
   - Build command used
   - Error messages
   - Expected vs actual behavior
