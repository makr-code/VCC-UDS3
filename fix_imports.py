#!/usr/bin/env python3
"""
UDS3 Import Fix Script

Korrigiert die relativen Import-Probleme in der UDS3 Struktur nach der Reorganisation.
"""

import os
import re
from pathlib import Path

def fix_imports_in_file(file_path: Path):
    """Korrigiert Import-Statements in einer einzelnen Datei."""
    print(f"Processing: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Mapping von alten zu neuen Import-Pfaden
    import_fixes = [
        # Relative imports zu absolute imports
        (r'from \.\.manager\.', 'from manager.'),
        (r'from \.\.api\.', 'from api.'),
        (r'from \.\.compliance\.', 'from compliance.'),
        (r'from \.\.core\.', 'from core.'),
        (r'from \.\.legacy\.', 'from legacy.'),
        
        # Alte Modul-Namen zu neuen Pfaden
        (r'from uds3_security_quality import', 'from compliance.security_quality import'),
        (r'from uds3_vector_filter import', 'from api.vector_filter import'),
        (r'from uds3_graph_filter import', 'from api.graph_filter import'),
        (r'from uds3_relational_filter import', 'from api.relational_filter import'),
        (r'from uds3_file_storage_filter import', 'from api.file_filter import'),
        (r'from uds3_query_filters import', 'from api.filters import'),
        (r'from uds3_advanced_crud import', 'from api.crud import'),
        (r'from uds3_crud_strategies import', 'from api.crud_strategies import'),
        (r'from uds3_saga_orchestrator import', 'from manager.saga import'),
        (r'from uds3_streaming_operations import', 'from manager.streaming import'),
        (r'from uds3_archive_operations import', 'from manager.archive import'),
        (r'from uds3_delete_operations import', 'from manager.delete import'),
        (r'from uds3_saga_compliance import', 'from manager.compliance import'),
        (r'from uds3_streaming_saga_integration import', 'from manager.streaming_saga import'),
        (r'from uds3_relations_core import', 'from core.relations import'),
        (r'from uds3_relations_data_framework import', 'from core.framework import'),
        (r'from uds3_single_record_cache import', 'from core.cache import'),
        (r'from uds3_database_schemas import', 'from core.schemas import'),
        (r'from uds3_core import', 'from core.database import'),
        (r'from uds3_polyglot_query import', 'from api.query import'),
        
        # Entferne try/except blocks für nicht existierende Module
        (r'from uds3_vpb_operations import.*?print\("Warning: VPB Operations module not available"\)', 
         '# VPB Operations module not implemented\nVPB_OPERATIONS_AVAILABLE = False'),
        (r'from uds3_identity_service import.*?print\("Warning: Identity Service not available"\)',
         '# Identity Service module not implemented\nIDENTITY_SERVICE_AVAILABLE = False'),
        (r'from uds3_dsgvo_core import.*?print\("Warning: DSGVO Core not available"\)',
         '# DSGVO Core module not implemented\nDSGVO_CORE_AVAILABLE = False'),
    ]
    
    # Wende alle Korrekturen an
    for pattern, replacement in import_fixes:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)
    
    # Schreibe nur wenn Änderungen vorgenommen wurden
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✅ Fixed imports in {file_path}")
        return True
    else:
        print(f"  ➡️  No changes needed in {file_path}")
        return False

def fix_all_imports():
    """Korrigiert Imports in allen relevanten UDS3 Dateien."""
    print("=== UDS3 IMPORT FIX SCRIPT ===")
    print()
    
    uds3_root = Path('.')
    
    # Dateien die Import-Korrekturen benötigen
    target_files = [
        'core/database.py',
        'core/schemas.py', 
        'core/relations.py',
        'core/framework.py',
        'core/cache.py',
        'manager/saga.py',
        'manager/streaming.py',
        'manager/archive.py',
        'manager/delete.py',
        'manager/compliance.py',
        'manager/streaming_saga.py',
        'api/manager.py',
        'api/database.py',
        'api/search.py',
        'api/crud.py',
        'api/vector_filter.py',
        'api/graph_filter.py',
        'api/relational_filter.py',
        'api/file_filter.py',
        'api/filters.py',
        'api/query.py',
        'legacy/core.py',
    ]
    
    fixed_count = 0
    
    for file_path_str in target_files:
        file_path = uds3_root / file_path_str
        
        if file_path.exists():
            if fix_imports_in_file(file_path):
                fixed_count += 1
        else:
            print(f"⚠️  File not found: {file_path}")
    
    print()
    print(f"✅ Import fix complete!")
    print(f"   - Processed {len(target_files)} files")
    print(f"   - Fixed imports in {fixed_count} files")
    
    # Test ob Warnings reduziert wurden
    print()
    print("🧪 Testing import warnings...")
    try:
        import subprocess
        result = subprocess.run([
            'python', '-c', 'import config; print("✅ Config import successful")'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Basic import test passed")
        else:
            print(f"⚠️  Import test failed: {result.stderr}")
    except Exception as e:
        print(f"⚠️  Could not run import test: {e}")

if __name__ == "__main__":
    fix_all_imports()