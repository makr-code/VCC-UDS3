#!/usr/bin/env python3
"""
UDS3 Import Update Tool
Automatisches Aktualisieren aller Import-Statements nach Refactoring
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Set

# Import-Mapping: alt → neu
IMPORT_MAPPINGS = {
    # === CORE ===
    "from uds3.core.polyglot_manager import": "from uds3.core.polyglot_manager import",
    "from uds3.core.polyglot_manager import": "from uds3.core.polyglot_manager import",
    "from uds3.core import polyglot_manager": "from uds3.core import polyglot_manager",
    "from uds3.core.embeddings import": "from uds3.core.embeddings import",
    "from uds3.core.embeddings import": "from uds3.core.embeddings import",
    "from uds3.core.llm_ollama import": "from uds3.core.llm_ollama import",
    "from uds3.core.llm_ollama import": "from uds3.core.llm_ollama import",
    "from uds3.core.rag_pipeline import": "from uds3.core.rag_pipeline import",
    "from uds3.core.rag_pipeline import": "from uds3.core.rag_pipeline import",
    
    # === VPB ===
    "from uds3.vpb.operations import": "from uds3.vpb.operations import",
    "from uds3.vpb.operations import": "from uds3.vpb.operations import",
    "from uds3.vpb import operations": "from uds3.vpb import operations",
    "from uds3.vpb.parser_bpmn import": "from uds3.vpb.parser_bpmn import",
    "from uds3.vpb.parser_bpmn import": "from uds3.vpb.parser_bpmn import",
    "from uds3.vpb.parser_epk import": "from uds3.vpb.parser_epk import",
    "from uds3.vpb.parser_epk import": "from uds3.vpb.parser_epk import",
    "from uds3.vpb.parser_petri import": "from uds3.vpb.parser_petri import",
    
    # === COMPLIANCE ===
    "from uds3.compliance.dsgvo_core import": "from uds3.compliance.dsgvo_core import",
    "from uds3.compliance.dsgvo_core import": "from uds3.compliance.dsgvo_core import",
    "from uds3.compliance import dsgvo_core": "from uds3.compliance import dsgvo_core",
    "from uds3.compliance.security_quality import": "from uds3.compliance.security_quality import",
    "from uds3.compliance.security_quality import": "from uds3.compliance.security_quality import",
    "from uds3.compliance.identity_service import": "from uds3.compliance.identity_service import",
    "from uds3.compliance.identity_service import": "from uds3.compliance.identity_service import",
    
    # === INTEGRATION ===
    "from uds3.integration.saga_integration import": "from uds3.integration.saga_integration import",
    "from uds3.integration.saga_integration import": "from uds3.integration.saga_integration import",
    "from uds3.integration import saga_integration": "from uds3.integration import saga_integration",
    "from uds3.integration.adaptive_strategy import": "from uds3.integration.adaptive_strategy import",
    "from uds3.integration.adaptive_strategy import": "from uds3.integration.adaptive_strategy import",
    "from uds3.integration.distributor import": "from uds3.integration.distributor import",
    "from uds3.integration.distributor import": "from uds3.integration.distributor import",
    
    # === LEGACY ===
    "from uds3.legacy.core import": "from uds3.legacy.core import",
    "from uds3.legacy.core import": "from uds3.legacy.core import",
    "from uds3.legacy import core": "from uds3.legacy import core",
    "from uds3.legacy.rag_enhanced import": "from uds3.legacy.rag_enhanced import",
    "from uds3.legacy.rag_enhanced import": "from uds3.legacy.rag_enhanced import",
}

# Relative Imports innerhalb der Module
RELATIVE_IMPORT_PATTERNS = {
    r"from \.\.database\.": "from uds3.database.",  # ..database.X → uds3.database.X
    r"from \.database\.": "from uds3.database.",    # .database.X → uds3.database.X
}

def find_python_files(base_path: Path, exclude_dirs: Set[str]) -> List[Path]:
    """
    Findet alle Python-Dateien rekursiv.
    
    Args:
        base_path: Wurzelverzeichnis
        exclude_dirs: Ordner zum Ausschließen (z.B. legacy, __pycache__)
    
    Returns:
        Liste von Pfaden zu Python-Dateien
    """
    python_files = []
    
    for root, dirs, files in os.walk(base_path):
        # Entferne ausgeschlossene Ordner aus der Iteration
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)
    
    return python_files

def update_imports_in_file(file_path: Path, mappings: Dict[str, str]) -> Tuple[bool, int]:
    """
    Aktualisiert Imports in einer Datei.
    
    Args:
        file_path: Pfad zur Python-Datei
        mappings: Dictionary mit alt → neu Mappings
    
    Returns:
        (changed, num_replacements)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
    except Exception as e:
        print(f"❌ Fehler beim Lesen von {file_path}: {e}")
        return False, 0
    
    modified_content = original_content
    num_replacements = 0
    
    # Wende alle Mappings an
    for old_import, new_import in mappings.items():
        if old_import in modified_content:
            modified_content = modified_content.replace(old_import, new_import)
            num_replacements += modified_content.count(new_import) - original_content.count(new_import)
    
    # Wende relative Import-Patterns an
    for pattern, replacement in RELATIVE_IMPORT_PATTERNS.items():
        matches = re.findall(pattern, modified_content)
        if matches:
            modified_content = re.sub(pattern, replacement, modified_content)
            num_replacements += len(matches)
    
    # Schreibe nur wenn Änderungen vorgenommen wurden
    if modified_content != original_content:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            return True, num_replacements
        except Exception as e:
            print(f"❌ Fehler beim Schreiben von {file_path}: {e}")
            return False, 0
    
    return False, 0

def main():
    """Hauptfunktion: Aktualisiert Imports in allen Python-Dateien"""
    base_path = Path(__file__).parent
    print(f"🚀 UDS3 Import Update Tool")
    print(f"📁 Basis-Pfad: {base_path}\n")
    
    # Finde alle Python-Dateien (außer legacy & __pycache__)
    exclude_dirs = {'__pycache__', '.git', 'venv', '.pytest_cache'}
    python_files = find_python_files(base_path, exclude_dirs)
    
    print(f"📝 {len(python_files)} Python-Dateien gefunden\n")
    
    updated_count = 0
    total_replacements = 0
    
    # Legacy-Dateien separat behandeln (nur relative Imports)
    legacy_files = [f for f in python_files if 'legacy' in f.parts]
    regular_files = [f for f in python_files if 'legacy' not in f.parts]
    
    # Reguläre Dateien: Alle Mappings
    print("📦 Aktualisiere reguläre Module...")
    for file_path in regular_files:
        rel_path = file_path.relative_to(base_path)
        changed, num_replacements = update_imports_in_file(file_path, IMPORT_MAPPINGS)
        
        if changed:
            print(f"✅ {rel_path}: {num_replacements} Ersetzung(en)")
            updated_count += 1
            total_replacements += num_replacements
    
    # Legacy-Dateien: Nur relative Imports (keine Umschreibung auf neue Struktur)
    print("\n📦 Aktualisiere Legacy-Module (nur relative Imports)...")
    for file_path in legacy_files:
        rel_path = file_path.relative_to(base_path)
        changed, num_replacements = update_imports_in_file(file_path, {})  # Nur Patterns
        
        if changed:
            print(f"✅ {rel_path}: {num_replacements} Ersetzung(en)")
            updated_count += 1
            total_replacements += num_replacements
    
    # Zusammenfassung
    print(f"\n{'='*60}")
    print(f"📊 ZUSAMMENFASSUNG")
    print(f"{'='*60}")
    print(f"✅ Dateien aktualisiert:  {updated_count}/{len(python_files)}")
    print(f"🔄 Imports ersetzt:       {total_replacements}")
    print(f"{'='*60}")
    
    if updated_count > 0:
        print("\n🎉 Import-Updates erfolgreich!")
        print("\n📝 Nächste Schritte:")
        print("   1. python generate_init_files.py")
        print("   2. pytest tests/")
        return 0
    else:
        print("\n⚠️  Keine Änderungen vorgenommen.")
        return 0

if __name__ == "__main__":
    sys.exit(main())
