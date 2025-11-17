#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
count_loc.py

Automated LOC (Lines of Code) Counter for UDS3
Prevents documentation drift by tracking actual LOC counts.

Usage:
    python scripts/automation/count_loc.py
    python scripts/automation/count_loc.py --update-docs
"""

import os
import sys
from pathlib import Path
from typing import Dict, List
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def count_lines(filepath: Path) -> int:
    """Count non-empty, non-comment lines in a Python file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        count = 0
        in_multiline_comment = False
        
        for line in lines:
            stripped = line.strip()
            
            # Skip empty lines
            if not stripped:
                continue
            
            # Handle multiline comments
            if '"""' in stripped or "'''" in stripped:
                in_multiline_comment = not in_multiline_comment
                continue
            
            if in_multiline_comment:
                continue
            
            # Skip single-line comments
            if stripped.startswith('#'):
                continue
            
            count += 1
        
        return count
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return 0


def scan_directory(directory: Path, pattern: str = "*.py") -> Dict[str, int]:
    """Scan directory for Python files and count LOC."""
    results = {}
    
    for filepath in directory.rglob(pattern):
        # Skip test files and __pycache__
        if '__pycache__' in str(filepath) or 'test_' in filepath.name:
            continue
        
        relative_path = str(filepath.relative_to(directory.parent))
        loc = count_lines(filepath)
        results[relative_path] = loc
    
    return results


def generate_report(scan_results: Dict[str, int]) -> str:
    """Generate LOC report."""
    report = []
    report.append("# UDS3 Lines of Code Report")
    report.append(f"Generated: {__import__('datetime').datetime.now().isoformat()}")
    report.append("")
    
    # Group by module
    modules = {}
    for filepath, loc in sorted(scan_results.items()):
        module = filepath.split('/')[0]
        if module not in modules:
            modules[module] = []
        modules[module].append((filepath, loc))
    
    total_loc = 0
    
    for module, files in sorted(modules.items()):
        module_total = sum(loc for _, loc in files)
        total_loc += module_total
        
        report.append(f"\n## {module.upper()} ({module_total:,} lines)")
        report.append("")
        report.append("| File | LOC |")
        report.append("|------|-----|")
        
        for filepath, loc in sorted(files, key=lambda x: x[1], reverse=True):
            filename = filepath.split('/')[-1]
            report.append(f"| {filename} | {loc:,} |")
    
    report.append(f"\n## Total: {total_loc:,} lines")
    
    return "\n".join(report)


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Count LOC in UDS3 project')
    parser.add_argument('--update-docs', action='store_true',
                       help='Update IMPLEMENTATION_STATUS.md with current counts')
    parser.add_argument('--output', default='LOC_REPORT.md',
                       help='Output file for report')
    
    args = parser.parse_args()
    
    # Scan main modules
    root = Path(__file__).parent.parent.parent
    
    modules_to_scan = ['api', 'core', 'database', 'security', 'manager', 'search']
    
    print("Scanning UDS3 modules...")
    all_results = {}
    
    for module in modules_to_scan:
        module_path = root / module
        if module_path.exists():
            print(f"  Scanning {module}/...")
            results = scan_directory(module_path)
            all_results.update(results)
    
    # Generate report
    report = generate_report(all_results)
    
    # Save report
    output_file = root / args.output
    with open(output_file, 'w') as f:
        f.write(report)
    
    print(f"\nReport saved to: {output_file}")
    print(f"Total LOC: {sum(all_results.values()):,}")
    
    # Key files
    key_files = {
        'api/saga_crud.py': 1569,
        'api/search_api.py': 557,
        'api/secure_api.py': 694,
        'security/__init__.py': 673,
    }
    
    print("\nKey Files:")
    for filepath, expected in key_files.items():
        actual = all_results.get(filepath, 0)
        status = "✓" if abs(actual - expected) < 50 else "✗"
        print(f"  {status} {filepath}: {actual} (expected ~{expected})")
    
    if args.update_docs:
        print("\nUpdating documentation...")
        # This would update IMPLEMENTATION_STATUS.md
        print("  (Documentation update not implemented in this version)")


if __name__ == '__main__':
    main()
