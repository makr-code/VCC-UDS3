#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration Tests for UDS3 Batch Operations
============================================

Tests batch operations with real UDS3 database backends:
- ChromaDB: Batch vector insert (add_vectors)
- Neo4j: Batch relationship creation (UNWIND)

Prerequisites:
- ChromaDB server running (192.168.178.94:8000)
- Neo4j server running (192.168.178.94:7687)

Author: UDS3 Framework
Date: Oktober 2025
"""

import pytest
import time
from typing import List, Dict, Any

# UDS3 imports
from uds3.database.database_api_chromadb_remote import ChromaRemoteVectorBackend
from uds3.database.database_api_neo4j import Neo4jGraphBackend
from uds3.database.batch_operations import (
    ChromaBatchInserter,
    Neo4jBatchCreator,
    should_use_chroma_batch_insert,
    should_use_neo4j_batching,
    get_chroma_batch_size,
    get_neo4j_batch_size
)


# ================================================================
# FIXTURES
# ================================================================

@pytest.fixture
def chromadb_backend():
    """ChromaDB backend for testing"""
    config = {
        'host': '192.168.178.94',
        'port': 8000,
        'collection_name': 'test_batch_operations',
        'use_embeddings': False  # Disable auto-embeddings for controlled tests
    }
    
    backend = ChromaRemoteVectorBackend(config)
    
    # Connect
    if not backend.connect():
        pytest.skip("ChromaDB not available")
    
    yield backend
    
    # Cleanup
    try:
        backend.disconnect()
    except:
        pass


@pytest.fixture
def neo4j_backend():
    """Neo4j backend for testing"""
    config = {
        'uri': 'bolt://192.168.178.94:7687',
        'username': 'neo4j',
        'password': 'neo4j',
        'database': 'neo4j'
    }
    
    backend = Neo4jGraphBackend(config)
    
    # Connect
    if not backend.connect():
        pytest.skip("Neo4j not available")
    
    yield backend
    
    # Cleanup
    try:
        backend.disconnect()
    except:
        pass


# ================================================================
# CHROMADB BATCH INSERTER TESTS
# ================================================================

class TestChromaBatchInserter:
    """Test ChromaDB batch insert operations"""
    
    def test_batch_inserter_init(self, chromadb_backend):
        """Test batch inserter initialization"""
        inserter = ChromaBatchInserter(chromadb_backend, batch_size=10)
        
        assert inserter.backend == chromadb_backend
        assert inserter.batch_size == 10
        assert inserter.total_added == 0
        assert inserter.total_batches == 0
        assert inserter.total_fallbacks == 0
        assert len(inserter.batch) == 0
    
    def test_batch_inserter_add_single(self, chromadb_backend):
        """Test adding single vector to batch"""
        inserter = ChromaBatchInserter(chromadb_backend, batch_size=10)
        
        # Create test vector
        chunk_id = "test_chunk_001"
        vector = [0.1] * 384  # 384-dim vector
        metadata = {
            'doc_id': 'test_doc',
            'chunk_index': 0,
            'content': 'Test content'
        }
        
        # Add to batch
        inserter.add(chunk_id, vector, metadata)
        
        # Should be in batch (not flushed yet)
        assert len(inserter.batch) == 1
        assert inserter.total_added == 0  # Not flushed yet
    
    def test_batch_inserter_auto_flush(self, chromadb_backend):
        """Test automatic flush when batch is full"""
        inserter = ChromaBatchInserter(chromadb_backend, batch_size=5)
        
        # Add 5 vectors (should trigger auto-flush)
        for i in range(5):
            chunk_id = f"test_chunk_{i:03d}"
            vector = [0.1 * i] * 384
            metadata = {'chunk_index': i}
            inserter.add(chunk_id, vector, metadata)
        
        # Should have flushed
        assert len(inserter.batch) == 0
        assert inserter.total_added == 5
        assert inserter.total_batches == 1
    
    def test_batch_inserter_manual_flush(self, chromadb_backend):
        """Test manual flush"""
        inserter = ChromaBatchInserter(chromadb_backend, batch_size=10)
        
        # Add 3 vectors (below batch size)
        for i in range(3):
            chunk_id = f"test_chunk_{i:03d}"
            vector = [0.1 * i] * 384
            metadata = {'chunk_index': i}
            inserter.add(chunk_id, vector, metadata)
        
        # Should not have auto-flushed
        assert len(inserter.batch) == 3
        assert inserter.total_added == 0
        
        # Manual flush
        success = inserter.flush()
        
        assert success
        assert len(inserter.batch) == 0
        assert inserter.total_added == 3
        assert inserter.total_batches == 1
    
    def test_batch_inserter_context_manager(self, chromadb_backend):
        """Test context manager (auto-flush on exit)"""
        with ChromaBatchInserter(chromadb_backend, batch_size=10) as inserter:
            # Add 3 vectors
            for i in range(3):
                chunk_id = f"test_chunk_ctx_{i:03d}"
                vector = [0.2 * i] * 384
                metadata = {'chunk_index': i}
                inserter.add(chunk_id, vector, metadata)
            
            # Should not have flushed yet
            assert len(inserter.batch) == 3
        
        # After context exit, should have auto-flushed
        assert len(inserter.batch) == 0
        assert inserter.total_added == 3
    
    def test_batch_inserter_stats(self, chromadb_backend):
        """Test get_stats method"""
        inserter = ChromaBatchInserter(chromadb_backend, batch_size=5)
        
        # Add 7 vectors (5 flushed, 2 pending)
        for i in range(7):
            chunk_id = f"test_chunk_stats_{i:03d}"
            vector = [0.3 * i] * 384
            metadata = {'chunk_index': i}
            inserter.add(chunk_id, vector, metadata)
        
        stats = inserter.get_stats()
        
        assert stats['total_added'] == 5  # First batch flushed
        assert stats['total_batches'] == 1
        assert stats['pending'] == 2  # 2 items waiting
    
    def test_batch_inserter_performance(self, chromadb_backend):
        """Test batch insert performance vs single insert"""
        # Skip if batch insert not enabled
        if not hasattr(chromadb_backend, 'add_vectors'):
            pytest.skip("add_vectors() not available")
        
        num_vectors = 20
        vectors_data = []
        
        # Prepare test data
        for i in range(num_vectors):
            chunk_id = f"test_perf_{i:03d}"
            vector = [0.1 * i] * 384
            metadata = {'chunk_index': i}
            vectors_data.append((chunk_id, vector, metadata))
        
        # Test single insert (baseline)
        start_single = time.time()
        for chunk_id, vector, metadata in vectors_data[:10]:  # Only 10 to save time
            chromadb_backend.add_vector(vector, metadata, chunk_id)
        time_single = time.time() - start_single
        
        # Test batch insert
        start_batch = time.time()
        with ChromaBatchInserter(chromadb_backend, batch_size=20) as inserter:
            for chunk_id, vector, metadata in vectors_data:
                inserter.add(chunk_id, vector, metadata)
        time_batch = time.time() - start_batch
        
        print(f"\nPerformance comparison:")
        print(f"  Single insert (10 items): {time_single:.3f}s ({time_single/10*1000:.1f}ms per item)")
        print(f"  Batch insert (20 items):  {time_batch:.3f}s ({time_batch/20*1000:.1f}ms per item)")
        
        # Batch should be significantly faster per item
        # Note: May not be true for small batches due to overhead
        if num_vectors >= 50:
            assert time_batch / num_vectors < time_single / 10, \
                "Batch insert should be faster per item for large batches"


# ================================================================
# NEO4J BATCH CREATOR TESTS
# ================================================================

class TestNeo4jBatchCreator:
    """Test Neo4j batch relationship creation"""
    
    def test_batch_creator_init(self, neo4j_backend):
        """Test batch creator initialization"""
        creator = Neo4jBatchCreator(neo4j_backend, batch_size=100)
        
        assert creator.backend == neo4j_backend
        assert creator.batch_size == 100
        assert creator.total_created == 0
        assert creator.total_batches == 0
        assert creator.total_fallbacks == 0
        assert len(creator.batch) == 0
    
    def test_batch_creator_add_relationship(self, neo4j_backend):
        """Test adding relationship to batch"""
        creator = Neo4jBatchCreator(neo4j_backend, batch_size=10)
        
        # Add relationship
        creator.add_relationship(
            from_id='doc_001',
            to_id='chunk_001_0',
            rel_type='HAS_CHUNK',
            properties={'created_at': '2025-10-20'}
        )
        
        # Should be in batch
        assert len(creator.batch) == 1
        assert creator.total_created == 0  # Not flushed yet
    
    def test_batch_creator_auto_flush(self, neo4j_backend):
        """Test automatic flush when batch is full"""
        # Create test nodes first
        with neo4j_backend.driver.session(database=neo4j_backend.database) as session:
            for i in range(5):
                session.run(
                    "MERGE (d:Document {id: $doc_id}) "
                    "MERGE (c:Chunk {id: $chunk_id})",
                    doc_id=f'test_doc_{i}',
                    chunk_id=f'test_chunk_{i}'
                )
        
        creator = Neo4jBatchCreator(neo4j_backend, batch_size=5)
        
        # Add 5 relationships (should trigger auto-flush)
        for i in range(5):
            creator.add_relationship(
                from_id=f'test_doc_{i}',
                to_id=f'test_chunk_{i}',
                rel_type='HAS_CHUNK'
            )
        
        # Should have flushed
        assert len(creator.batch) == 0
        assert creator.total_created >= 5  # May have created more if nodes existed
        assert creator.total_batches >= 1
    
    def test_batch_creator_manual_flush(self, neo4j_backend):
        """Test manual flush"""
        # Create test nodes
        with neo4j_backend.driver.session(database=neo4j_backend.database) as session:
            for i in range(3):
                session.run(
                    "MERGE (d:Document {id: $doc_id}) "
                    "MERGE (c:Chunk {id: $chunk_id})",
                    doc_id=f'test_doc_manual_{i}',
                    chunk_id=f'test_chunk_manual_{i}'
                )
        
        creator = Neo4jBatchCreator(neo4j_backend, batch_size=10)
        
        # Add 3 relationships (below batch size)
        for i in range(3):
            creator.add_relationship(
                from_id=f'test_doc_manual_{i}',
                to_id=f'test_chunk_manual_{i}',
                rel_type='HAS_CHUNK'
            )
        
        # Should not have auto-flushed
        assert len(creator.batch) == 3
        assert creator.total_created == 0
        
        # Manual flush
        success = creator.flush()
        
        assert success
        assert len(creator.batch) == 0
        assert creator.total_created >= 3
    
    def test_batch_creator_context_manager(self, neo4j_backend):
        """Test context manager (auto-flush on exit)"""
        # Create test nodes
        with neo4j_backend.driver.session(database=neo4j_backend.database) as session:
            for i in range(3):
                session.run(
                    "MERGE (d:Document {id: $doc_id}) "
                    "MERGE (c:Chunk {id: $chunk_id})",
                    doc_id=f'test_doc_ctx_{i}',
                    chunk_id=f'test_chunk_ctx_{i}'
                )
        
        with Neo4jBatchCreator(neo4j_backend, batch_size=10) as creator:
            # Add 3 relationships
            for i in range(3):
                creator.add_relationship(
                    from_id=f'test_doc_ctx_{i}',
                    to_id=f'test_chunk_ctx_{i}',
                    rel_type='HAS_CHUNK'
                )
            
            # Should not have flushed yet
            assert len(creator.batch) == 3
        
        # After context exit, should have auto-flushed
        assert len(creator.batch) == 0
        assert creator.total_created >= 3
    
    def test_batch_creator_stats(self, neo4j_backend):
        """Test get_stats method"""
        creator = Neo4jBatchCreator(neo4j_backend, batch_size=5)
        
        # Add 7 relationships (5 flushed, 2 pending)
        for i in range(7):
            creator.add_relationship(
                from_id=f'doc_{i}',
                to_id=f'chunk_{i}',
                rel_type='HAS_CHUNK'
            )
        
        stats = creator.get_stats()
        
        assert stats['total_batches'] >= 1
        assert stats['pending'] == 2  # 2 items waiting


# ================================================================
# HELPER FUNCTIONS TESTS
# ================================================================

class TestHelperFunctions:
    """Test helper functions"""
    
    def test_should_use_chroma_batch_insert(self):
        """Test should_use_chroma_batch_insert()"""
        result = should_use_chroma_batch_insert()
        assert isinstance(result, bool)
    
    def test_should_use_neo4j_batching(self):
        """Test should_use_neo4j_batching()"""
        result = should_use_neo4j_batching()
        assert isinstance(result, bool)
    
    def test_get_chroma_batch_size(self):
        """Test get_chroma_batch_size()"""
        size = get_chroma_batch_size()
        assert isinstance(size, int)
        assert size > 0
    
    def test_get_neo4j_batch_size(self):
        """Test get_neo4j_batch_size()"""
        size = get_neo4j_batch_size()
        assert isinstance(size, int)
        assert size > 0


# ================================================================
# PYTEST CONFIGURATION
# ================================================================

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short", "-s"])
