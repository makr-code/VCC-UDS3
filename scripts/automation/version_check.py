#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
version_check.py

Automated Version Consistency Checker for UDS3
Ensures version numbers are consistent across all files.

Usage:
    python scripts/automation/version_check.py
    python scripts/automation/version_check.py --fix
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple


def extract_version_from_file(filepath: Path, patterns: List[str]) -> str:
    """Extract version from file using regex patterns."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        
        return None
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None


def check_version_consistency() -> List[Tuple[str, str]]:
    """Check version consistency across project files."""
    root = Path(__file__).parent.parent.parent
    
    version_files = {
        'setup.py': [r'version=["\']([^"\']+)["\']'],
        'pyproject.toml': [r'version\s*=\s*["\']([^"\']+)["\']'],
        '__init__.py': [r'__version__\s*=\s*["\']([^"\']+)["\']'],
        'README.md': [r'Version:\s*([0-9.]+)', r'v([0-9.]+)'],
        'IMPLEMENTATION_STATUS.md': [r'Version:\s*([0-9.]+)'],
    }
    
    versions = {}
    
    print("Checking version consistency...")
    print("")
    
    for filename, patterns in version_files.items():
        filepath = root / filename
        if filepath.exists():
            version = extract_version_from_file(filepath, patterns)
            if version:
                versions[filename] = version
                print(f"  {filename}: {version}")
    
    # Check consistency
    unique_versions = set(versions.values())
    
    print("")
    if len(unique_versions) == 1:
        version = list(unique_versions)[0]
        print(f"✓ All versions consistent: {version}")
        return []
    else:
        print("✗ Version inconsistencies detected:")
        inconsistencies = []
        for filename, version in versions.items():
            inconsistencies.append((filename, version))
        return inconsistencies


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Check version consistency')
    parser.add_argument('--fix', action='store_true',
                       help='Automatically fix inconsistencies')
    
    args = parser.parse_args()
    
    inconsistencies = check_version_consistency()
    
    if inconsistencies:
        print("\nInconsistent versions found:")
        for filename, version in inconsistencies:
            print(f"  {filename}: {version}")
        
        if args.fix:
            print("\nAutomatic fix not implemented. Please manually update versions.")
        
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
