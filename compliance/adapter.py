#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
adapter.py

adapter.py
UDS3 Compliance Adapter - Integration Layer for Compliance Modules
Connects DSGVO, Security, and Identity Services with UDS3PolyglotManager
to provide comprehensive compliance middleware for all UDS3 operations.
This adapter ensures:
- PII Detection & Masking for all saved documents
- Audit Logging for all CRUD operations
- Soft/Hard Delete strategies
- Multi-User Identity Management
- Security Quality Validation
- DSGVO Rights (Access, Erasure, Portability)
Usage:
from uds3.core import UDS3PolyglotManager
from uds3.compliance import ComplianceAdapter
polyglot = UDS3PolyglotManager(backend_config=db_manager)
compliance = ComplianceAdapter(
polyglot_manager=polyglot,
auto_pii_detection=True,
audit_enabled=True
)
# Save document with automatic PII detection & audit
doc = compliance.save_document_secure(
collection="contracts",
data={"name": "Max Mustermann", "email": "max@example.com"}
Part of UDS3 (Unified Database Strategy v3)

Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)
License: MIT with Government Partnership Commons Clause
Repository: https://github.com/makr-code/VCC-UDS3
"""

import logging
import uuid
from typing import Dict, List, Optional, Any, Literal
from datetime import datetime
from dataclasses import asdict

from core.polyglot_manager import UDS3PolyglotManager
from compliance.dsgvo_core import (
    UDS3DSGVOCore,
    PIIType,
    DSGVOProcessingBasis,
    DSGVOOperationType,
    PIIMapping,
    ConsentRecord,
    DSGVOAuditEntry
)
from compliance.security_quality import (
    DataSecurityManager,
    DataQualityManager,
    SecurityLevel,
    QualityConfig
)
from compliance.identity_service import (
    UDS3IdentityService,
    IdentityRecord
)

logger = logging.getLogger(__name__)


class ComplianceAdapter:
    """
    Compliance Adapter - Bridge between UDS3 PolyglotManager and Compliance Modules.

    Provides:
    - Automatic PII Detection & Masking
    - Audit Logging for all operations
    - Soft/Hard Delete strategies
    - Identity Management
    - Security & Quality Validation
    - DSGVO Rights implementation
    """

    def __init__(
        self,
        polyglot_manager: UDS3PolyglotManager,
        auto_pii_detection: bool = True,
        audit_enabled: bool = True,
        security_level: SecurityLevel = SecurityLevel.INTERNAL,
        quality_config: Optional[QualityConfig] = None,
        retention_years: int = 7
    ):
        """
        Initialize Compliance Adapter.

        Args:
            polyglot_manager: UDS3PolyglotManager instance
            auto_pii_detection: Automatically detect and mask PII in documents
            audit_enabled: Enable audit logging for all operations
            security_level: Security level for document encryption
            quality_config: Configuration for data quality validation
            retention_years: Data retention period (default 7 years for Germany)
        """
        self.polyglot_manager = polyglot_manager
        self.auto_pii_detection = auto_pii_detection
        self.audit_enabled = audit_enabled

        # Initialize compliance modules
        # Note: strict_mode=False allows operation without full backend (for testing)
        self.dsgvo = UDS3DSGVOCore(
            database_manager=polyglot_manager.relational_backend,
            retention_years=retention_years,
            auto_anonymize=auto_pii_detection,
            strict_mode=False  # Allow graceful degradation
        )

        self.security = DataSecurityManager(security_level=security_level)

        self.quality = DataQualityManager(config=quality_config)

        self.identity = UDS3IdentityService(
            relational_backend=polyglot_manager.relational_backend
        )

        logger.info(
            f"ComplianceAdapter initialized (PII: {auto_pii_detection}, "
            f"Audit: {audit_enabled}, Security: {security_level.value})"
        )

    # ========================================================================
    # CRUD Operations with Compliance
    # ========================================================================

    def save_document_secure(
        self,
        collection: str,
        data: Dict[str, Any],
        subject_id: Optional[str] = None,
        processing_basis: DSGVOProcessingBasis = DSGVOProcessingBasis.LEGAL_OBLIGATION,
        consent_id: Optional[str] = None,
        mask_pii: bool = True,
        validate_quality: bool = True,
        performed_by: str = "system"
    ) -> Dict[str, Any]:
        """
        Save document with automatic compliance processing.

        Features:
        - PII Detection & Masking
        - Quality Validation
        - Audit Logging
        - Identity Management

        Args:
            collection: Collection/table name
            data: Document data
            subject_id: DSGVO subject ID (if applicable)
            processing_basis: Legal basis for processing
            consent_id: Consent record ID (if based on consent)
            mask_pii: Mask detected PII
            validate_quality: Validate data quality
            performed_by: User/system performing the operation

        Returns:
            Dict with document_id, pii_detected, quality_score, audit_id
        """
        start_time = datetime.now()
        result = {
            "document_id": None,
            "pii_detected": [],
            "pii_masked": False,
            "quality_score": None,
            "audit_id": None,
            "warnings": []
        }

        try:
            # Step 1: PII Detection
            if self.auto_pii_detection:
                pii_findings = self.dsgvo.detect_pii(content=data)
                result["pii_detected"] = pii_findings

                if pii_findings and mask_pii:
                    # Anonymize content
                    anonymized_result = self.dsgvo.anonymize_content(
                        content=data,
                        processing_basis=processing_basis,
                        subject_id=subject_id,
                        consent_id=consent_id
                    )
                    data = anonymized_result["anonymized_content"]
                    result["pii_masked"] = True
                    result["pii_mappings"] = anonymized_result.get("pii_mappings", [])

                    logger.info(
                        f"PII detected and masked: {len(pii_findings)} fields"
                    )

            # Step 2: Quality Validation
            if validate_quality:
                quality_result = self.quality.calculate_document_quality_score(
                    doc_data=data,
                    collection_name=collection
                )
                result["quality_score"] = quality_result["overall_score"]
                result["quality_metrics"] = quality_result

                # Warn if quality is below threshold
                if quality_result["overall_score"] < 0.6:
                    result["warnings"].append(
                        f"Low quality score: {quality_result['overall_score']:.2f}"
                    )
                    logger.warning(
                        f"Document quality below threshold: "
                        f"{quality_result['overall_score']:.2f}"
                    )

            # Step 3: Save via PolyglotManager
            doc_id = self.polyglot_manager.save_document(
                collection=collection,
                data=data
            )
            result["document_id"] = doc_id

            # Step 4: Audit Logging
            if self.audit_enabled:
                audit_entry = self.dsgvo._create_audit_entry(
                    operation=DSGVOOperationType.PII_DETECTION if pii_findings else None,
                    subject_id=subject_id,
                    document_id=doc_id,
                    processing_basis=processing_basis,
                    performed_by=performed_by,
                    details={
                        "collection": collection,
                        "pii_detected": len(pii_findings),
                        "pii_masked": result["pii_masked"],
                        "quality_score": result["quality_score"],
                        "processing_time_ms": int((datetime.now() - start_time).total_seconds() * 1000)
                    }
                )
                result["audit_id"] = audit_entry.audit_id

            logger.info(
                f"Document saved securely: {doc_id} "
                f"(PII: {len(pii_findings)}, Quality: {result['quality_score']:.2f if result['quality_score'] else 'N/A'})"
            )

            return result

        except Exception as e:
            logger.error(f"Error saving document securely: {e}")
            result["error"] = str(e)
            return result

    def get_document_secure(
        self,
        collection: str,
        document_id: str,
        subject_id: Optional[str] = None,
        unmask_pii: bool = False,
        performed_by: str = "system"
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve document with compliance checks.

        Features:
        - Audit Logging
        - Optional PII unmasking (requires authorization)

        Args:
            collection: Collection/table name
            document_id: Document ID
            subject_id: DSGVO subject ID
            unmask_pii: Unmask PII (requires proper authorization)
            performed_by: User/system performing the operation

        Returns:
            Document data or None
        """
        try:
            # Retrieve document
            doc = self.polyglot_manager.get_document(
                collection=collection,
                document_id=document_id
            )

            if not doc:
                return None

            # Audit Logging
            if self.audit_enabled:
                self.dsgvo._create_audit_entry(
                    operation=DSGVOOperationType.RIGHT_TO_ACCESS,
                    subject_id=subject_id,
                    document_id=document_id,
                    processing_basis=DSGVOProcessingBasis.LEGAL_OBLIGATION,
                    performed_by=performed_by,
                    details={"collection": collection, "unmask_pii": unmask_pii}
                )

            # TODO: Implement PII unmasking (requires secure key management)
            if unmask_pii:
                logger.warning(
                    "PII unmasking requested but not yet implemented "
                    "(requires secure key management)"
                )

            return doc

        except Exception as e:
            logger.error(f"Error retrieving document securely: {e}")
            return None

    def delete_document_secure(
        self,
        collection: str,
        document_id: str,
        subject_id: Optional[str] = None,
        soft_delete: bool = True,
        reason: str = "user_request",
        performed_by: str = "system"
    ) -> Dict[str, Any]:
        """
        Delete document with compliance (soft or hard delete).

        Features:
        - Soft Delete (mark as deleted, retain for audit)
        - Hard Delete (permanent removal)
        - Audit Logging
        - DSGVO Right to Erasure

        Args:
            collection: Collection/table name
            document_id: Document ID
            subject_id: DSGVO subject ID
            soft_delete: Use soft delete (True) or hard delete (False)
            reason: Reason for deletion
            performed_by: User/system performing the operation

        Returns:
            Dict with success status and audit_id
        """
        result = {"success": False, "audit_id": None}

        try:
            if soft_delete:
                # Soft Delete: Mark as deleted
                doc = self.polyglot_manager.get_document(collection, document_id)
                if doc:
                    doc["_deleted"] = True
                    doc["_deleted_at"] = datetime.now().isoformat()
                    doc["_deleted_reason"] = reason
                    doc["_deleted_by"] = performed_by

                    self.polyglot_manager.update_document(
                        collection=collection,
                        document_id=document_id,
                        updates=doc
                    )
                    result["success"] = True
                    result["delete_type"] = "soft"
            else:
                # Hard Delete: Permanent removal
                success = self.polyglot_manager.delete_document(
                    collection=collection,
                    document_id=document_id
                )
                result["success"] = success
                result["delete_type"] = "hard"

            # Audit Logging
            if self.audit_enabled:
                audit_entry = self.dsgvo._create_audit_entry(
                    operation=DSGVOOperationType.RIGHT_TO_ERASURE,
                    subject_id=subject_id,
                    document_id=document_id,
                    processing_basis=DSGVOProcessingBasis.LEGAL_OBLIGATION,
                    performed_by=performed_by,
                    details={
                        "collection": collection,
                        "delete_type": result["delete_type"],
                        "reason": reason
                    }
                )
                result["audit_id"] = audit_entry.audit_id

            logger.info(
                f"Document deleted ({result['delete_type']}): {document_id}"
            )

            return result

        except Exception as e:
            logger.error(f"Error deleting document securely: {e}")
            result["error"] = str(e)
            return result

    def list_documents_secure(
        self,
        collection: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        exclude_deleted: bool = True
    ) -> List[Dict[str, Any]]:
        """
        List documents with compliance filtering.

        Args:
            collection: Collection/table name
            filters: Additional filters
            limit: Maximum number of documents
            exclude_deleted: Exclude soft-deleted documents

        Returns:
            List of documents
        """
        try:
            docs = self.polyglot_manager.list_documents(
                collection=collection,
                filters=filters,
                limit=limit
            )

            # Filter out soft-deleted documents
            if exclude_deleted:
                docs = [doc for doc in docs if not doc.get("_deleted", False)]

            return docs

        except Exception as e:
            logger.error(f"Error listing documents securely: {e}")
            return []

    # ========================================================================
    # DSGVO Rights Implementation
    # ========================================================================

    def dsgvo_right_to_access(
        self,
        subject_id: str,
        performed_by: str = "system"
    ) -> Dict[str, Any]:
        """
        Implement DSGVO Right to Access (Art. 15).

        Returns all data associated with a subject.

        Args:
            subject_id: DSGVO subject ID
            performed_by: User/system performing the operation

        Returns:
            Dict with all subject data
        """
        try:
            result = self.dsgvo.dsgvo_right_to_access(subject_id=subject_id)

            # Audit Logging
            if self.audit_enabled:
                self.dsgvo._create_audit_entry(
                    operation=DSGVOOperationType.RIGHT_TO_ACCESS,
                    subject_id=subject_id,
                    processing_basis=DSGVOProcessingBasis.LEGAL_OBLIGATION,
                    performed_by=performed_by,
                    details={"documents_found": len(result.get("documents", []))}
                )

            return result

        except Exception as e:
            logger.error(f"Error processing Right to Access: {e}")
            return {"error": str(e)}

    def dsgvo_right_to_erasure(
        self,
        subject_id: str,
        reason: str = "user_request",
        performed_by: str = "system"
    ) -> Dict[str, Any]:
        """
        Implement DSGVO Right to Erasure (Art. 17).

        Deletes all data associated with a subject.

        Args:
            subject_id: DSGVO subject ID
            reason: Reason for deletion
            performed_by: User/system performing the operation

        Returns:
            Dict with deletion results
        """
        try:
            result = self.dsgvo.dsgvo_right_to_erasure(
                subject_id=subject_id,
                reason=reason
            )

            # Audit Logging (already done in UDS3DSGVOCore)

            return result

        except Exception as e:
            logger.error(f"Error processing Right to Erasure: {e}")
            return {"error": str(e)}

    def dsgvo_right_to_portability(
        self,
        subject_id: str,
        format: Literal["json", "csv", "xml"] = "json",
        performed_by: str = "system"
    ) -> Dict[str, Any]:
        """
        Implement DSGVO Right to Data Portability (Art. 20).

        Returns subject data in machine-readable format.

        Args:
            subject_id: DSGVO subject ID
            format: Export format (json, csv, xml)
            performed_by: User/system performing the operation

        Returns:
            Dict with exported data
        """
        try:
            result = self.dsgvo.dsgvo_right_to_portability(subject_id=subject_id)

            # Audit Logging
            if self.audit_enabled:
                self.dsgvo._create_audit_entry(
                    operation=DSGVOOperationType.RIGHT_TO_PORTABILITY,
                    subject_id=subject_id,
                    processing_basis=DSGVOProcessingBasis.LEGAL_OBLIGATION,
                    performed_by=performed_by,
                    details={"format": format}
                )

            return result

        except Exception as e:
            logger.error(f"Error processing Right to Portability: {e}")
            return {"error": str(e)}

    # ========================================================================
    # Consent Management
    # ========================================================================

    def grant_consent(
        self,
        subject_id: str,
        purpose: str,
        data_categories: List[PIIType],
        valid_days: int = 365,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConsentRecord:
        """
        Grant DSGVO consent for data processing.

        Args:
            subject_id: DSGVO subject ID
            purpose: Purpose of data processing
            data_categories: Categories of data covered by consent
            valid_days: Consent validity period (days)
            metadata: Additional metadata

        Returns:
            ConsentRecord
        """
        try:
            consent = self.dsgvo.grant_consent(
                subject_id=subject_id,
                purpose=purpose,
                data_categories=data_categories,
                valid_days=valid_days,
                metadata=metadata or {}
            )

            logger.info(f"Consent granted: {consent.consent_id} for {subject_id}")

            return consent

        except Exception as e:
            logger.error(f"Error granting consent: {e}")
            raise

    def revoke_consent(
        self,
        consent_id: str,
        performed_by: str = "system"
    ) -> bool:
        """
        Revoke DSGVO consent.

        Args:
            consent_id: Consent record ID
            performed_by: User/system performing the operation

        Returns:
            Success status
        """
        try:
            success = self.dsgvo.revoke_consent(consent_id=consent_id)

            # Audit Logging
            if self.audit_enabled and success:
                self.dsgvo._create_audit_entry(
                    operation=DSGVOOperationType.CONSENT_REVOKED,
                    processing_basis=DSGVOProcessingBasis.CONSENT,
                    performed_by=performed_by,
                    details={"consent_id": consent_id}
                )

            logger.info(f"Consent revoked: {consent_id}")

            return success

        except Exception as e:
            logger.error(f"Error revoking consent: {e}")
            return False

    # ========================================================================
    # Identity Management
    # ========================================================================

    def create_identity(
        self,
        aktenzeichen: Optional[str] = None,
        backend_ids: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> IdentityRecord:
        """
        Create or ensure identity record.

        Args:
            aktenzeichen: Case reference number (optional)
            backend_ids: Backend-specific IDs (vector_db_id, graph_db_id, etc.)
            metadata: Additional metadata

        Returns:
            IdentityRecord
        """
        try:
            identity = self.identity.ensure_identity(
                aktenzeichen=aktenzeichen,
                metadata=metadata or {}
            )

            # Bind backend IDs if provided
            if backend_ids:
                for backend_type, backend_id in backend_ids.items():
                    self.identity.bind_backend_ids(
                        uuid_value=identity.uuid,
                        backend_ids={backend_type: backend_id}
                    )

            logger.info(f"Identity created: {identity.uuid}")

            return identity

        except Exception as e:
            logger.error(f"Error creating identity: {e}")
            raise

    def resolve_identity(
        self,
        uuid_value: Optional[str] = None,
        aktenzeichen: Optional[str] = None
    ) -> Optional[IdentityRecord]:
        """
        Resolve identity by UUID or Aktenzeichen.

        Args:
            uuid_value: UUID to resolve
            aktenzeichen: Aktenzeichen to resolve

        Returns:
            IdentityRecord or None
        """
        try:
            if uuid_value:
                return self.identity.resolve_by_uuid(uuid_value)
            elif aktenzeichen:
                return self.identity.resolve_by_aktenzeichen(aktenzeichen)
            else:
                raise ValueError("Either uuid_value or aktenzeichen must be provided")

        except Exception as e:
            logger.error(f"Error resolving identity: {e}")
            return None

    # ========================================================================
    # Compliance Reports
    # ========================================================================

    def get_compliance_report(self) -> Dict[str, Any]:
        """
        Get comprehensive compliance report.

        Returns:
            Dict with compliance statistics
        """
        try:
            report = self.dsgvo.get_compliance_report()

            # Add quality statistics
            # TODO: Implement quality statistics aggregation

            return report

        except Exception as e:
            logger.error(f"Error generating compliance report: {e}")
            return {"error": str(e)}

    def verify_audit_integrity(self) -> Dict[str, Any]:
        """
        Verify audit log integrity (tamper detection).

        Returns:
            Dict with integrity check results
        """
        try:
            return self.dsgvo._verify_audit_integrity()

        except Exception as e:
            logger.error(f"Error verifying audit integrity: {e}")
            return {"error": str(e)}

    # ========================================================================
    # Batch Operations
    # ========================================================================

    def batch_save_documents_secure(
        self,
        collection: str,
        documents: List[Dict[str, Any]],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Batch save documents with compliance processing.

        Args:
            collection: Collection/table name
            documents: List of documents
            **kwargs: Additional arguments for save_document_secure

        Returns:
            List of results
        """
        results = []

        for doc in documents:
            result = self.save_document_secure(
                collection=collection,
                data=doc,
                **kwargs
            )
            results.append(result)

        logger.info(f"Batch saved {len(results)} documents securely")

        return results

    # ========================================================================
    # Statistics
    # ========================================================================

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get compliance adapter statistics.

        Returns:
            Dict with statistics
        """
        try:
            compliance_report = self.get_compliance_report()

            stats = {
                "compliance": compliance_report,
                "configuration": {
                    "auto_pii_detection": self.auto_pii_detection,
                    "audit_enabled": self.audit_enabled,
                    "security_level": self.security.security_level.value
                }
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {"error": str(e)}


# ============================================================================
# Factory Function
# ============================================================================

def create_compliance_adapter(
    polyglot_manager: UDS3PolyglotManager,
    **kwargs
) -> ComplianceAdapter:
    """
    Factory function to create ComplianceAdapter.

    Args:
        polyglot_manager: UDS3PolyglotManager instance
        **kwargs: Additional arguments for ComplianceAdapter

    Returns:
        ComplianceAdapter instance

    Example:
        >>> from uds3.core import UDS3PolyglotManager
        >>> from uds3.compliance import create_compliance_adapter
        >>>
        >>> polyglot = UDS3PolyglotManager(backend_config=db_manager)
        >>> compliance = create_compliance_adapter(
        ...     polyglot_manager=polyglot,
        ...     auto_pii_detection=True,
        ...     audit_enabled=True
        ... )
    """
    return ComplianceAdapter(polyglot_manager=polyglot_manager, **kwargs)
