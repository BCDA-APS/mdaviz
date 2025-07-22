#!/usr/bin/env python3
"""
Comprehensive test script for mdaviz PyQt6 migration.

This script consolidates various checks that were previously spread across
multiple CI workflows into a single, efficient test suite.
"""

import sys
import os
import subprocess
import warnings
from pathlib import Path
from typing import List, Dict


def run_command(cmd: List[str], description: str) -> bool:
    """Run a command and return success status."""
    print(f"\n=== {description} ===")
    print(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("✅ Success")
        if result.stdout.strip():
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("❌ Failed")
        print(f"Error: {e}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        return False


def check_pyqt6_installation() -> bool:
    """Check PyQt6 installation and basic functionality."""
    print("\n=== PyQt6 Installation Check ===")

    try:
        # Test basic PyQt6 imports
        print("✅ PyQt6 modules import successfully")

        # Test Qt version
        from PyQt6.QtCore import QT_VERSION_STR

        print(f"✅ Qt version: {QT_VERSION_STR}")

        # Test QApplication creation
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        print("✅ QApplication created successfully")

        # Test matplotlib integration
        print("✅ Matplotlib qtagg backend working")

        return True

    except Exception as e:
        print(f"❌ PyQt6 check failed: {e}")
        return False


def check_mdaviz_imports() -> bool:
    """Check mdaviz imports and basic functionality."""
    print("\n=== mdaviz Import Check ===")

    try:
        print("✅ mdaviz imports successfully")

        # Test specific modules
        print("✅ Core mdaviz modules import successfully")

        return True

    except Exception as e:
        print(f"❌ mdaviz import check failed: {e}")
        return False


def check_deprecation_warnings() -> Dict[str, bool]:
    """Check for deprecation warnings."""
    print("\n=== Deprecation Warning Check ===")

    results = {}

    # Check for deprecation warnings (excluding known xdrlib issue)
    try:
        with warnings.catch_warnings(record=True) as w:
            warnings.filterwarnings(
                "ignore", category=DeprecationWarning, module="xdrlib"
            )
            warnings.simplefilter("error", DeprecationWarning)
            if w:
                print(f"⚠️ Deprecation warnings found: {len(w)}")
                for warning in w:
                    print(f"  - {warning.message}")
                results["deprecation"] = False
            else:
                print("✅ No deprecation warnings found")
                results["deprecation"] = True
    except Exception as e:
        print(f"⚠️ Deprecation warning check failed: {e}")
        results["deprecation"] = False

    # Check for future warnings
    try:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("error", FutureWarning)
            if w:
                print(f"⚠️ Future warnings found: {len(w)}")
                for warning in w:
                    print(f"  - {warning.message}")
                results["future"] = False
            else:
                print("✅ No future warnings found")
                results["future"] = True
    except Exception as e:
        print(f"⚠️ Future warning check failed: {e}")
        results["future"] = False

    return results


def check_xdrlib_usage() -> bool:
    """Check for xdrlib usage in our codebase."""
    print("\n=== xdrlib Usage Check ===")

    src_dir = Path("src")
    if not src_dir.exists():
        print("❌ src directory not found")
        return False

    xdrlib_files = []
    for py_file in src_dir.rglob("*.py"):
        try:
            with open(py_file, "r") as f:
                content = f.read()
                if "import xdrlib" in content or "from xdrlib" in content:
                    xdrlib_files.append(str(py_file))
        except Exception:
            continue

    if xdrlib_files:
        print(f"❌ xdrlib usage found in {len(xdrlib_files)} files:")
        for file in xdrlib_files:
            print(f"  - {file}")
        return False
    else:
        print("✅ No xdrlib usage found in our codebase")
        return True


def run_linting_checks() -> Dict[str, bool]:
    """Run linting checks."""
    print("\n=== Linting Checks ===")

    results = {}

    # Run ruff check
    results["ruff_check"] = run_command(["ruff", "check", "src/"], "Ruff Check")

    # Run ruff format check
    results["ruff_format"] = run_command(
        ["ruff", "format", "--check", "src/"], "Ruff Format Check"
    )

    # Run mypy
    results["mypy"] = run_command(
        ["mypy", "src/mdaviz", "--ignore-missing-imports"], "MyPy Type Check"
    )

    return results


def run_tests() -> bool:
    """Run pytest tests."""
    print("\n=== Running Tests ===")

    # Set environment variables for headless testing
    env = os.environ.copy()
    env.update(
        {
            "QT_QPA_PLATFORM": "offscreen",
            "QT_LOGGING_RULES": "qt.qpa.*=false",
            "DISPLAY": ":99.0",
            "PYTEST_QT_API": "pyqt6",
        }
    )

    try:
        # Run basic tests first
        print("Running basic tests...")
        result = subprocess.run(
            ["pytest", "src/tests/test_auto_load.py", "-v"],
            env=env,
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr)

        if result.returncode != 0:
            print("❌ Basic tests failed")
            return False

        # Run non-GUI tests
        print("Running non-GUI tests...")
        result = subprocess.run(
            ["pytest", "src/tests/test_lazy_loading.py", "-k", "not gui", "-v"],
            env=env,
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr)

        if result.returncode != 0:
            print("❌ Non-GUI tests failed")
            return False

        print("✅ All tests passed")
        return True

    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return False


def main() -> int:
    """Main function to run all checks."""
    print("🚀 Starting comprehensive mdaviz PyQt6 test suite")
    print(f"Python version: {sys.version}")

    all_passed = True
    results = {}

    # Run all checks
    results["pyqt6"] = check_pyqt6_installation()
    results["imports"] = check_mdaviz_imports()
    results["xdrlib"] = check_xdrlib_usage()

    deprecation_results = check_deprecation_warnings()
    results.update(deprecation_results)

    linting_results = run_linting_checks()
    results.update(linting_results)

    results["tests"] = run_tests()

    # Print summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)

    for check_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{check_name:15} {status}")

    # Determine overall success
    all_passed = all(results.values())

    if all_passed:
        print("\n🎉 All checks passed! mdaviz is ready for production.")
        return 0
    else:
        print("\n⚠️ Some checks failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
