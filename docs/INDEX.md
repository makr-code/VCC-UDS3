# UDS3 Dokumentation

Dieses Verzeichnis enthält die gesamte Dokumentation des UDS3-Systems.

## 📚 Hauptdokumentation

### Benutzer-Dokumentation
- [README.md](README.md) - Hauptdokumentation und Übersicht
- [UDS3_RAG_README.md](UDS3_RAG_README.md) - RAG-spezifische Dokumentation
- [uds3_rag_requirements.txt](uds3_rag_requirements.txt) - RAG-Abhängigkeiten

### Entwickler-Dokumentation  
- [DEVELOPMENT.md](DEVELOPMENT.md) - Entwicklungsrichtlinien
- [CONTRIBUTING.md](CONTRIBUTING.md) - Beitragsrichtlinien
- [ROADMAP.md](ROADMAP.md) - Entwicklungsroadmap

## 🔄 Change Management

### Releases & Versioning
- [CHANGELOG.md](CHANGELOG.md) - Änderungshistorie
- [RELEASE_INSTRUCTIONS.md](RELEASE_INSTRUCTIONS.md) - Release-Anweisungen
- [GITHUB_RELEASE_v2.3.0.md](GITHUB_RELEASE_v2.3.0.md) - Spezifisches Release

### Git & Entwicklung
- [GIT_COMMIT_COMMANDS.md](GIT_COMMIT_COMMANDS.md) - Git-Kommandos
- [COMMIT_MESSAGE_PHASE3.md](COMMIT_MESSAGE_PHASE3.md) - Commit-Nachrichten Phase 3

## 🧹 Reorganisation & Cleanup

### Aktuelle Reorganisation
- [UDS3_UPDATE_REPORT.md](UDS3_UPDATE_REPORT.md) - Update-Bericht (24. Okt 2025)
- [REORGANISATION_PLAN.md](REORGANISATION_PLAN.md) - Reorganisationsplan

### Historisches Cleanup
- [CLEANUP_PLAN.md](CLEANUP_PLAN.md) - Cleanup-Planung
- [CLEANUP_SUMMARY.md](CLEANUP_SUMMARY.md) - Cleanup-Zusammenfassung

## 📋 Task Management
- [todo.md](todo.md) - Allgemeine TODOs
- [todo_actions.md](todo_actions.md) - Action Items

## 📁 Neue UDS3-Struktur (ab v3.1.0)

Nach der Reorganisation vom 24. Oktober 2025:

```
uds3/
├── core/           # Kernkomponenten (Database, Schemas, Relations)
├── manager/        # Management & Orchestrierung (SAGA, Streaming, Archive)
├── api/            # API-Schnittstellen (Manager, Search, CRUD, Filter)
├── doku/          # Dokumentation (dieses Verzeichnis)
├── archive/       # Legacy-Dateien
├── legacy/        # Rückwärtskompatibilität
├── vpb/           # VPB-Submodule
└── __init__.py    # Hauptexport
```

## 🚀 Quick Start

### Neue API verwenden:
```python
# Einfache Verwendung
from uds3 import get_api
api = get_api()

# Dokument erstellen
doc_id = api.create_document({"title": "Test"})

# Suchen
results = api.search_documents("Verwaltungsrecht")
```

### Legacy-Kompatibilität:
```python
# Alte Imports funktionieren weiterhin
from uds3.legacy import LegacyCore
```

## 📞 Support

Für Fragen zur Dokumentation oder zum System:
- Prüfe die relevante Dokumentation in diesem Verzeichnis
- Für API-Änderungen siehe [UDS3_UPDATE_REPORT.md](UDS3_UPDATE_REPORT.md)
- Für Entwicklung siehe [DEVELOPMENT.md](DEVELOPMENT.md)