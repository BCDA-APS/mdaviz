#!/usr/bin/env python3
"""
Script to convert debug print statements to proper logging calls.

This script helps identify and convert print statements with "DEBUG:" prefix
to appropriate logging calls using the new mdaviz.logger module.
"""

import os
import re
import sys
from pathlib import Path


def find_debug_prints(directory):
    """Find all debug print statements in Python files."""
    debug_prints = []

    for root, dirs, files in os.walk(directory):
        # Skip certain directories
        dirs[:] = [
            d
            for d in dirs
            if d not in [".git", "__pycache__", "htmlcov", ".pytest_cache"]
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
                        if "print(" in line and "DEBUG:" in line:
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

    # Extract the message from the print statement
    # Handle different print formats:
    # print("DEBUG: message")
    # print(f"DEBUG: message {variable}")
    # print("DEBUG: message", variable)

    # Remove the print() wrapper
    if line.startswith("print(") and line.endswith(")"):
        inner_content = line[6:-1]  # Remove print( and )
    else:
        return None  # Can't parse this format

    # Check if it's a debug statement
    if "DEBUG:" not in inner_content:
        return None

    # Extract the message after "DEBUG:"
    if "DEBUG:" in inner_content:
        # Handle f-string format
        if inner_content.startswith('f"') or inner_content.startswith("f'"):
            # f"DEBUG: message {var}"
            message = inner_content[2:-1]  # Remove f" and "
            if "DEBUG:" in message:
                message = message.split("DEBUG:", 1)[1].strip()
                return f'logger.debug(f"{message}")'
        elif inner_content.startswith('"') or inner_content.startswith("'"):
            # "DEBUG: message"
            message = inner_content[1:-1]  # Remove quotes
            if "DEBUG:" in message:
                message = message.split("DEBUG:", 1)[1].strip()
                return f'logger.debug("{message}")'
        else:
            # Handle other formats like print("DEBUG: message", variable)
            parts = inner_content.split(",")
            if len(parts) > 1:
                # This is a more complex case, might need manual review
                return f"# TODO: Convert complex debug print: {line}"

    return None


def generate_conversion_report(debug_prints):
    """Generate a report of debug prints that need conversion."""
    print("=== DEBUG PRINT CONVERSION REPORT ===\n")

    for debug_print in debug_prints:
        converted = convert_debug_print_to_logger(debug_print)

        print(f"File: {debug_print['file']}")
        print(f"Line: {debug_print['line']}")
        print(f"Original: {debug_print['content']}")

        if converted:
            print(f"Converted: {converted}")
        else:
            print("Converted: # TODO: Manual conversion needed")

        print("-" * 80)


def generate_conversion_script(debug_prints):
    """Generate a script to automatically convert debug prints."""
    script_content = """#!/usr/bin/env python3
\"\"\"
Auto-generated script to convert debug print statements to logger calls.
Run this script to automatically convert the identified debug prints.
\"\"\"

import re
from pathlib import Path

def convert_file(file_path):
    \"\"\"Convert debug prints in a single file.\"\"\"
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\\n')
    modified = False
    
    # Check if logger import is needed
    needs_logger_import = False
    for line in lines:
        if 'print(' in line and 'DEBUG:' in line:
            needs_logger_import = True
            break
    
    # Add logger import if needed
    if needs_logger_import:
        # Find the right place to add the import
        import_added = False
        for i, line in enumerate(lines):
            if line.startswith('from mdaviz') or line.startswith('import mdaviz'):
                # Add logger import after other mdaviz imports
                if 'logger' not in content:
                    lines.insert(i + 1, 'from mdaviz.logger import get_logger')
                    lines.insert(i + 2, '')
                    lines.insert(i + 3, f'# Get logger for this module')
                    lines.insert(i + 4, f'logger = get_logger("{file_path.stem}")')
                    lines.insert(i + 5, '')
                    import_added = True
                    break
        
        if not import_added:
            # Add at the top if no mdaviz imports found
            lines.insert(0, 'from mdaviz.logger import get_logger')
            lines.insert(1, '')
            lines.insert(2, f'# Get logger for this module')
            lines.insert(3, f'logger = get_logger("{file_path.stem}")')
            lines.insert(4, '')
    
    # Convert debug prints
    for i, line in enumerate(lines):
        if 'print(' in line and 'DEBUG:' in line:
            converted = convert_debug_print_to_logger({
                'content': line,
                'module': file_path.stem
            })
            if converted:
                lines[i] = converted
                modified = True
    
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\\n'.join(lines))
        print(f"Converted: {file_path}")
    else:
        print(f"No changes needed: {file_path}")

def convert_debug_print_to_logger(debug_print):
    \"\"\"Convert a debug print statement to a logger call.\"\"\"
    line = debug_print['content']
    module = debug_print['module']
    
    # Remove the print() wrapper
    if line.startswith('print(') and line.endswith(')'):
        inner_content = line[6:-1]  # Remove print( and )
    else:
        return None
    
    # Check if it's a debug statement
    if 'DEBUG:' not in inner_content:
        return None
    
    # Extract the message after "DEBUG:"
    if inner_content.startswith('f"') or inner_content.startswith("f'"):
        # f"DEBUG: message {var}"
        message = inner_content[2:-1]  # Remove f" and "
        if 'DEBUG:' in message:
            message = message.split('DEBUG:', 1)[1].strip()
            return f'logger.debug(f"{message}")'
    elif inner_content.startswith('"') or inner_content.startswith("'"):
        # "DEBUG: message"
        message = inner_content[1:-1]  # Remove quotes
        if 'DEBUG:' in message:
            message = message.split('DEBUG:', 1)[1].strip()
            return f'logger.debug("{message}")'
    
    return None

# Files to convert:
"""

    # Add file conversion calls
    files_to_convert = set()
    for debug_print in debug_prints:
        files_to_convert.add(debug_print["file"])

    for file_path in sorted(files_to_convert):
        script_content += f'convert_file(Path("{file_path}"))\n'

    script_content += '\nprint("\\nConversion complete!")'

    return script_content


def main():
    """Main function."""
    if len(sys.argv) != 2:
        print("Usage: python convert_debug_to_logger.py <directory>")
        sys.exit(1)

    directory = Path(sys.argv[1])
    if not directory.exists():
        print(f"Directory {directory} does not exist")
        sys.exit(1)

    print(f"Scanning {directory} for debug print statements...")
    debug_prints = find_debug_prints(directory)

    if not debug_prints:
        print("No debug print statements found!")
        return

    print(
        f"Found {len(debug_prints)} debug print statements in {len(set(d['file'] for d in debug_prints))} files"
    )

    # Generate report
    generate_conversion_report(debug_prints)

    # Generate conversion script
    script_content = generate_conversion_script(debug_prints)
    script_path = Path("convert_debug_prints.py")

    with open(script_path, "w") as f:
        f.write(script_content)

    print(f"\nGenerated conversion script: {script_path}")
    print("Run this script to automatically convert the debug prints:")
    print(f"python {script_path}")


if __name__ == "__main__":
    main()
