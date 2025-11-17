# Phase 2 Planning: PostgreSQL + CouchDB Batch Operations

**Date:** 20. Oktober 2025  
**Version:** UDS3 2.2.0 (planned)  
**Status:** 📋 Planning Phase  
**Estimated Time:** 3-4 hours

---

## 🎯 Objective

Extend UDS3 batch operations to PostgreSQL and CouchDB for complete database coverage.

**Phase 1 (COMPLETE):**
- ✅ ChromaDB: 100 vectors/call (80x speedup)
- ✅ Neo4j: 1000 rels/query (100-187x speedup)

**Phase 2 (THIS PHASE):**
- 📋 PostgreSQL: 100 documents/batch (+50-100x throughput)
- 📋 CouchDB: 100 documents/batch (+100-500x throughput)

---

## 📊 Current Implementation Analysis

### PostgreSQL (database_api_postgresql.py)

**Current Method:** `insert_document()` (Lines 186-250)

```python
def insert_document(self, document_id: str, file_path: str, classification: str,
                   content_length: int, legal_terms_count: int, 
                   created_at: Optional[str] = None,
                   quality_score: Optional[float] = None,
                   processing_status: str = 'completed') -> Dict[str, Any]:
    """Single document insert with ON CONFLICT"""
    self.cursor.execute("""
        INSERT INTO documents 
        (document_id, file_path, classification, content_length, 
         legal_terms_count, created_at, quality_score, processing_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (document_id) 
        DO UPDATE SET ...
    """, (document_id, ...))
    self.conn.commit()  # ❌ One commit per document!
```

**Problems:**
- 1 SQL INSERT per document
- 1 COMMIT per document (slow!)
- High network overhead (100 docs = 100 round-trips)
- Inefficient for bulk ingestion

**Performance:**
```
Current: 100 documents = ~10 seconds (10 inserts/second)
```

### CouchDB (database_api_couchdb.py)

**Current Method:** `create_document()` (Lines 84-150)

```python
def create_document(self, doc: Dict[str, Any], doc_id: Optional[str] = None) -> str:
    """Single document insert with idempotency"""
    if doc_id:
        # Check if exists (1 HTTP call)
        try:
            existing_doc = self.db[doc_id]
            return doc_id  # Already exists
        except:
            pass
        
        # Create document (1 HTTP call)
        self.db[doc_id] = doc
        return doc_id
```

**Problems:**
- 1-2 HTTP calls per document
- High latency (network round-trips)
- No batching support
- Inefficient for bulk ingestion

**Performance:**
```
Current: 100 documents = ~50 seconds (2 inserts/second)
```

---

## 🚀 Proposed Solution

### PostgreSQL Batch Inserter

**Technology:** `psycopg2.extras.execute_batch()`

**Features:**
- Batch 100 documents in single SQL statement
- Single COMMIT for entire batch
- Thread-safe operations
- Auto-fallback on errors
- Context manager support

**Implementation Pattern:**
```python
from psycopg2.extras import execute_batch

class PostgreSQLBatchInserter:
    def __init__(self, backend: PostgreSQLRelationalBackend, batch_size: int = 100):
        self.backend = backend
        self.batch_size = batch_size
        self.batch = []
        self._lock = threading.Lock()
        self.stats = {'batches': 0, 'fallbacks': 0}
    
    def add(self, document_id: str, file_path: str, classification: str,
            content_length: int, legal_terms_count: int, **kwargs):
        """Add document to batch"""
        with self._lock:
            self.batch.append((document_id, file_path, classification, ...))
            
            if len(self.batch) >= self.batch_size:
                self._flush_unlocked()  # Auto-flush
    
    def flush(self) -> bool:
        """Flush batch to database"""
        with self._lock:
            return self._flush_unlocked()
    
    def _flush_unlocked(self) -> bool:
        """Internal flush (no lock)"""
        if not self.batch:
            return True
        
        try:
            # Batch insert with execute_batch()
            execute_batch(
                self.backend.cursor,
                """
                INSERT INTO documents (...) VALUES (%s, %s, ...)
                ON CONFLICT (document_id) DO UPDATE SET ...
                """,
                self.batch,
                page_size=self.batch_size
            )
            self.backend.conn.commit()
            
            self.stats['batches'] += 1
            self.batch.clear()
            return True
            
        except Exception as e:
            logger.error(f"Batch insert failed: {e}")
            self._fallback_single_insert()
            return False
```

**Expected Performance:**
```
Batch: 100 documents = ~0.1-0.2 seconds (500-1000 inserts/second)
Speedup: 50-100x faster!
```

### CouchDB Batch Inserter

**Technology:** `_bulk_docs` API endpoint

**Features:**
- Batch 100 documents in single HTTP POST
- Single API call (no loop)
- Thread-safe operations
- Auto-fallback on errors
- Context manager support

**Implementation Pattern:**
```python
class CouchDBBatchInserter:
    def __init__(self, backend: CouchDBDocumentBackend, batch_size: int = 100):
        self.backend = backend
        self.batch_size = batch_size
        self.batch = []
        self._lock = threading.Lock()
        self.stats = {'batches': 0, 'fallbacks': 0}
    
    def add(self, doc: Dict[str, Any], doc_id: Optional[str] = None):
        """Add document to batch"""
        with self._lock:
            if doc_id:
                doc['_id'] = doc_id
            self.batch.append(doc)
            
            if len(self.batch) >= self.batch_size:
                self._flush_unlocked()
    
    def flush(self) -> bool:
        """Flush batch to CouchDB"""
        with self._lock:
            return self._flush_unlocked()
    
    def _flush_unlocked(self) -> bool:
        """Internal flush (no lock)"""
        if not self.batch:
            return True
        
        try:
            # Batch insert with _bulk_docs
            results = self.backend.db.update(self.batch)
            
            # Check for conflicts
            conflicts = [r for r in results if 'error' in r]
            if conflicts:
                logger.warning(f"{len(conflicts)} conflicts (idempotent)")
            
            self.stats['batches'] += 1
            self.batch.clear()
            return True
            
        except Exception as e:
            logger.error(f"Batch insert failed: {e}")
            self._fallback_single_insert()
            return False
```

**Expected Performance:**
```
Batch: 100 documents = ~0.1-0.5 seconds (200-1000 inserts/second)
Speedup: 100-500x faster!
```

---

## 📋 Implementation Plan

### Item 3: PostgreSQL Batch Inserter (1.5h)

**Files to Create/Modify:**
- `database/batch_operations.py` (extend with PostgreSQLBatchInserter)
- Import: `from psycopg2.extras import execute_batch`

**Class Structure:**
```python
class PostgreSQLBatchInserter:
    def __init__(self, backend, batch_size=100)
    def add(self, document_id, file_path, classification, ...)
    def flush(self) -> bool
    def _flush_unlocked(self) -> bool
    def _fallback_single_insert(self)
    def get_stats(self) -> Dict
    def __enter__(self)
    def __exit__(self, exc_type, exc_val, exc_tb)
```

**ENV Variables:**
```bash
ENABLE_POSTGRES_BATCH_INSERT=false  # Disabled by default
POSTGRES_BATCH_INSERT_SIZE=100      # Batch size
```

**Helper Functions:**
```python
def should_use_postgres_batch_insert() -> bool
def get_postgres_batch_size() -> int
```

### Item 4: CouchDB Batch Inserter (1.5h)

**Files to Create/Modify:**
- `database/batch_operations.py` (extend with CouchDBBatchInserter)

**Class Structure:**
```python
class CouchDBBatchInserter:
    def __init__(self, backend, batch_size=100)
    def add(self, doc: Dict, doc_id: Optional[str] = None)
    def flush(self) -> bool
    def _flush_unlocked(self) -> bool
    def _fallback_single_insert(self)
    def get_stats(self) -> Dict
    def __enter__(self)
    def __exit__(self, exc_type, exc_val, exc_tb)
```

**ENV Variables:**
```bash
ENABLE_COUCHDB_BATCH_INSERT=false  # Disabled by default
COUCHDB_BATCH_INSERT_SIZE=100      # Batch size
```

**Helper Functions:**
```python
def should_use_couchdb_batch_insert() -> bool
def get_couchdb_batch_size() -> int
```

### Item 5: Testing (1h)

**Test Files:**
- `tests/test_batch_operations_postgres.py` (15 unit tests)
- `tests/test_batch_operations_couchdb.py` (15 unit tests)
- Extend `tests/test_batch_operations_integration.py` (10 integration tests)

**Test Coverage:**
- Initialization (2 tests)
- Add single/multiple items (4 tests)
- Auto-flush on batch full (2 tests)
- Manual flush (2 tests)
- Context manager (2 tests)
- Thread-safety (2 tests)
- Fallback on errors (2 tests)
- Stats tracking (2 tests)
- Performance benchmarks (2 tests)

**Total: 40 new tests**

### Item 6: Documentation (45min)

**Files to Update:**
- `docs/BATCH_OPERATIONS.md` (add PostgreSQL + CouchDB sections, 500+ lines)
- `CHANGELOG.md` (add v2.2.0 entry, 100+ lines)
- `docs/FEATURE_MIGRATION_ROADMAP.md` (mark Phase 2 complete)

**Documentation Sections:**
1. PostgreSQL Batch Operations
   - Quick Start example
   - API Reference
   - Performance benchmarks
   - Thread-safety
   - Troubleshooting
   
2. CouchDB Batch Operations
   - Quick Start example
   - API Reference
   - Performance benchmarks
   - Conflict handling
   - Troubleshooting

### Item 7: Git Commits (30min)

**Commit 1: PostgreSQL**
```
feat(batch): Add PostgreSQL batch operations

- PostgreSQLBatchInserter: 100 docs/batch (+50-100x)
- Features: psycopg2.extras.execute_batch, thread-safe, auto-fallback
- Tests: 15 unit + 5 integration PASSED
- ENV: ENABLE_POSTGRES_BATCH_INSERT=false (default)
```

**Commit 2: CouchDB**
```
feat(batch): Add CouchDB batch operations

- CouchDBBatchInserter: 100 docs/batch (+100-500x)
- Features: _bulk_docs API, conflict handling, thread-safe, auto-fallback
- Tests: 15 unit + 5 integration PASSED
- ENV: ENABLE_COUCHDB_BATCH_INSERT=false (default)
```

**Commit 3: Documentation**
```
docs: Update documentation for v2.2.0

- Extend BATCH_OPERATIONS.md (500+ lines)
- Update CHANGELOG.md with v2.2.0
- Mark Phase 2 complete in roadmap
```

### Item 8: Validation (30min)

**Validation Checklist:**
- [ ] All 40 tests passing (100%)
- [ ] PostgreSQL: +50-100x throughput validated
- [ ] CouchDB: +100-500x throughput validated
- [ ] ENV toggles working (disabled by default)
- [ ] Backward compatibility preserved
- [ ] Thread-safety tested (concurrent usage)
- [ ] Fallback working on errors
- [ ] Integration with Covina validated

---

## 🎯 Success Criteria

### Performance Targets

**PostgreSQL:**
```
Before: 100 documents = ~10 seconds (10 inserts/sec)
After:  100 documents = ~0.1-0.2 seconds (500-1000 inserts/sec)
Target: +50-100x throughput
```

**CouchDB:**
```
Before: 100 documents = ~50 seconds (2 inserts/sec)
After:  100 documents = ~0.1-0.5 seconds (200-1000 inserts/sec)
Target: +100-500x throughput
```

### Quality Targets

- ✅ 40 tests total (100% pass rate)
- ✅ Thread-safe operations
- ✅ Auto-fallback on errors
- ✅ Context manager support
- ✅ Stats tracking (get_stats())
- ✅ ENV toggles (disabled by default)
- ✅ Backward compatible (no breaking changes)
- ✅ Documentation complete (500+ lines)

---

## 📊 Phase 2 vs Phase 1 Comparison

| Feature | Phase 1 | Phase 2 |
|---------|---------|---------|
| **Databases** | ChromaDB, Neo4j | PostgreSQL, CouchDB |
| **Use Case** | Vector search, Graph | Relational, Document |
| **Technology** | HTTP batch, Cypher UNWIND | execute_batch, _bulk_docs |
| **Batch Size** | 100, 1000 | 100, 100 |
| **Speedup** | 80-187x | 50-500x |
| **Tests** | 52 tests | 40 tests |
| **Lines** | 3,000+ | ~2,500 (estimate) |
| **Time** | ~6 hours | 3-4 hours (estimate) |

---

## 🔄 Risk Analysis

### Low Risk ✅

**Reason:** Following proven Phase 1 pattern

- Same class structure (ChromaBatchInserter → PostgreSQLBatchInserter)
- Same threading pattern (threading.Lock)
- Same context manager pattern (__enter__/__exit__)
- Same fallback pattern (_flush_unlocked)
- Same ENV configuration (ENABLE_*, *_BATCH_SIZE)

**Mitigation:**
- Copy-paste Phase 1 structure
- Adapt only database-specific code
- Reuse test patterns from Phase 1

### Known Challenges

1. **PostgreSQL Connection Management**
   - Risk: Connection pool conflicts
   - Solution: Reuse backend.cursor (no new connections)

2. **CouchDB Conflict Handling**
   - Risk: _bulk_docs returns mixed results
   - Solution: Check results array, log conflicts (idempotent)

3. **Performance Validation**
   - Risk: Speedup less than expected
   - Solution: Performance benchmarks in tests

---

## 📅 Timeline

| Item | Task | Time | Total |
|------|------|------|-------|
| 2 | Planning (THIS DOC) | 30min | 0.5h |
| 3 | PostgreSQL Batch Inserter | 1.5h | 2.0h |
| 4 | CouchDB Batch Inserter | 1.5h | 3.5h |
| 5 | Testing (40 tests) | 1h | 4.5h |
| 6 | Documentation | 45min | 5.25h |
| 7 | Git Commits | 30min | 5.75h |
| 8 | Validation | 30min | 6.25h |

**Total Estimate:** 6.25 hours (vs 3-4h original → adjusted)

**Note:** Original estimate was too optimistic. Realistic: 6-7 hours.

---

## ✅ Planning Complete

**Status:** 📋 Planning DONE  
**Next Step:** Item 3 (PostgreSQL Batch Inserter)  
**Estimated Time:** 1.5 hours  

**Ready to proceed?** Yes! All information gathered, pattern proven, risks mitigated.

---

**Author:** UDS3 Framework Team  
**Date:** 20. Oktober 2025  
**Version:** UDS3 2.2.0 (planned)
