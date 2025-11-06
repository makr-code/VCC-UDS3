#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration Tests

End-to-end tests for complete UDS3 workflows:
- Document ingestion → processing → retrieval
- Multi-database synchronization
- SAGA with streaming
- Cross-component integration
"""
import pytest
import tempfile
import os
from pathlib import Path

# Integration imports
from database.database_api_sqlite import SQLiteDatabaseAPI
from saga.saga_orchestrator import SAGAOrchestrator, SAGAStep
from streaming.streaming_operations import StreamingProcessor, StreamConfig
from search.query_filters_relational import RelationalFilter
from compliance.dsgvo_core import DSGVOCompliance


class TestDocumentWorkflow:
    """Test complete document workflow"""
    
    @pytest.fixture
    def system(self):
        """Setup complete UDS3 system"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db = SQLiteDatabaseAPI(db_path)
        
        # Create tables
        db.execute_query("""
            CREATE TABLE documents (
                id INTEGER PRIMARY KEY,
                title TEXT,
                content TEXT,
                status TEXT,
                created_date TEXT
            )
        """)
        
        db.execute_query("""
            CREATE TABLE embeddings (
                doc_id INTEGER,
                embedding_vector TEXT,
                FOREIGN KEY (doc_id) REFERENCES documents(id)
            )
        """)
        
        yield db
        
        db.close()
        os.unlink(db_path)
    
    def test_document_ingestion_pipeline(self, system):
        """Test: Upload → Parse → Store → Index"""
        db = system
        
        # Step 1: Ingest document
        doc_title = "Test Document"
        doc_content = "This is a test document for UDS3"
        
        db.execute_query(
            "INSERT INTO documents (title, content, status, created_date) VALUES (?, ?, ?, ?)",
            (doc_title, doc_content, "ingested", "2024-01-01")
        )
        
        doc_id = db.execute_query("SELECT last_insert_rowid()")[0][0]
        
        # Step 2: Process (generate embedding)
        # Mock embedding
        embedding = "[0.1, 0.2, 0.3]"
        db.execute_query(
            "INSERT INTO embeddings (doc_id, embedding_vector) VALUES (?, ?)",
            (doc_id, embedding)
        )
        
        # Step 3: Update status
        db.execute_query(
            "UPDATE documents SET status = ? WHERE id = ?",
            ("indexed", doc_id)
        )
        
        # Verify complete workflow
        result = db.execute_query(
            "SELECT d.title, d.status, e.embedding_vector FROM documents d "
            "JOIN embeddings e ON d.id = e.doc_id WHERE d.id = ?",
            (doc_id,)
        )
        
        assert result[0][0] == doc_title
        assert result[0][1] == "indexed"
        assert result[0][2] == embedding
    
    def test_document_retrieval_pipeline(self, system):
        """Test: Query → Filter → Rank → Return"""
        db = system
        
        # Setup test documents
        docs = [
            ("Finance Report 2024", "Financial analysis", "indexed"),
            ("HR Policy", "Human resources guidelines", "indexed"),
            ("IT Security Guide", "Security best practices", "indexed")
        ]
        
        for title, content, status in docs:
            db.execute_query(
                "INSERT INTO documents (title, content, status, created_date) VALUES (?, ?, ?, ?)",
                (title, content, status, "2024-01-01")
            )
        
        # Query with filter
        filter = RelationalFilter(db, table="documents")
        results = filter.filter(status="indexed")
        
        assert len(results) == 3
    
    def test_document_update_saga(self, system):
        """Test: Document update with SAGA pattern"""
        db = system
        orchestrator = SAGAOrchestrator(database=db)
        
        # Insert initial document
        db.execute_query(
            "INSERT INTO documents (title, content, status, created_date) VALUES (?, ?, ?, ?)",
            ("Original Title", "Original content", "indexed", "2024-01-01")
        )
        doc_id = db.execute_query("SELECT last_insert_rowid()")[0][0]
        
        # SAGA: Update document with rollback capability
        steps = [
            SAGAStep(
                name="update_document",
                action=lambda: db.execute_query(
                    "UPDATE documents SET title = ?, content = ? WHERE id = ?",
                    ("Updated Title", "Updated content", doc_id)
                ),
                compensation=lambda: db.execute_query(
                    "UPDATE documents SET title = ?, content = ? WHERE id = ?",
                    ("Original Title", "Original content", doc_id)
                )
            ),
            SAGAStep(
                name="update_embedding",
                action=lambda: db.execute_query(
                    "INSERT INTO embeddings (doc_id, embedding_vector) VALUES (?, ?)",
                    (doc_id, "[0.4, 0.5, 0.6]")
                ),
                compensation=lambda: db.execute_query(
                    "DELETE FROM embeddings WHERE doc_id = ?",
                    (doc_id,)
                )
            )
        ]
        
        result = orchestrator.execute_saga(steps)
        assert result.success is True
        
        # Verify update
        doc = db.execute_query("SELECT title FROM documents WHERE id = ?", (doc_id,))
        assert doc[0][0] == "Updated Title"


class TestMultiDatabaseSync:
    """Test synchronization across multiple databases"""
    
    @pytest.fixture
    def dbs(self):
        """Create multiple databases"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f1:
            db1_path = f1.name
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f2:
            db2_path = f2.name
        
        db1 = SQLiteDatabaseAPI(db1_path)
        db2 = SQLiteDatabaseAPI(db2_path)
        
        # Create same schema in both
        for db in [db1, db2]:
            db.execute_query("""
                CREATE TABLE sync_test (
                    id INTEGER PRIMARY KEY,
                    data TEXT,
                    sync_timestamp TEXT
                )
            """)
        
        yield db1, db2
        
        db1.close()
        db2.close()
        os.unlink(db1_path)
        os.unlink(db2_path)
    
    def test_cross_database_sync(self, dbs):
        """Test syncing data between databases"""
        db1, db2 = dbs
        
        # Insert into db1
        db1.execute_query(
            "INSERT INTO sync_test (data, sync_timestamp) VALUES (?, ?)",
            ("test data", "2024-01-01T12:00:00")
        )
        
        # Sync to db2
        data = db1.execute_query("SELECT id, data, sync_timestamp FROM sync_test")
        for record in data:
            db2.execute_query(
                "INSERT INTO sync_test (id, data, sync_timestamp) VALUES (?, ?, ?)",
                record
            )
        
        # Verify sync
        db2_data = db2.execute_query("SELECT data FROM sync_test")
        assert len(db2_data) == 1
        assert db2_data[0][0] == "test data"


class TestStreamingSAGAIntegration:
    """Test SAGA with streaming operations"""
    
    @pytest.fixture
    def system(self):
        """Setup system"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db = SQLiteDatabaseAPI(db_path)
        
        db.execute_query("""
            CREATE TABLE stream_saga_test (
                id INTEGER PRIMARY KEY,
                data TEXT,
                processed BOOLEAN DEFAULT 0
            )
        """)
        
        yield db
        
        db.close()
        os.unlink(db_path)
    
    def test_streaming_with_saga_per_batch(self, system):
        """Test: Stream data with SAGA for each batch"""
        db = system
        
        # Insert test data
        for i in range(100):
            db.execute_query(
                "INSERT INTO stream_saga_test (data) VALUES (?)",
                (f"record_{i}",)
            )
        
        # Stream and process with SAGA
        config = StreamConfig(batch_size=10)
        processor = StreamingProcessor(db, config)
        orchestrator = SAGAOrchestrator(database=db)
        
        batches_processed = 0
        
        for batch in processor.stream_records("stream_saga_test"):
            # Create SAGA for batch processing
            steps = []
            for record in batch:
                record_id = record[0]
                step = SAGAStep(
                    name=f"process_record_{record_id}",
                    action=lambda rid=record_id: db.execute_query(
                        "UPDATE stream_saga_test SET processed = 1 WHERE id = ?",
                        (rid,)
                    ),
                    compensation=lambda rid=record_id: db.execute_query(
                        "UPDATE stream_saga_test SET processed = 0 WHERE id = ?",
                        (rid,)
                    )
                )
                steps.append(step)
            
            # Execute SAGA for batch
            result = orchestrator.execute_saga(steps)
            if result.success:
                batches_processed += 1
        
        # Verify all processed
        count = db.execute_query(
            "SELECT COUNT(*) FROM stream_saga_test WHERE processed = 1"
        )
        assert count[0][0] == 100
        assert batches_processed == 10  # 100 records / 10 per batch


class TestComplianceIntegration:
    """Test compliance integration with core operations"""
    
    @pytest.fixture
    def system(self):
        """Setup system"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db = SQLiteDatabaseAPI(db_path)
        
        db.execute_query("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT,
                email TEXT,
                created_date TEXT
            )
        """)
        
        yield db
        
        db.close()
        os.unlink(db_path)
    
    def test_gdpr_compliant_workflow(self, system):
        """Test: GDPR-compliant data handling"""
        db = system
        compliance = DSGVOCompliance(db)
        
        # User registration
        db.execute_query(
            "INSERT INTO users (name, email, created_date) VALUES (?, ?, ?)",
            ("Test User", "test@example.com", "2024-01-01")
        )
        user_id = db.execute_query("SELECT last_insert_rowid()")[0][0]
        
        # User requests data export (GDPR Art. 20)
        user_data = compliance.export_user_data(table="users", user_id=user_id)
        assert user_data is not None
        
        # User requests deletion (GDPR Art. 17)
        compliance.delete_user_data(table="users", user_id=user_id)
        
        # Verify deletion
        result = db.execute_query("SELECT COUNT(*) FROM users WHERE id = ?", (user_id,))
        assert result[0][0] == 0


class TestErrorRecovery:
    """Test system-wide error recovery"""
    
    @pytest.fixture
    def system(self):
        """Setup system"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db = SQLiteDatabaseAPI(db_path)
        
        db.execute_query("""
            CREATE TABLE recovery_test (
                id INTEGER PRIMARY KEY,
                data TEXT
            )
        """)
        
        yield db
        
        db.close()
        os.unlink(db_path)
    
    def test_saga_failure_recovery(self, system):
        """Test: SAGA compensates on failure"""
        db = system
        orchestrator = SAGAOrchestrator(database=db)
        
        steps = [
            SAGAStep(
                name="insert1",
                action=lambda: db.execute_query(
                    "INSERT INTO recovery_test (data) VALUES (?)", ("step1",)
                ),
                compensation=lambda: db.execute_query(
                    "DELETE FROM recovery_test WHERE data = ?", ("step1",)
                )
            ),
            SAGAStep(
                name="failing_step",
                action=lambda: self._raise_error(),
                compensation=lambda: None
            )
        ]
        
        # Execute (should fail and compensate)
        result = orchestrator.execute_saga(steps)
        assert result.success is False
        
        # Verify compensation (step1 should be rolled back)
        count = db.execute_query("SELECT COUNT(*) FROM recovery_test")
        assert count[0][0] == 0
    
    def _raise_error(self):
        """Helper to simulate failure"""
        raise Exception("Simulated failure")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
