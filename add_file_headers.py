#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
add_file_headers.py - Add standardized headers to all Python files in UDS3

This script adds a consistent file header to all .py files in the UDS3 project.

Author: Martin Krüger (ma.krueger@outlook.com)
Project: UDS3 - Unified Database Strategy v3
License: MIT with Government Partnership Commons Clause
Created: 2025-10-24
"""

import os
from pathlib import Path
from typing import List, Tuple

# Standard file header template
HEADER_TEMPLATE = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{filename}

{description}

Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)
License: MIT with Government Partnership Commons Clause
Repository: https://github.com/makr-code/VCC-UDS3
"""
'''

# Directories to process
DIRS_TO_PROCESS = [
    ".",  # Root
    "api",
    "core", 
    "database",
    "security",
    "search",
    "manager",
    "operations",
    "query",
    "relations",
    "saga",
    "compliance",
    "dsgvo",
    "domain",
    "embeddings",
    "cypher",
    "sql",
    "vpb",
    "legacy",
    "tools",
    "tests",
]

# Files to skip
SKIP_FILES = {
    "__pycache__",
    ".pyc",
    ".pyo",
    "setup.py",  # Has its own structure
    "config_local.py",  # User-specific
}

# Directories to skip
SKIP_DIRS = {
    "__pycache__",
    ".git",
    ".pytest_cache",
    ".mypy_cache",
    "venv",
    ".venv",
    "build",
    "dist",
    "*.egg-info",
    "archive",
    "examples_archive",
    "database_backup",
}

def has_header(content: str) -> bool:
    """Check if file already has a header."""
    lines = content.split('\n')
    # Check first 10 lines for existing header markers
    first_lines = '\n'.join(lines[:10])
    return (
        'Author: Martin Krüger' in first_lines or
        'ma.krueger@outlook.com' in first_lines or
        'Part of UDS3' in first_lines
    )

def extract_description(content: str, filename: str) -> str:
    """Extract description from existing docstring or create default."""
    lines = content.split('\n')
    
    # Look for existing module docstring
    in_docstring = False
    docstring_lines = []
    
    for i, line in enumerate(lines[:30]):  # Check first 30 lines
        stripped = line.strip()
        
        # Skip shebang and encoding
        if stripped.startswith('#!') or 'coding' in stripped:
            continue
            
        # Find docstring
        if '"""' in stripped or "'''" in stripped:
            if not in_docstring:
                in_docstring = True
                # Get content after opening quotes
                after_quotes = stripped.split('"""')[1] if '"""' in stripped else stripped.split("'''")[1]
                if after_quotes.strip():
                    docstring_lines.append(after_quotes.strip())
            else:
                # Closing quotes found
                before_quotes = stripped.split('"""')[0] if '"""' in stripped else stripped.split("'''")[0]
                if before_quotes.strip():
                    docstring_lines.append(before_quotes.strip())
                break
        elif in_docstring:
            if stripped:
                docstring_lines.append(stripped)
    
    if docstring_lines:
        # Clean up description
        description = '\n'.join(docstring_lines)
        # Remove common patterns
        description = description.replace('UDS3 - Unified Data Strategy 3.0', '')
        description = description.replace('Clean Modular Architecture', '')
        description = description.strip()
        if description:
            return description
    
    # Default descriptions based on filename
    defaults = {
        '__init__.py': 'Package initialization and exports',
        '__main__.py': 'Command-line interface entry point',
        'config.py': 'Configuration management',
        'database_api': 'Database backend implementation',
        'secure_api.py': 'Security wrapper for database operations',
        'search_api.py': 'Search API implementation',
        'manager.py': 'API manager and orchestration',
        'crud.py': 'CRUD operations',
        'saga': 'SAGA pattern implementation',
        'batch': 'Batch operations',
        'test_': 'Unit tests',
    }
    
    for pattern, desc in defaults.items():
        if pattern in filename:
            return desc
    
    # Generic description
    module_name = filename.replace('.py', '').replace('_', ' ').title()
    return f'{module_name} module'

def add_header_to_file(filepath: Path) -> Tuple[bool, str]:
    """Add header to a single Python file."""
    try:
        # Read existing content
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if already has header
        if has_header(content):
            return False, "Already has header"
        
        # Extract description
        description = extract_description(content, filepath.name)
        
        # Create header
        header = HEADER_TEMPLATE.format(
            filename=filepath.name,
            description=description
        )
        
        # Remove old shebang/encoding/docstring if present
        lines = content.split('\n')
        start_idx = 0
        
        for i, line in enumerate(lines[:30]):
            stripped = line.strip()
            if stripped.startswith('#!') or 'coding' in stripped:
                start_idx = i + 1
            elif stripped.startswith('"""') or stripped.startswith("'''"):
                # Find closing quotes
                quote_char = '"""' if '"""' in stripped else "'''"
                if stripped.count(quote_char) >= 2:
                    # Single line docstring
                    start_idx = i + 1
                    break
                else:
                    # Multi-line docstring
                    for j in range(i + 1, min(i + 50, len(lines))):
                        if quote_char in lines[j]:
                            start_idx = j + 1
                            break
                break
            elif stripped and not stripped.startswith('#'):
                # First actual code
                break
        
        # Preserve rest of content
        rest_content = '\n'.join(lines[start_idx:]).lstrip('\n')
        
        # Combine header and content
        new_content = header + '\n' + rest_content
        
        # Write back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return True, "Header added"
        
    except Exception as e:
        return False, f"Error: {str(e)}"

def should_skip(path: Path) -> bool:
    """Check if file/directory should be skipped."""
    # Skip if in skip files
    if path.name in SKIP_FILES:
        return True
    
    # Skip if any parent directory is in skip dirs
    for parent in path.parents:
        if parent.name in SKIP_DIRS:
            return True
    
    return False

def process_directory(base_dir: Path, dir_name: str) -> List[Tuple[str, bool, str]]:
    """Process all Python files in a directory."""
    results = []
    dir_path = base_dir / dir_name if dir_name != "." else base_dir
    
    if not dir_path.exists():
        return results
    
    # Find all .py files
    for py_file in dir_path.rglob("*.py"):
        if should_skip(py_file):
            continue
        
        relative_path = py_file.relative_to(base_dir)
        success, message = add_header_to_file(py_file)
        results.append((str(relative_path), success, message))
    
    return results

def main():
    """Main execution."""
    print("=" * 80)
    print("Adding File Headers to UDS3 Python Files")
    print("=" * 80)
    print()
    
    base_dir = Path(__file__).parent
    
    all_results = []
    
    for dir_name in DIRS_TO_PROCESS:
        print(f"\nProcessing directory: {dir_name}")
        results = process_directory(base_dir, dir_name)
        all_results.extend(results)
        
        # Print results for this directory
        added = sum(1 for _, success, _ in results if success)
        skipped = sum(1 for _, success, _ in results if not success)
        
        if results:
            print(f"  Added headers: {added}")
            print(f"  Skipped: {skipped}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    total_added = sum(1 for _, success, _ in all_results if success)
    total_skipped = sum(1 for _, success, _ in all_results if not success)
    
    print(f"\nTotal files processed: {len(all_results)}")
    print(f"Headers added: {total_added}")
    print(f"Skipped: {total_skipped}")
    
    # Show which files were modified
    if total_added > 0:
        print("\n" + "-" * 80)
        print("Modified files:")
        print("-" * 80)
        for filepath, success, message in all_results:
            if success:
                print(f"  ✅ {filepath}")
    
    # Show skipped files (for review)
    if total_skipped > 0 and total_skipped < 20:  # Only show if not too many
        print("\n" + "-" * 80)
        print("Skipped files:")
        print("-" * 80)
        for filepath, success, message in all_results:
            if not success:
                print(f"  ⏭️  {filepath} - {message}")
    
    print("\n" + "=" * 80)
    print("✅ File header update complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()
