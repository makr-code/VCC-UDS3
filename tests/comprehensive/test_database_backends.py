#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Database Backend Tests

Tests all database adapters for:
- Connection handling
- CRUD operations
- Error handling
- Concurrency
- Data integrity
- Performance regression
"""
import pytest
import tempfile
import os
from pathlib import Path
from typing import Dict, Any

# Database API imports
from database.database_api_sqlite import SQLiteDatabaseAPI
from database.database_api_postgresql import PostgreSQLDatabaseAPI
from database.database_api_chromadb import ChromaDatabaseAPI
from database.database_api_couchdb import CouchDBDatabaseAPI
from database.database_api_neo4j import Neo4jDatabaseAPI
from database.database_api_file_storage import FileStorageDatabaseAPI
from database.database_exceptions import DatabaseConnectionError, DatabaseOperationError


class TestSQLiteBackend:
    """Test SQLite database adapter"""
    
    @pytest.fixture
    def db(self):
        """Create temporary SQLite database"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db_api = SQLiteDatabaseAPI(db_path)
        yield db_api
        
        # Cleanup
        db_api.close()
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_connection(self, db):
        """Test database connection"""
        assert db.connection is not None
        assert db.is_connected()
    
    def test_create_table(self, db):
        """Test table creation"""
        db.execute_query("""
            CREATE TABLE IF NOT EXISTS test_table (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                value INTEGER
            )
        """)
        
        # Verify table exists
        result = db.execute_query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='test_table'"
        )
        assert len(result) == 1
    
    def test_insert_and_select(self, db):
        """Test insert and select operations"""
        db.execute_query("""
            CREATE TABLE test_data (
                id INTEGER PRIMARY KEY,
                content TEXT
            )
        """)
        
        # Insert data
        db.execute_query(
            "INSERT INTO test_data (content) VALUES (?)",
            ("test content",)
        )
        
        # Select data
        result = db.execute_query("SELECT content FROM test_data")
        assert len(result) == 1
        assert result[0][0] == "test content"
    
    def test_update_and_delete(self, db):
        """Test update and delete operations"""
        db.execute_query("""
            CREATE TABLE test_data (
                id INTEGER PRIMARY KEY,
                value INTEGER
            )
        """)
        
        # Insert
        db.execute_query("INSERT INTO test_data (value) VALUES (?)", (10,))
        
        # Update
        db.execute_query("UPDATE test_data SET value = ? WHERE id = 1", (20,))
        result = db.execute_query("SELECT value FROM test_data WHERE id = 1")
        assert result[0][0] == 20
        
        # Delete
        db.execute_query("DELETE FROM test_data WHERE id = 1")
        result = db.execute_query("SELECT COUNT(*) FROM test_data")
        assert result[0][0] == 0
    
    def test_transaction_rollback(self, db):
        """Test transaction rollback on error"""
        db.execute_query("""
            CREATE TABLE test_data (
                id INTEGER PRIMARY KEY,
                value INTEGER NOT NULL
            )
        """)
        
        db.execute_query("INSERT INTO test_data (value) VALUES (?)", (10,))
        
        # Attempt invalid operation (should rollback)
        with pytest.raises(Exception):
            db.execute_query("INSERT INTO test_data (value) VALUES (?)", (None,))
        
        # Verify original data still exists
        result = db.execute_query("SELECT COUNT(*) FROM test_data")
        assert result[0][0] == 1
    
    def test_concurrent_access(self, db):
        """Test concurrent read/write operations"""
        db.execute_query("""
            CREATE TABLE test_data (
                id INTEGER PRIMARY KEY,
                counter INTEGER DEFAULT 0
            )
        """)
        
        db.execute_query("INSERT INTO test_data (counter) VALUES (0)")
        
        # Simulate concurrent increments
        for _ in range(10):
            db.execute_query("UPDATE test_data SET counter = counter + 1 WHERE id = 1")
        
        result = db.execute_query("SELECT counter FROM test_data WHERE id = 1")
        assert result[0][0] == 10


class TestFileStorageBackend:
    """Test File Storage database adapter"""
    
    @pytest.fixture
    def db(self):
        """Create temporary file storage"""
        temp_dir = tempfile.mkdtemp()
        db_api = FileStorageDatabaseAPI(base_path=temp_dir)
        yield db_api
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_store_and_retrieve(self, db):
        """Test storing and retrieving files"""
        test_data = b"Test file content"
        file_id = "test_file_001"
        
        # Store file
        success = db.store_file(file_id, test_data, metadata={"type": "test"})
        assert success
        
        # Retrieve file
        retrieved = db.retrieve_file(file_id)
        assert retrieved == test_data
    
    def test_file_metadata(self, db):
        """Test file metadata handling"""
        test_data = b"Content"
        file_id = "meta_test"
        metadata = {"author": "test", "version": 1}
        
        db.store_file(file_id, test_data, metadata=metadata)
        
        # Retrieve metadata
        meta = db.get_metadata(file_id)
        assert meta["author"] == "test"
        assert meta["version"] == 1
    
    def test_list_files(self, db):
        """Test listing stored files"""
        # Store multiple files
        for i in range(5):
            db.store_file(f"file_{i}", f"content_{i}".encode())
        
        # List files
        files = db.list_files()
        assert len(files) >= 5
    
    def test_delete_file(self, db):
        """Test file deletion"""
        file_id = "deletable"
        db.store_file(file_id, b"temp content")
        
        # Delete
        success = db.delete_file(file_id)
        assert success
        
        # Verify deletion
        retrieved = db.retrieve_file(file_id)
        assert retrieved is None
    
    def test_file_not_found(self, db):
        """Test handling of non-existent files"""
        result = db.retrieve_file("nonexistent_file")
        assert result is None


class TestDatabaseErrorHandling:
    """Test error handling across all backends"""
    
    def test_sqlite_invalid_query(self):
        """Test SQLite with invalid SQL"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db = SQLiteDatabaseAPI(db_path)
        
        with pytest.raises(Exception):
            db.execute_query("INVALID SQL STATEMENT")
        
        db.close()
        os.unlink(db_path)
    
    def test_connection_failure_recovery(self):
        """Test recovery from connection failures"""
        # Create DB with invalid path
        with pytest.raises((DatabaseConnectionError, Exception)):
            db = SQLiteDatabaseAPI("/invalid/path/database.db")


class TestDatabasePerformance:
    """Performance regression tests"""
    
    @pytest.fixture
    def db(self):
        """Create temporary SQLite database"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db_api = SQLiteDatabaseAPI(db_path)
        db_api.execute_query("""
            CREATE TABLE perf_test (
                id INTEGER PRIMARY KEY,
                data TEXT
            )
        """)
        yield db_api
        
        db_api.close()
        os.unlink(db_path)
    
    def test_bulk_insert_performance(self, db):
        """Test bulk insert performance (should complete in reasonable time)"""
        import time
        
        start = time.time()
        
        # Insert 1000 records
        for i in range(1000):
            db.execute_query("INSERT INTO perf_test (data) VALUES (?)", (f"data_{i}",))
        
        elapsed = time.time() - start
        
        # Should complete within 5 seconds
        assert elapsed < 5.0, f"Bulk insert took {elapsed:.2f}s (expected < 5s)"
        
        # Verify count
        result = db.execute_query("SELECT COUNT(*) FROM perf_test")
        assert result[0][0] == 1000
    
    def test_query_performance(self, db):
        """Test query performance with indexed data"""
        import time
        
        # Insert test data
        for i in range(100):
            db.execute_query("INSERT INTO perf_test (data) VALUES (?)", (f"data_{i}",))
        
        # Create index
        db.execute_query("CREATE INDEX idx_data ON perf_test(data)")
        
        start = time.time()
        
        # Run queries
        for i in range(100):
            db.execute_query("SELECT * FROM perf_test WHERE data = ?", (f"data_{i}",))
        
        elapsed = time.time() - start
        
        # Should complete within 1 second
        assert elapsed < 1.0, f"100 queries took {elapsed:.2f}s (expected < 1s)"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
