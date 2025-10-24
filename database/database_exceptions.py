#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
database_exceptions.py

database_exceptions.py
Database API Exception Framework
=================================
Zentrale Exception-Klassen für alle Database Backends
mit detailliertem Error-Handling und Logging.
Author: UDS3 System
Date: 2025-10-09
Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)
License: MIT with Government Partnership Commons Clause
Repository: https://github.com/makr-code/VCC-UDS3

Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)
License: MIT with Government Partnership Commons Clause
Repository: https://github.com/makr-code/VCC-UDS3
"""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Basis-Exception für alle Database-Fehler"""
    
    def __init__(
        self, 
        message: str, 
        backend: str,
        operation: str,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        self.message = message
        self.backend = backend
        self.operation = operation
        self.details = details or {}
        self.original_error = original_error
        
        # Konstruiere detaillierte Fehlermeldung
        error_msg = f"[{backend}] {operation} failed: {message}"
        
        if details:
            error_msg += f"\nDetails: {details}"
        
        if original_error:
            error_msg += f"\nOriginal Error: {type(original_error).__name__}: {str(original_error)}"
        
        super().__init__(error_msg)
        
        # Logge Fehler automatisch
        logger.error(error_msg)
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiere Exception zu Dictionary für JSON-Responses"""
        return {
            "error_type": self.__class__.__name__,
            "backend": self.backend,
            "operation": self.operation,
            "message": self.message,
            "details": self.details,
            "original_error": str(self.original_error) if self.original_error else None
        }


class ConnectionError(DatabaseError):
    """Database-Verbindungsfehler"""
    
    def __init__(self, backend: str, host: str, port: int, original_error: Optional[Exception] = None):
        details = {
            "host": host,
            "port": port,
            "connection_string": f"{host}:{port}"
        }
        super().__init__(
            message=f"Connection to {host}:{port} failed",
            backend=backend,
            operation="connect",
            details=details,
            original_error=original_error
        )


class AuthenticationError(DatabaseError):
    """Database-Authentifizierungsfehler"""
    
    def __init__(self, backend: str, username: str, original_error: Optional[Exception] = None):
        details = {"username": username}
        super().__init__(
            message=f"Authentication failed for user '{username}'",
            backend=backend,
            operation="authenticate",
            details=details,
            original_error=original_error
        )


class CollectionNotFoundError(DatabaseError):
    """Collection/Table nicht gefunden"""
    
    def __init__(self, backend: str, collection_name: str, available_collections: Optional[list] = None):
        details = {
            "collection_name": collection_name,
            "available_collections": available_collections or []
        }
        super().__init__(
            message=f"Collection '{collection_name}' not found",
            backend=backend,
            operation="access_collection",
            details=details
        )


class DocumentNotFoundError(DatabaseError):
    """Dokument nicht gefunden"""
    
    def __init__(self, backend: str, document_id: str, collection: Optional[str] = None):
        details = {
            "document_id": document_id,
            "collection": collection
        }
        super().__init__(
            message=f"Document '{document_id}' not found",
            backend=backend,
            operation="fetch_document",
            details=details
        )


class InsertError(DatabaseError):
    """Fehler beim Einfügen von Daten"""
    
    def __init__(
        self, 
        backend: str, 
        operation_type: str,
        record_count: int,
        original_error: Optional[Exception] = None,
        failed_records: Optional[list] = None
    ):
        details = {
            "operation_type": operation_type,
            "record_count": record_count,
            "failed_records": failed_records or []
        }
        super().__init__(
            message=f"Insert operation failed for {record_count} records",
            backend=backend,
            operation=f"insert_{operation_type}",
            details=details,
            original_error=original_error
        )


class QueryError(DatabaseError):
    """Fehler bei Query-Operationen"""
    
    def __init__(
        self, 
        backend: str, 
        query: str,
        query_type: str = "unknown",
        original_error: Optional[Exception] = None
    ):
        details = {
            "query": query[:500] if len(query) > 500 else query,  # Truncate lange Queries
            "query_type": query_type
        }
        super().__init__(
            message=f"Query execution failed",
            backend=backend,
            operation="execute_query",
            details=details,
            original_error=original_error
        )


class ConfigurationError(DatabaseError):
    """Fehler in Database-Konfiguration"""
    
    def __init__(
        self, 
        backend: str, 
        missing_params: Optional[list] = None,
        invalid_params: Optional[Dict[str, str]] = None
    ):
        details = {
            "missing_parameters": missing_params or [],
            "invalid_parameters": invalid_params or {}
        }
        super().__init__(
            message="Database configuration invalid",
            backend=backend,
            operation="validate_config",
            details=details
        )


class APIVersionError(DatabaseError):
    """API-Versions-Inkompatibilität"""
    
    def __init__(
        self, 
        backend: str, 
        required_version: str,
        actual_version: str,
        compatible_versions: Optional[list] = None
    ):
        details = {
            "required_version": required_version,
            "actual_version": actual_version,
            "compatible_versions": compatible_versions or []
        }
        super().__init__(
            message=f"API version mismatch: required {required_version}, got {actual_version}",
            backend=backend,
            operation="version_check",
            details=details
        )


# Convenience Functions für strukturiertes Error-Logging

def log_operation_start(backend: str, operation: str, **kwargs):
    """Logge Start einer Database-Operation"""
    details = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
    logger.info(f"🔄 [{backend}] Starting: {operation} | {details}")


def log_operation_success(backend: str, operation: str, **kwargs):
    """Logge erfolgreiche Database-Operation"""
    details = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
    logger.info(f"✅ [{backend}] Success: {operation} | {details}")


def log_operation_failure(backend: str, operation: str, error: Exception, **kwargs):
    """Logge fehlgeschlagene Database-Operation"""
    details = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
    logger.error(f"❌ [{backend}] Failed: {operation} | {details}")
    logger.error(f"   Error: {type(error).__name__}: {str(error)}")
    
    # Stack Trace nur bei DEBUG-Level
    if logger.isEnabledFor(logging.DEBUG):
        import traceback
        logger.debug(f"   Traceback:\n{traceback.format_exc()}")


def log_operation_warning(backend: str, operation: str, message: str, **kwargs):
    """Logge Warnung während Database-Operation"""
    details = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
    logger.warning(f"⚠️ [{backend}] Warning: {operation} | {message} | {details}")


# ============================================================================
# SAGA-Specific Exceptions
# ============================================================================

class SagaError(DatabaseError):
    """Basis-Exception für alle SAGA-bezogenen Fehler"""
    
    def __init__(
        self,
        message: str,
        saga_id: str,
        operation: str,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        self.saga_id = saga_id
        details = details or {}
        details["saga_id"] = saga_id
        
        super().__init__(
            message=message,
            backend="SAGA",
            operation=operation,
            details=details,
            original_error=original_error
        )


class SagaExecutionError(SagaError):
    """SAGA Step-Execution fehlgeschlagen"""
    
    def __init__(
        self,
        saga_id: str,
        step_id: str,
        step_name: str,
        original_error: Optional[Exception] = None,
        payload: Optional[Dict] = None
    ):
        details = {
            "step_id": step_id,
            "step_name": step_name,
            "payload": payload or {}
        }
        super().__init__(
            message=f"Step '{step_name}' execution failed",
            saga_id=saga_id,
            operation="execute_step",
            details=details,
            original_error=original_error
        )
        self.step_id = step_id
        self.step_name = step_name


class SagaCompensationError(SagaError):
    """SAGA Compensation fehlgeschlagen"""
    
    def __init__(
        self,
        saga_id: str,
        step_id: str,
        compensation_name: str,
        original_error: Optional[Exception] = None,
        retry_count: int = 0
    ):
        details = {
            "step_id": step_id,
            "compensation_name": compensation_name,
            "retry_count": retry_count
        }
        super().__init__(
            message=f"Compensation '{compensation_name}' failed after {retry_count} retries",
            saga_id=saga_id,
            operation="compensate",
            details=details,
            original_error=original_error
        )
        self.step_id = step_id
        self.compensation_name = compensation_name
        self.retry_count = retry_count


class SagaLockError(SagaError):
    """SAGA Lock-Acquisition fehlgeschlagen"""
    
    def __init__(
        self,
        saga_id: str,
        timeout_seconds: float,
        original_error: Optional[Exception] = None
    ):
        details = {
            "timeout_seconds": timeout_seconds,
            "lock_type": "advisory"
        }
        super().__init__(
            message=f"Failed to acquire lock after {timeout_seconds}s",
            saga_id=saga_id,
            operation="acquire_lock",
            details=details,
            original_error=original_error
        )
        self.timeout_seconds = timeout_seconds


class SagaTimeoutError(SagaError):
    """SAGA Transaction Timeout"""
    
    def __init__(
        self,
        saga_id: str,
        elapsed_seconds: float,
        timeout_threshold: float = 300.0
    ):
        details = {
            "elapsed_seconds": elapsed_seconds,
            "timeout_threshold": timeout_threshold
        }
        super().__init__(
            message=f"Transaction timeout: {elapsed_seconds}s elapsed (threshold: {timeout_threshold}s)",
            saga_id=saga_id,
            operation="execute_saga",
            details=details
        )
        self.elapsed_seconds = elapsed_seconds
        self.timeout_threshold = timeout_threshold


class SagaIdempotencyError(SagaError):
    """SAGA Idempotenz-Verletzung"""
    
    def __init__(
        self,
        saga_id: str,
        step_id: str,
        idempotency_key: str,
        existing_status: str
    ):
        details = {
            "step_id": step_id,
            "idempotency_key": idempotency_key,
            "existing_status": existing_status
        }
        super().__init__(
            message=f"Idempotency violation: step '{step_id}' already executed with status '{existing_status}'",
            saga_id=saga_id,
            operation="check_idempotency",
            details=details
        )
        self.step_id = step_id
        self.idempotency_key = idempotency_key
        self.existing_status = existing_status


# ============================================================================
# Database-Specific Exceptions
# ============================================================================

class PostgreSQLDeadlockError(DatabaseError):
    """PostgreSQL Deadlock detected"""
    
    def __init__(
        self,
        table: str,
        query: str,
        original_error: Optional[Exception] = None
    ):
        details = {
            "table": table,
            "query": query[:500] if len(query) > 500 else query
        }
        super().__init__(
            message=f"Deadlock detected on table '{table}'",
            backend="PostgreSQL",
            operation="execute_query",
            details=details,
            original_error=original_error
        )
        self.table = table
        self.query = query


class CouchDBConflictError(DatabaseError):
    """CouchDB _rev Conflict (HTTP 409)"""
    
    def __init__(
        self,
        document_id: str,
        expected_rev: Optional[str] = None,
        actual_rev: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        details = {
            "document_id": document_id,
            "expected_rev": expected_rev,
            "actual_rev": actual_rev
        }
        super().__init__(
            message=f"Document conflict for '{document_id}' (_rev mismatch)",
            backend="CouchDB",
            operation="update_document",
            details=details,
            original_error=original_error
        )
        self.document_id = document_id
        self.expected_rev = expected_rev
        self.actual_rev = actual_rev


class ChromaDBUUIDError(DatabaseError):
    """ChromaDB Collection-ID UUID Validation Error"""
    
    def __init__(
        self,
        collection_name: str,
        invalid_id: str,
        original_error: Optional[Exception] = None
    ):
        details = {
            "collection_name": collection_name,
            "invalid_id": invalid_id,
            "required_format": "UUIDv4"
        }
        super().__init__(
            message=f"Invalid Collection ID '{invalid_id}' (must be UUIDv4)",
            backend="ChromaDB",
            operation="validate_collection_id",
            details=details,
            original_error=original_error
        )
        self.collection_name = collection_name
        self.invalid_id = invalid_id


class Neo4jCypherError(DatabaseError):
    """Neo4j Cypher Query Syntax Error"""
    
    def __init__(
        self,
        query: str,
        error_message: str,
        original_error: Optional[Exception] = None
    ):
        details = {
            "query": query[:500] if len(query) > 500 else query,
            "cypher_error": error_message
        }
        super().__init__(
            message=f"Cypher query failed: {error_message}",
            backend="Neo4j",
            operation="execute_cypher",
            details=details,
            original_error=original_error
        )
        self.query = query
        self.cypher_error_message = error_message
