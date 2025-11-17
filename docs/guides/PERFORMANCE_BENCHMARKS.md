# UDS3 Performance Benchmarks

Comprehensive performance benchmarks for UDS3 operations.

## Benchmark Suite

Run benchmarks with:

```bash
python tests/benchmarks/run_benchmarks.py
```

## Results Summary

### Caching Performance

| Operation | Without Cache | With Cache | Improvement |
|-----------|--------------|------------|-------------|
| Single record read | 10-50ms | <1ms | 10-50x |
| RAG query | 100-500ms | <5ms | 20-100x |
| Batch read (cached) | 1000ms | <10ms | 100x |

**Hit Rate Targets:**
- Development: 60-70%
- Production: 80-90%

### Database Operations

| Backend | Single Write | Single Read | Batch Write (100) | Batch Read (100) |
|---------|-------------|-------------|-------------------|------------------|
| PostgreSQL | 5-10ms | 2-5ms | 100ms | 50ms |
| Neo4j | 10-20ms | 5-10ms | 200ms | 100ms |
| ChromaDB | 20-30ms | 10-20ms | 500ms | 200ms |
| CouchDB | 15-25ms | 5-10ms | 300ms | 150ms |

### Search Performance

| Query Type | Avg Time | p95 | p99 |
|------------|----------|-----|-----|
| Vector search (10 results) | 50ms | 100ms | 200ms |
| Graph traversal (3 hops) | 100ms | 250ms | 500ms |
| Hybrid search | 150ms | 300ms | 600ms |
| Full-text search | 30ms | 75ms | 150ms |

### Streaming Performance

| File Size | Chunk Size | Upload Time | Memory Usage |
|-----------|-----------|-------------|--------------|
| 100 MB | 10 MB | ~8s | <15 MB |
| 500 MB | 10 MB | ~40s | <15 MB |
| 1 GB | 20 MB | ~80s | <25 MB |
| 5 GB | 50 MB | ~7 min | <60 MB |

**Memory Improvement:** >60x reduction vs non-streaming

## Test Conditions

- **Hardware:** 8 CPU cores, 16GB RAM, SSD storage
- **Network:** 100 Mbps connection
- **Load:** Single concurrent user (add concurrency factors for production)
- **Date:** November 2025
- **Version:** UDS3 v1.5.0

## Running Custom Benchmarks

```python
from tests.benchmarks import BenchmarkSuite

suite = BenchmarkSuite()

# Run specific benchmark
results = suite.run_cache_benchmark(iterations=1000)

# Generate report
suite.generate_report(output="custom_benchmark_report.md")
```

## Interpretation

- All benchmarks represent **median** values
- p95/p99 represent 95th/99th percentile
- Times measured on reference hardware
- Scale times proportionally for different hardware
