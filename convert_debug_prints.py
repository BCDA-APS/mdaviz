#!/usr/bin/env python3
"""
Auto-generated script to convert debug print statements to logger calls.
Run this script to automatically convert the identified debug prints.
"""

import re
from pathlib import Path

def convert_file(file_path):
    """Convert debug prints in a single file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
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
            f.write('\n'.join(lines))
        print(f"Converted: {file_path}")
    else:
        print(f"No changes needed: {file_path}")

def convert_debug_print_to_logger(debug_print):
    """Convert a debug print statement to a logger call."""
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
convert_file(Path("src/mdaviz/chartview.py"))
convert_file(Path("src/mdaviz/mda_file.py"))
convert_file(Path("src/mdaviz/mda_file_table_model.py"))
convert_file(Path("src/mdaviz/mda_file_table_view.py"))
convert_file(Path("src/mdaviz/mda_file_viz.py"))
convert_file(Path("src/mdaviz/mda_folder.py"))

print("\nConversion complete!")