# UDS3 Caching System

**Status:** Production Ready ✅  
**Module:** `core/cache.py`, `core/rag_cache.py`  
**Lines of Code:** 1,028 (737 + 291)  
**References:** 46 files across codebase

---

## Overview

UDS3 includes a sophisticated caching system optimized for single-record read operations with LRU (Least Recently Used) eviction policy and TTL (Time-To-Live) automatic invalidation. The caching layer significantly improves read performance by reducing database roundtrips.

### Key Features

- **LRU Eviction Policy:** Automatically removes least recently used entries when cache is full
- **TTL Support:** Time-based automatic invalidation for stale data prevention
- **Thread-Safe Operations:** Lock-based synchronization for concurrent access
- **Performance Monitoring:** Built-in statistics and metrics tracking
- **Flexible Invalidation:** Single entry, pattern-based, or full cache invalidation
- **Warmup Mechanism:** Pre-load frequently accessed records on startup
- **Memory Management:** Configurable memory limits and size tracking

---

## Architecture

### Cache Hierarchy

```
┌─────────────────────────────────────────┐
│         Application Layer               │
├─────────────────────────────────────────┤
│      UDS3 Database Strategy             │
├─────────────────────────────────────────┤
│         Cache Layer (LRU + TTL)         │
│  ┌──────────┐  ┌──────────┐            │
│  │ Record   │  │   RAG    │            │
│  │  Cache   │  │  Cache   │            │
│  └──────────┘  └──────────┘            │
├─────────────────────────────────────────┤
│    Database Backends (PostgreSQL,      │
│    Neo4j, ChromaDB, CouchDB, SQLite)   │
└─────────────────────────────────────────┘
```

### Components

1. **RecordCache** (`core/cache.py`)
   - Primary cache for single database records
   - LRU eviction with configurable size limits
   - TTL-based expiration

2. **RAGCache** (`core/rag_cache.py`)
   - Specialized cache for RAG (Retrieval-Augmented Generation) queries
   - Caches embeddings and search results
   - Query fingerprinting for cache key generation

---

## Core Classes

### CacheEntry

Represents a single cache entry with metadata:

```python
@dataclass
class CacheEntry:
    document_id: str
    data: Dict[str, Any]
    created_at: float          # Timestamp
    last_accessed: float       # For LRU eviction
    access_count: int          # Access statistics
    ttl_seconds: Optional[float]  # Time-to-live
    status: CacheStatus        # VALID, EXPIRED, INVALIDATED
    size_bytes: int            # Memory tracking
```

### CacheStatistics

Performance metrics tracking:

```python
@dataclass
class CacheStatistics:
    hits: int                  # Successful cache hits
    misses: int                # Cache misses
    evictions: int             # LRU evictions
    invalidations: int         # Manual invalidations
    total_requests: int        # Total cache queries
    hit_rate: float            # Calculated hit rate %
    miss_rate: float           # Calculated miss rate %
```

### CacheConfig

Configuration options:

```python
@dataclass
class CacheConfig:
    max_size: int = 1000              # Max entries
    default_ttl_seconds: float = 300  # 5 minutes
    enable_stats: bool = True         # Statistics tracking
    auto_cleanup_interval: float = 60 # Cleanup frequency
    invalidation_strategy: str        # IMMEDIATE, LAZY, SCHEDULED
    warmup_enabled: bool = False      # Pre-load on startup
    max_memory_mb: Optional[float]    # Memory limit
```

---

## Usage Examples

### Basic Caching

```python
from core.cache import RecordCache, CacheConfig

# Initialize cache
config = CacheConfig(
    max_size=5000,
    default_ttl_seconds=600,  # 10 minutes
    enable_stats=True
)
cache = RecordCache(config)

# Store in cache
document_id = "doc_12345"
data = {"title": "Example", "content": "..."}
cache.put(document_id, data, ttl_seconds=300)

# Retrieve from cache
cached_data = cache.get(document_id)
if cached_data:
    print("Cache hit!")
else:
    print("Cache miss - fetch from database")
    # Fetch and cache...
```

### RAG Query Caching

```python
from core.rag_cache import RAGCache

rag_cache = RAGCache(max_size=1000, ttl_seconds=3600)

# Cache search results
query = "administrative law procedures"
results = rag_cache.get_query_results(query)

if results is None:
    # Perform expensive search
    results = perform_vector_search(query)
    rag_cache.put_query_results(query, results)
```

### Cache Invalidation

```python
# Invalidate single entry
cache.invalidate(document_id)

# Pattern-based invalidation (all documents starting with "legal_")
cache.invalidate_pattern("^legal_.*")

# Clear entire cache
cache.clear()
```

### Statistics Monitoring

```python
# Get cache statistics
stats = cache.get_statistics()
print(f"Hit Rate: {stats.hit_rate:.2f}%")
print(f"Miss Rate: {stats.miss_rate:.2f}%")
print(f"Total Requests: {stats.total_requests}")
print(f"Cache Size: {stats.total_size_mb:.2f} MB")

# Export to dict for logging
stats_dict = stats.to_dict()
logger.info(f"Cache performance: {stats_dict}")
```

---

## Performance Characteristics

### Cache Hit Performance

| Operation | Without Cache | With Cache (Hit) | Improvement |
|-----------|--------------|------------------|-------------|
| Single record read | 10-50ms | <1ms | **10-50x** |
| RAG query | 100-500ms | <5ms | **20-100x** |
| Batch read (cached) | 1000ms | <10ms | **100x** |

### Hit Rate Targets

- **Development:** 60-70% (frequent data changes)
- **Production:** 80-90% (stable data)
- **RAG queries:** 70-85% (similar queries)

### Memory Usage

- **Default config:** ~50-100 MB (1000 entries)
- **Large config:** ~500 MB - 1 GB (5000+ entries)
- **Auto-cleanup:** Triggered at 90% of max_memory_mb

---

## Configuration Best Practices

### Development Environment

```python
config = CacheConfig(
    max_size=100,           # Smaller cache
    default_ttl_seconds=60, # Short TTL (1 minute)
    enable_stats=True,      # Monitor performance
    auto_cleanup_interval=30
)
```

### Production Environment

```python
config = CacheConfig(
    max_size=5000,            # Larger cache
    default_ttl_seconds=600,  # 10 minutes
    enable_stats=True,
    auto_cleanup_interval=120,
    max_memory_mb=500,        # 500 MB limit
    warmup_enabled=True       # Pre-load frequent data
)
```

### RAG-Heavy Workload

```python
rag_cache_config = CacheConfig(
    max_size=2000,            # More query results
    default_ttl_seconds=3600, # 1 hour (stable embeddings)
    enable_stats=True
)
```

---

## Cache Invalidation Strategies

### 1. Immediate Invalidation

Best for: Real-time consistency requirements

```python
config.invalidation_strategy = InvalidationStrategy.IMMEDIATE
# Cache entries removed immediately on invalidate() call
```

### 2. Lazy Invalidation

Best for: Performance-critical applications

```python
config.invalidation_strategy = InvalidationStrategy.LAZY
# Entries marked as invalid, removed on next access
```

### 3. Scheduled Cleanup

Best for: Batch-oriented workflows

```python
config.invalidation_strategy = InvalidationStrategy.SCHEDULED
# Background thread cleans up periodically
```

---

## Integration with UDS3

### Automatic Caching in Database APIs

Most UDS3 database APIs automatically use caching:

```python
from uds3 import get_optimized_unified_strategy

strategy = get_optimized_unified_strategy()

# Caching happens automatically
document = await strategy.get_document(document_id)  # Cached
document2 = await strategy.get_document(document_id) # Cache hit!
```

### Manual Cache Control

```python
# Access underlying cache
cache = strategy._record_cache

# Check cache status
if cache.has(document_id):
    print("Document is cached")

# Force cache refresh
cache.invalidate(document_id)
document = await strategy.get_document(document_id)  # Fetches fresh
```

---

## Monitoring and Debugging

### Enable Debug Logging

```python
import logging
logging.getLogger('core.cache').setLevel(logging.DEBUG)
```

### Cache Statistics Dashboard

```python
def print_cache_dashboard(cache):
    stats = cache.get_statistics()
    print("=" * 50)
    print("CACHE PERFORMANCE DASHBOARD")
    print("=" * 50)
    print(f"Hit Rate:        {stats.hit_rate:6.2f}%")
    print(f"Miss Rate:       {stats.miss_rate:6.2f}%")
    print(f"Total Requests:  {stats.total_requests:,}")
    print(f"Hits:            {stats.hits:,}")
    print(f"Misses:          {stats.misses:,}")
    print(f"Evictions:       {stats.evictions:,}")
    print(f"Cache Size:      {stats.total_size_mb:.2f} MB")
    print(f"Avg Access Time: {stats.average_access_time_ms:.2f} ms")
    print("=" * 50)
```

### Health Check

```python
def check_cache_health(cache):
    stats = cache.get_statistics()
    
    # Alert on low hit rate
    if stats.hit_rate < 50:
        logger.warning(f"Low cache hit rate: {stats.hit_rate:.2f}%")
    
    # Alert on high memory
    if stats.total_size_mb > 450:  # 90% of 500 MB limit
        logger.warning(f"Cache memory high: {stats.total_size_mb:.2f} MB")
```

---

## Troubleshooting

### Low Hit Rate

**Problem:** Hit rate below 50%

**Solutions:**
1. Increase `max_size` (more entries cached)
2. Increase `default_ttl_seconds` (longer cache lifetime)
3. Enable warmup for frequently accessed data
4. Check access patterns (are queries unique?)

### Memory Issues

**Problem:** Cache using too much memory

**Solutions:**
1. Decrease `max_size`
2. Set `max_memory_mb` limit
3. Decrease `default_ttl_seconds`
4. Enable compression (if available)

### Stale Data

**Problem:** Cached data is outdated

**Solutions:**
1. Decrease `default_ttl_seconds`
2. Implement event-driven invalidation
3. Use immediate invalidation strategy
4. Call `cache.invalidate()` after updates

---

## Related Documentation

- [Batch Operations](../BATCH_OPERATIONS.md) - Batch caching strategies
- [RAG Pipeline](UDS3_RAG_README.md) - RAG-specific caching
- [Performance Tuning](../CONFIGURATION_GUIDE.md) - Configuration options

---

## API Reference

### RecordCache Methods

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `put()` | Store entry | `(id, data, ttl_seconds)` | None |
| `get()` | Retrieve entry | `(id)` | Dict or None |
| `has()` | Check if cached | `(id)` | bool |
| `invalidate()` | Remove entry | `(id)` | bool |
| `invalidate_pattern()` | Remove by regex | `(pattern)` | int |
| `clear()` | Clear all | None | None |
| `get_statistics()` | Get stats | None | CacheStatistics |
| `warmup()` | Pre-load data | `(ids)` | None |

---

**Last Updated:** November 17, 2025  
**Version:** 1.5.0  
**Status:** Production Ready ✅
