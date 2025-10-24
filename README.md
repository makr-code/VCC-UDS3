# UDS3 - Unified Database Strategy v3.0

**Enterprise-ready Multi-Database Distribution System with PKI-Integrated Security**

UDS3 ist ein hochmodernes Multi-Database Framework für administrative und rechtliche Dokumente AI LLM RAG Framework mit voller SAGA-Unterstützung, DSGVO-Compliance, Search API und umfassender Sicherheitsarchitektur.

---

## 🏛️ Das VCC-Ökosystem

### Vision: Digitale Verwaltungstransformation

Das **VCC (Verwaltungs-Cloud-Collaboration) Ökosystem** ist eine integrierte Plattform für die Digitalisierung öffentlicher Verwaltung mit Fokus auf Rechtssicherheit, Datenschutz und Interoperabilität.

### Kernkomponenten

#### 🔐 **VCC PKI (Public Key Infrastructure)**
*Repository: VCC-PKI*

- **Funktion:** Enterprise-grade Zertifikatsverwaltung und mTLS-Kommunikation
- **Features:**
  - Root CA und Intermediate CA Management
  - Automatische Zertifikatserstellung für Services
  - Certificate Revocation Lists (CRL)
  - Web-GUI und CLI für Administration
- **Integration:** Alle VCC-Services nutzen PKI-Zertifikate für sichere Kommunikation
- **Status:** Production-Ready ✅

#### 👤 **User Service (.NET/C#)**
*Repository: VCC-User*

- **Funktion:** Zentrale Benutzerverwaltung und Authentifizierung
- **Features:**
  - Keycloak-Integration für SSO
  - Active Directory Anbindung
  - Rollen- und Rechteverwaltung
  - JWT-basierte Authentifizierung
- **Integration:** Authentifiziert Zugriffe auf alle VCC-Services
- **Status:** Production-Ready ✅

#### 🗄️ **UDS3 (Unified Database Strategy)**
*Repository: VCC-UDS3 (dieses Projekt)*

- **Funktion:** Multi-Database Backend für strukturierte und unstrukturierte Daten
- **Aufgaben im Ökosystem:**
  - **Datenpersistenz:** Zentrale Speicherebene für alle VCC-Anwendungen
  - **Polyglot Persistence:** Optimale Datenbankwahl je Anwendungsfall
    - **Neo4j:** Rechtshierarchien, Verweisstrukturen, Prozessgraphen
    - **ChromaDB:** Semantische Suche über Rechtsdokumente
    - **PostgreSQL:** Strukturierte Metadaten, Audit-Logs
    - **CouchDB:** Binäre Anhänge, Original-Dokumente
  - **Search API:** Hochleistungs-Suche mit Hybrid-Retrieval (Vector + Graph + Relational)
  - **SAGA Transactions:** Verteilte Transaktionssicherheit über mehrere Datenbanken
  - **DSGVO-Compliance:** Automatische Datenklassifizierung und Löschfristen
  - **Security Layer:** Row-Level Security und RBAC für alle Datenzugriffe
- **Konsumenten:** VERITAS, Clara, Covina (siehe unten)
- **Status:** Production-Ready ✅

#### ⚖️ **VERITAS (Verwaltungsrecht Information & Textanalyse AI System)**
*Repository: VCC-User/services/veritas*

- **Funktion:** AI-gestütztes Rechtsauskunftssystem für Verwaltungsrecht
- **Features:**
  - RAG (Retrieval-Augmented Generation) über Gesetze, Verordnungen, Urteile
  - Natürlichsprachliche Q&A für Verwaltungsmitarbeiter
  - Quellenangaben mit Paragraphen-Verweisen
- **UDS3-Nutzung:**
  - Neo4j: Rechtshierarchien (BauGB → LBO BW → Gemeindesatzung)
  - ChromaDB: Semantische Ähnlichkeitssuche
  - PostgreSQL: Metadaten-Filterung (Geltungsbereich, Datum)
- **Status:** Prototype ⚠️

#### 📄 **Clara (Document Processing & Classification)**
*Repository: VCC-User/services/clara*

- **Funktion:** Automatische Dokumentenverarbeitung und -klassifizierung
- **Features:**
  - OCR für eingescannte Dokumente
  - Automatische Klassifizierung (Bauantrag, Bescheid, Einspruch, etc.)
  - Metadaten-Extraktion (Datum, Aktenzeichen, Beteiligte)
  - Workflow-Routing basierend auf Dokumenttyp
- **UDS3-Nutzung:**
  - PostgreSQL: Dokument-Metadaten und Workflow-Status
  - CouchDB: Original-Dokumente und OCR-Ergebnisse
  - Neo4j: Dokumenten-Beziehungen (Antwort auf Antrag, etc.)
- **Status:** Prototype ⚠️

#### 🔄 **Covina (Process Mining & Orchestration)**
*Repository: VCC-User/services/covina*

- **Funktion:** Verwaltungsprozess-Analyse und -Optimierung
- **Features:**
  - Process Mining über historische Vorgänge
  - Bottleneck-Erkennung in Genehmigungsverfahren
  - BPMN-Import und -Export
  - Workflow-Orchestrierung
- **UDS3-Nutzung:**
  - Neo4j: Prozessgraphen und Ablaufmodelle
  - PostgreSQL: Event-Logs und Performance-Metriken
- **Status:** Prototype ⚠️

### Systemarchitektur

```
┌─────────────────────────────────────────────────────────────────┐
│                      VCC Ökosystem                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   │
│  │ VERITAS  │   │  Clara   │   │ Covina   │   │  User    │   │
│  │   AI     │   │  Docs    │   │ Process  │   │  Mgmt    │   │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘   │
│       │              │              │              │          │
│       └──────────────┴──────────────┴──────────────┘          │
│                           │                                    │
│              ┌────────────▼────────────┐                       │
│              │    UDS3 Backend         │                       │
│              │  (Multi-DB Strategy)    │                       │
│              └─┬─────┬─────┬─────┬────┘                       │
│                │     │     │     │                             │
│         ┌──────▼┐ ┌──▼──┐ ┌▼───┐ ┌▼────┐                     │
│         │ Neo4j │ │Chroma││PgSQL││Couch│                     │
│         └───────┘ └─────┘ └────┘ └─────┘                     │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │           VCC PKI (Certificate Authority)                │ │
│  │    - Root CA  - Service Certs  - mTLS  - CRL            │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │         Keycloak SSO + Active Directory Stub             │ │
│  └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### UDS3 als Herzstück des Ökosystems

**Warum Multi-Database?**

Verwaltungsdaten sind heterogen:
- **Strukturiert:** Bürgerdaten, Aktenzeichen → PostgreSQL
- **Graphbasiert:** Gesetzeshierarchien, Prozessabläufe → Neo4j  
- **Semantisch:** Volltext-Rechtsdokumente → ChromaDB (Vector Search)
- **Binär:** Scans, PDFs, Unterschriften → CouchDB (File Storage)

UDS3 vereint diese Speichertypen unter einer einheitlichen API und ermöglicht:
- **Transaktionssicherheit** über Datenbank-Grenzen (SAGA Pattern)
- **Optimale Performance** durch Spezialisierung (Right Tool for the Job)
- **DSGVO-Konformität** durch zentrale Compliance-Schicht
- **Sicherheit** durch PKI-Integration und Row-Level Security

### Deployment-Modell

**Containerisiert mit Docker Compose:**
```yaml
services:
  uds3-backend:     # UDS3 API Gateway
  neo4j:            # Graph Database
  chromadb:         # Vector Database
  postgresql:       # Relational Database
  couchdb:          # Document Database
  
  veritas:          # AI Legal Assistant
  clara:            # Document Processor
  covina:           # Process Mining
  
  user-service:     # User Management
  keycloak:         # SSO Provider
  pki-manager:      # Certificate Authority
```

**Produktiv-Umgebung (geplant):**
- Kubernetes mit Helm Charts
- Automatisches Scaling für UDS3 und AI-Services
- Hochverfügbarkeit: PostgreSQL (Patroni), Neo4j (Cluster)
- Monitoring: Prometheus + Grafana

---

## 🚀 Quick Start

### Installation

```bash
pip install -e .
```

### Basic Usage

```python
from uds3 import get_optimized_unified_strategy

# Initialize strategy
strategy = get_optimized_unified_strategy()

# Create document
doc = strategy.saga_crud.create_document(
    content="Beispiel-Dokument",
    metadata={"type": "regulation"}
)

# Search documents (NEW in v1.4.0 ⭐)
results = await strategy.search_api.hybrid_search(
    query="Photovoltaik Anforderungen",
    top_k=10
)
```

## ✨ Features

### � Security Layer (NEW in v1.4.0 ⭐)

Enterprise-grade security with PKI integration and least privilege access control:

```python
from security import User, UserRole, UDS3SecurityManager
from database.secure_api import SecureDatabaseAPI

# Initialize security with PKI
security = UDS3SecurityManager(
    pki_ca_cert_path="/path/to/ca.pem",
    enable_pki_auth=True
)

# Wrap database API with security
secure_api = SecureDatabaseAPI(database_api, security)

# All operations require authenticated user
user = User("alice", "alice", "alice@vcc.local", UserRole.USER)
doc_id = secure_api.create(user, {"title": "My Document"})
docs = secure_api.read(user, {})  # Only sees own documents
```

**Security Features:**
- ✅ **Row-Level Security (RLS):** Users can only access their own data
- ✅ **Role-Based Access Control (RBAC):** 5 roles, 15 granular permissions
- ✅ **PKI Certificate Authentication:** Integration with VCC PKI system
- ✅ **Comprehensive Audit Logging:** All operations tracked
- ✅ **API Rate Limiting:** DOS protection and fair resource allocation
- ✅ **Zero-Trust Architecture:** Every request authenticated and authorized

See [Security Documentation](docs/SECURITY.md) for complete details.

### �🔍 Search API (NEW in v1.4.0)

High-level search interface across Vector, Graph and Relational backends:

```python
from uds3 import get_optimized_unified_strategy
from uds3.search import SearchQuery

strategy = get_optimized_unified_strategy()

# Vector Search (Semantic Similarity)
results = await strategy.search_api.vector_search(embedding, top_k=10)

# Graph Search (Relationships)
results = await strategy.search_api.graph_search("Photovoltaik", top_k=10)

# Hybrid Search (Best of Both Worlds)
query = SearchQuery(
    query_text="Was regelt § 58 LBO BW?",
    top_k=10,
    search_types=["vector", "graph"],
    weights={"vector": 0.5, "graph": 0.5}
)
results = await strategy.search_api.hybrid_search(query)
```

**Benefits:**
- ✅ **Unified API:** One interface for all search types
- ✅ **Type Safety:** Dataclasses for queries and results
- ✅ **Error Handling:** Automatic retry logic and graceful degradation
- ✅ **Lazy Loading:** Efficient resource management
- ✅ **Production Ready:** 100% test coverage

See [UDS3 Search API Production Guide](docs/UDS3_SEARCH_API_PRODUCTION_GUIDE.md) for details.

### 📊 Multi-Database Support

- **Vector DB (ChromaDB):** Semantic search, content embeddings
- **Graph DB (Neo4j):** Relationships, hierarchies, network analysis
- **Relational DB (PostgreSQL):** Structured metadata, fast filtering
- **File Storage (CouchDB):** Binary assets, original files

### 🔄 SAGA Pattern

Distributed transactions with automatic compensation:

```python
from uds3.saga import SagaDatabaseCRUD

saga_crud = strategy.saga_crud

# Transactional document creation
doc = saga_crud.create_document(
    content="...",
    metadata={...}
)
```

### 🔒 DSGVO Compliance

Built-in data protection:

```python
from uds3.dsgvo import DSGVOOperationType, PIIType

# Track PII processing
strategy.dsgvo_core.track_processing(
    operation=DSGVOOperationType.READ,
    pii_type=PIIType.NAME,
    subject_id="user_123"
)

# Anonymize after retention
strategy.dsgvo_core.anonymize_expired_data()
```

### 🗑️ Advanced CRUD Operations

- **Soft Delete:** Recoverable deletion with archive
- **Hard Delete:** Permanent removal with cascade
- **Restore:** Recover soft-deleted documents
- **Archive:** Long-term storage with retention policies

## 📚 Documentation

- **[Security Architecture](docs/SECURITY.md)** - Complete security layer documentation (PKI, RBAC, RLS, Audit)
- **[Search API Production Guide](docs/UDS3_SEARCH_API_PRODUCTION_GUIDE.md)** - Complete search API documentation
- **[Search API Integration Decision](docs/UDS3_SEARCH_API_INTEGRATION_DECISION.md)** - Architecture decision
- **[PostgreSQL/CouchDB Integration](docs/POSTGRES_COUCHDB_INTEGRATION.md)** - Backend integration guide

## 🔄 Migration from v1.3.x

### Search API (v1.4.0)

**Old Way (Deprecated):**
```python
from uds3.uds3_search_api import UDS3SearchAPI
from uds3.uds3_core import get_optimized_unified_strategy

strategy = get_optimized_unified_strategy()
search_api = UDS3SearchAPI(strategy)
results = await search_api.hybrid_search(query)
```

**New Way (Recommended ⭐):**
```python
from uds3 import get_optimized_unified_strategy

strategy = get_optimized_unified_strategy()
results = await strategy.search_api.hybrid_search(query)
```

**Benefits:**
- -50% imports (2 → 1)
- -33% code (3 LOC → 2 LOC)
- +100% discoverability (IDE autocomplete)

The old import path (`uds3.uds3_search_api`) still works with a deprecation warning and will be removed in v1.5.0 (~3 months).

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=uds3 --cov-report=html

# Run specific test suite
pytest tests/test_search_api.py -v
```

## 📊 Backends Status

- **Neo4j:** 1930 documents, PRODUCTION-READY ✅
- **ChromaDB:** Remote API, PRODUCTION-READY ✅
- **PostgreSQL:** Active (metadata storage) ✅
- **CouchDB:** Active (file storage) ✅

## 🎯 Roadmap

### v1.5.0 (Current - October 2025)
- ✅ All backends production-ready (ChromaDB, Neo4j, PostgreSQL, CouchDB)
- ✅ Removed deprecated `uds3.uds3_search_api` import
- ✅ Documentation improvements and status updates
- 🔄 PostgreSQL execute_sql() API (in progress)
- 🔄 Enhanced search filters (planned)
- 🔄 Advanced reranking algorithms (planned)

### v1.4.0 (Completed - October 2025)
- ✅ Search API integrated into core
- ✅ Property-based access (`strategy.search_api`)
- ✅ Backward-compatible migration path
- ✅ 100% test coverage
- ✅ **Security Layer:** PKI-integrated RBAC/RLS with audit logging
- ✅ **Secure Database API:** Row-level security for all database operations
- ✅ **Zero-Trust Architecture:** Certificate-based authentication

### v2.0.0 (Future)
- Complete RAG Framework
- Reranking API
- Generation API
- Evaluation API

## 📝 Changelog

### v1.5.0 (2025-10-24) 🚀 PRODUCTION RELEASE

**All Backends Production-Ready:**
- ✅ **ChromaDB:** Remote API fully operational (removed fallback mode)
- ✅ **Neo4j:** 1930+ documents validated
- ✅ **PostgreSQL:** Active metadata storage
- ✅ **CouchDB:** Active file storage

**Breaking Changes:**
- ⚠️ **Removed:** Deprecated `uds3.uds3_search_api` module
  - Migration: Use `strategy.search_api` property instead
  - Deprecation period: 3 months (announced in v1.4.0)

**Documentation:**
- 📄 Updated backend status across all documentation
- 📄 Removed obsolete "fallback mode" warnings
- 📄 Updated roadmap and version information

### v1.4.0 (2025-10-24) 🔒 SECURITY RELEASE

**Security Features (NEW ⭐):**
- ✨ **Row-Level Security (RLS):** Automatic data ownership filtering
- ✨ **RBAC System:** 5 roles (SYSTEM, ADMIN, SERVICE, USER, READONLY) with 15 granular permissions
- ✨ **PKI Authentication:** Certificate-based authentication with VCC PKI integration
- ✨ **Audit Logging:** Complete audit trail for all database operations
- ✨ **Rate Limiting:** DOS protection with per-role quotas
- ✨ **Secure Database API:** Security wrapper for all database backends
- ✨ **Zero-Trust Architecture:** Every request authenticated and authorized

**Search Features:**
- ✨ **Search API Property:** Direct access via `strategy.search_api` (lazy-loaded)
- ✨ **Improved DX:** -50% imports, +100% discoverability
- ✨ **Type Safety:** Enhanced dataclasses for SearchQuery and SearchResult

**Migration:**
- ✅ **Backward Compatible:** Old import path still works with deprecation warning
- ⏱️ **Deprecation Period:** 3 months (removed in v1.5.0)
- 📚 **Migration Guide:** See README and docs/UDS3_SEARCH_API_INTEGRATION_DECISION.md

**Testing:**
- ✅ 100% test coverage for Search API
- ✅ 3/3 security test suites passed
- ✅ 3/3 integration test suites passed
- ✅ Production validation with 1930 Neo4j documents

**Documentation:**
- 📄 New: docs/SECURITY.md (680 LOC) - Complete security architecture
- 📄 New: UDS3_SEARCH_API_PRODUCTION_GUIDE.md (1950 LOC)
- 📄 New: UDS3_SEARCH_API_INTEGRATION_DECISION.md (2000 LOC)
- 📄 Updated: README.md with Security and Search API examples

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

**Government & Public Sector Partners:**  
Organizations working in government or public administration are especially encouraged to contribute improvements back to the project. See our [Government Partnership Commons Clause](LICENSE) for details. Contributors are recognized in [CONTRIBUTORS.md](CONTRIBUTORS.md).

## 📄 License

**MIT License with Government Partnership Commons Clause**

This project is licensed under the permissive MIT License, with a non-binding request for government and public sector users to share improvements back to the community. 

- ✅ **Free to use** commercially and privately
- ✅ **No legal obligation** to share modifications
- 🤝 **Encouraged to contribute** improvements, especially for public sector use cases

See [LICENSE](LICENSE) file for complete details.

**Why this license?** UDS3 is designed for government partnerships and public administration. Shared improvements strengthen security and reduce duplicate efforts across agencies, while respecting the freedom granted by MIT.

## 👥 Contributors

See [CONTRIBUTORS.md](CONTRIBUTORS.md) for organizations and individuals who have contributed to UDS3.

## 🔗 Related Projects

- **VERITAS:** Administrative law Q&A system using UDS3
- **Clara:** Document processing pipeline with UDS3
- **Covina:** Process mining with UDS3 backend

---

**Developed by Martin Krüger** (ma.krueger@outlook.com)  
**Made with ❤️ for Government & Public Sector**
