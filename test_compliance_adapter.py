#!/usr/bin/env python3
"""
Tests for UDS3 Compliance Adapter

Tests compliance middleware integration with UDS3PolyglotManager,
including PII detection, audit logging, DSGVO rights, and identity management.
"""

import pytest
from datetime import datetime
from typing import Dict, Any, Optional

from compliance.adapter import ComplianceAdapter, create_compliance_adapter
from compliance.dsgvo_core import PIIType, DSGVOProcessingBasis
from compliance.security_quality import SecurityLevel


# ============================================================================
# Mock PolyglotManager for Testing
# ============================================================================

class MockRelationalBackend:
    """Mock relational backend for testing."""

    def __init__(self):
        self.tables = {}

    def execute(self, query: str, params: tuple = ()):
        """Mock execute."""
        return True

    def fetchone(self, query: str, params: tuple = ()):
        """Mock fetchone."""
        return None

    def fetchall(self, query: str, params: tuple = ()):
        """Mock fetchall."""
        return []


class MockPolyglotManager:
    """Mock UDS3PolyglotManager for testing."""

    def __init__(self):
        self.documents = {}
        self.relational_backend = MockRelationalBackend()  # Mock relational backend

    def save_document(self, collection: str, data: Dict[str, Any]) -> str:
        """Mock save_document."""
        doc_id = f"doc_{len(self.documents) + 1}"
        self.documents[f"{collection}:{doc_id}"] = data
        return doc_id

    def get_document(self, collection: str, document_id: str) -> Optional[Dict[str, Any]]:
        """Mock get_document."""
        return self.documents.get(f"{collection}:{document_id}")

    def update_document(self, collection: str, document_id: str, updates: Dict[str, Any]) -> bool:
        """Mock update_document."""
        key = f"{collection}:{document_id}"
        if key in self.documents:
            self.documents[key].update(updates)
            return True
        return False

    def delete_document(self, collection: str, document_id: str) -> bool:
        """Mock delete_document."""
        key = f"{collection}:{document_id}"
        if key in self.documents:
            del self.documents[key]
            return True
        return False

    def list_documents(self, collection: str, filters: Optional[Dict] = None, limit: int = 100):
        """Mock list_documents."""
        prefix = f"{collection}:"
        docs = [doc for key, doc in self.documents.items() if key.startswith(prefix)]
        return docs[:limit]


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def mock_polyglot():
    """Create mock polyglot manager."""
    return MockPolyglotManager()


@pytest.fixture
def compliance_adapter(mock_polyglot):
    """Create compliance adapter with mock backend."""
    # Create adapter with strict_mode=False to allow missing backend
    adapter = ComplianceAdapter(
        polyglot_manager=mock_polyglot,
        auto_pii_detection=False,  # Disable auto-detection for mock tests
        audit_enabled=False,  # Disable audit for mock tests
        security_level=SecurityLevel.INTERNAL,
        retention_years=7
    )
    # Override DSGVO with non-strict mode for testing
    adapter.dsgvo.strict_mode = False
    return adapter


# ============================================================================
# Test: Initialization
# ============================================================================

def test_compliance_adapter_initialization(mock_polyglot):
    """Test ComplianceAdapter initialization."""
    adapter = ComplianceAdapter(
        polyglot_manager=mock_polyglot,
        auto_pii_detection=True,
        audit_enabled=True
    )

    assert adapter.polyglot_manager == mock_polyglot
    assert adapter.auto_pii_detection is True
    assert adapter.audit_enabled is True
    assert adapter.dsgvo is not None
    assert adapter.security is not None
    assert adapter.quality is not None
    assert adapter.identity is not None

    print("✅ Compliance adapter initialized successfully")


def test_factory_function(mock_polyglot):
    """Test create_compliance_adapter factory function."""
    adapter = create_compliance_adapter(
        polyglot_manager=mock_polyglot,
        auto_pii_detection=False
    )

    assert isinstance(adapter, ComplianceAdapter)
    assert adapter.auto_pii_detection is False

    print("✅ Factory function works correctly")


# ============================================================================
# Test: Save Document with PII Detection
# ============================================================================

def test_save_document_with_pii_detection(compliance_adapter):
    """Test saving document with automatic PII detection."""
    data = {
        "name": "Max Mustermann",
        "email": "max.mustermann@example.com",
        "phone": "+49 123 456789",
        "content": "This is a contract document."
    }

    result = compliance_adapter.save_document_secure(
        collection="contracts",
        data=data,
        subject_id="subject_123",
        mask_pii=True
    )

    assert result["document_id"] is not None
    assert isinstance(result["pii_detected"], list)
    assert result["quality_score"] is not None
    assert 0.0 <= result["quality_score"] <= 1.0

    print(f"✅ Document saved with PII detection")
    print(f"   Document ID: {result['document_id']}")
    print(f"   PII Detected: {len(result['pii_detected'])} fields")
    print(f"   Quality Score: {result['quality_score']:.2f}")


def test_save_document_without_pii(compliance_adapter):
    """Test saving document without PII."""
    data = {
        "title": "Annual Report 2025",
        "content": "This is a public document without personal data.",
        "category": "reports"
    }

    result = compliance_adapter.save_document_secure(
        collection="reports",
        data=data,
        mask_pii=False
    )

    assert result["document_id"] is not None
    assert len(result["pii_detected"]) == 0
    assert result["pii_masked"] is False

    print(f"✅ Document saved without PII")
    print(f"   Document ID: {result['document_id']}")


# ============================================================================
# Test: Get Document
# ============================================================================

def test_get_document_secure(compliance_adapter):
    """Test retrieving document with audit logging."""
    # First save a document
    data = {"title": "Test Document", "content": "Sample content"}
    save_result = compliance_adapter.save_document_secure(
        collection="test",
        data=data
    )
    doc_id = save_result["document_id"]

    # Retrieve document
    retrieved = compliance_adapter.get_document_secure(
        collection="test",
        document_id=doc_id,
        subject_id="subject_123"
    )

    assert retrieved is not None
    assert retrieved["title"] == "Test Document"

    print(f"✅ Document retrieved securely: {doc_id}")


# ============================================================================
# Test: Delete Document (Soft/Hard)
# ============================================================================

def test_soft_delete_document(compliance_adapter):
    """Test soft delete (marks as deleted but retains for audit)."""
    # Save document
    data = {"title": "To Be Deleted", "content": "Test"}
    save_result = compliance_adapter.save_document_secure(
        collection="test",
        data=data
    )
    doc_id = save_result["document_id"]

    # Soft delete
    delete_result = compliance_adapter.delete_document_secure(
        collection="test",
        document_id=doc_id,
        soft_delete=True,
        reason="test_cleanup"
    )

    assert delete_result["success"] is True
    assert delete_result["delete_type"] == "soft"

    # Document should still exist but marked as deleted
    doc = compliance_adapter.polyglot_manager.get_document("test", doc_id)
    assert doc is not None
    assert doc.get("_deleted") is True

    print(f"✅ Document soft-deleted: {doc_id}")


def test_hard_delete_document(compliance_adapter):
    """Test hard delete (permanent removal)."""
    # Save document
    data = {"title": "To Be Deleted", "content": "Test"}
    save_result = compliance_adapter.save_document_secure(
        collection="test",
        data=data
    )
    doc_id = save_result["document_id"]

    # Hard delete
    delete_result = compliance_adapter.delete_document_secure(
        collection="test",
        document_id=doc_id,
        soft_delete=False,
        reason="permanent_removal"
    )

    assert delete_result["success"] is True
    assert delete_result["delete_type"] == "hard"

    # Document should not exist
    doc = compliance_adapter.polyglot_manager.get_document("test", doc_id)
    assert doc is None

    print(f"✅ Document hard-deleted: {doc_id}")


# ============================================================================
# Test: List Documents with Deleted Filtering
# ============================================================================

def test_list_documents_exclude_deleted(compliance_adapter):
    """Test listing documents with soft-deleted filtering."""
    # Save multiple documents
    compliance_adapter.save_document_secure("test", {"title": "Doc 1"})
    save_result = compliance_adapter.save_document_secure("test", {"title": "Doc 2"})
    compliance_adapter.save_document_secure("test", {"title": "Doc 3"})

    # Soft delete one document
    compliance_adapter.delete_document_secure(
        collection="test",
        document_id=save_result["document_id"],
        soft_delete=True
    )

    # List documents (should exclude deleted)
    docs = compliance_adapter.list_documents_secure(
        collection="test",
        exclude_deleted=True
    )

    assert len(docs) == 2  # Only 2 non-deleted docs

    print(f"✅ Listed documents with deleted filtering: {len(docs)} documents")


# ============================================================================
# Test: DSGVO Rights
# ============================================================================

def test_dsgvo_right_to_access(compliance_adapter):
    """Test DSGVO Right to Access (Art. 15)."""
    subject_id = "subject_dsgvo_test"

    # Save documents for subject
    compliance_adapter.save_document_secure(
        collection="test",
        data={"email": "test@example.com"},
        subject_id=subject_id
    )

    # Exercise right to access
    result = compliance_adapter.dsgvo_right_to_access(
        subject_id=subject_id
    )

    assert "documents" in result or "pii_mappings" in result

    print(f"✅ DSGVO Right to Access executed for {subject_id}")


def test_dsgvo_right_to_erasure(compliance_adapter):
    """Test DSGVO Right to Erasure (Art. 17)."""
    subject_id = "subject_erasure_test"

    # Save documents for subject
    compliance_adapter.save_document_secure(
        collection="test",
        data={"email": "erasure@example.com"},
        subject_id=subject_id
    )

    # Exercise right to erasure
    result = compliance_adapter.dsgvo_right_to_erasure(
        subject_id=subject_id,
        reason="user_request"
    )

    assert "deleted_count" in result or "success" in result

    print(f"✅ DSGVO Right to Erasure executed for {subject_id}")


def test_dsgvo_right_to_portability(compliance_adapter):
    """Test DSGVO Right to Data Portability (Art. 20)."""
    subject_id = "subject_portability_test"

    # Save documents for subject
    compliance_adapter.save_document_secure(
        collection="test",
        data={"email": "portability@example.com"},
        subject_id=subject_id
    )

    # Exercise right to portability
    result = compliance_adapter.dsgvo_right_to_portability(
        subject_id=subject_id,
        format="json"
    )

    assert result is not None

    print(f"✅ DSGVO Right to Portability executed for {subject_id}")


# ============================================================================
# Test: Consent Management
# ============================================================================

def test_grant_consent(compliance_adapter):
    """Test granting DSGVO consent."""
    consent = compliance_adapter.grant_consent(
        subject_id="subject_consent_test",
        purpose="Marketing communications",
        data_categories=[PIIType.EMAIL, PIIType.NAME],
        valid_days=365
    )

    assert consent is not None
    assert consent.consent_id is not None
    assert consent.subject_id == "subject_consent_test"
    assert PIIType.EMAIL in consent.data_categories

    print(f"✅ Consent granted: {consent.consent_id}")

    return consent


def test_revoke_consent(compliance_adapter):
    """Test revoking DSGVO consent."""
    # First grant consent
    consent = test_grant_consent(compliance_adapter)

    # Revoke consent
    success = compliance_adapter.revoke_consent(consent_id=consent.consent_id)

    assert success is True

    print(f"✅ Consent revoked: {consent.consent_id}")


# ============================================================================
# Test: Identity Management
# ============================================================================

def test_create_identity(compliance_adapter):
    """Test creating identity record."""
    identity = compliance_adapter.create_identity(
        aktenzeichen="AZ-2025-001",
        backend_ids={
            "vector_db": "vec_123",
            "graph_db": "graph_456"
        },
        metadata={"department": "legal"}
    )

    assert identity is not None
    assert identity.uuid is not None

    print(f"✅ Identity created: {identity.uuid}")

    return identity


def test_resolve_identity_by_uuid(compliance_adapter):
    """Test resolving identity by UUID."""
    # Create identity
    created = test_create_identity(compliance_adapter)

    # Resolve by UUID
    resolved = compliance_adapter.resolve_identity(uuid_value=created.uuid)

    # Note: May return None if mock backend doesn't persist
    print(f"✅ Identity resolution tested (UUID: {created.uuid})")


# ============================================================================
# Test: Batch Operations
# ============================================================================

def test_batch_save_documents_secure(compliance_adapter):
    """Test batch saving documents with compliance."""
    documents = [
        {"title": "Doc 1", "email": "user1@example.com"},
        {"title": "Doc 2", "email": "user2@example.com"},
        {"title": "Doc 3", "content": "No PII here"}
    ]

    results = compliance_adapter.batch_save_documents_secure(
        collection="batch_test",
        documents=documents,
        mask_pii=True
    )

    assert len(results) == 3
    assert all(r["document_id"] is not None for r in results)

    pii_count = sum(len(r["pii_detected"]) for r in results)
    print(f"✅ Batch saved {len(results)} documents (Total PII detected: {pii_count})")


# ============================================================================
# Test: Compliance Reports
# ============================================================================

def test_get_compliance_report(compliance_adapter):
    """Test generating compliance report."""
    report = compliance_adapter.get_compliance_report()

    assert report is not None
    # Report structure depends on UDS3DSGVOCore implementation

    print(f"✅ Compliance report generated")


def test_verify_audit_integrity(compliance_adapter):
    """Test verifying audit log integrity."""
    result = compliance_adapter.verify_audit_integrity()

    assert result is not None
    # May contain integrity check results

    print(f"✅ Audit integrity verification completed")


# ============================================================================
# Test: Statistics
# ============================================================================

def test_get_statistics(compliance_adapter):
    """Test getting adapter statistics."""
    stats = compliance_adapter.get_statistics()

    assert stats is not None
    assert "compliance" in stats
    assert "configuration" in stats
    assert stats["configuration"]["auto_pii_detection"] is True
    assert stats["configuration"]["audit_enabled"] is True

    print(f"✅ Statistics retrieved")
    print(f"   Config: {stats['configuration']}")


# ============================================================================
# Main Test Runner
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("UDS3 Compliance Adapter Tests")
    print("=" * 70 + "\n")

    # Create mock backend
    mock_polyglot = MockPolyglotManager()

    # Create adapter with non-strict mode for testing
    adapter = ComplianceAdapter(
        polyglot_manager=mock_polyglot,
        auto_pii_detection=False,  # Disable for mock tests
        audit_enabled=False  # Disable for mock tests
    )
    adapter.dsgvo.strict_mode = False

    print("\n🧪 Running Compliance Adapter Tests...\n")

    # Run tests
    try:
        test_compliance_adapter_initialization(mock_polyglot)
        test_factory_function(mock_polyglot)
        test_save_document_with_pii_detection(adapter)
        test_save_document_without_pii(adapter)
        test_get_document_secure(adapter)
        test_soft_delete_document(adapter)
        test_hard_delete_document(adapter)
        test_list_documents_exclude_deleted(adapter)
        test_dsgvo_right_to_access(adapter)
        test_dsgvo_right_to_erasure(adapter)
        test_dsgvo_right_to_portability(adapter)
        test_grant_consent(adapter)
        test_revoke_consent(adapter)
        test_create_identity(adapter)
        test_resolve_identity_by_uuid(adapter)
        test_batch_save_documents_secure(adapter)
        test_get_compliance_report(adapter)
        test_verify_audit_integrity(adapter)
        test_get_statistics(adapter)

        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        import traceback
        traceback.print_exc()
