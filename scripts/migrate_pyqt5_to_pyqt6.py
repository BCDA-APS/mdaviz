#!/usr/bin/env python3
"""
Migration script: PyQt5 → PyQt6

This script automates the migration from PyQt5 to PyQt6 by:
1. Updating import statements
2. Fixing deprecated API usage
3. Updating matplotlib backend imports
4. Providing a summary of changes

Usage:
    python scripts/migrate_pyqt5_to_pyqt6.py [--dry-run] [--backup]

Options:
    --dry-run    Show what would be changed without making changes
    --backup     Create backup files before making changes
"""

import argparse
import re
import shutil
import sys
from pathlib import Path



def create_backup(file_path: Path) -> Path:
    """Create a backup of the file."""
    backup_path = file_path.with_suffix(f"{file_path.suffix}.pyqt5_backup")
    shutil.copy2(file_path, backup_path)
    return backup_path


def update_imports(content: str) -> tuple[str, list[str]]:
    """
    Update PyQt5 imports to PyQt6.
    
    Returns:
        tuple: (updated_content, list_of_changes)
    """
    changes = []
    original_content = content
    
    # Update import statements
    if "from PyQt5." in content:
        content = re.sub(r'from PyQt5\.', 'from PyQt6.', content)
        changes.append("Updated PyQt5 imports to PyQt6")
    
    if "import PyQt5" in content:
        content = re.sub(r'import PyQt5', 'import PyQt6', content)
        changes.append("Updated PyQt5 module imports to PyQt6")
    
    # Update matplotlib backend imports
    if "matplotlib.backends.backend_qt5agg" in content:
        content = re.sub(
            r'from matplotlib\.backends\.backend_qt5agg',
            'from matplotlib.backends.backend_qtagg',
            content
        )
        content = re.sub(
            r'import matplotlib\.backends\.backend_qt5agg',
            'import matplotlib.backends.backend_qtagg',
            content
        )
        changes.append("Updated matplotlib backend from qt5agg to qtagg")
    
    return content, changes


def update_api_usage(content: str) -> tuple[str, list[str]]:
    """
    Update deprecated PyQt5 API usage to PyQt6 compatible code.
    
    Returns:
        tuple: (updated_content, list_of_changes)
    """
    changes = []
    
    # Update QDesktopWidget usage
    if "QDesktopWidget" in content:
        # Replace QDesktopWidget().screenGeometry() with QApplication.primaryScreen().geometry()
        content = re.sub(
            r'QDesktopWidget\(\)\.screenGeometry\(\)',
            'QApplication.primaryScreen().geometry()',
            content
        )
        
        # Remove QDesktopWidget imports if no longer used
        if "QDesktopWidget" not in content:
            content = re.sub(
                r'from PyQt6\.QtWidgets import.*QDesktopWidget.*\n',
                '',
                content
            )
            content = re.sub(
                r', QDesktopWidget',
                '',
                content
            )
            content = re.sub(
                r'QDesktopWidget, ',
                '',
                content
            )
        
        changes.append("Updated QDesktopWidget usage to QApplication.primaryScreen()")
    
    # Update QVariant usage (simplify where possible)
    if "QVariant" in content:
        # Simple cases where QVariant is no longer needed
        content = re.sub(
            r'QVariant\(([^)]+)\)',
            r'\1',
            content
        )
        changes.append("Simplified QVariant usage")
    
    return content, changes


def update_file(file_path: Path, dry_run: bool = False, create_backups: bool = False) -> tuple[bool, list[str]]:
    """
    Update a single file from PyQt5 to PyQt6.
    
    Args:
        file_path: Path to the file to update
        dry_run: If True, don't make changes, just report what would be done
        create_backups: If True, create backup files before making changes
    
    Returns:
        tuple: (was_changed, list_of_changes)
    """
    if not file_path.exists():
        return False, ["File does not exist"]
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    all_changes = []
    
    # Update imports
    content, import_changes = update_imports(content)
    all_changes.extend(import_changes)
    
    # Update API usage
    content, api_changes = update_api_usage(content)
    all_changes.extend(api_changes)
    
    # Check if any changes were made
    if content == original_content:
        return False, []
    
    if not dry_run:
        # Create backup if requested
        if create_backups:
            backup_path = create_backup(file_path)
            all_changes.append(f"Created backup: {backup_path}")
        
        # Write updated content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return True, all_changes


def find_python_files(src_dir: Path) -> list[Path]:
    """Find all Python files in the source directory."""
    python_files = []
    for py_file in src_dir.rglob("*.py"):
        # Skip backup files and cache directories
        if (".pyqt5_backup" in py_file.name or 
            "__pycache__" in py_file.parts or
            ".pytest_cache" in py_file.parts):
            continue
        python_files.append(py_file)
    return sorted(python_files)


def main():
    """Main migration function."""
    parser = argparse.ArgumentParser(
        description="Migrate PyQt5 code to PyQt6",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/migrate_pyqt5_to_pyqt6.py --dry-run
  python scripts/migrate_pyqt5_to_pyqt6.py --backup
  python scripts/migrate_pyqt5_to_pyqt6.py
        """
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes"
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Create backup files before making changes"
    )
    parser.add_argument(
        "--src-dir",
        type=Path,
        default=Path("src"),
        help="Source directory to migrate (default: src)"
    )
    
    args = parser.parse_args()
    
    if not args.src_dir.exists():
        print(f"Error: Source directory '{args.src_dir}' does not exist")
        sys.exit(1)
    
    print(f"PyQt5 → PyQt6 Migration Script")
    print(f"Source directory: {args.src_dir}")
    print(f"Dry run: {args.dry_run}")
    print(f"Create backups: {args.backup}")
    print("-" * 50)
    
    # Find all Python files
    python_files = find_python_files(args.src_dir)
    print(f"Found {len(python_files)} Python files to check")
    
    # Process files
    migrated_files = []
    total_changes = 0
    
    for py_file in python_files:
        print(f"\nProcessing: {py_file}")
        
        was_changed, changes = update_file(
            py_file, 
            dry_run=args.dry_run, 
            create_backups=args.backup
        )
        
        if was_changed:
            migrated_files.append(py_file)
            total_changes += len(changes)
            
            if args.dry_run:
                print(f"  Would make {len(changes)} changes:")
            else:
                print(f"  Made {len(changes)} changes:")
            
            for change in changes:
                print(f"    - {change}")
        else:
            print("  No changes needed")
    
    # Summary
    print("\n" + "=" * 50)
    print("MIGRATION SUMMARY")
    print("=" * 50)
    print(f"Files processed: {len(python_files)}")
    print(f"Files migrated: {len(migrated_files)}")
    print(f"Total changes: {total_changes}")
    
    if args.dry_run:
        print("\nThis was a dry run. No files were actually modified.")
        print("Run without --dry-run to apply the changes.")
    else:
        print(f"\nMigration completed successfully!")
        
        if migrated_files:
            print("\nMigrated files:")
            for file_path in migrated_files:
                print(f"  - {file_path}")
        
        if args.backup:
            print("\nBackup files created with .pyqt5_backup extension")
    
    # Next steps
    print("\n" + "=" * 50)
    print("NEXT STEPS")
    print("=" * 50)
    print("1. Update dependencies in pyproject.toml:")
    print("   - Change 'PyQt5' to 'PyQt6'")
    print("   - Update matplotlib to >=3.8.0")
    print("   - Update pytest-qt to >=4.2.0")
    print()
    print("2. Update env.yml:")
    print("   - Change 'pyqt =5' to 'pyqt =6'")
    print("   - Change 'qt =5' to 'qt =6'")
    print()
    print("3. Test the application:")
    print("   - Run: pytest src/tests -v")
    print("   - Test GUI functionality manually")
    print("   - Check for any remaining PyQt5 references")
    print()
    print("4. Update CI/CD configurations if needed")
    print()
    print("5. Update documentation and release notes")


if __name__ == "__main__":
    main() 