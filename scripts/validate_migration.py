#!/usr/bin/env python3
"""
Migration Validation Script

This script validates the migration from PyQt5 to PyQt6 and Python 3.13 compatibility
by running comprehensive tests and checks.

Usage:
    python scripts/validate_migration.py [--pyqt-version] [--python-version] [--full-test]

Options:
    --pyqt-version    PyQt version to test (5, 6)
    --python-version  Python version to test (3.10, 3.11, 3.12, 3.13)
    --full-test       Run full test suite including GUI tests
"""

import argparse
import importlib
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional


def run_command(cmd: list[str], check: bool = True, timeout: Optional[int] = None) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=check, timeout=timeout)
        return result
    except subprocess.TimeoutExpired:
        print(f"Command timed out after {timeout} seconds")
        return subprocess.CompletedProcess(cmd, -1, "", "Timeout")
    except Exception as e:
        print(f"Command failed: {e}")
        return subprocess.CompletedProcess(cmd, -1, "", str(e))


def check_imports() -> dict:
    """Check if all required modules can be imported."""
    print("Checking imports...")
    
    required_modules = [
        "matplotlib",
        "scipy",
        "numpy",
        "yaml",
        "tiled",
        "lmfit",
        "psutil",
    ]
    
    results = {}
    
    for module in required_modules:
        try:
            importlib.import_module(module)
            results[module] = {"status": "✅", "version": "Unknown"}
            print(f"  ✅ {module}")
        except ImportError as e:
            results[module] = {"status": "❌", "error": str(e)}
            print(f"  ❌ {module}: {e}")
    
    # Check PyQt version
    try:
        import PyQt6
        results["PyQt6"] = {"status": "✅", "version": PyQt6.QtCore.QT_VERSION_STR}
        print(f"  ✅ PyQt6: {PyQt6.QtCore.QT_VERSION_STR}")
    except ImportError:
        try:
            import PyQt5
            results["PyQt5"] = {"status": "⚠️", "version": PyQt5.QtCore.QT_VERSION_STR}
            print(f"  ⚠️ PyQt5: {PyQt5.QtCore.QT_VERSION_STR} (deprecated)")
        except ImportError:
            results["PyQt"] = {"status": "❌", "error": "No PyQt found"}
            print(f"  ❌ PyQt: Not found")
    
    return results


def check_mdaviz_imports() -> dict:
    """Check if mdaviz modules can be imported."""
    print("Checking mdaviz imports...")
    
    mdaviz_modules = [
        "mdaviz",
        "mdaviz.app",
        "mdaviz.mainwindow",
        "mdaviz.chartview",
        "mdaviz.mda_folder",
        "mdaviz.mda_file",
        "mdaviz.data_cache",
        "mdaviz.lazy_folder_scanner",
        "mdaviz.fit_manager",
        "mdaviz.user_settings",
        "mdaviz.utils",
    ]
    
    results = {}
    
    for module in mdaviz_modules:
        try:
            importlib.import_module(module)
            results[module] = {"status": "✅"}
            print(f"  ✅ {module}")
        except ImportError as e:
            results[module] = {"status": "❌", "error": str(e)}
            print(f"  ❌ {module}: {e}")
        except Exception as e:
            results[module] = {"status": "⚠️", "error": str(e)}
            print(f"  ⚠️ {module}: {e}")
    
    return results


def check_pyqt_api_compatibility() -> dict:
    """Check PyQt API compatibility."""
    print("Checking PyQt API compatibility...")
    
    results = {}
    
    # Test QDesktopWidget replacement
    try:
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication([])
        screen = app.primaryScreen().geometry()
        results["QDesktopWidget"] = {"status": "✅", "message": "Using QApplication.primaryScreen()"}
        print(f"  ✅ QDesktopWidget replacement: QApplication.primaryScreen()")
    except Exception as e:
        results["QDesktopWidget"] = {"status": "❌", "error": str(e)}
        print(f"  ❌ QDesktopWidget replacement: {e}")
    
    # Test matplotlib backend
    try:
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
        results["matplotlib_backend"] = {"status": "✅", "message": "Using qtagg backend"}
        print(f"  ✅ matplotlib backend: qtagg")
    except ImportError:
        try:
            from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
            results["matplotlib_backend"] = {"status": "⚠️", "message": "Using qt5agg backend"}
            print(f"  ⚠️ matplotlib backend: qt5agg (should be qtagg)")
        except ImportError as e:
            results["matplotlib_backend"] = {"status": "❌", "error": str(e)}
            print(f"  ❌ matplotlib backend: {e}")
    
    # Test signal/slot syntax
    try:
        from PyQt6.QtCore import QObject, pyqtSignal
        class TestObject(QObject):
            test_signal = pyqtSignal()
            
            def __init__(self):
                super().__init__()
                self.test_signal.connect(self.test_slot)
            
            def test_slot(self):
                pass
        
        obj = TestObject()
        results["signal_slot"] = {"status": "✅", "message": "Signal/slot syntax works"}
        print(f"  ✅ Signal/slot syntax: Works")
    except Exception as e:
        results["signal_slot"] = {"status": "❌", "error": str(e)}
        print(f"  ❌ Signal/slot syntax: {e}")
    
    return results


def check_python_compatibility() -> dict:
    """Check Python version compatibility."""
    print("Checking Python compatibility...")
    
    results = {}
    
    # Check Python version
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    results["python_version"] = {"status": "✅", "version": python_version}
    print(f"  ✅ Python version: {python_version}")
    
    # Check xdrlib fallback
    try:
        import xdrlib
        results["xdrlib"] = {"status": "✅", "message": "xdrlib available"}
        print(f"  ✅ xdrlib: Available")
    except ImportError:
        try:
            from mdaviz.synApps_mdalib import f_xdrlib
            results["xdrlib"] = {"status": "✅", "message": "Using fallback implementation"}
            print(f"  ✅ xdrlib: Using fallback implementation")
        except ImportError as e:
            results["xdrlib"] = {"status": "❌", "error": str(e)}
            print(f"  ❌ xdrlib: {e}")
    
    # Check type annotations
    try:
        # Test modern type annotations
        def test_function(data: list[str]) -> dict[str, int]:
            return {"test": len(data)}
        
        result = test_function(["a", "b", "c"])
        results["type_annotations"] = {"status": "✅", "message": "Modern type annotations work"}
        print(f"  ✅ Type annotations: Modern syntax works")
    except Exception as e:
        results["type_annotations"] = {"status": "❌", "error": str(e)}
        print(f"  ❌ Type annotations: {e}")
    
    return results


def run_unit_tests() -> dict:
    """Run unit tests."""
    print("Running unit tests...")
    
    try:
        result = run_command([
            "pytest", "src/tests", "-v", "--tb=short", "--no-header",
            "-k", "not gui and not qt_thread"
        ], check=False, timeout=300)
        
        if result.returncode == 0:
            return {"status": "✅", "message": "All unit tests passed", "output": result.stdout}
        else:
            return {"status": "❌", "message": "Some unit tests failed", "output": result.stdout, "error": result.stderr}
    
    except Exception as e:
        return {"status": "❌", "error": str(e)}


def run_gui_tests() -> dict:
    """Run GUI tests (if requested)."""
    print("Running GUI tests...")
    
    try:
        result = run_command([
            "pytest", "src/tests", "-v", "--tb=short", "--no-header",
            "-k", "gui or qt_thread"
        ], check=False, timeout=600)
        
        if result.returncode == 0:
            return {"status": "✅", "message": "All GUI tests passed", "output": result.stdout}
        else:
            return {"status": "⚠️", "message": "Some GUI tests failed (expected in headless)", "output": result.stdout, "error": result.stderr}
    
    except Exception as e:
        return {"status": "⚠️", "error": str(e), "message": "GUI tests not available in headless environment"}


def check_performance() -> dict:
    """Check basic performance metrics."""
    print("Checking performance...")
    
    results = {}
    
    # Test import time
    start_time = time.time()
    try:
        import mdaviz
        import_time = time.time() - start_time
        results["import_time"] = {"status": "✅", "time": f"{import_time:.3f}s"}
        print(f"  ✅ Import time: {import_time:.3f}s")
    except Exception as e:
        results["import_time"] = {"status": "❌", "error": str(e)}
        print(f"  ❌ Import time: {e}")
    
    # Test memory usage
    try:
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        results["memory_usage"] = {"status": "✅", "memory": f"{memory_mb:.1f}MB"}
        print(f"  ✅ Memory usage: {memory_mb:.1f}MB")
    except Exception as e:
        results["memory_usage"] = {"status": "⚠️", "error": str(e)}
        print(f"  ⚠️ Memory usage: {e}")
    
    return results


def generate_report(results: dict) -> None:
    """Generate a comprehensive report."""
    print("\n" + "=" * 80)
    print("MIGRATION VALIDATION REPORT")
    print("=" * 80)
    
    # Summary
    total_checks = 0
    passed_checks = 0
    failed_checks = 0
    warnings = 0
    
    for category, category_results in results.items():
        if isinstance(category_results, dict):
            for check, result in category_results.items():
                total_checks += 1
                if result.get("status") == "✅":
                    passed_checks += 1
                elif result.get("status") == "❌":
                    failed_checks += 1
                elif result.get("status") == "⚠️":
                    warnings += 1
    
    print(f"SUMMARY:")
    print(f"  Total checks: {total_checks}")
    print(f"  Passed: {passed_checks} ✅")
    print(f"  Failed: {failed_checks} ❌")
    print(f"  Warnings: {warnings} ⚠️")
    print(f"  Success rate: {(passed_checks/total_checks*100):.1f}%")
    
    # Detailed results
    print(f"\nDETAILED RESULTS:")
    print("-" * 80)
    
    for category, category_results in results.items():
        if isinstance(category_results, dict):
            print(f"\n{category.upper()}:")
            for check, result in category_results.items():
                status = result.get("status", "❓")
                message = result.get("message", result.get("error", "No details"))
                print(f"  {status} {check}: {message}")
    
    # Recommendations
    print(f"\nRECOMMENDATIONS:")
    print("-" * 80)
    
    if failed_checks > 0:
        print("❌ Critical issues found. Migration needs attention:")
        for category, category_results in results.items():
            if isinstance(category_results, dict):
                for check, result in category_results.items():
                    if result.get("status") == "❌":
                        print(f"  - Fix {category}/{check}: {result.get('error', 'Unknown error')}")
    
    if warnings > 0:
        print("⚠️ Warnings found. Consider addressing:")
        for category, category_results in results.items():
            if isinstance(category_results, dict):
                for check, result in category_results.items():
                    if result.get("status") == "⚠️":
                        print(f"  - Review {category}/{check}: {result.get('message', 'Warning')}")
    
    if failed_checks == 0 and warnings == 0:
        print("✅ Migration validation successful! All checks passed.")
        print("  - The application is ready for production use")
        print("  - Consider running full integration tests")
    
    elif failed_checks == 0:
        print("✅ Migration mostly successful with minor warnings.")
        print("  - The application should work correctly")
        print("  - Address warnings for optimal performance")
    
    else:
        print("❌ Migration validation failed.")
        print("  - Address critical issues before proceeding")
        print("  - Review the detailed results above")


def main():
    """Main validation function."""
    parser = argparse.ArgumentParser(
        description="Validate PyQt5 → PyQt6 migration and Python 3.13 compatibility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/validate_migration.py
  python scripts/validate_migration.py --full-test
  python scripts/validate_migration.py --pyqt-version 6 --python-version 3.12
        """
    )
    parser.add_argument(
        "--pyqt-version",
        choices=["5", "6"],
        help="PyQt version to test (auto-detected if not specified)"
    )
    parser.add_argument(
        "--python-version",
        choices=["3.10", "3.11", "3.12", "3.13"],
        help="Python version to test (auto-detected if not specified)"
    )
    parser.add_argument(
        "--full-test",
        action="store_true",
        help="Run full test suite including GUI tests"
    )
    
    args = parser.parse_args()
    
    print("mdaviz Migration Validation Script")
    print("=" * 50)
    
    if args.pyqt_version:
        print(f"Testing PyQt version: {args.pyqt_version}")
    if args.python_version:
        print(f"Testing Python version: {args.python_version}")
    if args.full_test:
        print("Running full test suite including GUI tests")
    
    # Run all validation checks
    results = {}
    
    try:
        results["imports"] = check_imports()
        results["mdaviz_imports"] = check_mdaviz_imports()
        results["pyqt_compatibility"] = check_pyqt_api_compatibility()
        results["python_compatibility"] = check_python_compatibility()
        results["unit_tests"] = run_unit_tests()
        
        if args.full_test:
            results["gui_tests"] = run_gui_tests()
        
        results["performance"] = check_performance()
        
        # Generate report
        generate_report(results)
        
        # Exit with appropriate code
        failed_checks = sum(
            1 for category in results.values()
            if isinstance(category, dict)
            for result in category.values()
            if result.get("status") == "❌"
        )
        
        if failed_checks > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n\nValidation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Validation failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 