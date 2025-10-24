# UDS3 - Unified Database Strategy v3.0

**Enterprise-ready Multi-Database Distribution System with PKI-Integrated Security**

UDS3 ist ein hochmodernes Multi-Database Framework für administrative und rechtliche Dokumente mit voller SAGA-Unterstützung, DSGVO-Compliance, Search API und umfassender Sicherheitsarchitektur.

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
- **ChromaDB:** Remote API (fallback mode) ⚠️
- **PostgreSQL:** Active (metadata storage) ✅
- **CouchDB:** Active (file storage) ✅

## 🎯 Roadmap

### v1.4.0 (Current)
- ✅ Search API integrated into core
- ✅ Property-based access (`strategy.search_api`)
- ✅ Backward-compatible migration path
- ✅ 100% test coverage
- ✅ **Security Layer:** PKI-integrated RBAC/RLS with audit logging
- ✅ **Secure Database API:** Row-level security for all database operations
- ✅ **Zero-Trust Architecture:** Certificate-based authentication

### v1.5.0 (Planned - ~3 months)
- Remove deprecated `uds3.uds3_search_api` import
- PostgreSQL execute_sql() API
- ChromaDB Remote API fix
- Enhanced search filters

### v2.0.0 (Future)
- Complete RAG Framework
- Reranking API
- Generation API
- Evaluation API

## 📝 Changelog

### v1.4.0 (2025-10-24)

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

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🔗 Related Projects

- **VERITAS:** Administrative law Q&A system using UDS3
- **Clara:** Document processing pipeline with UDS3
- **Covina:** Process mining with UDS3 backend

---

**Made with ❤️ by the UDS3 Team**
