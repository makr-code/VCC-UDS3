#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_batch_operations_phase2.py

test_batch_operations_phase2.py
Unit Tests for Phase 2 Batch Operations (PostgreSQL + CouchDB)
Tests PostgreSQLBatchInserter and CouchDBBatchInserter classes
with mock backends to validate functionality without database dependencies.
Test Coverage:
- PostgreSQL: 15 unit tests
- CouchDB: 15 unit tests
- Total: 30 tests
Author: UDS3 Framework
Date: Oktober 2025
Version: 2.2.0
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
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# Import classes under test
from database.batch_operations import (
    PostgreSQLBatchInserter,
    CouchDBBatchInserter,
    should_use_postgres_batch_insert,
    should_use_couchdb_batch_insert,
    get_postgres_batch_size,
    get_couchdb_batch_size
)


# ================================================================
# POSTGRESQL BATCH INSERTER TESTS
# ================================================================

class TestPostgreSQLBatchInserter:
    """Unit tests for PostgreSQLBatchInserter"""
    
    def test_init(self):
        """Test PostgreSQLBatchInserter initialization"""
        backend = Mock()
        inserter = PostgreSQLBatchInserter(backend, batch_size=50)
        
        assert inserter.backend == backend
        assert inserter.batch_size == 50
        assert inserter.total_added == 0
        assert inserter.total_batches == 0
        assert inserter.total_fallbacks == 0
        assert len(inserter.batch) == 0
    
    def test_add_single_item(self):
        """Test adding single document to batch"""
        backend = Mock()
        inserter = PostgreSQLBatchInserter(backend, batch_size=100)
        
        inserter.add(
            document_id='doc1',
            file_path='/path/to/doc1.pdf',
            classification='contract',
            content_length=1000,
            legal_terms_count=5
        )
        
        assert len(inserter.batch) == 1
        assert inserter.total_added == 1
        assert inserter.batch[0][0] == 'doc1'  # document_id
    
    def test_add_multiple_items_no_flush(self):
        """Test adding multiple documents without auto-flush"""
        backend = Mock()
        inserter = PostgreSQLBatchInserter(backend, batch_size=100)
        
        for i in range(10):
            inserter.add(
                document_id=f'doc{i}',
                file_path=f'/path/to/doc{i}.pdf',
                classification='contract',
                content_length=1000,
                legal_terms_count=5
            )
        
        assert len(inserter.batch) == 10
        assert inserter.total_added == 10
        assert inserter.total_batches == 0  # No auto-flush yet
    
    def test_auto_flush_on_batch_full(self):
        """Test auto-flush when batch size is reached"""
        backend = Mock()
        backend.connect = Mock()
        backend.cursor = Mock()
        backend.conn = Mock()
        backend.conn.commit = Mock()
        
        inserter = PostgreSQLBatchInserter(backend, batch_size=5)
        
        # Mock execute_batch to succeed
        with patch('psycopg2.extras.execute_batch') as mock_execute_batch:
            mock_execute_batch.return_value = None
            
            # Add 5 documents → should auto-flush
            for i in range(5):
                inserter.add(
                    document_id=f'doc{i}',
                    file_path=f'/path/to/doc{i}.pdf',
                    classification='contract',
                    content_length=1000,
                    legal_terms_count=5
                )
            
            # Verify flush occurred
            assert len(inserter.batch) == 0  # Batch cleared
            assert inserter.total_added == 5
            assert inserter.total_batches == 1
            assert mock_execute_batch.called
    
    def test_manual_flush(self):
        """Test manual flush"""
        backend = Mock()
        backend.connect = Mock()
        backend.cursor = Mock()
        backend.conn = Mock()
        backend.conn.commit = Mock()
        
        inserter = PostgreSQLBatchInserter(backend, batch_size=100)
        
        # Add 3 documents
        for i in range(3):
            inserter.add(
                document_id=f'doc{i}',
                file_path=f'/path/to/doc{i}.pdf',
                classification='contract',
                content_length=1000,
                legal_terms_count=5
            )
        
        assert len(inserter.batch) == 3
        
        # Manual flush
        with patch('psycopg2.extras.execute_batch') as mock_execute_batch:
            mock_execute_batch.return_value = None
            success = inserter.flush()
        
        assert success is True
        assert len(inserter.batch) == 0
        assert inserter.total_batches == 1
    
    def test_flush_empty_batch(self):
        """Test flushing empty batch (no-op)"""
        backend = Mock()
        inserter = PostgreSQLBatchInserter(backend, batch_size=100)
        
        success = inserter.flush()
        
        assert success is True
        assert inserter.total_batches == 0
    
    def test_batch_insert_success(self):
        """Test successful batch insert"""
        backend = Mock()
        backend.connect = Mock()
        backend.cursor = Mock()
        backend.conn = Mock()
        backend.conn.commit = Mock()
        
        inserter = PostgreSQLBatchInserter(backend, batch_size=100)
        
        # Add 3 documents
        for i in range(3):
            inserter.add(
                document_id=f'doc{i}',
                file_path=f'/path/to/doc{i}.pdf',
                classification='contract',
                content_length=1000,
                legal_terms_count=5
            )
        
        # Mock execute_batch to succeed
        with patch('psycopg2.extras.execute_batch') as mock_execute_batch:
            mock_execute_batch.return_value = None
            success = inserter.flush()
        
        assert success is True
        assert backend.conn.commit.called
        assert len(inserter.batch) == 0
    
    def test_fallback_on_batch_failure(self):
        """Test fallback to single inserts on batch failure"""
        backend = Mock()
        backend.connect = Mock()
        backend.cursor = Mock()
        backend.conn = Mock()
        backend.conn.commit = Mock()
        backend.conn.rollback = Mock()
        backend.insert_document = Mock(return_value={'success': True})
        
        inserter = PostgreSQLBatchInserter(backend, batch_size=100)
        
        # Add 3 documents
        for i in range(3):
            inserter.add(
                document_id=f'doc{i}',
                file_path=f'/path/to/doc{i}.pdf',
                classification='contract',
                content_length=1000,
                legal_terms_count=5
            )
        
        # Mock execute_batch to fail
        with patch('psycopg2.extras.execute_batch') as mock_execute_batch:
            mock_execute_batch.side_effect = Exception("Batch failed")
            success = inserter.flush()
        
        assert success is False
        assert inserter.total_fallbacks == 1
        assert backend.insert_document.call_count == 3  # 3 fallback inserts
        assert len(inserter.batch) == 0  # Batch cleared after fallback
    
    def test_context_manager(self):
        """Test using inserter as context manager"""
        backend = Mock()
        backend.connect = Mock()
        backend.cursor = Mock()
        backend.conn = Mock()
        backend.conn.commit = Mock()
        
        with patch('psycopg2.extras.execute_batch') as mock_execute_batch:
            mock_execute_batch.return_value = None
            
            with PostgreSQLBatchInserter(backend, batch_size=100) as inserter:
                inserter.add(
                    document_id='doc1',
                    file_path='/path/to/doc1.pdf',
                    classification='contract',
                    content_length=1000,
                    legal_terms_count=5
                )
            
            # Context manager should auto-flush on exit
            assert mock_execute_batch.called
    
    def test_get_stats(self):
        """Test get_stats method"""
        backend = Mock()
        inserter = PostgreSQLBatchInserter(backend, batch_size=100)
        
        # Add 3 documents
        for i in range(3):
            inserter.add(
                document_id=f'doc{i}',
                file_path=f'/path/to/doc{i}.pdf',
                classification='contract',
                content_length=1000,
                legal_terms_count=5
            )
        
        stats = inserter.get_stats()
        
        assert stats['total_added'] == 3
        assert stats['total_batches'] == 0
        assert stats['total_fallbacks'] == 0
        assert stats['pending'] == 3
    
    def test_thread_safety(self):
        """Test thread-safe concurrent adds"""
        backend = Mock()
        backend.connect = Mock()
        backend.cursor = Mock()
        backend.conn = Mock()
        backend.conn.commit = Mock()
        
        inserter = PostgreSQLBatchInserter(backend, batch_size=1000)
        
        def add_documents(start_idx, count):
            for i in range(start_idx, start_idx + count):
                inserter.add(
                    document_id=f'doc{i}',
                    file_path=f'/path/to/doc{i}.pdf',
                    classification='contract',
                    content_length=1000,
                    legal_terms_count=5
                )
        
        # Concurrent adds from 10 threads
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(add_documents, i * 10, 10)
                for i in range(10)
            ]
            for future in futures:
                future.result()
        
        # All 100 documents should be added
        assert inserter.total_added == 100
        assert len(inserter.batch) == 100
    
    def test_created_at_default(self):
        """Test that created_at defaults to current time"""
        backend = Mock()
        inserter = PostgreSQLBatchInserter(backend, batch_size=100)
        
        before = datetime.now().isoformat()
        
        inserter.add(
            document_id='doc1',
            file_path='/path/to/doc1.pdf',
            classification='contract',
            content_length=1000,
            legal_terms_count=5
        )
        
        after = datetime.now().isoformat()
        
        # created_at should be between before and after
        created_at = inserter.batch[0][5]  # 6th element is created_at
        assert before <= created_at <= after
    
    def test_optional_parameters(self):
        """Test optional parameters (quality_score, processing_status)"""
        backend = Mock()
        inserter = PostgreSQLBatchInserter(backend, batch_size=100)
        
        inserter.add(
            document_id='doc1',
            file_path='/path/to/doc1.pdf',
            classification='contract',
            content_length=1000,
            legal_terms_count=5,
            quality_score=0.95,
            processing_status='pending'
        )
        
        # Verify optional params in batch
        assert inserter.batch[0][6] == 0.95  # quality_score
        assert inserter.batch[0][7] == 'pending'  # processing_status
    
    def test_batch_insert_with_exception_rollback(self):
        """Test that connection rolls back on batch insert exception"""
        backend = Mock()
        backend.connect = Mock()
        backend.cursor = Mock()
        backend.conn = Mock()
        backend.conn.commit = Mock()
        backend.conn.rollback = Mock()
        backend.insert_document = Mock(return_value={'success': True})
        
        inserter = PostgreSQLBatchInserter(backend, batch_size=100)
        
        inserter.add(
            document_id='doc1',
            file_path='/path/to/doc1.pdf',
            classification='contract',
            content_length=1000,
            legal_terms_count=5
        )
        
        # Mock execute_batch to raise exception
        with patch('psycopg2.extras.execute_batch') as mock_execute_batch:
            mock_execute_batch.side_effect = Exception("DB error")
            success = inserter.flush()
        
        assert success is False
        assert backend.conn.rollback.called


# ================================================================
# COUCHDB BATCH INSERTER TESTS
# ================================================================

class TestCouchDBBatchInserter:
    """Unit tests for CouchDBBatchInserter"""
    
    def test_init(self):
        """Test CouchDBBatchInserter initialization"""
        backend = Mock()
        inserter = CouchDBBatchInserter(backend, batch_size=50)
        
        assert inserter.backend == backend
        assert inserter.batch_size == 50
        assert inserter.total_added == 0
        assert inserter.total_batches == 0
        assert inserter.total_fallbacks == 0
        assert inserter.total_conflicts == 0
        assert len(inserter.batch) == 0
    
    def test_add_single_item(self):
        """Test adding single document to batch"""
        backend = Mock()
        inserter = CouchDBBatchInserter(backend, batch_size=100)
        
        doc = {'content': 'test', 'type': 'contract'}
        inserter.add(doc, doc_id='doc1')
        
        assert len(inserter.batch) == 1
        assert inserter.total_added == 1
        assert inserter.batch[0]['_id'] == 'doc1'
    
    def test_add_multiple_items_no_flush(self):
        """Test adding multiple documents without auto-flush"""
        backend = Mock()
        inserter = CouchDBBatchInserter(backend, batch_size=100)
        
        for i in range(10):
            doc = {'content': f'test{i}', 'type': 'contract'}
            inserter.add(doc, doc_id=f'doc{i}')
        
        assert len(inserter.batch) == 10
        assert inserter.total_added == 10
        assert inserter.total_batches == 0
    
    def test_auto_flush_on_batch_full(self):
        """Test auto-flush when batch size is reached"""
        backend = Mock()
        backend.db = Mock()
        backend.db.update = Mock(return_value=[
            {'id': 'doc0', 'ok': True},
            {'id': 'doc1', 'ok': True},
            {'id': 'doc2', 'ok': True},
            {'id': 'doc3', 'ok': True},
            {'id': 'doc4', 'ok': True}
        ])
        
        inserter = CouchDBBatchInserter(backend, batch_size=5)
        
        # Add 5 documents → should auto-flush
        for i in range(5):
            doc = {'content': f'test{i}', 'type': 'contract'}
            inserter.add(doc, doc_id=f'doc{i}')
        
        # Verify flush occurred
        assert len(inserter.batch) == 0
        assert inserter.total_added == 5
        assert inserter.total_batches == 1
        assert backend.db.update.called
    
    def test_manual_flush(self):
        """Test manual flush"""
        backend = Mock()
        backend.db = Mock()
        backend.db.update = Mock(return_value=[
            {'id': 'doc0', 'ok': True},
            {'id': 'doc1', 'ok': True},
            {'id': 'doc2', 'ok': True}
        ])
        
        inserter = CouchDBBatchInserter(backend, batch_size=100)
        
        # Add 3 documents
        for i in range(3):
            doc = {'content': f'test{i}', 'type': 'contract'}
            inserter.add(doc, doc_id=f'doc{i}')
        
        assert len(inserter.batch) == 3
        
        success = inserter.flush()
        
        assert success is True
        assert len(inserter.batch) == 0
        assert inserter.total_batches == 1
    
    def test_flush_empty_batch(self):
        """Test flushing empty batch (no-op)"""
        backend = Mock()
        inserter = CouchDBBatchInserter(backend, batch_size=100)
        
        success = inserter.flush()
        
        assert success is True
        assert inserter.total_batches == 0
    
    def test_batch_insert_success(self):
        """Test successful batch insert"""
        backend = Mock()
        backend.db = Mock()
        backend.db.update = Mock(return_value=[
            {'id': 'doc0', 'ok': True},
            {'id': 'doc1', 'ok': True},
            {'id': 'doc2', 'ok': True}
        ])
        
        inserter = CouchDBBatchInserter(backend, batch_size=100)
        
        for i in range(3):
            doc = {'content': f'test{i}', 'type': 'contract'}
            inserter.add(doc, doc_id=f'doc{i}')
        
        success = inserter.flush()
        
        assert success is True
        assert backend.db.update.called
        assert len(inserter.batch) == 0
    
    def test_fallback_on_batch_failure(self):
        """Test fallback to single inserts on batch failure"""
        backend = Mock()
        backend.db = Mock()
        backend.db.update = Mock(side_effect=Exception("DB error"))
        backend.create_document = Mock(return_value='doc_id')
        
        inserter = CouchDBBatchInserter(backend, batch_size=100)
        
        for i in range(3):
            doc = {'content': f'test{i}', 'type': 'contract'}
            inserter.add(doc, doc_id=f'doc{i}')
        
        success = inserter.flush()
        
        assert success is False
        assert inserter.total_fallbacks == 1
        assert backend.create_document.call_count == 3
        assert len(inserter.batch) == 0
    
    def test_context_manager(self):
        """Test using inserter as context manager"""
        backend = Mock()
        backend.db = Mock()
        backend.db.update = Mock(return_value=[{'id': 'doc1', 'ok': True}])
        
        with CouchDBBatchInserter(backend, batch_size=100) as inserter:
            doc = {'content': 'test', 'type': 'contract'}
            inserter.add(doc, doc_id='doc1')
        
        # Context manager should auto-flush on exit
        assert backend.db.update.called
    
    def test_get_stats(self):
        """Test get_stats method"""
        backend = Mock()
        inserter = CouchDBBatchInserter(backend, batch_size=100)
        
        for i in range(3):
            doc = {'content': f'test{i}', 'type': 'contract'}
            inserter.add(doc, doc_id=f'doc{i}')
        
        stats = inserter.get_stats()
        
        assert stats['total_added'] == 3
        assert stats['total_batches'] == 0
        assert stats['total_fallbacks'] == 0
        assert stats['total_conflicts'] == 0
        assert stats['pending'] == 3
    
    def test_thread_safety(self):
        """Test thread-safe concurrent adds"""
        backend = Mock()
        backend.db = Mock()
        backend.db.update = Mock(return_value=[])
        
        inserter = CouchDBBatchInserter(backend, batch_size=1000)
        
        def add_documents(start_idx, count):
            for i in range(start_idx, start_idx + count):
                doc = {'content': f'test{i}', 'type': 'contract'}
                inserter.add(doc, doc_id=f'doc{i}')
        
        # Concurrent adds from 10 threads
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(add_documents, i * 10, 10)
                for i in range(10)
            ]
            for future in futures:
                future.result()
        
        assert inserter.total_added == 100
        assert len(inserter.batch) == 100
    
    def test_conflict_handling(self):
        """Test conflict handling (idempotent)"""
        backend = Mock()
        backend.db = Mock()
        backend.db.update = Mock(return_value=[
            {'id': 'doc0', 'ok': True},
            {'id': 'doc1', 'error': 'conflict'},  # Conflict
            {'id': 'doc2', 'ok': True}
        ])
        
        inserter = CouchDBBatchInserter(backend, batch_size=100)
        
        for i in range(3):
            doc = {'content': f'test{i}', 'type': 'contract'}
            inserter.add(doc, doc_id=f'doc{i}')
        
        success = inserter.flush()
        
        assert success is True  # Conflicts are OK (idempotent)
        assert inserter.total_conflicts == 1
    
    def test_non_conflict_errors(self):
        """Test that non-conflict errors trigger failure"""
        backend = Mock()
        backend.db = Mock()
        backend.db.update = Mock(return_value=[
            {'id': 'doc0', 'ok': True},
            {'id': 'doc1', 'error': 'forbidden'},  # Non-conflict error
            {'id': 'doc2', 'ok': True}
        ])
        backend.create_document = Mock(return_value='doc_id')
        
        inserter = CouchDBBatchInserter(backend, batch_size=100)
        
        for i in range(3):
            doc = {'content': f'test{i}', 'type': 'contract'}
            inserter.add(doc, doc_id=f'doc{i}')
        
        success = inserter.flush()
        
        assert success is False  # Non-conflict errors → fallback
        assert inserter.total_fallbacks == 1
    
    def test_add_without_doc_id(self):
        """Test adding document without explicit doc_id"""
        backend = Mock()
        inserter = CouchDBBatchInserter(backend, batch_size=100)
        
        doc = {'content': 'test', 'type': 'contract'}
        inserter.add(doc)  # No doc_id
        
        assert len(inserter.batch) == 1
        assert '_id' not in inserter.batch[0]  # CouchDB will generate UUID


# ================================================================
# HELPER FUNCTION TESTS
# ================================================================

class TestHelperFunctions:
    """Unit tests for helper functions"""
    
    def test_should_use_postgres_batch_insert(self):
        """Test should_use_postgres_batch_insert helper"""
        result = should_use_postgres_batch_insert()
        assert isinstance(result, bool)
    
    def test_should_use_couchdb_batch_insert(self):
        """Test should_use_couchdb_batch_insert helper"""
        result = should_use_couchdb_batch_insert()
        assert isinstance(result, bool)
    
    def test_get_postgres_batch_size(self):
        """Test get_postgres_batch_size helper"""
        size = get_postgres_batch_size()
        assert isinstance(size, int)
        assert size > 0
    
    def test_get_couchdb_batch_size(self):
        """Test get_couchdb_batch_size helper"""
        size = get_couchdb_batch_size()
        assert isinstance(size, int)
        assert size > 0


# ================================================================
# RUN TESTS
# ================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
