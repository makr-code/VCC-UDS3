#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_batch_operations.py

test_batch_operations.py
Unit Tests for UDS3 Batch Operations
=====================================
Mock-based unit tests for batch operations (no server dependency).
Tests batch logic, thread safety, error handling, and statistics.
Author: UDS3 Framework
Date: Oktober 2025
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
import threading
import time
from typing import List, Tuple, Dict, Any
from unittest.mock import Mock, MagicMock, patch, call

# UDS3 imports
from uds3.database.batch_operations import (
    ChromaBatchInserter,
    Neo4jBatchCreator,
    should_use_chroma_batch_insert,
    should_use_neo4j_batching,
    get_chroma_batch_size,
    get_neo4j_batch_size,
    ENABLE_CHROMA_BATCH_INSERT,
    ENABLE_NEO4J_BATCHING,
    CHROMA_BATCH_INSERT_SIZE,
    NEO4J_BATCH_SIZE
)


# ================================================================
# CHROMADB BATCH INSERTER TESTS
# ================================================================

class TestChromaBatchInserterUnit:
    """Unit tests for ChromaBatchInserter (mock-based)"""
    
    def test_init(self):
        """Test initialization with default parameters"""
        backend = Mock()
        inserter = ChromaBatchInserter(backend, batch_size=50)
        
        assert inserter.backend == backend
        assert inserter.batch_size == 50
        assert inserter.total_added == 0
        assert inserter.total_batches == 0
        assert inserter.total_fallbacks == 0
        assert len(inserter.batch) == 0
        assert inserter._lock is not None
    
    def test_add_single_item(self):
        """Test adding single item to batch"""
        backend = Mock()
        inserter = ChromaBatchInserter(backend, batch_size=10)
        
        chunk_id = "chunk_001"
        vector = [0.1] * 384
        metadata = {'doc_id': 'doc_001'}
        
        inserter.add(chunk_id, vector, metadata)
        
        assert len(inserter.batch) == 1
        assert inserter.batch[0] == (chunk_id, vector, metadata)
        assert inserter.total_added == 0  # Not flushed yet
    
    def test_add_multiple_items_no_flush(self):
        """Test adding multiple items below batch size"""
        backend = Mock()
        inserter = ChromaBatchInserter(backend, batch_size=10)
        
        # Add 5 items (below batch_size=10)
        for i in range(5):
            inserter.add(f"chunk_{i}", [0.1 * i] * 384, {'index': i})
        
        assert len(inserter.batch) == 5
        assert inserter.total_added == 0  # Not flushed yet
    
    def test_auto_flush_on_batch_full(self):
        """Test automatic flush when batch reaches size limit"""
        backend = Mock()
        backend.add_vectors = Mock(return_value=True)
        
        inserter = ChromaBatchInserter(backend, batch_size=5)
        
        # Add 5 items (should trigger auto-flush)
        for i in range(5):
            inserter.add(f"chunk_{i}", [0.1 * i] * 384, {'index': i})
        
        # Should have flushed
        assert len(inserter.batch) == 0
        assert inserter.total_added == 5
        assert inserter.total_batches == 1
        backend.add_vectors.assert_called_once()
    
    def test_manual_flush(self):
        """Test manual flush with pending items"""
        backend = Mock()
        backend.add_vectors = Mock(return_value=True)
        
        inserter = ChromaBatchInserter(backend, batch_size=10)
        
        # Add 3 items
        for i in range(3):
            inserter.add(f"chunk_{i}", [0.1 * i] * 384, {'index': i})
        
        assert len(inserter.batch) == 3
        
        # Manual flush
        success = inserter.flush()
        
        assert success is True
        assert len(inserter.batch) == 0
        assert inserter.total_added == 3
        assert inserter.total_batches == 1
        backend.add_vectors.assert_called_once()
    
    def test_flush_empty_batch(self):
        """Test flushing empty batch (no-op)"""
        backend = Mock()
        inserter = ChromaBatchInserter(backend, batch_size=10)
        
        success = inserter.flush()
        
        assert success is True
        assert inserter.total_added == 0
        assert inserter.total_batches == 0
        backend.add_vectors.assert_not_called()
    
    def test_batch_insert_success(self):
        """Test successful batch insert"""
        backend = Mock()
        backend.add_vectors = Mock(return_value=True)
        
        inserter = ChromaBatchInserter(backend, batch_size=10)
        
        # Add and flush 3 items
        for i in range(3):
            inserter.add(f"chunk_{i}", [0.1 * i] * 384, {'index': i})
        
        # Batch should have 3 items before flush
        assert len(inserter.batch) == 3
        
        inserter.flush()
        
        # After flush, batch should be empty
        assert len(inserter.batch) == 0
        
        # Verify add_vectors was called once
        backend.add_vectors.assert_called_once()
        
        # Verify the batched data was correct
        call_args = backend.add_vectors.call_args[0][0]
        assert len(call_args) == 3
        assert call_args[0][0] == "chunk_0"
        assert call_args[1][0] == "chunk_1"
        assert call_args[2][0] == "chunk_2"
    
    def test_fallback_on_batch_failure(self):
        """Test fallback to per-item insert when batch fails"""
        backend = Mock()
        backend.add_vectors = Mock(return_value=False)  # Batch fails
        backend.add_vector = Mock(return_value=True)     # Per-item succeeds
        
        inserter = ChromaBatchInserter(backend, batch_size=10)
        
        # Add and flush 3 items
        for i in range(3):
            inserter.add(f"chunk_{i}", [0.1 * i] * 384, {'index': i})
        success = inserter.flush()
        
        # Should have fallen back to per-item insert
        assert success is True
        assert inserter.total_added == 3
        assert inserter.total_fallbacks == 1
        assert backend.add_vector.call_count == 3
    
    def test_fallback_on_exception(self):
        """Test fallback when batch insert throws exception"""
        backend = Mock()
        backend.add_vectors = Mock(side_effect=Exception("API Error"))
        backend.add_vector = Mock(return_value=True)
        
        inserter = ChromaBatchInserter(backend, batch_size=10)
        
        # Add and flush 2 items
        for i in range(2):
            inserter.add(f"chunk_{i}", [0.1 * i] * 384, {'index': i})
        success = inserter.flush()
        
        # Should have fallen back
        assert success is True
        assert inserter.total_added == 2
        assert inserter.total_fallbacks == 1
    
    def test_no_add_vectors_method(self):
        """Test fallback when backend lacks add_vectors method"""
        backend = Mock(spec=[])  # No methods
        backend.add_vector = Mock(return_value=True)
        
        inserter = ChromaBatchInserter(backend, batch_size=10)
        
        inserter.add("chunk_001", [0.1] * 384, {})
        success = inserter.flush()
        
        assert success is True
        assert inserter.total_fallbacks == 1
        backend.add_vector.assert_called_once()
    
    def test_context_manager(self):
        """Test context manager auto-flush"""
        backend = Mock()
        backend.add_vectors = Mock(return_value=True)
        
        with ChromaBatchInserter(backend, batch_size=10) as inserter:
            for i in range(3):
                inserter.add(f"chunk_{i}", [0.1 * i] * 384, {'index': i})
            
            # Should not have flushed yet
            assert len(inserter.batch) == 3
        
        # After context exit, should have auto-flushed
        assert len(inserter.batch) == 0
        assert inserter.total_added == 3
        backend.add_vectors.assert_called_once()
    
    def test_get_stats(self):
        """Test statistics tracking"""
        backend = Mock()
        backend.add_vectors = Mock(return_value=True)
        
        inserter = ChromaBatchInserter(backend, batch_size=5)
        
        # Add 7 items (5 flushed, 2 pending)
        for i in range(7):
            inserter.add(f"chunk_{i}", [0.1 * i] * 384, {'index': i})
        
        stats = inserter.get_stats()
        
        assert stats['total_added'] == 5
        assert stats['total_batches'] == 1
        assert stats['total_fallbacks'] == 0
        assert stats['pending'] == 2
    
    def test_thread_safety(self):
        """Test thread-safe batch operations"""
        backend = Mock()
        backend.add_vectors = Mock(return_value=True)
        
        inserter = ChromaBatchInserter(backend, batch_size=100)
        
        results = []
        
        def add_items(thread_id: int):
            for i in range(10):
                inserter.add(f"chunk_{thread_id}_{i}", [0.1] * 384, {'thread': thread_id})
            results.append(thread_id)
        
        # Create 5 threads adding items concurrently
        threads = []
        for i in range(5):
            thread = threading.Thread(target=add_items, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # All threads should have completed
        assert len(results) == 5
        
        # Flush remaining items
        inserter.flush()
        
        # Should have added 50 items total
        assert inserter.total_added == 50
    
    def test_partial_fallback_failure(self):
        """Test partial failure in fallback mode"""
        backend = Mock()
        backend.add_vectors = Mock(return_value=False)
        
        # First 2 items succeed, 3rd fails
        backend.add_vector = Mock(side_effect=[True, True, False])
        
        inserter = ChromaBatchInserter(backend, batch_size=10)
        
        for i in range(3):
            inserter.add(f"chunk_{i}", [0.1 * i] * 384, {'index': i})
        
        success = inserter.flush()
        
        # Should return True (at least one succeeded)
        assert success is True
        assert inserter.total_added == 2
        assert backend.add_vector.call_count == 3


# ================================================================
# NEO4J BATCH CREATOR TESTS
# ================================================================

class TestNeo4jBatchCreatorUnit:
    """Unit tests for Neo4jBatchCreator (mock-based)"""
    
    def test_init(self):
        """Test initialization with default parameters"""
        backend = Mock()
        creator = Neo4jBatchCreator(backend, batch_size=500)
        
        assert creator.backend == backend
        assert creator.batch_size == 500
        assert creator.total_created == 0
        assert creator.total_batches == 0
        assert creator.total_fallbacks == 0
        assert len(creator.batch) == 0
        assert creator._lock is not None
    
    def test_add_relationship(self):
        """Test adding relationship to batch"""
        backend = Mock()
        creator = Neo4jBatchCreator(backend, batch_size=10)
        
        creator.add_relationship(
            from_id='doc_001',
            to_id='chunk_001',
            rel_type='HAS_CHUNK',
            properties={'created': '2025-10-20'}
        )
        
        assert len(creator.batch) == 1
        assert creator.batch[0]['from_id'] == 'doc_001'
        assert creator.batch[0]['to_id'] == 'chunk_001'
        assert creator.batch[0]['rel_type'] == 'HAS_CHUNK'
        assert creator.batch[0]['properties'] == {'created': '2025-10-20'}
    
    def test_add_multiple_relationships(self):
        """Test adding multiple relationships"""
        backend = Mock()
        creator = Neo4jBatchCreator(backend, batch_size=10)
        
        for i in range(5):
            creator.add_relationship(
                from_id=f'doc_{i}',
                to_id=f'chunk_{i}',
                rel_type='HAS_CHUNK'
            )
        
        assert len(creator.batch) == 5
        assert creator.total_created == 0  # Not flushed yet
    
    def test_auto_flush_on_batch_full(self):
        """Test automatic flush when batch is full"""
        backend = Mock()
        backend.driver = Mock()
        backend.database = 'neo4j'
        
        # Mock session and result
        session = Mock()
        session.run = Mock(return_value=Mock(single=Mock(return_value={'created_count': 5})))
        backend.driver.session = Mock(return_value=session)
        session.__enter__ = Mock(return_value=session)
        session.__exit__ = Mock(return_value=False)
        
        creator = Neo4jBatchCreator(backend, batch_size=5)
        
        # Add 5 relationships (should trigger auto-flush)
        for i in range(5):
            creator.add_relationship(f'doc_{i}', f'chunk_{i}', 'HAS_CHUNK')
        
        # Should have flushed
        assert len(creator.batch) == 0
        assert creator.total_created == 5
        assert creator.total_batches == 1
    
    def test_manual_flush(self):
        """Test manual flush"""
        backend = Mock()
        backend.driver = Mock()
        backend.database = 'neo4j'
        
        session = Mock()
        session.run = Mock(return_value=Mock(single=Mock(return_value={'created_count': 3})))
        backend.driver.session = Mock(return_value=session)
        session.__enter__ = Mock(return_value=session)
        session.__exit__ = Mock(return_value=False)
        
        creator = Neo4jBatchCreator(backend, batch_size=10)
        
        # Add 3 relationships
        for i in range(3):
            creator.add_relationship(f'doc_{i}', f'chunk_{i}', 'HAS_CHUNK')
        
        assert len(creator.batch) == 3
        
        # Manual flush
        success = creator.flush()
        
        assert success is True
        assert len(creator.batch) == 0
        assert creator.total_created == 3
    
    def test_flush_empty_batch(self):
        """Test flushing empty batch (no-op)"""
        backend = Mock()
        creator = Neo4jBatchCreator(backend, batch_size=10)
        
        success = creator.flush()
        
        assert success is True
        assert creator.total_created == 0
    
    def test_no_driver_fallback(self):
        """Test fallback when driver not available"""
        backend = Mock()
        backend.driver = None
        backend.create_relationship_by_id = Mock(return_value='rel_123')
        
        creator = Neo4jBatchCreator(backend, batch_size=10)
        
        creator.add_relationship('doc_001', 'chunk_001', 'HAS_CHUNK')
        success = creator.flush()
        
        # Should have fallen back to per-item create
        assert success is True
        assert creator.total_fallbacks == 1
        backend.create_relationship_by_id.assert_called_once()
    
    def test_apoc_fallback_to_manual_merge(self):
        """Test fallback from APOC to manual MERGE"""
        backend = Mock()
        backend.driver = Mock()
        backend.database = 'neo4j'
        
        session = Mock()
        
        # First call (APOC) fails, subsequent calls (manual MERGE) succeed
        session.run = Mock(side_effect=[
            Exception("APOC not available"),  # APOC query fails
            Mock(single=Mock(return_value={'r': 'rel_1'})),  # Manual query 1
            Mock(single=Mock(return_value={'r': 'rel_2'}))   # Manual query 2
        ])
        
        backend.driver.session = Mock(return_value=session)
        session.__enter__ = Mock(return_value=session)
        session.__exit__ = Mock(return_value=False)
        
        creator = Neo4jBatchCreator(backend, batch_size=10)
        
        # Add 2 relationships
        creator.add_relationship('doc_1', 'chunk_1', 'HAS_CHUNK')
        creator.add_relationship('doc_2', 'chunk_2', 'HAS_CHUNK')
        
        success = creator.flush()
        
        # Should have succeeded with manual MERGE fallback
        assert success is True
        assert creator.total_created == 2
    
    def test_context_manager(self):
        """Test context manager auto-flush"""
        backend = Mock()
        backend.driver = Mock()
        backend.database = 'neo4j'
        
        session = Mock()
        session.run = Mock(return_value=Mock(single=Mock(return_value={'created_count': 2})))
        backend.driver.session = Mock(return_value=session)
        session.__enter__ = Mock(return_value=session)
        session.__exit__ = Mock(return_value=False)
        
        with Neo4jBatchCreator(backend, batch_size=10) as creator:
            creator.add_relationship('doc_1', 'chunk_1', 'HAS_CHUNK')
            creator.add_relationship('doc_2', 'chunk_2', 'HAS_CHUNK')
            
            # Should not have flushed yet
            assert len(creator.batch) == 2
        
        # After context exit, should have auto-flushed
        assert len(creator.batch) == 0
        assert creator.total_created == 2
    
    def test_get_stats(self):
        """Test statistics tracking"""
        backend = Mock()
        backend.driver = Mock()
        backend.database = 'neo4j'
        
        session = Mock()
        session.run = Mock(return_value=Mock(single=Mock(return_value={'created_count': 5})))
        backend.driver.session = Mock(return_value=session)
        session.__enter__ = Mock(return_value=session)
        session.__exit__ = Mock(return_value=False)
        
        creator = Neo4jBatchCreator(backend, batch_size=5)
        
        # Add 7 relationships (5 flushed, 2 pending)
        for i in range(7):
            creator.add_relationship(f'doc_{i}', f'chunk_{i}', 'HAS_CHUNK')
        
        stats = creator.get_stats()
        
        assert stats['total_created'] == 5
        assert stats['total_batches'] == 1
        assert stats['pending'] == 2
    
    def test_thread_safety(self):
        """Test thread-safe batch operations"""
        backend = Mock()
        backend.driver = Mock()
        backend.database = 'neo4j'
        
        session = Mock()
        session.run = Mock(return_value=Mock(single=Mock(return_value={'created_count': 50})))
        backend.driver.session = Mock(return_value=session)
        session.__enter__ = Mock(return_value=session)
        session.__exit__ = Mock(return_value=False)
        
        creator = Neo4jBatchCreator(backend, batch_size=100)
        
        results = []
        
        def add_relationships(thread_id: int):
            for i in range(10):
                creator.add_relationship(
                    f'doc_{thread_id}_{i}',
                    f'chunk_{thread_id}_{i}',
                    'HAS_CHUNK'
                )
            results.append(thread_id)
        
        # Create 5 threads adding relationships concurrently
        threads = []
        for i in range(5):
            thread = threading.Thread(target=add_relationships, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # All threads should have completed
        assert len(results) == 5
        
        # Flush remaining items
        creator.flush()
        
        # Should have added 50 relationships total
        assert creator.total_created == 50


# ================================================================
# HELPER FUNCTIONS TESTS
# ================================================================

class TestHelperFunctions:
    """Test helper functions"""
    
    def test_should_use_chroma_batch_insert(self):
        """Test should_use_chroma_batch_insert() returns correct value"""
        result = should_use_chroma_batch_insert()
        assert result == ENABLE_CHROMA_BATCH_INSERT
        assert isinstance(result, bool)
    
    def test_should_use_neo4j_batching(self):
        """Test should_use_neo4j_batching() returns correct value"""
        result = should_use_neo4j_batching()
        assert result == ENABLE_NEO4J_BATCHING
        assert isinstance(result, bool)
    
    def test_get_chroma_batch_size(self):
        """Test get_chroma_batch_size() returns correct value"""
        size = get_chroma_batch_size()
        assert size == CHROMA_BATCH_INSERT_SIZE
        assert isinstance(size, int)
        assert size > 0
    
    def test_get_neo4j_batch_size(self):
        """Test get_neo4j_batch_size() returns correct value"""
        size = get_neo4j_batch_size()
        assert size == NEO4J_BATCH_SIZE
        assert isinstance(size, int)
        assert size > 0


# ================================================================
# PYTEST CONFIGURATION
# ================================================================

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
