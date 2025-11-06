#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smoke Tests - Quick validation that core UDS3 components work

These tests verify basic functionality without mocking.
"""
import pytest
import tempfile
import os


class TestSQLiteBackendSmoke:
    """Smoke tests for SQLite backend"""
    
    def test_backend_import(self):
        """Test that SQLite backend can be imported"""
        from database.database_api_sqlite import SQLiteRelationalBackend
        assert SQLiteRelationalBackend is not None
    
    def test_backend_connection(self):
        """Test basic database connection"""
        from database.database_api_sqlite import SQLiteRelationalBackend
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            config = {'database_path': db_path}
            backend = SQLiteRelationalBackend(config)
            
            # Connect
            result = backend.connect()
            assert result is True, "Connection should succeed"
            assert backend.is_available(), "Backend should be available"
            
            # Disconnect
            backend.disconnect()
            
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_basic_query(self):
        """Test basic SQL query execution"""
        from database.database_api_sqlite import SQLiteRelationalBackend
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            config = {'database_path': db_path}
            backend = SQLiteRelationalBackend(config)
            backend.connect()
            
            # Create table
            backend.execute_query("""
                CREATE TABLE test_table (
                    id TEXT PRIMARY KEY,
                    value INTEGER
                )
            """)
            
            # Insert data
            backend.execute_query(
                "INSERT INTO test_table (id, value) VALUES (?, ?)",
                ("test_id_1", 42)
            )
            
            # Query data
            result = backend.execute_query("SELECT value FROM test_table WHERE id = ?", ("test_id_1",))
            assert result is not None
            assert len(result) > 0
            
            backend.disconnect()
            
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


class TestFileStorageBackendSmoke:
    """Smoke tests for File Storage backend"""
    
    def test_backend_import(self):
        """Test that File Storage backend can be imported"""
        from database.database_api_file_storage import FileSystemStorageBackend
        assert FileSystemStorageBackend is not None
    
    def test_backend_basic_operations(self):
        """Test basic file storage operations"""
        from database.database_api_file_storage import FileSystemStorageBackend
        
        temp_dir = tempfile.mkdtemp()
        
        try:
            config = {'base_path': temp_dir}
            backend = FileSystemStorageBackend(config)
            backend.connect()
            
            # Store file using correct method name
            test_data = b"Test file content"
            file_id = "test_file_001"
            
            # FileSystemStorageBackend uses store_asset(), not store()
            result = backend.store_asset(
                data=test_data,
                filename=file_id,
                metadata={"type": "test"}
            )
            assert result is not None, "store_asset should return result"
            
            backend.disconnect()
            
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestDatabaseExceptionsSmoke:
    """Smoke tests for exception handling"""
    
    def test_exceptions_import(self):
        """Test that exception classes can be imported"""
        from database.database_exceptions import (
            DatabaseError,
            ConnectionError,  # Not DatabaseConnectionError
            QueryError,
            InsertError
        )
        assert DatabaseError is not None
        assert ConnectionError is not None
        assert QueryError is not None


class TestConfigurationSmoke:
    """Smoke tests for configuration"""
    
    def test_config_import(self):
        """Test that config modules can be imported"""
        try:
            import config
            assert config is not None
        except ImportError:
            pytest.skip("config module not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
