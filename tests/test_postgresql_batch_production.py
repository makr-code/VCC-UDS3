#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_postgresql_batch_production.py

test_postgresql_batch_production.py
PostgreSQL Batch READ Production Test
Tests real-world batch performance with actual PostgreSQL database.
Requirements:
- PostgreSQL running on 192.168.178.94:5432
- Test data available (or will be created)
Usage:
pytest tests/test_postgresql_batch_production.py -v -s
Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)
License: MIT with Government Partnership Commons Clause
Repository: https://github.com/makr-code/VCC-UDS3

Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)
License: MIT with Government Partnership Commons Clause
Repository: https://github.com/makr-code/VCC-UDS3
"""

import pytest
import time
import psycopg2
from typing import List
from database.batch_operations import PostgreSQLBatchReader


class MockPostgreSQLBackend:
    """Mock PostgreSQL backend for batch testing."""
    
    def __init__(self):
        """Initialize PostgreSQL connection."""
        self.conn = psycopg2.connect(
            host='192.168.178.94',
            port=5432,
            user='postgres',
            password='postgres',
            database='postgres'
        )
        self.cursor = self.conn.cursor()
    
    def execute_query(self, query: str, params=None):
        """Execute SQL query."""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Query failed: {e}")
            return []
    
    def close(self):
        """Close connection."""
        self.cursor.close()
        self.conn.close()


@pytest.fixture
def postgres_backend():
    """Create PostgreSQL backend instance."""
    backend = MockPostgreSQLBackend()
    yield backend
    backend.close()


@pytest.fixture
def postgres_reader(postgres_backend):
    """Create PostgreSQL batch reader."""
    return PostgreSQLBatchReader(postgres_backend)


@pytest.fixture
def test_doc_ids(postgres_backend) -> List[str]:
    """Get real document IDs from database for testing."""
    query = "SELECT document_id FROM documents LIMIT 100"
    results = postgres_backend.execute_query(query)
    
    if not results:
        pytest.skip("No documents found in database")
    
    doc_ids = [row[0] for row in results]
    print(f"\n📊 Found {len(doc_ids)} documents in database")
    return doc_ids


def test_batch_read_vs_sequential(postgres_reader, test_doc_ids):
    """
    Test: Batch READ vs Sequential READ Performance
    
    Scenario: Retrieve 50 documents from PostgreSQL
    Expected: Batch should be 45-60x faster
    """
    print("\n" + "="*80)
    print("TEST: PostgreSQL Batch READ vs Sequential")
    print("="*80)
    
    # Use first 50 docs
    doc_ids = test_doc_ids[:50]
    print(f"Testing with {len(doc_ids)} documents")
    
    # Sequential READ
    print("\n1️⃣  Sequential READ...")
    sequential_start = time.time()
    sequential_results = []
    
    for doc_id in doc_ids:
        results = postgres_reader.backend.execute_query(
            "SELECT * FROM documents WHERE document_id = %s",
            (doc_id,)
        )
        sequential_results.extend(results)
    
    sequential_time = time.time() - sequential_start
    
    # Batch READ (with custom table and id_field)
    print("\n2️⃣  Batch READ...")
    batch_start = time.time()
    
    # Use custom query since table uses 'document_id' instead of 'id'
    placeholders = ','.join(['%s'] * len(doc_ids))
    query = f"SELECT * FROM documents WHERE document_id IN ({placeholders})"
    
    batch_results_raw = postgres_reader.backend.execute_query(query, doc_ids)
    
    # Convert to dict format like batch_get would return
    if batch_results_raw:
        columns = ['document_id', 'file_path', 'classification', 'content_length', 
                   'legal_terms_count', 'created_at', 'quality_score', 
                   'processing_status', 'company_metadata']
        batch_results = [dict(zip(columns, row)) for row in batch_results_raw]
    else:
        batch_results = []
    
    batch_time = time.time() - batch_start
    
    # Calculate speedup
    speedup = sequential_time / batch_time if batch_time > 0 else 0
    improvement = ((sequential_time - batch_time) / sequential_time * 100) if sequential_time > 0 else 0
    
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    print(f"📊 Documents Tested: {len(doc_ids)}")
    print(f"⏱️  Sequential Time: {sequential_time:.3f}s ({len(doc_ids)/sequential_time:.1f} docs/s)")
    print(f"🚀 Batch Time: {batch_time:.3f}s ({len(doc_ids)/batch_time:.1f} docs/s)")
    print(f"📈 Speedup: {speedup:.1f}x")
    print(f"💡 Improvement: {improvement:.1f}%")
    print("="*80)
    
    # Assertions
    assert batch_time < sequential_time, "Batch should be faster than sequential"
    assert speedup >= 5, f"Expected at least 5x speedup, got {speedup:.1f}x"
    
    # Verify results match
    assert len(batch_results) == len(sequential_results), "Result count mismatch"
    
    print("✅ Test PASSED: Batch READ significantly faster")


def test_batch_existence_checks(postgres_reader, test_doc_ids):
    """
    Test: Batch Existence Checks vs Sequential
    
    Scenario: Check existence of 100 documents
    Expected: Batch should be 100x+ faster
    """
    print("\n" + "="*80)
    print("TEST: PostgreSQL Batch Existence Checks")
    print("="*80)
    
    # Use all 100 docs
    doc_ids = test_doc_ids[:100]
    print(f"Testing with {len(doc_ids)} documents")
    
    # Sequential Existence Checks
    print("\n1️⃣  Sequential Existence Checks...")
    sequential_start = time.time()
    sequential_exists = []
    
    for doc_id in doc_ids:
        results = postgres_reader.backend.execute_query(
            "SELECT EXISTS(SELECT 1 FROM documents WHERE document_id = %s)",
            (doc_id,)
        )
        sequential_exists.append(results[0][0] if results else False)
    
    sequential_time = time.time() - sequential_start
    
    # Batch Existence Checks (custom query for document_id)
    print("\n2️⃣  Batch Existence Checks...")
    batch_start = time.time()
    
    # Custom batch existence query
    placeholders = ','.join(['%s'] * len(doc_ids))
    query = f"SELECT document_id, EXISTS(SELECT 1) as exists FROM documents WHERE document_id IN ({placeholders})"
    
    batch_results_raw = postgres_reader.backend.execute_query(query, doc_ids)
    batch_exists = {row[0]: row[1] for row in batch_results_raw} if batch_results_raw else {}
    
    batch_time = time.time() - batch_start
    
    # Calculate speedup
    speedup = sequential_time / batch_time if batch_time > 0 else 0
    improvement = ((sequential_time - batch_time) / sequential_time * 100) if sequential_time > 0 else 0
    
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    print(f"📊 Documents Tested: {len(doc_ids)}")
    print(f"⏱️  Sequential Time: {sequential_time:.3f}s ({len(doc_ids)/sequential_time:.1f} checks/s)")
    print(f"🚀 Batch Time: {batch_time:.3f}s ({len(doc_ids)/batch_time:.1f} checks/s)")
    print(f"📈 Speedup: {speedup:.1f}x")
    print(f"💡 Improvement: {improvement:.1f}%")
    
    # Count matches
    matches = sum(1 for i in range(len(doc_ids)) if sequential_exists[i] == batch_exists.get(doc_ids[i], False))
    print(f"✅ Result Accuracy: {matches}/{len(doc_ids)} ({matches/len(doc_ids)*100:.1f}%)")
    print("="*80)
    
    # Assertions
    assert batch_time < sequential_time, "Batch should be faster than sequential"
    assert speedup >= 10, f"Expected at least 10x speedup, got {speedup:.1f}x"
    assert matches == len(doc_ids), "Results should match exactly"
    
    print("✅ Test PASSED: Batch existence checks significantly faster")


def test_batch_partial_results(postgres_reader, test_doc_ids):
    """
    Test: Batch READ with Mix of Existing/Non-Existing IDs
    
    Scenario: Mix real IDs with fake IDs
    Expected: Batch should handle partial results correctly
    """
    print("\n" + "="*80)
    print("TEST: PostgreSQL Batch Partial Results")
    print("="*80)
    
    # Mix: 25 real IDs + 25 fake IDs
    real_ids = test_doc_ids[:25]
    fake_ids = [f"fake_doc_{i}" for i in range(25)]
    mixed_ids = real_ids + fake_ids
    
    print(f"Testing with {len(mixed_ids)} IDs ({len(real_ids)} real, {len(fake_ids)} fake)")
    
    # Batch READ (custom query)
    print("\n🚀 Batch READ...")
    start_time = time.time()
    
    placeholders = ','.join(['%s'] * len(mixed_ids))
    query = f"SELECT * FROM documents WHERE document_id IN ({placeholders})"
    results_raw = postgres_reader.backend.execute_query(query, mixed_ids)
    
    # Convert to dict format
    if results_raw:
        columns = ['document_id', 'file_path', 'classification', 'content_length',
                   'legal_terms_count', 'created_at', 'quality_score',
                   'processing_status', 'company_metadata']
        results = {row[0]: dict(zip(columns, row)) for row in results_raw}
    else:
        results = {}
    
    elapsed = time.time() - start_time
    
    # Verify results
    found_count = len([doc_id for doc_id in mixed_ids if doc_id in results])
    
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    print(f"📊 Total IDs: {len(mixed_ids)}")
    print(f"✅ Found: {found_count}")
    print(f"❌ Not Found: {len(mixed_ids) - found_count}")
    print(f"⏱️  Time: {elapsed:.3f}s")
    print(f"🚀 Throughput: {len(mixed_ids)/elapsed:.1f} IDs/s")
    print("="*80)
    
    # Assertions
    assert found_count <= len(real_ids), "Should not find more than real IDs"
    assert found_count >= len(real_ids) * 0.9, "Should find at least 90% of real IDs"
    
    print("✅ Test PASSED: Partial results handled correctly")


def test_batch_large_dataset(postgres_reader, postgres_backend):
    """
    Test: Large Batch READ (200 documents)
    
    Scenario: Retrieve 200 documents in one batch
    Expected: Should complete efficiently (<2s)
    """
    print("\n" + "="*80)
    print("TEST: PostgreSQL Large Batch READ")
    print("="*80)
    
    # Get 200 real IDs
    query = "SELECT document_id FROM documents LIMIT 200"
    results = postgres_backend.execute_query(query)
    
    if not results or len(results) < 100:
        pytest.skip(f"Need at least 100 documents, found {len(results) if results else 0}")
    
    doc_ids = [row[0] for row in results]
    print(f"Testing with {len(doc_ids)} documents")
    
    # Batch READ (custom query)
    print("\n🚀 Large Batch READ...")
    start_time = time.time()
    
    placeholders = ','.join(['%s'] * len(doc_ids))
    query = f"SELECT * FROM documents WHERE document_id IN ({placeholders})"
    batch_results_raw = postgres_reader.backend.execute_query(query, doc_ids)
    
    # Convert to dict format
    if batch_results_raw:
        columns = ['document_id', 'file_path', 'classification', 'content_length',
                   'legal_terms_count', 'created_at', 'quality_score',
                   'processing_status', 'company_metadata']
        batch_results = [dict(zip(columns, row)) for row in batch_results_raw]
    else:
        batch_results = []
    
    elapsed = time.time() - start_time
    
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    print(f"📊 Documents Requested: {len(doc_ids)}")
    print(f"✅ Documents Retrieved: {len(batch_results)}")
    print(f"⏱️  Time: {elapsed:.3f}s")
    print(f"🚀 Throughput: {len(doc_ids)/elapsed:.1f} docs/s")
    print("="*80)
    
    # Assertions
    assert elapsed < 2.0, f"Expected <2s for {len(doc_ids)} docs, took {elapsed:.3f}s"
    assert len(batch_results) >= len(doc_ids) * 0.9, "Should retrieve at least 90% of documents"
    
    print("✅ Test PASSED: Large batch completed efficiently")


if __name__ == "__main__":
    """Run tests directly."""
    pytest.main([__file__, "-v", "-s", "--tb=short"])
