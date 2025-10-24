#!/usr/bin/env python3
"""
UDS3 Import Update Script
Aktualisiert alle alten uds3_* Imports auf die neue modulare Struktur
"""

import os
import re
from pathlib import Path

# Import-Mappings für die neue Struktur
IMPORT_MAPPINGS = {
    # Core imports
    'from uds3_database_schemas import': 'from .schemas import',
    'from uds3_relations_core import': 'from .relations import', 
    'from uds3_relations_data_framework import': 'from .framework import',
    'from uds3_single_record_cache import': 'from .cache import',
    
    # Manager imports (from core/database.py perspective)
    'from uds3_delete_operations import': 'from ..manager.delete import',
    'from uds3_archive_operations import': 'from ..manager.archive import',
    'from uds3_streaming_operations import': 'from ..manager.streaming import',
    'from uds3_streaming_saga_integration import': 'from ..manager.streaming_saga import',
    'from uds3_saga_orchestrator import': 'from ..manager.saga import',
    'from uds3_saga_compliance import': 'from ..manager.compliance import',
    'from uds3_saga_step_builders import': 'from ..manager.saga_steps import',
    'from uds3_follow_up_orchestrator import': 'from ..manager.followup import',
    'from uds3_complete_process_integration import': 'from ..manager.process import',
    
    # API imports (from core/database.py perspective)
    'from uds3_api_manager import': 'from ..api.manager import',
    'from uds3_database_api import': 'from ..api.database import',
    'from uds3_search_api import': 'from ..api.search import',
    'from uds3_advanced_crud import': 'from ..api.crud import',
    'from uds3_crud_strategies import': 'from ..api.crud_strategies import',
    'from uds3_polyglot_query import': 'from ..api.query import',
    'from uds3_query_filters import': 'from ..api.filters import',
    'from uds3_vector_filter import': 'from ..api.vector_filter import',
    'from uds3_graph_filter import': 'from ..api.graph_filter import', 
    'from uds3_relational_filter import': 'from ..api.relational_filter import',
    'from uds3_file_storage_filter import': 'from ..api.file_filter import',
    'from uds3_naming_strategy import': 'from ..api.naming import',
    'from uds3_naming_integration import': 'from ..api.naming_integration import',
    'from uds3_geo_extension import': 'from ..api.geo import',
    'from uds3_process_parser_base import': 'from ..api.parser_base import',
    'from uds3_petrinet_parser import': 'from ..api.petrinet import',
    'from uds3_workflow_net_analyzer import': 'from ..api.workflow import',
}

def update_imports_in_file(file_path: Path) -> int:
    """
    Updates imports in a single file
    Returns number of replacements made
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        replacements = 0
        
        for old_import, new_import in IMPORT_MAPPINGS.items():
            if old_import in content:
                content = content.replace(old_import, new_import)
                replacements += 1
                
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Updated {file_path}: {replacements} replacements")
        
        return replacements
        
    except Exception as e:
        print(f"❌ Error updating {file_path}: {e}")
        return 0

def main():
    """Main update function"""
    print("🔄 Starting UDS3 Import Update...")
    print("=" * 50)
    
    uds3_root = Path("c:/VCC/uds3")
    total_replacements = 0
    files_updated = 0
    
    # Update files in core/, manager/, api/ directories
    for directory in ['core', 'manager', 'api']:
        dir_path = uds3_root / directory
        if dir_path.exists():
            print(f"\n📁 Updating {directory}/ directory:")
            for py_file in dir_path.glob("*.py"):
                if py_file.name != '__init__.py':  # Skip __init__.py files
                    replacements = update_imports_in_file(py_file)
                    if replacements > 0:
                        total_replacements += replacements
                        files_updated += 1
    
    print(f"\n🎉 Import update completed!")
    print(f"   Files updated: {files_updated}")
    print(f"   Total replacements: {total_replacements}")
    
if __name__ == "__main__":
    main()