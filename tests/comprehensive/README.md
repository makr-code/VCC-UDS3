# UDS3 Comprehensive Test Suite

Umfangreiche Test-Suite für das UDS3-System zur Fehler- und Bug-Erkennung.

## 📋 Test-Kategorien

### 1. Database Backend Tests (`test_database_backends.py`)
- **SQLite**: Connection, CRUD, Transaktionen, Concurrency, Performance
- **File Storage**: Store/Retrieve, Metadata, List/Delete
- **Fehlerbehandlung**: Ungültige Queries, Connection Failures
- **Performance**: Bulk Insert (1000 Einträge < 5s), Query Performance (100 Queries < 1s)

### 2. SAGA Orchestration Tests (`test_saga_orchestration.py`)
- **Erfolgreiche SAGAs**: Multi-Step Execution
- **Compensation**: Rollback bei Fehlern
- **Idempotenz**: Wiederholte Ausführung mit gleicher ID
- **Recovery**: Retry-Mechanismen
- **Step Builders**: DatabaseInsertStep, SAGA-Chains

### 3. Streaming & Batch Tests (`test_streaming_operations.py`)
- **Streaming**: Backpressure, Error Recovery
- **Batch Processing**: Bulk Insert/Update
- **Adaptive Batching**: Dynamische Batch-Größen
- **Single-Record Cache**: Hit/Miss, LRU Eviction
- **Memory Management**: Bounded Streaming

### 4. Query Filter Tests (`test_query_filters.py`)
- **Relational Filters**: Equality, Combined, Date Range, LIKE, IN
- **Vector Filters**: Cosine Similarity, Euclidean Distance, Threshold
- **Graph Filters**: Relationships, Paths, Subgraphs
- **File Storage Filters**: Extension, Size, Content, Date
- **Combined Filters**: AND/OR Kombinationen

### 5. Compliance & Security Tests (`test_compliance_security.py`)
- **DSGVO**: Anonymisierung, Recht auf Vergessenwerden (Art. 17), Datenportabilität (Art. 20)
- **Anonymisierung**: Name, Email, Telefon, Adresse
- **Security**: Quality Checks, Vulnerability Scans
- **Audit Logging**: Access Logs, Modification Logs, Audit Trails
- **Access Control**: RBAC, Permission Inheritance
- **Consent Management**: Einwilligungsverfolgung
- **Data Retention**: Automatisierte Löschung

### 6. Integration Tests (`test_integration_full.py`)
- **Document Workflow**: Ingestion → Processing → Retrieval
- **Multi-Database Sync**: Cross-Database Synchronization
- **SAGA + Streaming**: Kombination beider Patterns
- **GDPR Compliance**: End-to-End DSGVO-konforme Workflows
- **Error Recovery**: System-weite Fehlerbehandlung

### 7. Test Infrastructure
- **pytest.ini**: Konfiguration (Markers, Logging, Timeouts)
- **conftest.py**: Shared Fixtures (Databases, Test Data, Helpers)

## 🚀 Test-Ausführung

### Alle Tests ausführen
```bash
pytest tests/comprehensive/
```

### Einzelne Kategorie ausführen
```bash
pytest tests/comprehensive/test_database_backends.py -v
pytest tests/comprehensive/test_saga_orchestration.py -v
pytest tests/comprehensive/test_streaming_operations.py -v
pytest tests/comprehensive/test_query_filters.py -v
pytest tests/comprehensive/test_compliance_security.py -v
pytest tests/comprehensive/test_integration_full.py -v
```

### Mit Marker filtern
```bash
pytest -m database        # Nur Database-Tests
pytest -m saga            # Nur SAGA-Tests
pytest -m integration     # Nur Integrationstests
pytest -m performance     # Nur Performance-Tests
```

### Mit Coverage-Report
```bash
pytest tests/comprehensive/ --cov=database --cov=saga --cov=streaming --cov=search --cov=compliance --cov-report=html
```

### Parallel ausführen (schneller)
```bash
pytest tests/comprehensive/ -n auto
```

## 📊 Erwartete Ergebnisse

### Performance-Benchmarks
- **Bulk Insert**: 1000 Einträge in < 5 Sekunden
- **Query Performance**: 100 Queries in < 1 Sekunde
- **Streaming**: Memory bleibt begrenzt bei großen Datasets

### Compliance-Anforderungen
- **DSGVO Art. 17**: Recht auf Vergessenwerden funktioniert
- **DSGVO Art. 20**: Datenportabilität funktioniert
- **Anonymisierung**: Personenbezogene Daten werden korrekt anonymisiert
- **Audit Logs**: Alle Zugriffe werden protokolliert

### Error Handling
- **SAGA Compensation**: Rollback funktioniert bei Fehlern
- **Transaction Rollback**: Ungültige Operationen werden zurückgerollt
- **Recovery**: Failed SAGAs werden automatisch wiederholt

## 🔧 Fixtures (tests/conftest.py)

### Database Fixtures
- `sqlite_db`: Leere SQLite-Datenbank
- `populated_db`: Datenbank mit Testdaten (Documents, Users)

### Data Fixtures
- `sample_text_data`: Text-Samples (short, medium, long, unicode, etc.)
- `sample_numeric_data`: Numerische Daten (integers, floats, negatives)
- `mock_embeddings`: Mock-Vektoren für Embedding-Tests
- `sample_file_data`: Temporäre Test-Dateien

### Helper Fixtures
- `create_test_table`: Factory für Tabellen-Erstellung
- `insert_test_data`: Factory für Daten-Insertion
- `benchmark_timer`: Performance-Messung
- `temp_dir`: Temporäres Verzeichnis (Session-Scope)

## 📝 Test-Abdeckung

### Getestete Module
- `database/database_api_sqlite.py`
- `database/database_api_file_storage.py`
- `saga/saga_orchestrator.py`
- `saga/saga_compensations.py`
- `saga/saga_error_recovery.py`
- `saga/saga_step_builders.py`
- `streaming/streaming_operations.py`
- `streaming/batch_operations.py`
- `streaming/single_record_cache.py`
- `search/query_filters_relational.py`
- `search/query_filters_vector.py`
- `search/query_filters_graph.py`
- `search/query_filters_file_storage.py`
- `compliance/dsgvo_core.py`
- `compliance/security_quality.py`
- `compliance/audit_logger.py`

### Test-Statistiken (Ziel)
- **Total Tests**: ~100+
- **Database Tests**: ~15
- **SAGA Tests**: ~10
- **Streaming Tests**: ~15
- **Filter Tests**: ~20
- **Compliance Tests**: ~20
- **Integration Tests**: ~10

## 🐛 Bug-Erkennung

Diese Test-Suite ist darauf ausgelegt, folgende Bug-Kategorien zu finden:

1. **Race Conditions**: Concurrency-Tests in Database Backends
2. **Memory Leaks**: Memory Management in Streaming
3. **Transaction Issues**: Rollback-Tests in SAGA
4. **Data Integrity**: CRUD-Tests, Constraint-Validierung
5. **Security Vulnerabilities**: DSGVO-Compliance, Anonymisierung
6. **Performance Regressions**: Performance-Benchmarks
7. **Integration Issues**: End-to-End Workflows

## 📦 Abhängigkeiten

```bash
pip install pytest pytest-cov pytest-xdist pytest-timeout numpy
```

## 🔄 CI/CD Integration

Tests können in GitHub Actions integriert werden:

```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.13'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-xdist
      - name: Run tests
        run: pytest tests/comprehensive/ -v --cov --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## 📈 Nächste Schritte

1. **Test-Ausführung**: `pytest tests/comprehensive/ -v`
2. **Fehler beheben**: Alle failing Tests analysieren
3. **Coverage erhöhen**: Fehlende Edge Cases hinzufügen
4. **Performance optimieren**: Benchmarks bei Bedarf anpassen
5. **Dokumentation**: Gefundene Bugs dokumentieren
