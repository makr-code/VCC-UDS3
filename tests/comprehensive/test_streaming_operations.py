#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streaming & Batch Operations Tests

Tests:
- Streaming with backpressure
- Batch optimization
- Single-record cache
- Adaptive batch sizing
- Memory management
"""
import pytest
import tempfile
import os
from typing import List, Iterator

# Streaming imports
from streaming.streaming_operations import StreamingProcessor, StreamConfig
from streaming.batch_operations import BatchProcessor, AdaptiveBatchProcessor
from streaming.single_record_cache import SingleRecordCache
from database.database_api_sqlite import SQLiteDatabaseAPI


class TestStreamingOperations:
    """Test streaming processor"""
    
    @pytest.fixture
    def db(self):
        """Create temporary database"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db_api = SQLiteDatabaseAPI(db_path)
        db_api.execute_query("""
            CREATE TABLE stream_test (
                id INTEGER PRIMARY KEY,
                data TEXT,
                processed BOOLEAN DEFAULT 0
            )
        """)
        yield db_api
        
        db_api.close()
        os.unlink(db_path)
    
    def test_stream_processing(self, db):
        """Test basic streaming"""
        # Insert test data
        for i in range(100):
            db.execute_query(
                "INSERT INTO stream_test (data) VALUES (?)",
                (f"record_{i}",)
            )
        
        # Stream and process
        config = StreamConfig(batch_size=10, max_buffer=50)
        processor = StreamingProcessor(db, config)
        
        processed_count = 0
        for batch in processor.stream_records("stream_test"):
            for record in batch:
                db.execute_query(
                    "UPDATE stream_test SET processed = 1 WHERE id = ?",
                    (record[0],)
                )
                processed_count += 1
        
        # Verify all processed
        assert processed_count == 100
        
        result = db.execute_query(
            "SELECT COUNT(*) FROM stream_test WHERE processed = 1"
        )
        assert result[0][0] == 100
    
    def test_streaming_backpressure(self, db):
        """Test backpressure handling"""
        # Insert large dataset
        for i in range(1000):
            db.execute_query(
                "INSERT INTO stream_test (data) VALUES (?)",
                (f"large_record_{i}" * 100,)  # Large records
            )
        
        config = StreamConfig(batch_size=10, max_buffer=30)
        processor = StreamingProcessor(db, config)
        
        batch_count = 0
        for batch in processor.stream_records("stream_test"):
            batch_count += 1
            # Simulate slow processing
            assert len(batch) <= config.batch_size
        
        # Should have created multiple batches
        assert batch_count > 10
    
    def test_streaming_error_recovery(self, db):
        """Test error recovery during streaming"""
        # Insert test data
        for i in range(50):
            db.execute_query(
                "INSERT INTO stream_test (data) VALUES (?)",
                (f"record_{i}",)
            )
        
        config = StreamConfig(batch_size=10)
        processor = StreamingProcessor(db, config)
        
        processed = 0
        errors = 0
        
        for batch in processor.stream_records("stream_test"):
            for record in batch:
                try:
                    # Simulate occasional error
                    if record[0] % 10 == 0:
                        raise Exception("Simulated error")
                    processed += 1
                except Exception:
                    errors += 1
        
        # Should process most records despite errors
        assert processed > 40
        assert errors > 0


class TestBatchOperations:
    """Test batch processing"""
    
    @pytest.fixture
    def db(self):
        """Create temporary database"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db_api = SQLiteDatabaseAPI(db_path)
        db_api.execute_query("""
            CREATE TABLE batch_test (
                id INTEGER PRIMARY KEY,
                value INTEGER
            )
        """)
        yield db_api
        
        db_api.close()
        os.unlink(db_path)
    
    def test_batch_insert(self, db):
        """Test batch insert optimization"""
        processor = BatchProcessor(db, batch_size=100)
        
        # Prepare data
        data = [(i,) for i in range(500)]
        
        # Batch insert
        processor.batch_insert("batch_test", "value", data)
        
        # Verify all inserted
        result = db.execute_query("SELECT COUNT(*) FROM batch_test")
        assert result[0][0] == 500
    
    def test_batch_update(self, db):
        """Test batch update"""
        # Insert test data
        for i in range(100):
            db.execute_query("INSERT INTO batch_test (value) VALUES (?)", (i,))
        
        processor = BatchProcessor(db, batch_size=20)
        
        # Batch update (double all values)
        updates = [(i * 2, i + 1) for i in range(100)]
        processor.batch_update(
            "batch_test",
            "UPDATE batch_test SET value = ? WHERE id = ?",
            updates
        )
        
        # Verify updates
        result = db.execute_query("SELECT value FROM batch_test WHERE id = 1")
        assert result[0][0] == 0  # 0 * 2 = 0
        
        result = db.execute_query("SELECT value FROM batch_test WHERE id = 50")
        assert result[0][0] == 98  # 49 * 2 = 98


class TestAdaptiveBatchProcessor:
    """Test adaptive batch sizing"""
    
    @pytest.fixture
    def db(self):
        """Create temporary database"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db_api = SQLiteDatabaseAPI(db_path)
        db_api.execute_query("""
            CREATE TABLE adaptive_test (
                id INTEGER PRIMARY KEY,
                data TEXT
            )
        """)
        yield db_api
        
        db_api.close()
        os.unlink(db_path)
    
    def test_adaptive_batch_sizing(self, db):
        """Test adaptive batch size adjustment"""
        processor = AdaptiveBatchProcessor(
            db,
            initial_batch_size=10,
            min_batch_size=5,
            max_batch_size=100
        )
        
        # Simulate processing with performance feedback
        for i in range(10):
            batch_size = processor.get_current_batch_size()
            
            # Simulate fast processing (should increase batch size)
            processor.record_performance(batch_size, processing_time=0.1)
        
        # Batch size should have increased
        final_batch_size = processor.get_current_batch_size()
        assert final_batch_size > 10
    
    def test_adaptive_batch_degradation(self, db):
        """Test batch size reduction on slow processing"""
        processor = AdaptiveBatchProcessor(
            db,
            initial_batch_size=50,
            min_batch_size=5,
            max_batch_size=100
        )
        
        # Simulate slow processing (should decrease batch size)
        for i in range(10):
            batch_size = processor.get_current_batch_size()
            processor.record_performance(batch_size, processing_time=5.0)
        
        # Batch size should have decreased
        final_batch_size = processor.get_current_batch_size()
        assert final_batch_size < 50


class TestSingleRecordCache:
    """Test single-record cache"""
    
    def test_cache_hit(self):
        """Test cache hit scenario"""
        cache = SingleRecordCache(max_size=10)
        
        # Store record
        cache.put("key1", {"data": "value1"})
        
        # Retrieve (should hit)
        result = cache.get("key1")
        assert result is not None
        assert result["data"] == "value1"
        
        # Verify hit rate
        stats = cache.get_stats()
        assert stats["hit_rate"] > 0
    
    def test_cache_miss(self):
        """Test cache miss scenario"""
        cache = SingleRecordCache(max_size=10)
        
        # Try to get non-existent key
        result = cache.get("nonexistent")
        assert result is None
        
        # Verify miss recorded
        stats = cache.get_stats()
        assert stats["misses"] == 1
    
    def test_cache_eviction(self):
        """Test LRU eviction"""
        cache = SingleRecordCache(max_size=3)
        
        # Fill cache
        cache.put("key1", {"data": "value1"})
        cache.put("key2", {"data": "value2"})
        cache.put("key3", {"data": "value3"})
        
        # Add one more (should evict key1)
        cache.put("key4", {"data": "value4"})
        
        # key1 should be evicted
        assert cache.get("key1") is None
        # key2, key3, key4 should exist
        assert cache.get("key2") is not None
        assert cache.get("key3") is not None
        assert cache.get("key4") is not None
    
    def test_cache_update(self):
        """Test updating cached value"""
        cache = SingleRecordCache(max_size=10)
        
        # Initial value
        cache.put("key1", {"data": "old_value"})
        
        # Update
        cache.put("key1", {"data": "new_value"})
        
        # Should return updated value
        result = cache.get("key1")
        assert result["data"] == "new_value"
    
    def test_cache_clear(self):
        """Test cache clearing"""
        cache = SingleRecordCache(max_size=10)
        
        # Add records
        for i in range(5):
            cache.put(f"key{i}", {"data": f"value{i}"})
        
        # Clear cache
        cache.clear()
        
        # All keys should be gone
        for i in range(5):
            assert cache.get(f"key{i}") is None
        
        # Stats should reset
        stats = cache.get_stats()
        assert stats["size"] == 0


class TestMemoryManagement:
    """Test memory management during streaming"""
    
    @pytest.fixture
    def db(self):
        """Create temporary database"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db_api = SQLiteDatabaseAPI(db_path)
        db_api.execute_query("""
            CREATE TABLE memory_test (
                id INTEGER PRIMARY KEY,
                large_data TEXT
            )
        """)
        yield db_api
        
        db_api.close()
        os.unlink(db_path)
    
    def test_memory_bounded_streaming(self, db):
        """Test memory stays bounded during large streaming"""
        # Insert large dataset
        large_text = "x" * 1000  # 1KB per record
        for i in range(1000):
            db.execute_query(
                "INSERT INTO memory_test (large_data) VALUES (?)",
                (large_text,)
            )
        
        config = StreamConfig(batch_size=10, max_buffer=30)
        processor = StreamingProcessor(db, config)
        
        # Stream without accumulating in memory
        processed = 0
        for batch in processor.stream_records("memory_test"):
            processed += len(batch)
            # Process and discard immediately
            batch = None
        
        assert processed == 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
