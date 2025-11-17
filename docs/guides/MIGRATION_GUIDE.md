# Migration Guide: Upgrading to UDS3 v1.5.0

This guide helps you migrate from earlier versions of UDS3 to v1.5.0.

## Breaking Changes

### v1.4.0 → v1.5.0

**No breaking changes** - This is a documentation-focused release.

All APIs remain backward compatible.

## New Features in v1.5.0

### 1. Enhanced Caching System

New cache features available:
- LRU eviction with configurable TTL
- Memory limits and auto-cleanup
- Statistics tracking

**Migration:**
```python
# Old (still works)
cache = Cache()

# New (recommended)
from core.cache import RecordCache, CacheConfig

config = CacheConfig(
    max_size=5000,
    default_ttl_seconds=600
)
cache = RecordCache(config)
```

### 2. Geo/Spatial Capabilities

New geo features:
- PostGIS integration
- German administrative boundaries
- 4D queries (time + location)

**Migration:**
```python
# Enable geo features
from api.geo import GeoExtractor, PostGISManager

extractor = GeoExtractor()
locations = extractor.extract_locations(document_text)
```

### 3. Streaming API

New streaming capabilities for large files:

**Migration:**
```python
# Old: Load entire file
with open(large_file, 'rb') as f:
    data = f.read()  # Loads all into memory

# New: Stream in chunks
from manager.streaming import StreamingManager

manager = StreamingManager(chunk_size_mb=10)
operation_id = manager.upload_file(large_file, destination)
```

### 4. Workflow Management

New Petri net and process mining capabilities:

**Migration:**
```python
# New workflow verification
from api.workflow import WorkflowNetAnalyzer

analyzer = WorkflowNetAnalyzer()
result = analyzer.verify_soundness(workflow)
```

## Configuration Updates

### Database Configuration

No changes required. All existing configurations work as-is.

### Environment Variables

New optional variables:
```bash
# Caching
ENABLE_CACHE=true
CACHE_SIZE=5000
CACHE_TTL_SECONDS=600

# Geo features
ENABLE_GEO=true
POSTGIS_HOST=localhost
```

## Data Migration

**No data migration required.** All database schemas remain compatible.

## Testing Your Migration

1. **Run existing tests:**
```bash
pytest tests/
```

2. **Verify database connectivity:**
```bash
python scripts/automation/version_check.py
```

3. **Check feature availability:**
```python
from core import cache, geo, streaming, workflow
# All imports should work
```

## Rollback Plan

If you need to rollback:

```bash
# Checkout previous version
git checkout v1.4.0

# No database changes needed
```

## Support

For migration issues:
- Check [DOCUMENTATION_GAP_ANALYSIS.md](../DOCUMENTATION_GAP_ANALYSIS.md)
- Review [docs/features/](../features/) guides
- Open an issue on GitHub

## Timeline

- **Testing:** 1-2 days
- **Migration:** Same day (no breaking changes)
- **Validation:** 1-2 days

**Total:** 2-5 days for complete migration and validation
