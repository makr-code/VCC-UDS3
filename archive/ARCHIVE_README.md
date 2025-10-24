# UDS3 Archive - Legacy Components and Files

## Archivierungsstrategie (24. Oktober 2025)

Diese Archivierung erfolgt zur Bereinigung und Optimierung des UDS3-Systems. Alle archivierten Dateien bleiben für Referenzzwecke erhalten.

## Archivierte Kategorien

### 1. Examples (`/archive/examples/`)
- **Zweck**: Demo- und Beispieldateien
- **Status**: Funktional aber nicht für Produktion
- **Dateien**: Alle `examples_*.py` Dateien
- **Grund**: Trennung von Produktionscode und Demonstrations-Code

### 2. Legacy Components (`/archive/legacy_components/`)
- **Zweck**: Veraltete Komponenten mit VERITAS-Schutz
- **Status**: Veraltet, ersetzt durch neuere Implementierungen
- **Dateien**: Komponenten vom 1. Oktober 2025 mit Lizenzschutz
- **Grund**: Veraltete APIs und Datenstrukturen

### 3. Deprecated APIs (`/archive/deprecated_apis/`)
- **Zweck**: Veraltete API-Komponenten
- **Status**: Funktional aber nicht mehr empfohlen
- **Dateien**: Ältere Prozess-Parser und Filter-Implementierungen
- **Grund**: Ersetzt durch modernere, konsolidierte APIs

### 4. Utilities (`/archive/utilities/`)
- **Zweck**: Hilfsskripte und Tools
- **Status**: Funktional aber nicht kernrelevant
- **Dateien**: Build-Scripts, Migration-Tools
- **Grund**: Reduzierung der Hauptverzeichnis-Komplexität

## Aktuelle Kernkomponenten (verbleiben im Hauptverzeichnis)

### Core API
- `uds3_core.py` - Hauptkomponente (aktualisiert 18. Oktober)
- `uds3_database_schemas.py` - Database Schemas (extrahiert und optimiert)
- `uds3_search_api.py` - Suchfunktionalität (aktualisiert 11. Oktober)

### Relations Framework
- `uds3_relations_core.py` - Beziehungsmanagement
- `uds3_relations_data_framework.py` - Datenframework

### SAGA Orchestration
- `uds3_saga_orchestrator.py` - SAGA-Pattern Implementation
- `uds3_saga_mock_orchestrator.py` - Mock für Testing

### Configuration
- `config.py` - Hauptkonfiguration (aktualisiert 24. Oktober)
- `config_local.py` - Lokale Überschreibungen
- `setup.py` - Package Setup

## Migration Notes

Alle archivierten Dateien können bei Bedarf wiederhergestellt werden. Die Legacy-Ordnerstruktur (`/legacy/`) bleibt bestehen für Kompatibilität.

## Nächste Schritte

1. ✅ Archivordner erstellt
2. 🔄 Legacy-Dateien verschieben
3. 📝 APIs aktualisieren und konsolidieren
4. 🧹 Import-Statements bereinigen
5. 🔍 Abhängigkeiten validieren