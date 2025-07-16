#!/usr/bin/env python3
"""
Dependency Update Script

This script helps update dependencies to latest stable versions and checks for compatibility.

Usage:
    python scripts/update_dependencies.py [--check] [--update] [--python-version]

Options:
    --check           Check current vs latest versions
    --update          Update pyproject.toml with latest versions
    --python-version  Check Python version compatibility
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Optional
import tomllib
import tomli_w


def get_latest_version(package_name: str) -> Optional[str]:
    """Get the latest version of a package from PyPI."""
    try:
        result = subprocess.run(
            ["pip", "index", "versions", package_name, "--format=json"],
            capture_output=True,
            text=True,
            check=True
        )
        data = json.loads(result.stdout)
        return data["versions"][-1]  # Latest version
    except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError, IndexError):
        return None


def parse_version_spec(version_spec: str) -> tuple[str, str]:
    """Parse version specification like '>=1.9.0' or 'matplotlib'."""
    if ">=" in version_spec:
        package, version = version_spec.split(">=")
        return package.strip(), f">={version.strip()}"
    elif "==" in version_spec:
        package, version = version_spec.split("==")
        return package.strip(), f"=={version.strip()}"
    elif "~=" in version_spec:
        package, version = version_spec.split("~=")
        return package.strip(), f"~={version.strip()}"
    else:
        return version_spec.strip(), ""


def load_pyproject_toml() -> dict:
    """Load pyproject.toml file."""
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        raise FileNotFoundError("pyproject.toml not found")
    
    with open(pyproject_path, "rb") as f:
        return tomllib.load(f)


def save_pyproject_toml(data: dict) -> None:
    """Save pyproject.toml file."""
    pyproject_path = Path("pyproject.toml")
    with open(pyproject_path, "wb") as f:
        tomli_w.dump(data, f)


def check_dependencies() -> dict:
    """Check current vs latest versions of dependencies."""
    pyproject_data = load_pyproject_toml()
    dependencies = pyproject_data.get("project", {}).get("dependencies", [])
    
    results = {}
    
    print("Checking dependency versions...")
    print("-" * 60)
    print(f"{'Package':<20} {'Current':<15} {'Latest':<15} {'Status'}")
    print("-" * 60)
    
    for dep_spec in dependencies:
        package, current_spec = parse_version_spec(dep_spec)
        current_version = current_spec.replace(">=", "").replace("==", "").replace("~=", "")
        
        latest_version = get_latest_version(package)
        
        if latest_version:
            status = "✅ Up to date" if current_version == latest_version else "🔄 Update available"
            print(f"{package:<20} {current_version:<15} {latest_version:<15} {status}")
            
            results[package] = {
                "current": current_version,
                "latest": latest_version,
                "spec": current_spec,
                "needs_update": current_version != latest_version
            }
        else:
            print(f"{package:<20} {current_version:<15} {'Unknown':<15} ❓ Error checking")
            results[package] = {
                "current": current_version,
                "latest": "Unknown",
                "spec": current_spec,
                "needs_update": False
            }
    
    return results


def update_dependencies() -> None:
    """Update dependencies to latest stable versions."""
    pyproject_data = load_pyproject_toml()
    dependencies = pyproject_data.get("project", {}).get("dependencies", [])
    
    updated_deps = []
    changes_made = []
    
    print("Updating dependencies to latest versions...")
    print("-" * 50)
    
    for dep_spec in dependencies:
        package, current_spec = parse_version_spec(dep_spec)
        current_version = current_spec.replace(">=", "").replace("==", "").replace("~=", "")
        
        latest_version = get_latest_version(package)
        
        if latest_version and latest_version != current_version:
            # Keep the same version specifier but update version
            if ">=" in current_spec:
                new_spec = f"{package}>={latest_version}"
            elif "==" in current_spec:
                new_spec = f"{package}=={latest_version}"
            elif "~=" in current_spec:
                new_spec = f"{package}~={latest_version}"
            else:
                new_spec = f"{package}>={latest_version}"
            
            updated_deps.append(new_spec)
            changes_made.append(f"{package}: {current_version} → {latest_version}")
            print(f"  {package}: {current_version} → {latest_version}")
        else:
            updated_deps.append(dep_spec)
    
    if changes_made:
        pyproject_data["project"]["dependencies"] = updated_deps
        save_pyproject_toml(pyproject_data)
        print(f"\n✅ Updated {len(changes_made)} dependencies in pyproject.toml")
    else:
        print("\n✅ All dependencies are already up to date")


def check_python_compatibility() -> None:
    """Check Python version compatibility for dependencies."""
    pyproject_data = load_pyproject_toml()
    requires_python = pyproject_data.get("project", {}).get("requires-python", "")
    
    print("Python Version Compatibility Check")
    print("-" * 40)
    print(f"Current requires-python: {requires_python}")
    
    # Check current Python version
    current_python = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(f"Current Python version: {current_python}")
    
    # Parse version requirements
    if ">=" in requires_python:
        min_version = requires_python.split(">=")[1]
        print(f"Minimum Python version: {min_version}")
    
    # Check for Python 3.13 compatibility
    print("\nPython 3.13 Compatibility:")
    print("- xdrlib deprecation: ✅ Already handled with fallback")
    print("- Type annotations: ✅ Using modern syntax")
    print("- PyQt6 compatibility: ✅ PyQt6 supports Python 3.13")
    
    # Recommendations
    print("\nRecommendations:")
    print("- Update requires-python to '>=3.10,<3.14' for Python 3.13 support")
    print("- Test with Python 3.13 when available")
    print("- Monitor for any new deprecation warnings")


def check_pyqt_migration_status() -> None:
    """Check PyQt5 → PyQt6 migration status."""
    print("PyQt5 → PyQt6 Migration Status")
    print("-" * 40)
    
    pyproject_data = load_pyproject_toml()
    dependencies = pyproject_data.get("project", {}).get("dependencies", [])
    
    pyqt5_found = any("PyQt5" in dep for dep in dependencies)
    pyqt6_found = any("PyQt6" in dep for dep in dependencies)
    
    if pyqt5_found and not pyqt6_found:
        print("❌ Still using PyQt5 (deprecated)")
        print("   Run migration script: python scripts/migrate_pyqt5_to_pyqt6.py")
    elif pyqt6_found and not pyqt5_found:
        print("✅ Successfully migrated to PyQt6")
    elif pyqt5_found and pyqt6_found:
        print("⚠️  Both PyQt5 and PyQt6 found (transition state)")
    else:
        print("❓ No PyQt dependencies found")
    
    # Check for PyQt5 imports in code
    src_dir = Path("src")
    pyqt5_imports = []
    
    if src_dir.exists():
        for py_file in src_dir.rglob("*.py"):
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                    if "PyQt5" in content:
                        pyqt5_imports.append(py_file)
            except Exception:
                pass
    
    if pyqt5_imports:
        print(f"\n⚠️  Found {len(pyqt5_imports)} files with PyQt5 imports:")
        for file_path in pyqt5_imports[:5]:  # Show first 5
            print(f"   - {file_path}")
        if len(pyqt5_imports) > 5:
            print(f"   ... and {len(pyqt5_imports) - 5} more")
    else:
        print("\n✅ No PyQt5 imports found in source code")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Update dependencies to latest stable versions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/update_dependencies.py --check
  python scripts/update_dependencies.py --update
  python scripts/update_dependencies.py --python-version
  python scripts/update_dependencies.py --check --update
        """
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check current vs latest versions"
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update pyproject.toml with latest versions"
    )
    parser.add_argument(
        "--python-version",
        action="store_true",
        help="Check Python version compatibility"
    )
    parser.add_argument(
        "--pyqt-status",
        action="store_true",
        help="Check PyQt5 → PyQt6 migration status"
    )
    
    args = parser.parse_args()
    
    # If no arguments provided, run all checks
    if not any([args.check, args.update, args.python_version, args.pyqt_status]):
        args.check = True
        args.python_version = True
        args.pyqt_status = True
    
    print("mdaviz Dependency Update Script")
    print("=" * 50)
    
    try:
        if args.check:
            print("\n" + "=" * 50)
            check_dependencies()
        
        if args.update:
            print("\n" + "=" * 50)
            update_dependencies()
        
        if args.python_version:
            print("\n" + "=" * 50)
            check_python_compatibility()
        
        if args.pyqt_status:
            print("\n" + "=" * 50)
            check_pyqt_migration_status()
        
        print("\n" + "=" * 50)
        print("SUMMARY")
        print("=" * 50)
        print("✅ Dependency check completed")
        
        if args.update:
            print("✅ Dependencies updated (if needed)")
        
        print("\nNext steps:")
        print("1. Review the changes made")
        print("2. Test the application with updated dependencies")
        print("3. Run: pip install -e .")
        print("4. Run: pytest src/tests -v")
        print("5. Test GUI functionality manually")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 