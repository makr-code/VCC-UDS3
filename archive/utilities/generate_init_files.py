#!/usr/bin/env python3
"""
UDS3 __init__.py Generator
Erstellt __init__.py Dateien für alle Domain-Module mit Re-Exports für Backwards Compatibility
"""

import os
import sys
from pathlib import Path
from typing import Dict, List

# Module-Struktur: Ordner → (Modul-Dateien, Re-Export-Klassen/Funktionen)
MODULE_STRUCTURE = {
    "core": {
        "files": ["polyglot_manager", "embeddings", "llm_ollama", "rag_pipeline"],
        "exports": {
            "polyglot_manager": ["UDS3PolyglotManager"],
            "embeddings": ["get_embedding", "get_embedding_batch", "similarity", "EmbeddingCache"],
            "llm_ollama": ["OllamaClient", "LLMResponse"],
            "rag_pipeline": ["RAGPipeline", "QueryType"],
        }
    },
    "vpb": {
        "files": ["operations", "parser_bpmn", "parser_epk"],
        "exports": {
            "operations": ["VPBProcess", "VPBTask", "VPBDocument", "VPBParticipant"],
            "parser_bpmn": ["BPMNParser"],
            "parser_epk": ["EPKParser"],
        }
    },
    "compliance": {
        "files": ["dsgvo_core", "security_quality", "identity_service"],
        "exports": {
            "dsgvo_core": ["DSGVOCore", "PIIDetector", "ComplianceEngine"],
            "security_quality": ["SecurityManager", "QualityFramework"],
            "identity_service": ["IdentityService", "User"],
        }
    },
    "integration": {
        "files": ["saga_integration", "adaptive_strategy", "distributor"],
        "exports": {
            "saga_integration": ["SAGACoordinator", "SAGAStep"],
            "adaptive_strategy": ["AdaptiveRouter", "RoutingStrategy"],
            "distributor": ["MultiDBDistributor"],
        }
    },
    "operations": {
        "files": [],  # Noch keine Dateien vorhanden
        "exports": {}
    },
    "query": {
        "files": [],  # Noch keine Dateien vorhanden
        "exports": {}
    },
    "domain": {
        "files": [],  # Noch keine Dateien vorhanden
        "exports": {}
    },
    "saga": {
        "files": [],  # Noch keine Dateien vorhanden
        "exports": {}
    },
    "relations": {
        "files": [],  # Noch keine Dateien vorhanden
        "exports": {}
    },
    "performance": {
        "files": [],  # Noch keine Dateien vorhanden
        "exports": {}
    },
    "legacy": {
        "files": ["core", "rag_enhanced"],
        "exports": {
            "core": ["UnifiedDatabaseStrategy"],
            "rag_enhanced": ["RAGEnhancedLLM"],
        }
    },
}

def generate_init_content(module_name: str, files: List[str], exports: Dict[str, List[str]]) -> str:
    """
    Generiert Inhalt für __init__.py Datei.
    
    Args:
        module_name: Name des Moduls (z.B. "core")
        files: Liste der Module-Dateien (ohne .py)
        exports: Dict mit Modul → Liste von Exporten
    
    Returns:
        Inhalt der __init__.py Datei als String
    """
    lines = [
        f'"""',
        f'UDS3 {module_name.capitalize()} Module',
        f'',
        f'Dieses Modul ist Teil der UDS3 Polyglot Persistence Architecture.',
        f'',
        f'Auto-generiert von generate_init_files.py',
        f'"""',
        f'',
    ]
    
    # Imports
    if exports:
        lines.append("# Exports für Backwards Compatibility")
        for module_file, export_list in exports.items():
            if export_list:
                exports_str = ", ".join(export_list)
                lines.append(f"from .{module_file} import {exports_str}")
        lines.append("")
    
    # __all__ Definition
    all_exports = []
    for export_list in exports.values():
        all_exports.extend(export_list)
    
    if all_exports:
        lines.append("__all__ = [")
        for export in sorted(all_exports):
            lines.append(f'    "{export}",')
        lines.append("]")
        lines.append("")
    
    # Modul-Metadata
    lines.extend([
        f'__module_name__ = "{module_name}"',
        f'__version__ = "2.0.0"',
    ])
    
    return "\n".join(lines) + "\n"

def create_init_file(base_path: Path, module_name: str, files: List[str], exports: Dict[str, List[str]]) -> bool:
    """
    Erstellt __init__.py Datei für ein Modul.
    
    Args:
        base_path: UDS3 Wurzelverzeichnis
        module_name: Name des Moduls (Ordner)
        files: Liste der Module-Dateien
        exports: Dict mit Exports
    
    Returns:
        True wenn erfolgreich, False sonst
    """
    module_path = base_path / module_name
    init_file = module_path / "__init__.py"
    
    # Überspringe wenn Ordner nicht existiert
    if not module_path.exists():
        print(f"⏭️  Überspringe {module_name}: Ordner existiert nicht")
        return False
    
    # Generiere Inhalt
    content = generate_init_content(module_name, files, exports)
    
    # Schreibe Datei
    try:
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Zähle Exports
        num_exports = sum(len(exp) for exp in exports.values())
        print(f"✅ {module_name}/__init__.py: {num_exports} Export(s)")
        return True
    except Exception as e:
        print(f"❌ Fehler beim Erstellen von {module_name}/__init__.py: {e}")
        return False

def create_root_init(base_path: Path) -> bool:
    """
    Erstellt Root __init__.py für uds3/ Paket.
    
    Args:
        base_path: UDS3 Wurzelverzeichnis
    
    Returns:
        True wenn erfolgreich
    """
    init_file = base_path / "__init__.py"
    
    content = '''"""
UDS3 - Unified Data Strategy 3.0
Polyglot Persistence Architecture

Auto-generiert von generate_init_files.py
"""

# High-Level Exports
from .core.polyglot_manager import UDS3PolyglotManager

# Version Info
__version__ = "2.0.0"
__author__ = "UDS3 Team"

# Convenience Exports
__all__ = [
    "UDS3PolyglotManager",
]

# Module Discovery
__modules__ = [
    "core",
    "vpb",
    "compliance",
    "integration",
    "operations",
    "query",
    "domain",
    "saga",
    "relations",
    "performance",
    "legacy",
]
'''
    
    try:
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ uds3/__init__.py erstellt")
        return True
    except Exception as e:
        print(f"❌ Fehler beim Erstellen von uds3/__init__.py: {e}")
        return False

def main():
    """Hauptfunktion: Erstellt alle __init__.py Dateien"""
    base_path = Path(__file__).parent
    print(f"🚀 UDS3 __init__.py Generator")
    print(f"📁 Basis-Pfad: {base_path}\n")
    
    success_count = 0
    skip_count = 0
    
    # Root __init__.py
    if create_root_init(base_path):
        success_count += 1
    
    print()  # Leerzeile
    
    # Module __init__.py
    for module_name, config in MODULE_STRUCTURE.items():
        files = config["files"]
        exports = config["exports"]
        
        if create_init_file(base_path, module_name, files, exports):
            success_count += 1
        else:
            skip_count += 1
    
    # Zusammenfassung
    print(f"\n{'='*60}")
    print(f"📊 ZUSAMMENFASSUNG")
    print(f"{'='*60}")
    print(f"✅ Erstellt:     {success_count}")
    print(f"⏭️  Übersprungen: {skip_count}")
    print(f"{'='*60}")
    
    if success_count > 0:
        print("\n🎉 __init__.py Dateien erfolgreich generiert!")
        print("\n📝 Nächste Schritte:")
        print("   1. pytest tests/")
        print("   2. git status")
        print("   3. git commit -m 'Refactor: Restructure UDS3 with domain folders'")
        return 0
    else:
        print("\n⚠️  Keine Dateien erstellt.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
