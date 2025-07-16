#!/usr/bin/env python3
"""
Test Environment Setup Script

This script helps set up test environments for different Python and Qt versions
to test the migration from PyQt5 to PyQt6 and Python 3.13 compatibility.

Usage:
    python scripts/setup_test_environment.py [--python-version] [--qt-version] [--create-env]

Options:
    --python-version  Python version to test (3.10, 3.11, 3.12, 3.13)
    --qt-version      Qt version to test (5, 6)
    --create-env      Create a new conda environment
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Optional


def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, check=check)
    return result


def check_conda_available() -> bool:
    """Check if conda is available."""
    try:
        run_command(["conda", "--version"], check=False)
        return True
    except FileNotFoundError:
        return False


def create_test_environment(python_version: str, qt_version: str) -> str:
    """Create a test environment with specified Python and Qt versions."""
    env_name = f"mdaviz-test-py{python_version}-qt{qt_version}"
    
    print(f"Creating test environment: {env_name}")
    
    # Create environment with Python version
    run_command([
        "conda", "create", "-n", env_name, 
        f"python={python_version}", "-y"
    ])
    
    # Install Qt dependencies
    if qt_version == "5":
        run_command([
            "conda", "run", "-n", env_name, "conda", "install",
            "pyqt=5", "qt=5", "-c", "conda-forge", "-y"
        ])
    else:  # qt_version == "6"
        run_command([
            "conda", "run", "-n", env_name, "conda", "install",
            "pyqt=6", "qt=6", "-c", "conda-forge", "-y"
        ])
    
    # Install other dependencies
    run_command([
        "conda", "run", "-n", env_name, "conda", "install",
        "matplotlib", "scipy", "numpy", "pyyaml", "-c", "conda-forge", "-y"
    ])
    
    # Install development dependencies
    run_command([
        "conda", "run", "-n", env_name, "pip", "install",
        "pytest", "pytest-cov", "pytest-qt", "ruff", "mypy", "pre-commit"
    ])
    
    return env_name


def test_environment(env_name: str) -> bool:
    """Test the environment by running basic checks."""
    print(f"Testing environment: {env_name}")
    
    try:
        # Test Python version
        result = run_command([
            "conda", "run", "-n", env_name, "python", "--version"
        ])
        print(f"Python: {result.stdout.strip()}")
        
        # Test Qt version
        result = run_command([
            "conda", "run", "-n", env_name, "python", "-c",
            "from PyQt6.QtCore import QT_VERSION_STR; print(f'Qt: {QT_VERSION_STR}')"
        ], check=False)
        
        if result.returncode != 0:
            # Try PyQt5
            result = run_command([
                "conda", "run", "-n", env_name, "python", "-c",
                "from PyQt5.QtCore import QT_VERSION_STR; print(f'Qt: {QT_VERSION_STR}')"
            ])
        
        print(f"Qt: {result.stdout.strip()}")
        
        # Test basic imports
        test_imports = [
            "import matplotlib",
            "import scipy",
            "import numpy",
            "import yaml",
            "import pytest",
        ]
        
        for import_stmt in test_imports:
            result = run_command([
                "conda", "run", "-n", env_name, "python", "-c", import_stmt
            ])
            print(f"✅ {import_stmt}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Test failed: {e}")
        return False


def run_tests(env_name: str) -> bool:
    """Run the test suite in the specified environment."""
    print(f"Running tests in environment: {env_name}")
    
    try:
        # Install the package in development mode
        run_command([
            "conda", "run", "-n", env_name, "pip", "install", "-e", "."
        ])
        
        # Run tests
        result = run_command([
            "conda", "run", "-n", env_name, "pytest", "src/tests", "-v", "--tb=short"
        ], check=False)
        
        if result.returncode == 0:
            print("✅ All tests passed!")
            return True
        else:
            print(f"❌ Some tests failed. Return code: {result.returncode}")
            print("Test output:")
            print(result.stdout)
            print("Test errors:")
            print(result.stderr)
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Test execution failed: {e}")
        return False


def list_environments() -> None:
    """List all available conda environments."""
    print("Available conda environments:")
    print("-" * 40)
    
    try:
        result = run_command(["conda", "env", "list"])
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error listing environments: {e}")


def cleanup_environment(env_name: str) -> None:
    """Remove a test environment."""
    print(f"Removing environment: {env_name}")
    
    try:
        run_command(["conda", "env", "remove", "-n", env_name, "-y"])
        print(f"✅ Environment {env_name} removed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to remove environment: {e}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Set up test environments for PyQt5/PyQt6 migration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/setup_test_environment.py --list
  python scripts/setup_test_environment.py --create-env --python-version 3.11 --qt-version 5
  python scripts/setup_test_environment.py --create-env --python-version 3.12 --qt-version 6
  python scripts/setup_test_environment.py --test-env mdaviz-test-py311-qt5
  python scripts/setup_test_environment.py --run-tests mdaviz-test-py312-qt6
  python scripts/setup_test_environment.py --cleanup mdaviz-test-py311-qt5
        """
    )
    parser.add_argument(
        "--python-version",
        choices=["3.10", "3.11", "3.12", "3.13"],
        default="3.11",
        help="Python version to test (default: 3.11)"
    )
    parser.add_argument(
        "--qt-version",
        choices=["5", "6"],
        default="6",
        help="Qt version to test (default: 6)"
    )
    parser.add_argument(
        "--create-env",
        action="store_true",
        help="Create a new conda environment"
    )
    parser.add_argument(
        "--test-env",
        type=str,
        help="Test an existing environment"
    )
    parser.add_argument(
        "--run-tests",
        type=str,
        help="Run tests in an existing environment"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all conda environments"
    )
    parser.add_argument(
        "--cleanup",
        type=str,
        help="Remove a test environment"
    )
    
    args = parser.parse_args()
    
    print("mdaviz Test Environment Setup Script")
    print("=" * 50)
    
    # Check if conda is available
    if not check_conda_available():
        print("❌ Error: conda is not available")
        print("Please install conda or miniconda first")
        sys.exit(1)
    
    try:
        if args.list:
            list_environments()
            return
        
        if args.cleanup:
            cleanup_environment(args.cleanup)
            return
        
        if args.create_env:
            env_name = create_test_environment(args.python_version, args.qt_version)
            print(f"\n✅ Environment created: {env_name}")
            
            # Test the environment
            if test_environment(env_name):
                print(f"\n✅ Environment {env_name} is ready for testing")
            else:
                print(f"\n❌ Environment {env_name} has issues")
        
        if args.test_env:
            if test_environment(args.test_env):
                print(f"\n✅ Environment {args.test_env} is working correctly")
            else:
                print(f"\n❌ Environment {args.test_env} has issues")
        
        if args.run_tests:
            if run_tests(args.run_tests):
                print(f"\n✅ Tests passed in environment {args.run_tests}")
            else:
                print(f"\n❌ Tests failed in environment {args.run_tests}")
        
        # If no specific action, show help
        if not any([args.create_env, args.test_env, args.run_tests, args.list, args.cleanup]):
            print("No action specified. Use --help for options.")
            print("\nQuick start:")
            print("  python scripts/setup_test_environment.py --create-env --python-version 3.11 --qt-version 6")
            print("  python scripts/setup_test_environment.py --run-tests mdaviz-test-py311-qt6")
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 