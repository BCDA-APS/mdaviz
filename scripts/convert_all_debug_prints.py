#!/usr/bin/env python3
"""
Comprehensive script to convert all debug print statements to proper logging calls.
This script handles various formats of debug prints including "DEBUG:", "Debug -", etc.
"""

import os
import re
import sys
from pathlib import Path


def find_all_debug_prints(directory):
    """Find all debug print statements in Python files."""
    debug_prints = []

    for root, dirs, files in os.walk(directory):
        # Skip certain directories
        dirs[:] = [
            d
            for d in dirs
            if d not in [".git", "__pycache__", "htmlcov", ".pytest_cache", "scripts"]
        ]

        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Find debug print statements
                    lines = content.split("\n")
                    for i, line in enumerate(lines, 1):
                        # Look for various debug print patterns
                        if "print(" in line and (
                            "DEBUG:" in line or "Debug -" in line or "Debug:" in line
                        ):
                            debug_prints.append(
                                {
                                    "file": file_path,
                                    "line": i,
                                    "content": line.strip(),
                                    "module": file_path.stem,
                                }
                            )
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")

    return debug_prints


def convert_debug_print_to_logger(debug_print):
    """Convert a debug print statement to a logger call."""
    line = debug_print["content"]
    module = debug_print["module"]

    # Skip commented out lines
    if line.strip().startswith("#"):
        return None

    # Remove the print() wrapper
    if line.startswith("print(") and line.endswith(")"):
        inner_content = line[6:-1]  # Remove print( and )
    else:
        return None  # Can't parse this format

    # Extract the message after debug prefixes
    message = None

    # Handle different debug prefixes
    debug_prefixes = ["DEBUG:", "Debug -", "Debug:"]

    for prefix in debug_prefixes:
        if prefix in inner_content:
            # Handle f-string format
            if inner_content.startswith('f"') or inner_content.startswith("f'"):
                # f"DEBUG: message {var}"
                message = inner_content[2:-1]  # Remove f" and "
                message = message.split(prefix, 1)[1].strip()
                return f'logger.debug(f"{message}")'
            elif inner_content.startswith('"') or inner_content.startswith("'"):
                # "DEBUG: message"
                message = inner_content[1:-1]  # Remove quotes
                message = message.split(prefix, 1)[1].strip()
                return f'logger.debug("{message}")'

    return None


def convert_file(file_path):
    """Convert debug prints in a single file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        lines = content.split("\n")
        modified = False

        # Check if logger import is needed
        needs_logger_import = False
        for line in lines:
            if "print(" in line and (
                "DEBUG:" in line or "Debug -" in line or "Debug:" in line
            ):
                needs_logger_import = True
                break

        # Add logger import if needed
        if needs_logger_import:
            # Find the right place to add the import
            import_added = False
            for i, line in enumerate(lines):
                if line.startswith("from mdaviz") or line.startswith("import mdaviz"):
                    # Add logger import after other mdaviz imports
                    if "logger" not in content:
                        lines.insert(i + 1, "from mdaviz.logger import get_logger")
                        lines.insert(i + 2, "")
                        lines.insert(i + 3, f"# Get logger for this module")
                        lines.insert(i + 4, f'logger = get_logger("{file_path.stem}")')
                        lines.insert(i + 5, "")
                        import_added = True
                        break

            if not import_added:
                # Add at the top if no mdaviz imports found
                lines.insert(0, "from mdaviz.logger import get_logger")
                lines.insert(1, "")
                lines.insert(2, f"# Get logger for this module")
                lines.insert(3, f'logger = get_logger("{file_path.stem}")')
                lines.insert(4, "")

        # Convert debug prints
        for i, line in enumerate(lines):
            if "print(" in line and (
                "DEBUG:" in line or "Debug -" in line or "Debug:" in line
            ):
                converted = convert_debug_print_to_logger(
                    {"content": line, "module": file_path.stem}
                )
                if converted:
                    lines[i] = converted
                    modified = True

        if modified:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            print(f"Converted: {file_path}")
            return True
        else:
            print(f"No changes needed: {file_path}")
            return False

    except Exception as e:
        print(f"Error converting {file_path}: {e}")
        return False


def main():
    """Main function."""
    if len(sys.argv) != 2:
        print("Usage: python convert_all_debug_prints.py <directory>")
        sys.exit(1)

    directory = Path(sys.argv[1])
    if not directory.exists():
        print(f"Directory {directory} does not exist")
        sys.exit(1)

    print(f"Scanning {directory} for all debug print statements...")
    debug_prints = find_all_debug_prints(directory)

    if not debug_prints:
        print("No debug print statements found!")
        return

    print(
        f"Found {len(debug_prints)} debug print statements in {len(set(d['file'] for d in debug_prints))} files"
    )

    # Show what we found
    print("\n=== DEBUG PRINTS FOUND ===")
    for debug_print in debug_prints:
        print(f"{debug_print['file']}:{debug_print['line']} - {debug_print['content']}")

    # Ask for confirmation
    response = input(f"\nConvert {len(debug_prints)} debug prints? (y/N): ")
    if response.lower() != "y":
        print("Conversion cancelled.")
        return

    # Convert files
    files_to_convert = set()
    for debug_print in debug_prints:
        files_to_convert.add(debug_print["file"])

    converted_count = 0
    for file_path in sorted(files_to_convert):
        if convert_file(file_path):
            converted_count += 1

    print(f"\nConversion complete! Modified {converted_count} files.")


if __name__ == "__main__":
    main()
