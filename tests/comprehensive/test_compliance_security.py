#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compliance & Security Tests

Tests:
- DSGVO compliance (anonymization, data protection)
- Security quality metrics
- Audit logging
- Data retention policies
- Access control
"""
import pytest
import tempfile
import os
from datetime import datetime, timedelta

# Compliance imports
from compliance.dsgvo_core import DSGVOCompliance, AnonymizationEngine
from compliance.security_quality import SecurityQualityChecker, QualityMetrics
from compliance.audit_logger import AuditLogger
from database.database_api_sqlite import SQLiteDatabaseAPI


class TestDSGVOCompliance:
    """Test DSGVO compliance features"""
    
    @pytest.fixture
    def db(self):
        """Create temporary database"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db_api = SQLiteDatabaseAPI(db_path)
        db_api.execute_query("""
            CREATE TABLE personal_data (
                id INTEGER PRIMARY KEY,
                name TEXT,
                email TEXT,
                phone TEXT,
                address TEXT,
                created_date TEXT
            )
        """)
        
        # Insert test data
        db_api.execute_query(
            "INSERT INTO personal_data (name, email, phone, address, created_date) VALUES (?, ?, ?, ?, ?)",
            ("Max Mustermann", "max@example.com", "+49 123 456789", "Musterstr. 1, 12345 Stadt", "2024-01-01")
        )
        
        yield db_api
        
        db_api.close()
        os.unlink(db_path)
    
    def test_data_anonymization(self, db):
        """Test personal data anonymization"""
        compliance = DSGVOCompliance(db)
        anonymizer = AnonymizationEngine()
        
        # Get original data
        original = db.execute_query("SELECT name, email, phone FROM personal_data WHERE id = 1")
        assert original[0][0] == "Max Mustermann"
        
        # Anonymize
        anonymized_name = anonymizer.anonymize_name(original[0][0])
        anonymized_email = anonymizer.anonymize_email(original[0][1])
        anonymized_phone = anonymizer.anonymize_phone(original[0][2])
        
        # Update with anonymized data
        db.execute_query(
            "UPDATE personal_data SET name = ?, email = ?, phone = ? WHERE id = 1",
            (anonymized_name, anonymized_email, anonymized_phone)
        )
        
        # Verify anonymization
        result = db.execute_query("SELECT name, email, phone FROM personal_data WHERE id = 1")
        assert result[0][0] != "Max Mustermann"
        assert "@" not in result[0][1] or result[0][1] != "max@example.com"
    
    def test_right_to_be_forgotten(self, db):
        """Test DSGVO right to be forgotten (Art. 17)"""
        compliance = DSGVOCompliance(db)
        
        # User requests deletion
        user_id = 1
        compliance.delete_user_data(table="personal_data", user_id=user_id)
        
        # Verify deletion
        result = db.execute_query("SELECT COUNT(*) FROM personal_data WHERE id = ?", (user_id,))
        assert result[0][0] == 0
    
    def test_data_export(self, db):
        """Test DSGVO data portability (Art. 20)"""
        compliance = DSGVOCompliance(db)
        
        # User requests data export
        user_data = compliance.export_user_data(table="personal_data", user_id=1)
        
        assert user_data is not None
        assert "name" in user_data
        assert "email" in user_data
    
    def test_consent_management(self, db):
        """Test consent tracking"""
        db.execute_query("""
            CREATE TABLE consents (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                purpose TEXT,
                granted BOOLEAN,
                timestamp TEXT
            )
        """)
        
        compliance = DSGVOCompliance(db)
        
        # Record consent
        compliance.record_consent(
            user_id=1,
            purpose="marketing",
            granted=True
        )
        
        # Verify consent
        result = db.execute_query(
            "SELECT granted FROM consents WHERE user_id = ? AND purpose = ?",
            (1, "marketing")
        )
        assert result[0][0] == 1  # True
    
    def test_data_retention_policy(self, db):
        """Test automated data retention enforcement"""
        compliance = DSGVOCompliance(db)
        
        # Insert old data (90 days ago)
        old_date = (datetime.now() - timedelta(days=90)).isoformat()
        db.execute_query(
            "INSERT INTO personal_data (name, email, created_date) VALUES (?, ?, ?)",
            ("Old User", "old@example.com", old_date)
        )
        
        # Apply retention policy (delete data older than 60 days)
        deleted_count = compliance.apply_retention_policy(
            table="personal_data",
            date_column="created_date",
            retention_days=60
        )
        
        assert deleted_count >= 1


class TestAnonymizationEngine:
    """Test anonymization techniques"""
    
    def test_name_anonymization(self):
        """Test name anonymization"""
        engine = AnonymizationEngine()
        
        original = "Max Mustermann"
        anonymized = engine.anonymize_name(original)
        
        # Should be different
        assert anonymized != original
        # Should maintain format (e.g., "User_XXXXX")
        assert "User" in anonymized or "*" in anonymized
    
    def test_email_anonymization(self):
        """Test email anonymization"""
        engine = AnonymizationEngine()
        
        original = "max.mustermann@example.com"
        anonymized = engine.anonymize_email(original)
        
        # Should preserve domain but anonymize user
        assert anonymized != original
        assert "@" in anonymized
    
    def test_phone_anonymization(self):
        """Test phone number anonymization"""
        engine = AnonymizationEngine()
        
        original = "+49 123 456789"
        anonymized = engine.anonymize_phone(original)
        
        # Should mask middle digits
        assert anonymized != original
        assert "*" in anonymized or "X" in anonymized
    
    def test_address_anonymization(self):
        """Test address anonymization"""
        engine = AnonymizationEngine()
        
        original = "Musterstraße 123, 12345 Berlin"
        anonymized = engine.anonymize_address(original)
        
        # Should preserve city but anonymize street/number
        assert anonymized != original


class TestSecurityQualityChecker:
    """Test security and quality metrics"""
    
    @pytest.fixture
    def db(self):
        """Create temporary database"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db_api = SQLiteDatabaseAPI(db_path)
        db_api.execute_query("""
            CREATE TABLE quality_test (
                id INTEGER PRIMARY KEY,
                data TEXT,
                quality_score REAL
            )
        """)
        
        yield db_api
        
        db_api.close()
        os.unlink(db_path)
    
    def test_data_quality_check(self, db):
        """Test data quality assessment"""
        checker = SecurityQualityChecker(db)
        
        # Insert test data
        db.execute_query("INSERT INTO quality_test (data) VALUES (?)", ("valid data",))
        db.execute_query("INSERT INTO quality_test (data) VALUES (?)", (None,))
        db.execute_query("INSERT INTO quality_test (data) VALUES (?)", ("",))
        
        # Check quality
        metrics = checker.check_data_quality(table="quality_test", column="data")
        
        assert "completeness" in metrics
        assert metrics["completeness"] < 1.0  # Has null/empty values
    
    def test_security_scan(self, db):
        """Test security vulnerability scan"""
        checker = SecurityQualityChecker(db)
        
        # Check for common security issues
        issues = checker.scan_security_issues(table="quality_test")
        
        # Should return list of issues (if any)
        assert isinstance(issues, list)
    
    def test_quality_metrics(self):
        """Test quality metrics calculation"""
        metrics = QualityMetrics()
        
        # Test data
        data = [1, 2, 3, None, 5, 6, None, 8]
        
        completeness = metrics.calculate_completeness(data)
        assert 0 <= completeness <= 1
        assert completeness < 1.0  # Has None values
        
        uniqueness = metrics.calculate_uniqueness(data)
        assert 0 <= uniqueness <= 1


class TestAuditLogger:
    """Test audit logging"""
    
    @pytest.fixture
    def db(self):
        """Create temporary database"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db_api = SQLiteDatabaseAPI(db_path)
        
        yield db_api
        
        db_api.close()
        os.unlink(db_path)
    
    def test_log_access(self, db):
        """Test access logging"""
        logger = AuditLogger(db)
        
        # Log data access
        logger.log_access(
            user_id="user123",
            resource="personal_data",
            action="READ",
            timestamp=datetime.now().isoformat()
        )
        
        # Verify log entry
        logs = logger.get_access_logs(user_id="user123")
        assert len(logs) >= 1
        assert logs[0]["action"] == "READ"
    
    def test_log_modification(self, db):
        """Test modification logging"""
        logger = AuditLogger(db)
        
        # Log data modification
        logger.log_modification(
            user_id="admin",
            resource="user_table",
            action="UPDATE",
            old_value="old",
            new_value="new"
        )
        
        # Verify log
        logs = logger.get_modification_logs(resource="user_table")
        assert len(logs) >= 1
    
    def test_audit_trail(self, db):
        """Test complete audit trail"""
        logger = AuditLogger(db)
        
        # Create audit trail
        logger.log_access("user1", "resource1", "READ")
        logger.log_access("user1", "resource1", "UPDATE")
        logger.log_access("user1", "resource1", "DELETE")
        
        # Get full trail
        trail = logger.get_audit_trail(user_id="user1", resource="resource1")
        
        assert len(trail) == 3
        # Should be chronologically ordered
        assert trail[0]["action"] == "READ"
        assert trail[-1]["action"] == "DELETE"


class TestAccessControl:
    """Test access control mechanisms"""
    
    def test_role_based_access(self):
        """Test RBAC (Role-Based Access Control)"""
        from compliance.access_control import AccessControl
        
        ac = AccessControl()
        
        # Define roles
        ac.define_role("admin", permissions=["READ", "WRITE", "DELETE"])
        ac.define_role("user", permissions=["READ"])
        
        # Assign role
        ac.assign_role("user123", "user")
        
        # Check permissions
        assert ac.has_permission("user123", "READ") is True
        assert ac.has_permission("user123", "DELETE") is False
    
    def test_permission_inheritance(self):
        """Test permission inheritance"""
        from compliance.access_control import AccessControl
        
        ac = AccessControl()
        
        # Define role hierarchy
        ac.define_role("admin", permissions=["READ", "WRITE", "DELETE"])
        ac.define_role("manager", parent="admin", permissions=["APPROVE"])
        
        ac.assign_role("manager1", "manager")
        
        # Should inherit admin permissions
        assert ac.has_permission("manager1", "READ") is True
        assert ac.has_permission("manager1", "APPROVE") is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
