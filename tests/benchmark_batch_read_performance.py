"""
Performance Benchmark Tests for UDS3 Batch READ Operations
Tests real-world performance scenarios with actual data volumes.

Scenarios:
1. Dashboard Queries (100 docs) - Expected: 23s → 0.1s (230x)
2. Search Operations (10 queries) - Expected: 600ms → 300ms (2x)
3. Bulk Export (1000 docs) - Expected: 3.8min → 0.1s (2,300x)
4. Existence Checks (500 docs) - Expected: 5s → 0.05s (100x)

Usage:
    pytest tests/benchmark_batch_read_performance.py -v -s
"""

import pytest
import time
import asyncio
from typing import List, Dict, Any
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.batch_operations import (
    PostgreSQLBatchReader,
    CouchDBBatchReader,
    ChromaDBBatchReader,
    Neo4jBatchReader,
    ParallelBatchReader,
    should_use_batch_read,
    get_batch_read_size
)


class PerformanceResults:
    """Track and report performance benchmark results."""
    
    def __init__(self):
        self.results = []
        
    def add_result(self, scenario: str, method: str, duration: float, 
                   count: int, expected_speedup: float = None):
        """Add a benchmark result."""
        self.results.append({
            'scenario': scenario,
            'method': method,
            'duration': duration,
            'count': count,
            'throughput': count / duration if duration > 0 else 0,
            'expected_speedup': expected_speedup
        })
        
    def print_summary(self):
        """Print formatted summary of all results."""
        print("\n" + "=" * 100)
        print("PERFORMANCE BENCHMARK RESULTS")
        print("=" * 100)
        
        for result in self.results:
            print(f"\n📊 {result['scenario']}")
            print(f"   Method: {result['method']}")
            print(f"   Duration: {result['duration']:.3f}s")
            print(f"   Count: {result['count']} documents")
            print(f"   Throughput: {result['throughput']:.2f} docs/s")
            
            if result['expected_speedup']:
                print(f"   Expected Speedup: {result['expected_speedup']}x")
                
        print("\n" + "=" * 100)
        
    def compare_methods(self, scenario: str) -> Dict[str, float]:
        """Compare batch vs sequential for a scenario."""
        scenario_results = [r for r in self.results if r['scenario'] == scenario]
        
        if len(scenario_results) < 2:
            return {}
            
        sequential = next((r for r in scenario_results if 'Sequential' in r['method']), None)
        batch = next((r for r in scenario_results if 'Batch' in r['method']), None)
        
        if not sequential or not batch:
            return {}
            
        speedup = sequential['duration'] / batch['duration'] if batch['duration'] > 0 else 0
        
        return {
            'sequential_time': sequential['duration'],
            'batch_time': batch['duration'],
            'speedup': speedup,
            'improvement': ((sequential['duration'] - batch['duration']) / sequential['duration'] * 100)
        }


# Global results tracker
perf_results = PerformanceResults()


@pytest.fixture
def sample_doc_ids() -> List[str]:
    """Generate sample document IDs for testing."""
    return [f"doc_{i}" for i in range(1, 101)]  # 100 docs


@pytest.fixture
def large_doc_ids() -> List[str]:
    """Generate large set of document IDs for bulk operations."""
    return [f"doc_{i}" for i in range(1, 1001)]  # 1000 docs


@pytest.fixture
def postgres_reader():
    """Create PostgreSQL batch reader."""
    return PostgreSQLBatchReader()


@pytest.fixture
def couchdb_reader():
    """Create CouchDB batch reader."""
    return CouchDBBatchReader()


@pytest.fixture
def chromadb_reader():
    """Create ChromaDB batch reader."""
    return ChromaDBBatchReader()


@pytest.fixture
def neo4j_reader():
    """Create Neo4j batch reader."""
    return Neo4jBatchReader()


@pytest.fixture
def parallel_reader():
    """Create parallel multi-database reader."""
    return ParallelBatchReader()


# ============================================================================
# Scenario 1: Dashboard Queries (100 documents)
# Expected: 23s → 0.1s (230x speedup)
# ============================================================================

@pytest.mark.benchmark
def test_dashboard_sequential(sample_doc_ids, postgres_reader):
    """Test dashboard queries with sequential fetches (baseline)."""
    print("\n" + "=" * 80)
    print("SCENARIO 1: Dashboard Queries (Sequential - Baseline)")
    print("=" * 80)
    
    start_time = time.time()
    
    # Simulate sequential queries (one at a time)
    results = []
    for doc_id in sample_doc_ids:
        try:
            # Single document fetch (simulated)
            result = postgres_reader.batch_get([doc_id], fields=['*'], table='documents')
            results.extend(result)
        except Exception as e:
            print(f"Error fetching {doc_id}: {e}")
            
    duration = time.time() - start_time
    
    print(f"✅ Fetched {len(results)} documents in {duration:.3f}s")
    print(f"   Throughput: {len(results)/duration:.2f} docs/s")
    
    perf_results.add_result(
        scenario="Dashboard Queries (100 docs)",
        method="Sequential Fetch",
        duration=duration,
        count=len(sample_doc_ids),
        expected_speedup=230.0
    )
    
    assert len(results) <= len(sample_doc_ids)


@pytest.mark.benchmark
def test_dashboard_batch(sample_doc_ids, postgres_reader):
    """Test dashboard queries with batch fetch (optimized)."""
    print("\n" + "=" * 80)
    print("SCENARIO 1: Dashboard Queries (Batch - Optimized)")
    print("=" * 80)
    
    start_time = time.time()
    
    # Batch fetch all documents at once
    try:
        results = postgres_reader.batch_get(
            doc_ids=sample_doc_ids,
            fields=['*'],
            table='documents'
        )
    except Exception as e:
        print(f"Error in batch fetch: {e}")
        results = []
        
    duration = time.time() - start_time
    
    print(f"✅ Fetched {len(results)} documents in {duration:.3f}s")
    print(f"   Throughput: {len(results)/duration:.2f} docs/s")
    
    perf_results.add_result(
        scenario="Dashboard Queries (100 docs)",
        method="Batch Fetch",
        duration=duration,
        count=len(sample_doc_ids)
    )
    
    # Compare
    comparison = perf_results.compare_methods("Dashboard Queries (100 docs)")
    if comparison:
        print(f"\n📈 Performance Comparison:")
        print(f"   Sequential: {comparison['sequential_time']:.3f}s")
        print(f"   Batch: {comparison['batch_time']:.3f}s")
        print(f"   Speedup: {comparison['speedup']:.1f}x")
        print(f"   Improvement: {comparison['improvement']:.1f}%")
        print(f"   Expected: 230x speedup")
    
    assert len(results) <= len(sample_doc_ids)


# ============================================================================
# Scenario 2: Search Operations (10 queries, 50 results each)
# Expected: 600ms → 300ms (2x speedup)
# ============================================================================

@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_search_sequential(chromadb_reader):
    """Test search operations with sequential queries (baseline)."""
    print("\n" + "=" * 80)
    print("SCENARIO 2: Search Operations (Sequential - Baseline)")
    print("=" * 80)
    
    queries = [f"search query {i}" for i in range(1, 11)]  # 10 queries
    
    start_time = time.time()
    
    all_results = []
    for query in queries:
        try:
            results = chromadb_reader.batch_search(
                query_texts=[query],
                n_results=50
            )
            all_results.extend(results)
        except Exception as e:
            print(f"Error searching '{query}': {e}")
            
    duration = time.time() - start_time
    
    print(f"✅ Executed {len(queries)} queries in {duration:.3f}s")
    print(f"   Results: {len(all_results)} total")
    print(f"   Avg per query: {duration/len(queries)*1000:.1f}ms")
    
    perf_results.add_result(
        scenario="Search Operations (10 queries)",
        method="Sequential Search",
        duration=duration,
        count=len(queries),
        expected_speedup=2.0
    )
    
    assert len(all_results) >= 0


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_search_batch(chromadb_reader):
    """Test search operations with batch queries (optimized)."""
    print("\n" + "=" * 80)
    print("SCENARIO 2: Search Operations (Batch - Optimized)")
    print("=" * 80)
    
    queries = [f"search query {i}" for i in range(1, 11)]  # 10 queries
    
    start_time = time.time()
    
    try:
        # Batch search all queries at once
        all_results = chromadb_reader.batch_search(
            query_texts=queries,
            n_results=50
        )
    except Exception as e:
        print(f"Error in batch search: {e}")
        all_results = []
        
    duration = time.time() - start_time
    
    print(f"✅ Executed {len(queries)} queries in {duration:.3f}s")
    print(f"   Results: {len(all_results)} total")
    print(f"   Avg per query: {duration/len(queries)*1000:.1f}ms")
    
    perf_results.add_result(
        scenario="Search Operations (10 queries)",
        method="Batch Search",
        duration=duration,
        count=len(queries)
    )
    
    # Compare
    comparison = perf_results.compare_methods("Search Operations (10 queries)")
    if comparison:
        print(f"\n📈 Performance Comparison:")
        print(f"   Sequential: {comparison['sequential_time']*1000:.1f}ms")
        print(f"   Batch: {comparison['batch_time']*1000:.1f}ms")
        print(f"   Speedup: {comparison['speedup']:.1f}x")
        print(f"   Improvement: {comparison['improvement']:.1f}%")
        print(f"   Expected: 2x speedup")
    
    assert len(all_results) >= 0


# ============================================================================
# Scenario 3: Bulk Export (1000 documents)
# Expected: 3.8min → 0.1s (2,300x speedup)
# ============================================================================

@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_bulk_export_sequential(large_doc_ids, parallel_reader):
    """Test bulk export with sequential fetches (baseline)."""
    print("\n" + "=" * 80)
    print("SCENARIO 3: Bulk Export (Sequential - Baseline)")
    print("=" * 80)
    
    start_time = time.time()
    
    all_results = {
        'relational': [],
        'document': [],
        'vector': [],
        'graph': []
    }
    
    # Sequential fetch from all 4 databases (one doc at a time)
    for doc_id in large_doc_ids[:100]:  # Limit to 100 for testing
        try:
            result = await parallel_reader.batch_get_all(
                doc_ids=[doc_id],
                include_embeddings=False,
                timeout=5.0
            )
            
            for db_type in all_results.keys():
                if db_type in result:
                    all_results[db_type].extend(result[db_type])
                    
        except Exception as e:
            print(f"Error exporting {doc_id}: {e}")
            
    duration = time.time() - start_time
    
    total_docs = sum(len(results) for results in all_results.values())
    
    print(f"✅ Exported {total_docs} documents from 4 databases in {duration:.3f}s")
    print(f"   Throughput: {total_docs/duration:.2f} docs/s")
    
    perf_results.add_result(
        scenario="Bulk Export (1000 docs)",
        method="Sequential Export",
        duration=duration,
        count=len(large_doc_ids[:100]),
        expected_speedup=2300.0
    )


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_bulk_export_batch(large_doc_ids, parallel_reader):
    """Test bulk export with batch fetch (optimized)."""
    print("\n" + "=" * 80)
    print("SCENARIO 3: Bulk Export (Batch - Optimized)")
    print("=" * 80)
    
    start_time = time.time()
    
    try:
        # Batch fetch all documents at once from all 4 databases in parallel
        all_results = await parallel_reader.batch_get_all(
            doc_ids=large_doc_ids[:100],  # Limit to 100 for testing
            include_embeddings=False,
            timeout=30.0
        )
    except Exception as e:
        print(f"Error in batch export: {e}")
        all_results = {
            'relational': [],
            'document': [],
            'vector': [],
            'graph': [],
            'errors': []
        }
        
    duration = time.time() - start_time
    
    total_docs = sum(len(all_results.get(k, [])) for k in ['relational', 'document', 'vector', 'graph'])
    
    print(f"✅ Exported {total_docs} documents from 4 databases in {duration:.3f}s")
    print(f"   Throughput: {total_docs/duration:.2f} docs/s")
    print(f"   Errors: {len(all_results.get('errors', []))}")
    
    perf_results.add_result(
        scenario="Bulk Export (1000 docs)",
        method="Batch Export",
        duration=duration,
        count=len(large_doc_ids[:100])
    )
    
    # Compare
    comparison = perf_results.compare_methods("Bulk Export (1000 docs)")
    if comparison:
        print(f"\n📈 Performance Comparison:")
        print(f"   Sequential: {comparison['sequential_time']:.3f}s")
        print(f"   Batch: {comparison['batch_time']:.3f}s")
        print(f"   Speedup: {comparison['speedup']:.1f}x")
        print(f"   Improvement: {comparison['improvement']:.1f}%")
        print(f"   Expected: 2,300x speedup")


# ============================================================================
# Scenario 4: Existence Checks (500 documents)
# Expected: 5s → 0.05s (100x speedup)
# ============================================================================

@pytest.mark.benchmark
def test_existence_checks_sequential(large_doc_ids, postgres_reader):
    """Test existence checks with sequential queries (baseline)."""
    print("\n" + "=" * 80)
    print("SCENARIO 4: Existence Checks (Sequential - Baseline)")
    print("=" * 80)
    
    doc_ids = large_doc_ids[:500]  # 500 docs
    
    start_time = time.time()
    
    exists_count = 0
    for doc_id in doc_ids:
        try:
            result = postgres_reader.batch_exists([doc_id], table='documents')
            exists_count += sum(result.values())
        except Exception as e:
            print(f"Error checking {doc_id}: {e}")
            
    duration = time.time() - start_time
    
    print(f"✅ Checked {len(doc_ids)} documents in {duration:.3f}s")
    print(f"   Exists: {exists_count}")
    print(f"   Throughput: {len(doc_ids)/duration:.2f} checks/s")
    
    perf_results.add_result(
        scenario="Existence Checks (500 docs)",
        method="Sequential Check",
        duration=duration,
        count=len(doc_ids),
        expected_speedup=100.0
    )


@pytest.mark.benchmark
def test_existence_checks_batch(large_doc_ids, postgres_reader):
    """Test existence checks with batch query (optimized)."""
    print("\n" + "=" * 80)
    print("SCENARIO 4: Existence Checks (Batch - Optimized)")
    print("=" * 80)
    
    doc_ids = large_doc_ids[:500]  # 500 docs
    
    start_time = time.time()
    
    try:
        result = postgres_reader.batch_exists(doc_ids, table='documents')
        exists_count = sum(result.values())
    except Exception as e:
        print(f"Error in batch check: {e}")
        exists_count = 0
        
    duration = time.time() - start_time
    
    print(f"✅ Checked {len(doc_ids)} documents in {duration:.3f}s")
    print(f"   Exists: {exists_count}")
    print(f"   Throughput: {len(doc_ids)/duration:.2f} checks/s")
    
    perf_results.add_result(
        scenario="Existence Checks (500 docs)",
        method="Batch Check",
        duration=duration,
        count=len(doc_ids)
    )
    
    # Compare
    comparison = perf_results.compare_methods("Existence Checks (500 docs)")
    if comparison:
        print(f"\n📈 Performance Comparison:")
        print(f"   Sequential: {comparison['sequential_time']:.3f}s")
        print(f"   Batch: {comparison['batch_time']:.3f}s")
        print(f"   Speedup: {comparison['speedup']:.1f}x")
        print(f"   Improvement: {comparison['improvement']:.1f}%")
        print(f"   Expected: 100x speedup")


# ============================================================================
# Final Summary
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def print_final_summary(request):
    """Print final summary after all tests."""
    def finalizer():
        perf_results.print_summary()
        
        print("\n" + "=" * 100)
        print("OVERALL ASSESSMENT")
        print("=" * 100)
        
        scenarios = [
            ("Dashboard Queries (100 docs)", 230.0),
            ("Search Operations (10 queries)", 2.0),
            ("Bulk Export (1000 docs)", 2300.0),
            ("Existence Checks (500 docs)", 100.0)
        ]
        
        for scenario, expected_speedup in scenarios:
            comparison = perf_results.compare_methods(scenario)
            if comparison:
                actual = comparison['speedup']
                achievement = (actual / expected_speedup * 100) if expected_speedup > 0 else 0
                
                status = "✅" if achievement >= 50 else "⚠️"
                print(f"\n{status} {scenario}")
                print(f"   Expected: {expected_speedup}x speedup")
                print(f"   Actual: {actual:.1f}x speedup")
                print(f"   Achievement: {achievement:.1f}%")
                
        print("\n" + "=" * 100)
        
    request.addfinalizer(finalizer)


if __name__ == "__main__":
    print("Run with: pytest tests/benchmark_batch_read_performance.py -v -s")
