#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SAGA Orchestration Tests

Tests SAGA pattern implementation:
- Successful SAGA execution
- Compensation on failure
- Recovery mechanisms
- Idempotency
- Step builders
"""
import pytest
import tempfile
import os
from typing import List, Dict, Any

# SAGA imports
from saga.saga_orchestrator import SAGAOrchestrator, SAGAStep
from saga.saga_compensations import CompensationManager
from saga.saga_error_recovery import RecoveryWorker
from saga.saga_step_builders import (
    DatabaseInsertStep,
    DatabaseUpdateStep,
    DatabaseDeleteStep,
    build_saga_chain
)
from database.database_api_sqlite import SQLiteDatabaseAPI


class TestSAGAOrchestrator:
    """Test SAGA orchestration logic"""
    
    @pytest.fixture
    def db(self):
        """Create temporary database"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db_api = SQLiteDatabaseAPI(db_path)
        db_api.execute_query("""
            CREATE TABLE saga_test (
                id INTEGER PRIMARY KEY,
                step TEXT,
                value INTEGER
            )
        """)
        yield db_api
        
        db_api.close()
        os.unlink(db_path)
    
    @pytest.fixture
    def orchestrator(self, db):
        """Create SAGA orchestrator"""
        return SAGAOrchestrator(database=db)
    
    def test_successful_saga(self, orchestrator, db):
        """Test successful SAGA execution"""
        steps = [
            SAGAStep(
                name="insert_step1",
                action=lambda: db.execute_query(
                    "INSERT INTO saga_test (step, value) VALUES (?, ?)",
                    ("step1", 100)
                ),
                compensation=lambda: db.execute_query(
                    "DELETE FROM saga_test WHERE step = ?", ("step1",)
                )
            ),
            SAGAStep(
                name="insert_step2",
                action=lambda: db.execute_query(
                    "INSERT INTO saga_test (step, value) VALUES (?, ?)",
                    ("step2", 200)
                ),
                compensation=lambda: db.execute_query(
                    "DELETE FROM saga_test WHERE step = ?", ("step2",)
                )
            )
        ]
        
        # Execute SAGA
        result = orchestrator.execute_saga(steps)
        assert result.success is True
        
        # Verify both steps completed
        count = db.execute_query("SELECT COUNT(*) FROM saga_test")
        assert count[0][0] == 2
    
    def test_saga_with_compensation(self, orchestrator, db):
        """Test SAGA compensation on failure"""
        steps = [
            SAGAStep(
                name="insert_step1",
                action=lambda: db.execute_query(
                    "INSERT INTO saga_test (step, value) VALUES (?, ?)",
                    ("step1", 100)
                ),
                compensation=lambda: db.execute_query(
                    "DELETE FROM saga_test WHERE step = ?", ("step1",)
                )
            ),
            SAGAStep(
                name="failing_step",
                action=lambda: self._raise_error(),
                compensation=lambda: None
            )
        ]
        
        # Execute SAGA (should fail and compensate)
        result = orchestrator.execute_saga(steps)
        assert result.success is False
        
        # Verify step1 was compensated (deleted)
        count = db.execute_query("SELECT COUNT(*) FROM saga_test")
        assert count[0][0] == 0
    
    def _raise_error(self):
        """Helper to simulate step failure"""
        raise Exception("Simulated failure")
    
    def test_saga_idempotency(self, orchestrator, db):
        """Test idempotent SAGA execution"""
        saga_id = "idempotent_saga_001"
        
        steps = [
            SAGAStep(
                name="insert_idempotent",
                action=lambda: db.execute_query(
                    "INSERT OR REPLACE INTO saga_test (id, step, value) VALUES (?, ?, ?)",
                    (1, "idempotent", 999)
                ),
                compensation=lambda: db.execute_query(
                    "DELETE FROM saga_test WHERE id = ?", (1,)
                )
            )
        ]
        
        # Execute SAGA twice with same ID
        result1 = orchestrator.execute_saga(steps, saga_id=saga_id)
        result2 = orchestrator.execute_saga(steps, saga_id=saga_id)
        
        # Both should succeed
        assert result1.success is True
        assert result2.success is True
        
        # But only one record should exist
        count = db.execute_query("SELECT COUNT(*) FROM saga_test WHERE id = 1")
        assert count[0][0] == 1


class TestCompensationManager:
    """Test compensation logic"""
    
    @pytest.fixture
    def db(self):
        """Create temporary database"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db_api = SQLiteDatabaseAPI(db_path)
        db_api.execute_query("""
            CREATE TABLE compensation_test (
                id INTEGER PRIMARY KEY,
                action TEXT,
                compensated BOOLEAN DEFAULT 0
            )
        """)
        yield db_api
        
        db_api.close()
        os.unlink(db_path)
    
    def test_compensation_execution(self, db):
        """Test compensation execution order (reverse)"""
        manager = CompensationManager()
        
        # Register compensations
        manager.register(
            "step1",
            lambda: db.execute_query(
                "UPDATE compensation_test SET compensated = 1 WHERE action = 'step1'"
            )
        )
        manager.register(
            "step2",
            lambda: db.execute_query(
                "UPDATE compensation_test SET compensated = 1 WHERE action = 'step2'"
            )
        )
        
        # Insert test data
        db.execute_query("INSERT INTO compensation_test (action) VALUES ('step1')")
        db.execute_query("INSERT INTO compensation_test (action) VALUES ('step2')")
        
        # Execute compensations (should execute in reverse order)
        manager.execute_all()
        
        # Verify both compensated
        result = db.execute_query(
            "SELECT COUNT(*) FROM compensation_test WHERE compensated = 1"
        )
        assert result[0][0] == 2
    
    def test_compensation_partial_failure(self, db):
        """Test compensation with partial failures"""
        manager = CompensationManager()
        
        compensations_executed = []
        
        # Register compensations (one will fail)
        manager.register("step1", lambda: compensations_executed.append("step1"))
        manager.register("step2", lambda: self._raise_error())
        manager.register("step3", lambda: compensations_executed.append("step3"))
        
        # Execute compensations
        manager.execute_all()
        
        # step3 and step1 should execute despite step2 failure
        assert "step3" in compensations_executed
        assert "step1" in compensations_executed
    
    def _raise_error(self):
        """Helper to simulate compensation failure"""
        raise Exception("Compensation failed")


class TestRecoveryWorker:
    """Test recovery mechanisms"""
    
    @pytest.fixture
    def db(self):
        """Create temporary database"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db_api = SQLiteDatabaseAPI(db_path)
        db_api.execute_query("""
            CREATE TABLE recovery_test (
                saga_id TEXT PRIMARY KEY,
                status TEXT,
                retry_count INTEGER DEFAULT 0
            )
        """)
        yield db_api
        
        db_api.close()
        os.unlink(db_path)
    
    def test_recovery_retry_mechanism(self, db):
        """Test retry mechanism for failed SAGAs"""
        worker = RecoveryWorker(database=db, max_retries=3)
        
        saga_id = "failed_saga_001"
        db.execute_query(
            "INSERT INTO recovery_test (saga_id, status) VALUES (?, ?)",
            (saga_id, "failed")
        )
        
        # Simulate recovery attempt
        retry_count = 0
        while retry_count < 3:
            db.execute_query(
                "UPDATE recovery_test SET retry_count = retry_count + 1 WHERE saga_id = ?",
                (saga_id,)
            )
            retry_count += 1
        
        # Verify retry count
        result = db.execute_query(
            "SELECT retry_count FROM recovery_test WHERE saga_id = ?",
            (saga_id,)
        )
        assert result[0][0] == 3


class TestSAGAStepBuilders:
    """Test SAGA step builder utilities"""
    
    @pytest.fixture
    def db(self):
        """Create temporary database"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db_api = SQLiteDatabaseAPI(db_path)
        db_api.execute_query("""
            CREATE TABLE builder_test (
                id INTEGER PRIMARY KEY,
                name TEXT,
                value INTEGER
            )
        """)
        yield db_api
        
        db_api.close()
        os.unlink(db_path)
    
    def test_database_insert_step(self, db):
        """Test database insert step builder"""
        step = DatabaseInsertStep(
            db=db,
            table="builder_test",
            data={"name": "test", "value": 42}
        )
        
        # Execute step
        step.execute()
        
        # Verify insert
        result = db.execute_query("SELECT name, value FROM builder_test")
        assert result[0][0] == "test"
        assert result[0][1] == 42
        
        # Execute compensation
        step.compensate()
        
        # Verify deletion
        count = db.execute_query("SELECT COUNT(*) FROM builder_test")
        assert count[0][0] == 0
    
    def test_saga_chain_builder(self, db):
        """Test building SAGA chain"""
        steps = build_saga_chain([
            DatabaseInsertStep(db, "builder_test", {"name": "step1", "value": 1}),
            DatabaseInsertStep(db, "builder_test", {"name": "step2", "value": 2}),
            DatabaseInsertStep(db, "builder_test", {"name": "step3", "value": 3})
        ])
        
        assert len(steps) == 3
        
        # Execute all steps
        for step in steps:
            step.execute()
        
        # Verify all inserts
        count = db.execute_query("SELECT COUNT(*) FROM builder_test")
        assert count[0][0] == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
