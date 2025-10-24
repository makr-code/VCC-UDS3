# UDS3 Verzeichnis-Reorganisation Plan

## Neue Struktur (nur 4 Hauptverzeichnisse im Root)

```
c:\VCC\uds3\
├── core/          # Kernkomponenten
├── manager/       # Management & Orchestrierung  
├── api/           # API-Schnittstellen
├── doku/          # Dokumentation
├── __init__.py    # Hauptexport
├── config.py      # Konfiguration
└── setup.py       # Package Setup
```

## Dateizuordnung und Umbenennung

### core/ (Kernkomponenten)
```
uds3_core.py                    → core/database.py
uds3_database_schemas.py        → core/schemas.py  
uds3_relations_core.py          → core/relations.py
uds3_relations_data_framework.py → core/framework.py
uds3_single_record_cache.py     → core/cache.py
```

### manager/ (Management & Orchestrierung)
```
uds3_saga_orchestrator.py       → manager/saga.py
uds3_saga_mock_orchestrator.py  → manager/saga_mock.py
uds3_saga_compliance.py         → manager/compliance.py
uds3_saga_step_builders.py      → manager/saga_steps.py
uds3_streaming_operations.py    → manager/streaming.py
uds3_streaming_saga_integration.py → manager/streaming_saga.py
uds3_archive_operations.py      → manager/archive.py
uds3_delete_operations.py       → manager/delete.py
uds3_follow_up_orchestrator.py  → manager/followup.py
uds3_complete_process_integration.py → manager/process.py
```

### api/ (API-Schnittstellen)
```
uds3_api_manager.py             → api/manager.py
uds3_database_api.py            → api/database.py
uds3_search_api.py              → api/search.py
uds3_advanced_crud.py           → api/crud.py
uds3_crud_strategies.py         → api/crud_strategies.py
uds3_polyglot_query.py          → api/query.py
uds3_query_filters.py           → api/filters.py
uds3_vector_filter.py           → api/vector_filter.py
uds3_graph_filter.py            → api/graph_filter.py
uds3_relational_filter.py       → api/relational_filter.py
uds3_file_storage_filter.py     → api/file_filter.py
uds3_naming_strategy.py         → api/naming.py
uds3_naming_integration.py      → api/naming_integration.py
uds3_geo_extension.py           → api/geo.py
uds3_process_parser_base.py     → api/parser_base.py
uds3_petrinet_parser.py         → api/petrinet.py
uds3_workflow_net_analyzer.py   → api/workflow.py
```

### doku/ (Dokumentation)
```
README.md                       → doku/README.md
UDS3_UPDATE_REPORT.md          → doku/update_report.md
UDS3_RAG_README.md             → doku/rag_readme.md
CHANGELOG.md                   → doku/changelog.md
DEVELOPMENT.md                 → doku/development.md
CONTRIBUTING.md                → doku/contributing.md
ROADMAP.md                     → doku/roadmap.md
RELEASE_INSTRUCTIONS.md        → doku/release_instructions.md
GIT_COMMIT_COMMANDS.md         → doku/git_commands.md
GITHUB_RELEASE_v2.3.0.md       → doku/github_release.md
CLEANUP_PLAN.md                → doku/cleanup_plan.md
CLEANUP_SUMMARY.md             → doku/cleanup_summary.md
COMMIT_MESSAGE_PHASE3.md       → doku/commit_message.md
todo.md                        → doku/todo.md
todo_actions.md                → doku/todo_actions.md
```

### Verbleiben im Root
```
__init__.py                    # Hauptexport (wird aktualisiert)
config.py                      # Hauptkonfiguration
config_local.py                # Lokale Konfiguration  
setup.py                       # Package Setup
pyproject.toml                 # Python Projekt Config
requirements.txt               # Dependencies
requirements-py313.txt         # Python 3.13 Dependencies
MANIFEST.in                    # Package Manifest
mypy.ini                       # MyPy Configuration
.gitignore                     # Git Ignore
```

### Behalten als Untermodule (bestehende Ordner)
```
archive/                       # Archivierte Dateien
legacy/                        # Legacy Support
vpb/                          # VPB Submodule
tests/                        # Tests
compliance/                   # Compliance Module
integration/                  # Integration Module
operations/                   # Operations Module
query/                        # Query Module
domain/                       # Domain Module
saga/                         # SAGA Module
relations/                    # Relations Module
performance/                  # Performance Module
search/                       # Search Module
security/                     # Security Module
```

### Entfernen/Archivieren
```
build_release.ps1             → archive/utilities/
cleanup_repository.ps1        → archive/utilities/
setup_dev.ps1                → archive/utilities/
create_github_release.ps1    → archive/utilities/
uds3_geo_config.json         → api/ (mit geo.py)
uds3_rag_requirements.txt    → doku/
```

## Vorteile der neuen Struktur

1. **Klare Trennung**: Nur 4 Hauptverzeichnisse statt 30+ Dateien im Root
2. **Kurze Namen**: Keine `uds3_` Präfixe mehr in Dateinamen
3. **Logische Gruppierung**: Verwandte Funktionen zusammengefasst
4. **Bessere Navigation**: Schnelleres Finden von Komponenten
5. **Sauberer Root**: Nur essenzielle Konfigurationsdateien

## Import-Änderungen

**Alt:**
```python
from uds3_core import UnifiedDatabaseStrategy
from uds3_api_manager import UDS3APIManager
from uds3_search_api import UDS3SearchAPI
```

**Neu:**
```python
from uds3.core.database import UnifiedDatabaseStrategy
from uds3.api.manager import UDS3APIManager  
from uds3.api.search import UDS3SearchAPI
```

**Oder über __init__.py (empfohlen):**
```python
from uds3 import UnifiedDatabaseStrategy, UDS3APIManager, UDS3SearchAPI
```