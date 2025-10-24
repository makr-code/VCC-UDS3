#!/usr/bin/env python3
"""
UDS3 File Renaming Tool
Automatisches Umbenennen und Verschieben von Dateien mit Git-History-Erhaltung
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Mapping: alt → neu (Zielpfad relativ zu uds3/)
FILE_MAPPINGS = {
    # === CORE MODULE ===
    "uds3_polyglot_manager.py": "core/polyglot_manager.py",
    "embeddings.py": "core/embeddings.py",
    "llm_ollama.py": "core/llm_ollama.py",
    "rag_pipeline.py": "core/rag_pipeline.py",
    
    # === VPB MODULE ===
    "uds3_vpb_operations.py": "vpb/operations.py",
    "uds3_bpmn_process_parser.py": "vpb/parser_bpmn.py",
    "uds3_epk_process_parser.py": "vpb/parser_epk.py",
    "uds3_petri_net_parser.py": "vpb/parser_petri.py",
    "uds3_vpb_dataminer.py": "vpb/dataminer.py",
    "uds3_vpb_gap_detection.py": "vpb/gap_detection.py",
    "uds3_process_migration.py": "vpb/migration.py",
    
    # === COMPLIANCE MODULE ===
    "uds3_dsgvo_core.py": "compliance/dsgvo_core.py",
    "uds3_security_quality.py": "compliance/security_quality.py",
    "uds3_identity_service.py": "compliance/identity_service.py",
    "uds3_audit_logger.py": "compliance/audit_logger.py",
    
    # === INTEGRATION MODULE ===
    "saga_multi_db_integration.py": "integration/saga_integration.py",
    "adaptive_multi_db_strategy.py": "integration/adaptive_strategy.py",
    "uds3_multi_db_distributor.py": "integration/distributor.py",
    "uds3_backend_governance.py": "integration/backend_governance.py",
    "uds3_module_status_manager.py": "integration/module_status.py",
    
    # === OPERATIONS MODULE ===
    "uds3_transaction_manager.py": "operations/transaction_manager.py",
    "uds3_backup_restore.py": "operations/backup_restore.py",
    "uds3_migration_manager.py": "operations/migration_manager.py",
    "uds3_health_monitor.py": "operations/health_monitor.py",
    
    # === QUERY MODULE ===
    "uds3_semantic_query_engine.py": "query/semantic_engine.py",
    "uds3_query_optimizer.py": "query/optimizer.py",
    "uds3_query_cache.py": "query/cache.py",
    "uds3_llm_query_translator.py": "query/llm_translator.py",
    
    # === DOMAIN MODULE ===
    "uds3_domain_model_manager.py": "domain/model_manager.py",
    "uds3_domain_validator.py": "domain/validator.py",
    "uds3_domain_migrator.py": "domain/migrator.py",
    
    # === SAGA MODULE (Advanced Transaction Patterns) ===
    "saga_coordinator.py": "saga/coordinator.py",
    "saga_compensation.py": "saga/compensation.py",
    "saga_logger.py": "saga/logger.py",
    
    # === RELATIONS MODULE ===
    "relation_db_adapter.py": "relations/adapter.py",
    "relation_query_builder.py": "relations/query_builder.py",
    "relation_migration_tool.py": "relations/migration_tool.py",
    
    # === PERFORMANCE MODULE ===
    "benchmark_polyglot_operations.py": "performance/benchmark_operations.py",
    "performance_monitor.py": "performance/monitor.py",
    "load_test_framework.py": "performance/load_test.py",
    
    # === LEGACY (zu deprecaten) ===
    "uds3_core.py": "legacy/core.py",
    "rag_enhanced_llm_integration.py": "legacy/rag_enhanced.py",
    "uds3_auto_schema.py": "legacy/auto_schema.py",
    "uds3_vector_db_adapter.py": "legacy/vector_db_adapter.py",
    
    # === EXAMPLES ARCHIV ===
    "test_combined_vpb_uds3.py": "examples_archive/test_combined_vpb_uds3.py",
    "test_uds3_core.py": "examples_archive/test_uds3_core.py",
    "test_adaptive_routing.py": "examples_archive/test_adaptive_routing.py",
    "test_saga_integration.py": "examples_archive/test_saga_integration.py",
}

def run_git_command(command: List[str], cwd: Path) -> Tuple[bool, str]:
    """Führt Git-Befehl aus und gibt (success, output) zurück"""
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)

def is_git_repo(path: Path) -> bool:
    """Prüft ob Pfad ein Git-Repository ist"""
    success, _ = run_git_command(["git", "rev-parse", "--git-dir"], path)
    return success

def file_exists_in_git(path: Path, file: str) -> bool:
    """Prüft ob Datei im Git-Index existiert"""
    success, _ = run_git_command(["git", "ls-files", "--error-unmatch", file], path)
    return success

def rename_file_with_git(base_path: Path, old_path: str, new_path: str) -> Tuple[bool, str]:
    """
    Benennt Datei mit Git mv um (erhält History).
    
    Args:
        base_path: Basis-Pfad (uds3/)
        old_path: Alter Pfad relativ zu base_path
        new_path: Neuer Pfad relativ zu base_path
    
    Returns:
        (success, message)
    """
    old_file = base_path / old_path
    new_file = base_path / new_path
    
    # Prüfe ob Quelldatei existiert
    if not old_file.exists():
        return False, f"❌ Quelldatei existiert nicht: {old_path}"
    
    # Prüfe ob Zieldatei bereits existiert
    if new_file.exists():
        return False, f"⚠️  Zieldatei existiert bereits: {new_path}"
    
    # Erstelle Ziel-Ordner falls nötig
    new_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Git mv (erhält History)
    if is_git_repo(base_path) and file_exists_in_git(base_path, old_path):
        success, output = run_git_command(
            ["git", "mv", old_path, new_path],
            base_path
        )
        if success:
            return True, f"✅ Git mv: {old_path} → {new_path}"
        else:
            return False, f"❌ Git mv fehlgeschlagen: {output}"
    else:
        # Fallback: Normales mv (falls nicht in Git)
        try:
            old_file.rename(new_file)
            return True, f"✅ Verschoben (nicht in Git): {old_path} → {new_path}"
        except Exception as e:
            return False, f"❌ Fehler beim Verschieben: {e}"

def main():
    """Hauptfunktion: Führt alle Umbenennungen durch"""
    base_path = Path(__file__).parent
    print(f"🚀 UDS3 File Renaming Tool")
    print(f"📁 Basis-Pfad: {base_path}")
    print(f"📝 {len(FILE_MAPPINGS)} Dateien zu verarbeiten\n")
    
    if not is_git_repo(base_path):
        print("⚠️  WARNUNG: Kein Git-Repository gefunden. History wird NICHT erhalten!")
        response = input("Trotzdem fortfahren? (ja/nein): ")
        if response.lower() != "ja":
            print("❌ Abbruch.")
            return 1
    
    success_count = 0
    fail_count = 0
    skip_count = 0
    
    # Sortiere nach Ordner (damit zusammenhängende Dateien gruppiert sind)
    sorted_mappings = sorted(FILE_MAPPINGS.items(), key=lambda x: x[1])
    
    for old_path, new_path in sorted_mappings:
        old_file = base_path / old_path
        
        # Überspringe wenn Datei nicht existiert
        if not old_file.exists():
            print(f"⏭️  Überspringe (existiert nicht): {old_path}")
            skip_count += 1
            continue
        
        success, message = rename_file_with_git(base_path, old_path, new_path)
        print(message)
        
        if success:
            success_count += 1
        else:
            fail_count += 1
    
    # Zusammenfassung
    print(f"\n{'='*60}")
    print(f"📊 ZUSAMMENFASSUNG")
    print(f"{'='*60}")
    print(f"✅ Erfolgreich: {success_count}")
    print(f"❌ Fehler:      {fail_count}")
    print(f"⏭️  Übersprungen: {skip_count}")
    print(f"{'='*60}")
    
    if fail_count > 0:
        print("\n⚠️  Es sind Fehler aufgetreten. Bitte prüfen Sie die Ausgabe oben.")
        return 1
    else:
        print("\n🎉 Alle Dateien erfolgreich verschoben!")
        print("\n📝 Nächste Schritte:")
        print("   1. python update_imports.py")
        print("   2. python generate_init_files.py")
        print("   3. pytest tests/")
        return 0

if __name__ == "__main__":
    sys.exit(main())
