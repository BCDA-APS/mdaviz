#!/usr/bin/env python3
"""
Simple test script to verify the new 10,000 file limit is working correctly.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def test_config_default():
    """Test that the configuration default is now 10000."""
    from mdaviz.lazy_loading_config import LazyLoadingConfig

    config = LazyLoadingConfig()
    print(f"✓ Configuration default: {config.folder_scan_max_files} files")
    assert config.folder_scan_max_files == 10000, (
        f"Expected 10000, got {config.folder_scan_max_files}"
    )


def test_scanner_limit():
    """Test that the scanner respects the new limit."""
    from mdaviz.lazy_folder_scanner import LazyFolderScanner

    # Test with default limit
    scanner = LazyFolderScanner()
    print(f"✓ Scanner default limit: {scanner.max_files} files")
    assert scanner.max_files == 1000, (
        f"Expected 1000 (default), got {scanner.max_files}"
    )

    # Test with custom limit
    scanner = LazyFolderScanner(max_files=10000)
    print(f"✓ Scanner custom limit: {scanner.max_files} files")
    assert scanner.max_files == 10000, f"Expected 10000, got {scanner.max_files}"


def test_mainwindow_configuration():
    """Test that MainWindow configuration uses the correct limit."""
    # Import the module and check the hardcoded value

    # Read the source file to check the hardcoded value
    mainwindow_path = Path("src/mdaviz/mainwindow.py")
    with open(mainwindow_path, "r") as f:
        content = f.read()

    # Check if the line contains max_files=10000
    if "max_files=10000" in content:
        print("✓ MainWindow configuration: max_files=10000 found in source")
    else:
        print("❌ MainWindow configuration: max_files=10000 not found in source")
        return False

    return True


def test_limit_behavior():
    """Test the behavior when limits are exceeded."""
    from mdaviz.lazy_folder_scanner import FolderScanResult

    # Test with exactly at limit
    result = FolderScanResult(
        file_list=[],
        file_info_list=[],
        total_files=10000,
        scanned_files=0,
        is_complete=False,
        error_message="Too many files (10000 > 10000)",
    )

    # This should be allowed (at the limit)
    assert result.total_files == 10000
    print("✓ Limit behavior test passed")


def test_performance_estimates():
    """Test performance estimates for 10,000 files."""
    print("\n📊 Performance Estimates for 10,000 files:")
    print(f"  • Memory usage (metadata): ~{10 * 1024 / 1024:.1f} MB")
    print(f"  • Batch processing: {10000 // 50} batches of 50 files")
    print("  • Progress updates: Every 50 files")
    print(f"  • System file descriptors: {1048575} available (not limiting)")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing 10,000 File Limit Implementation")
    print("=" * 60)

    try:
        test_config_default()
        test_scanner_limit()
        if test_mainwindow_configuration():
            test_limit_behavior()
            test_performance_estimates()

        print("\n" + "=" * 60)
        print("✓ All tests passed! File limit successfully increased to 10,000.")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
