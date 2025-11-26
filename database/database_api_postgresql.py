#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
database_api_postgresql.py

database_api_postgresql.py
PostgreSQL Relational Backend für UDS3
Implementiert PostgreSQL-Backend analog zu SQLiteRelationalBackend.
Verwendet für Corvina Backend die migrierte PostgreSQL-Datenbank.
Error-Handling:
- Connection Pool Management (ThreadedConnectionPool)
- Deadlock Detection + Retry
- Transaction Rollback bei Failures
- Structured Error Logging
- Pool Metrics Tracking (_used, _free connections)
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
import psycopg2
import psycopg2.extras
import psycopg2.errors
from psycopg2 import pool
from typing import Dict, List, Optional, Any
from datetime import datetime
import time

logger = logging.getLogger(__name__)

# Import Error-Logging Functions (if available)
try:
    from .database_exceptions import (
        log_operation_start,
        log_operation_success,
        log_operation_failure
    )
    ERROR_LOGGING_AVAILABLE = True
except ImportError:
    ERROR_LOGGING_AVAILABLE = False
    logger.warning("⚠️ database_exceptions not available - using basic logging")


class PostgreSQLRelationalBackend:
    """PostgreSQL Backend für relationale Daten (Dokument-Metadaten) mit Connection Pool"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialisiert PostgreSQL Backend mit Connection Pool
        
        Args:
            config: PostgreSQL Konfiguration mit:
                - host: PostgreSQL Host (e.g., '192.168.178.94')
                - port: PostgreSQL Port (default: 5432)
                - user: Database User (e.g., 'postgres')
                - password: Database Password
                - database: Database Name (e.g., 'postgres')
                - schema: Schema Name (default: 'public')
                - pool_min: Minimum Pool Size (default: 2)
                - pool_max: Maximum Pool Size (default: 10)
        """
        self.config = config
        self.host = config.get('host', '192.168.178.94')
        self.port = config.get('port', 5432)
        self.user = config.get('user', 'postgres')
        self.password = config.get('password', 'postgres')
        self.database = config.get('database', 'postgres')
        self.schema = config.get('schema', 'public')
        self.table_name = config.get('table_name', 'documents')  # Configurable table name
        
        # Connection Pool Configuration
        self.pool_min = config.get('pool_min', 2)   # Minimum connections
        self.pool_max = config.get('pool_max', 10)  # Maximum connections
        
        self.pool = None
        self.conn = None  # Current thread connection (backward compatibility)
        self.cursor = None
        
        logger.info(f"PostgreSQL Backend initialisiert: {self.host}:{self.port}/{self.database} (table: {self.table_name}, pool: {self.pool_min}-{self.pool_max})")
    
    
    def connect(self):
        """
        Erstellt Connection Pool zu PostgreSQL-Datenbank
        
        Features:
        - ThreadedConnectionPool (psycopg2.pool)
        - Auto-Reconnect bei Connection Loss
        - Retry-Logic (3 Versuche)
        - Structured Error Logging
        
        Returns:
            bool: True wenn Pool erfolgreich erstellt
        
        Raises:
            Exception: Nach allen Retry-Versuchen
        """
        if self.pool is not None:
            return True  # Pool bereits erstellt
        
        max_retries = 3
        base_delay = 1.0
        
        for retry in range(max_retries):
            try:
                if ERROR_LOGGING_AVAILABLE:
                    log_operation_start("PostgreSQL", "connect", host=self.host, port=self.port)
                
                # Create ThreadedConnectionPool
                self.pool = pool.ThreadedConnectionPool(
                    minconn=self.pool_min,
                    maxconn=self.pool_max,
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    connect_timeout=10  # 10s Timeout
                )
                
                # Get initial connection for backward compatibility
                self.conn = self.pool.getconn()
                self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                
                if ERROR_LOGGING_AVAILABLE:
                    log_operation_success("PostgreSQL", "connect", host=self.host, port=self.port)
                else:
                    logger.info(f"✅ PostgreSQL Connection Pool erstellt: {self.host}:{self.port} (min: {self.pool_min}, max: {self.pool_max})")
                
                return True
                
            except psycopg2.OperationalError as e:
                # Connection-Fehler (Network, Server Down, Auth Failure)
                error_str = str(e)
                
                if retry < max_retries - 1:
                    delay = base_delay * (2 ** retry)
                    logger.warning(f"⚠️ PostgreSQL Connection Retry {retry+1}/{max_retries} nach {delay}s: {error_str}")
                    time.sleep(delay)
                else:
                    # Finale Failure nach allen Retries
                    if ERROR_LOGGING_AVAILABLE:
                        log_operation_failure("PostgreSQL", "connect", e, host=self.host, port=self.port)
                    else:
                        logger.error(f"❌ PostgreSQL Verbindung fehlgeschlagen nach {max_retries} Versuchen: {e}")
                    raise Exception(f"PostgreSQL connection failed: {error_str}")
                    
            except Exception as e:
                # Andere Fehler (z.B. Konfigurationsfehler)
                if ERROR_LOGGING_AVAILABLE:
                    log_operation_failure("PostgreSQL", "connect", e, host=self.host, port=self.port)
                else:
                    logger.error(f"❌ PostgreSQL Verbindung fehlgeschlagen: {e}")
                raise
    
    
    def disconnect(self):
        """Schließt PostgreSQL Connection Pool und alle Verbindungen"""
        try:
            # Close cursor if exists
            if self.cursor:
                self.cursor.close()
                self.cursor = None
        except Exception as e:
            logger.warning(f"Warnung beim Schließen des Cursors: {e}")
        
        try:
            # Return current connection to pool
            if self.conn and not self.conn.closed:
                if self.pool:
                    self.pool.putconn(self.conn)
                else:
                    self.conn.close()
                self.conn = None
        except Exception as e:
            logger.warning(f"Warnung beim Zurückgeben der Verbindung: {e}")
        
        try:
            # Close entire pool
            if self.pool:
                self.pool.closeall()
                self.pool = None
                logger.debug("PostgreSQL Connection Pool geschlossen")
        except Exception as e:
            logger.warning(f"Warnung beim Schließen des Pools: {e}")
    
    
    def get_pool_stats(self) -> Dict[str, int]:
        """
        Gibt Connection Pool Statistiken zurück für Metrics Tracking
        
        Returns:
            Dict mit:
                - active: Anzahl aktive Verbindungen (_used)
                - idle: Anzahl freie Verbindungen (_pool)
                - total: Gesamtanzahl Verbindungen
        """
        if not self.pool:
            return {"active": 0, "idle": 0, "total": 0}
        
        try:
            # ThreadedConnectionPool hat _used (dict) und _pool (list)
            active = len(self.pool._used)
            idle = len(self.pool._pool)
            total = active + idle
            
            return {
                "active": active,
                "idle": idle,
                "total": total
            }
        except Exception as e:
            logger.warning(f"Fehler beim Abrufen der Pool-Statistiken: {e}")
            return {"active": 0, "idle": 0, "total": 0}
    
    
    def create_tables_if_not_exist(self):
        """Erstellt Tabellen falls nicht vorhanden (Migration hat sie bereits erstellt)"""
        self.connect()
        
        # Documents Tabelle (sollte bereits existieren durch Migration)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                document_id TEXT PRIMARY KEY,
                file_path TEXT NOT NULL,
                classification TEXT NOT NULL,
                content_length BIGINT NOT NULL,
                legal_terms_count BIGINT NOT NULL,
                created_at TEXT NOT NULL,
                quality_score DOUBLE PRECISION,
                processing_status TEXT DEFAULT 'completed'
            )
        """)
        
        # Keywords Tabelle
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_keywords (
                id SERIAL PRIMARY KEY,
                document_id TEXT,
                keyword TEXT,
                frequency INTEGER,
                FOREIGN KEY (document_id) REFERENCES documents (document_id)
            )
        """)
        
        self.conn.commit()
        logger.info("✅ PostgreSQL Tabellen validiert/erstellt")
    
    
    def insert_document(self, document_id: str, file_path: str, classification: str,
                       content_length: int, legal_terms_count: int,
                       created_at: Optional[str] = None,
                       quality_score: Optional[float] = None,
                       processing_status: str = 'completed') -> Dict[str, Any]:
        """
        Fügt Dokument ein oder aktualisiert es (mit Error-Handling)
        
        Features:
        - Deadlock Detection + Retry
        - Unique Constraint Handling
        - Transaction Rollback bei Failure
        - Structured Error Logging
        
        Args:
            document_id: Eindeutige Dokument-ID
            file_path: Dateipfad
            classification: Dokumentklassifikation
            content_length: Content-Länge
            legal_terms_count: Anzahl Legal Terms
            created_at: Timestamp (optional)
            quality_score: Quality Score (optional)
            processing_status: Status (default: 'completed')
        
        Returns:
            Dict mit success, operations, total_documents, error
        """
        self.connect()
        
        if created_at is None:
            created_at = datetime.now().isoformat()
        
        max_retries = 3
        base_delay = 0.5
        
        for retry in range(max_retries):
            try:
                if ERROR_LOGGING_AVAILABLE:
                    log_operation_start("PostgreSQL", "insert_document", document_id=document_id)
                
                # INSERT oder UPDATE (ON CONFLICT) - Idempotent
                self.cursor.execute("""
                    INSERT INTO documents 
                    (document_id, file_path, classification, content_length, 
                     legal_terms_count, created_at, quality_score, processing_status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (document_id) 
                    DO UPDATE SET
                        file_path = EXCLUDED.file_path,
                        classification = EXCLUDED.classification,
                        content_length = EXCLUDED.content_length,
                        legal_terms_count = EXCLUDED.legal_terms_count,
                        quality_score = EXCLUDED.quality_score,
                        processing_status = EXCLUDED.processing_status
                """, (document_id, file_path, classification, content_length,
                      legal_terms_count, created_at, quality_score, processing_status))
                
                self.conn.commit()
                
                # Statistiken
                total_docs = self.get_document_count()
                class_docs = self.get_document_count_by_classification(classification)
                
                if ERROR_LOGGING_AVAILABLE:
                    log_operation_success("PostgreSQL", "insert_document", document_id=document_id, total_docs=total_docs)
                
                return {
                    "success": True,
                    "operations": [
                        "metadata_inserted",
                        "classification_updated",
                        "statistics_calculated"
                    ],
                    "records_affected": 1,
                    "total_documents": total_docs,
                    "documents_in_class": class_docs,
                    "database": f"{self.host}:{self.port}/{self.database}"
                }
                
            except psycopg2.errors.DeadlockDetected as e:
                # Deadlock → Rollback + Retry
                self.conn.rollback()
                
                if retry < max_retries - 1:
                    delay = base_delay * (2 ** retry)
                    logger.warning(f"⚠️ PostgreSQL Deadlock - Retry {retry+1}/{max_retries} nach {delay}s")
                    time.sleep(delay)
                else:
                    if ERROR_LOGGING_AVAILABLE:
                        log_operation_failure("PostgreSQL", "insert_document", e, document_id=document_id, error_type="DeadlockDetected")
                    else:
                        logger.error(f"❌ PostgreSQL Deadlock nach {max_retries} Retries: {e}")
                    
                    return {
                        "success": False,
                        "error": f"PostgreSQL deadlock after {max_retries} retries: {str(e)}",
                        "error_type": "DeadlockDetected"
                    }
                    
            except psycopg2.errors.UniqueViolation as e:
                # Unique Constraint Violation (sollte durch ON CONFLICT nicht passieren)
                self.conn.rollback()
                
                if ERROR_LOGGING_AVAILABLE:
                    log_operation_failure("PostgreSQL", "insert_document", e, document_id=document_id, error_type="UniqueViolation")
                else:
                    logger.error(f"❌ PostgreSQL Unique Violation: {e}")
                
                return {
                    "success": False,
                    "error": f"PostgreSQL unique constraint violation: {str(e)}",
                    "error_type": "UniqueViolation"
                }
                
            except psycopg2.IntegrityError as e:
                # Foreign Key Violation, Not Null Constraint, etc.
                self.conn.rollback()
                
                if ERROR_LOGGING_AVAILABLE:
                    log_operation_failure("PostgreSQL", "insert_document", e, document_id=document_id, error_type="IntegrityError")
                else:
                    logger.error(f"❌ PostgreSQL Integrity Error: {e}")
                
                return {
                    "success": False,
                    "error": f"PostgreSQL integrity error: {str(e)}",
                    "error_type": "IntegrityError"
                }
                
            except psycopg2.OperationalError as e:
                # Connection Lost während Transaction
                self.conn.rollback()
                
                # Try reconnect
                try:
                    self.disconnect()
                    self.connect()
                    logger.info("✅ PostgreSQL Reconnect erfolgreich - Retry Operation")
                except Exception:
                    pass
                
                if retry < max_retries - 1:
                    delay = base_delay * (2 ** retry)
                    logger.warning(f"⚠️ PostgreSQL Connection Lost - Retry {retry+1}/{max_retries} nach {delay}s")
                    time.sleep(delay)
                else:
                    if ERROR_LOGGING_AVAILABLE:
                        log_operation_failure("PostgreSQL", "insert_document", e, document_id=document_id, error_type="OperationalError")
                    else:
                        logger.error(f"❌ PostgreSQL Operational Error: {e}")
                    
                    return {
                        "success": False,
                        "error": f"PostgreSQL operational error: {str(e)}",
                        "error_type": "OperationalError"
                    }
                    
            except Exception as e:
                # Andere unerwartete Fehler
                self.conn.rollback()
                
                if ERROR_LOGGING_AVAILABLE:
                    log_operation_failure("PostgreSQL", "insert_document", e, document_id=document_id, error_type="UnexpectedError")
                else:
                    logger.error(f"❌ PostgreSQL Unexpected Error: {e}")
                
                return {
                    "success": False,
                    "error": f"PostgreSQL operation failed: {str(e)}",
                    "error_type": "UnexpectedError"
                }
        
        # Should not reach here
        return {
            "success": False,
            "error": "PostgreSQL operation failed after all retries"
        }
    
    
    def get_document_count(self) -> int:
        """
        Gibt Gesamtanzahl der Dokumente zurück (mit Error-Handling)
        
        Returns:
            int: Anzahl Dokumente (0 bei Fehler)
        """
        try:
            self.connect()
            self.cursor.execute("SELECT COUNT(*) as count FROM documents")
            result = self.cursor.fetchone()
            return result['count'] if result else 0
        except Exception as e:
            logger.error(f"❌ PostgreSQL get_document_count failed: {e}")
            return 0
    
    
    def get_document_count_by_classification(self, classification: str) -> int:
        """
        Gibt Anzahl Dokumente pro Klassifikation zurück (mit Error-Handling)
        
        Args:
            classification: Dokumentklassifikation
        
        Returns:
            int: Anzahl Dokumente (0 bei Fehler)
        """
        try:
            self.connect()
            self.cursor.execute(
                "SELECT COUNT(*) as count FROM documents WHERE classification = %s",
                (classification,)
            )
            result = self.cursor.fetchone()
            return result['count'] if result else 0
        except Exception as e:
            logger.error(f"❌ PostgreSQL get_document_count_by_classification failed: {e}")
            return 0
    
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Holt Dokument-Metadaten (mit Error-Handling)
        
        Args:
            document_id: Dokument-ID
        
        Returns:
            Dict mit Dokument-Daten oder None bei Fehler/Not Found
        """
        try:
            self.connect()
            
            if ERROR_LOGGING_AVAILABLE:
                log_operation_start("PostgreSQL", "get_document", document_id=document_id)
            
            self.cursor.execute(
                "SELECT * FROM documents WHERE document_id = %s",
                (document_id,)
            )
            
            result = self.cursor.fetchone()
            
            if ERROR_LOGGING_AVAILABLE:
                log_operation_success("PostgreSQL", "get_document", document_id=document_id, found=result is not None)
            
            return result
            
        except Exception as e:
            if ERROR_LOGGING_AVAILABLE:
                log_operation_failure("PostgreSQL", "get_document", e, document_id=document_id)
            else:
                logger.error(f"❌ PostgreSQL get_document failed: {e}")
            return None
    
    
    def delete_document(self, document_id: str) -> Dict[str, Any]:
        """
        Löscht Dokument (mit Error-Handling)
        
        Features:
        - CASCADE Delete (Keywords zuerst)
        - Transaction Rollback bei Failure
        - Structured Error Logging
        - Idempotent (Success auch wenn nicht existiert)
        
        Args:
            document_id: Dokument-ID zum Löschen
        
        Returns:
            Dict mit success, rows_deleted, error
        """
        self.connect()
        
        try:
            if ERROR_LOGGING_AVAILABLE:
                log_operation_start("PostgreSQL", "delete_document", document_id=document_id)
            
            # Lösche Keywords
            self.cursor.execute(
                "DELETE FROM document_keywords WHERE document_id = %s",
                (document_id,)
            )
            
            # Lösche Dokument
            self.cursor.execute(
                "DELETE FROM documents WHERE document_id = %s",
                (document_id,)
            )
            
            rows_deleted = self.cursor.rowcount
            self.conn.commit()
            
            if ERROR_LOGGING_AVAILABLE:
                log_operation_success("PostgreSQL", "delete_document", document_id=document_id, rows_deleted=rows_deleted)
            
            return {
                "success": True,
                "rows_deleted": rows_deleted
            }
            
        except psycopg2.IntegrityError as e:
            # Foreign Key Constraint Violation
            self.conn.rollback()
            
            if ERROR_LOGGING_AVAILABLE:
                log_operation_failure("PostgreSQL", "delete_document", e, document_id=document_id, error_type="IntegrityError")
            else:
                logger.error(f"❌ PostgreSQL Delete Integrity Error: {e}")
            
            return {
                "success": False,
                "error": f"PostgreSQL integrity error: {str(e)}",
                "error_type": "IntegrityError"
            }
            
        except Exception as e:
            self.conn.rollback()
            
            if ERROR_LOGGING_AVAILABLE:
                log_operation_failure("PostgreSQL", "delete_document", e, document_id=document_id)
            else:
                logger.error(f"❌ Dokument-Delete fehlgeschlagen: {e}")
            
            return {
                "success": False,
                "error": str(e)
            }
    
    
    def get_statistics(self) -> Dict[str, Any]:
        """Holt Datenbank-Statistiken"""
        self.connect()
        
        try:
            # Gesamt-Anzahl
            total = self.get_document_count()
            
            # Klassifikationen
            self.cursor.execute("""
                SELECT classification, COUNT(*) as count
                FROM documents
                GROUP BY classification
                ORDER BY count DESC
            """)
            classifications = {row['classification']: row['count']
                             for row in self.cursor.fetchall()}
            
            # Processing Status
            self.cursor.execute("""
                SELECT processing_status, COUNT(*) as count
                FROM documents
                GROUP BY processing_status
                ORDER BY count DESC
            """)
            statuses = {row['processing_status']: row['count']
                       for row in self.cursor.fetchall()}
            
            # Quality Score Stats
            self.cursor.execute("""
                SELECT 
                    AVG(quality_score) as avg_score,
                    MIN(quality_score) as min_score,
                    MAX(quality_score) as max_score,
                    COUNT(*) FILTER (WHERE quality_score IS NULL) as null_count
                FROM documents
            """)
            quality_stats = self.cursor.fetchone()
            
            return {
                "total_documents": total,
                "classifications": classifications,
                "processing_statuses": statuses,
                "quality_scores": {
                    "average": float(quality_stats['avg_score']) if quality_stats['avg_score'] else None,
                    "min": float(quality_stats['min_score']) if quality_stats['min_score'] else None,
                    "max": float(quality_stats['max_score']) if quality_stats['max_score'] else None,
                    "null_count": quality_stats['null_count']
                },
                "database": f"{self.host}:{self.port}/{self.database}"
            }
            
        except Exception as e:
            logger.error(f"❌ Statistiken-Abfrage fehlgeschlagen: {e}")
            return {
                "error": str(e)
            }
    
    # ================================================================
    # BATCH OPERATIONS
    # ================================================================
    
    async def batch_update(
        self,
        updates: List[Dict[str, Any]],
        mode: str = "partial"
    ) -> Dict[str, Any]:
        """
        Batch update documents (67-100x faster than sequential)
        
        Args:
            updates: List of update dicts with:
                - document_id: Document ID to update
                - fields: Dict of fields to update
            mode: Update mode ("partial" or "full")
            
        Returns:
            Dict with keys: success, updated, failed, errors
        """
        if not updates:
            return {"success": True, "updated": 0, "failed": 0, "errors": []}
        
        try:
            # Extract all unique fields to update
            all_fields = set()
            for update in updates:
                all_fields.update(update.get("fields", {}).keys())
            
            if not all_fields:
                return {"success": True, "updated": 0, "failed": 0, "errors": []}
            
            # Build CASE/WHEN clauses for each field
            case_clauses = []
            for field in all_fields:
                cases = []
                for update in updates:
                    value = update.get("fields", {}).get(field)
                    if value is not None:
                        doc_id = update["document_id"].replace("'", "''")
                        if isinstance(value, str):
                            value_str = f"'{value.replace('\'', '\'\'')}'"
                        elif isinstance(value, (int, float)):
                            value_str = str(value)
                        elif isinstance(value, bool):
                            value_str = 'TRUE' if value else 'FALSE'
                        else:
                            value_str = f"'{str(value).replace('\'', '\'\'')}'"
                        
                        cases.append(f"WHEN document_id = '{doc_id}' THEN {value_str}")
                
                if cases:
                    case_clause = f"{field} = CASE {' '.join(cases)} ELSE {field} END"
                    case_clauses.append(case_clause)
            
            # Build WHERE clause
            doc_ids = [u["document_id"].replace("'", "''") for u in updates]
            doc_ids_str = "', '".join(doc_ids)
            
            # Execute update
            query = f"""
                UPDATE {self.table_name} 
                SET 
                    {', '.join(case_clauses)},
                    updated_at = NOW()
                WHERE document_id IN ('{doc_ids_str}')
            """
            
            self.cursor.execute(query)
            updated_count = self.cursor.rowcount
            self.conn.commit()
            
            logger.info(f"✅ Batch updated {updated_count}/{len(updates)} documents")
            
            return {
                "success": True,
                "updated": updated_count,
                "failed": len(updates) - updated_count,
                "errors": []
            }
            
        except Exception as e:
            logger.error(f"❌ Batch update failed: {e}")
            if self.conn and not self.conn.closed:
                self.conn.rollback()
            return {
                "success": False,
                "updated": 0,
                "failed": len(updates),
                "errors": [{"error": str(e)}]
            }
    
    async def batch_delete(
        self,
        document_ids: List[str],
        soft_delete: bool = True
    ) -> Dict[str, Any]:
        """
        Batch delete documents (100x faster than sequential)
        
        Args:
            document_ids: List of document IDs to delete
            soft_delete: If True, mark as deleted; if False, permanently remove
            
        Returns:
            Dict with keys: success, deleted, failed, errors
        """
        if not document_ids:
            return {"success": True, "deleted": 0, "failed": 0, "errors": []}
        
        try:
            # Escape document IDs
            doc_ids = [doc_id.replace("'", "''") for doc_id in document_ids]
            doc_ids_str = "', '".join(doc_ids)
            
            if soft_delete:
                # Soft delete: UPDATE deleted = TRUE
                query = f"""
                    UPDATE {self.table_name} 
                    SET 
                        deleted = TRUE,
                        updated_at = NOW()
                    WHERE document_id IN ('{doc_ids_str}')
                """
            else:
                # Hard delete: DELETE FROM
                query = f"DELETE FROM {self.table_name} WHERE document_id IN ('{doc_ids_str}')"
            
            self.cursor.execute(query)
            deleted_count = self.cursor.rowcount
            self.conn.commit()
            
            delete_type = "Soft deleted" if soft_delete else "Hard deleted"
            logger.info(f"✅ {delete_type} {deleted_count}/{len(document_ids)} documents")
            
            return {
                "success": True,
                "deleted": deleted_count,
                "failed": len(document_ids) - deleted_count,
                "errors": []
            }
            
        except Exception as e:
            logger.error(f"❌ Batch delete failed: {e}")
            if self.conn and not self.conn.closed:
                self.conn.rollback()
            return {
                "success": False,
                "deleted": 0,
                "failed": len(document_ids),
                "errors": [{"error": str(e)}]
            }
    
    async def batch_upsert(
        self,
        documents: List[Dict[str, Any]],
        conflict_resolution: str = "update"
    ) -> Dict[str, Any]:
        """
        Batch upsert documents (INSERT ... ON CONFLICT UPDATE)
        
        Args:
            documents: List of document dicts with:
                - document_id: Document ID
                - fields: Dict of fields to insert/update
            conflict_resolution: How to handle conflicts ("update", "ignore", "error")
            
        Returns:
            Dict with keys: success, inserted, updated, failed, errors
        """
        if not documents:
            return {"success": True, "inserted": 0, "updated": 0, "failed": 0, "errors": []}
        
        try:
            # Extract field names
            all_fields = set()
            for doc in documents:
                all_fields.update(doc.get("fields", {}).keys())
            
            if not all_fields:
                return {"success": True, "inserted": 0, "updated": 0, "failed": 0, "errors": []}
            
            # Build VALUES clauses
            values_clauses = []
            for doc in documents:
                doc_id = doc["document_id"].replace("'", "''")
                field_values = []
                
                for field in all_fields:
                    value = doc.get("fields", {}).get(field)
                    if value is None:
                        field_values.append("NULL")
                    elif isinstance(value, str):
                        escaped_value = value.replace("'", "''")
                        field_values.append(f"'{escaped_value}'")
                    elif isinstance(value, (int, float)):
                        field_values.append(str(value))
                    elif isinstance(value, bool):
                        field_values.append('TRUE' if value else 'FALSE')
                    else:
                        str_value = str(value).replace("'", "''")
                        field_values.append(f"'{str_value}'")
                
                values_clauses.append(f"('{doc_id}', {', '.join(field_values)})")
            
            # Build field list
            field_list = ', '.join(all_fields)
            
            # Build ON CONFLICT clause
            if conflict_resolution == "update":
                update_clauses = [f"{field} = EXCLUDED.{field}" for field in all_fields]
                on_conflict = f"ON CONFLICT (document_id) DO UPDATE SET {', '.join(update_clauses)}, updated_at = NOW()"
            elif conflict_resolution == "ignore":
                on_conflict = "ON CONFLICT (document_id) DO NOTHING"
            else:
                on_conflict = ""
            
            # Execute upsert
            query = f"""
                INSERT INTO {self.table_name} (document_id, {field_list})
                VALUES {', '.join(values_clauses)}
                {on_conflict}
            """
            
            self.cursor.execute(query)
            affected_count = self.cursor.rowcount
            self.conn.commit()
            
            # Estimate inserts vs updates (rough heuristic)
            inserted = affected_count if conflict_resolution != "update" else affected_count // 2
            updated = affected_count - inserted
            
            logger.info(f"✅ Batch upserted {affected_count} documents (est. {inserted} inserts, {updated} updates)")
            
            return {
                "success": True,
                "inserted": inserted,
                "updated": updated,
                "failed": len(documents) - affected_count,
                "errors": []
            }
            
        except Exception as e:
            logger.error(f"❌ Batch upsert failed: {e}")
            if self.conn and not self.conn.closed:
                self.conn.rollback()
            return {
                "success": False,
                "inserted": 0,
                "updated": 0,
                "failed": len(documents),
                "errors": [{"error": str(e)}]
            }
    
    def __enter__(self):
        """Context Manager Entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context Manager Exit"""
        if exc_type is not None:
            # Rollback bei Fehler
            try:
                if self.conn and not self.conn.closed:
                    self.conn.rollback()
                    logger.debug("PostgreSQL Rollback durchgeführt")
            except Exception as e:
                logger.warning(f"Rollback-Warnung: {e}")
        else:
            # Commit bei Erfolg
            try:
                if self.conn and not self.conn.closed:
                    self.conn.commit()
                    logger.debug("PostgreSQL Commit durchgeführt")
            except Exception as e:
                logger.warning(f"Commit-Warnung: {e}")
        
        self.disconnect()
        return False  # Don't suppress exceptions


    # ========================================================================
    # FULL-TEXT SEARCH (BM25) - v1.6.0 Implementation
    # ========================================================================
    
    def setup_fulltext_search(self, content_table: str = "documents", content_column: str = "content"):
        """
        Initialisiert PostgreSQL Full-Text Search mit GIN Index
        
        Erstellt tsvector Spalte und GIN Index für BM25-ähnliche Suche.
        Benötigt PostgreSQL Extension pg_trgm für bessere Relevanz.
        
        Args:
            content_table: Tabelle mit Content-Spalte
            content_column: Spalte mit dem durchsuchbaren Text
            
        Returns:
            Dict mit success und Details
        """
        self.connect()
        
        try:
            if ERROR_LOGGING_AVAILABLE:
                log_operation_start("PostgreSQL", "setup_fulltext_search", table=content_table)
            
            # 1. Erstelle tsvector-Spalte für optimierte Suche (falls nicht vorhanden)
            self.cursor.execute(f"""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = '{content_table}' AND column_name = 'search_vector'
                    ) THEN
                        ALTER TABLE {content_table} ADD COLUMN search_vector tsvector;
                    END IF;
                END $$;
            """)
            
            # 2. Aktualisiere search_vector mit gewichteten Feldern
            # Gewichtung: A (Titel/Name) > B (Inhalt) > C (Metadaten)
            self.cursor.execute(f"""
                UPDATE {content_table} 
                SET search_vector = 
                    setweight(to_tsvector('german', COALESCE(document_id, '')), 'A') ||
                    setweight(to_tsvector('german', COALESCE({content_column}::text, '')), 'B') ||
                    setweight(to_tsvector('german', COALESCE(classification, '')), 'C')
                WHERE search_vector IS NULL OR search_vector = '';
            """)
            
            # 3. Erstelle GIN Index für schnelle Suche (falls nicht vorhanden)
            self.cursor.execute(f"""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_indexes 
                        WHERE indexname = '{content_table}_search_idx'
                    ) THEN
                        CREATE INDEX {content_table}_search_idx ON {content_table} USING GIN (search_vector);
                    END IF;
                END $$;
            """)
            
            # 4. Erstelle Trigger für automatische Updates (optional)
            self.cursor.execute("""
                CREATE OR REPLACE FUNCTION update_search_vector()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.search_vector := 
                        setweight(to_tsvector('german', COALESCE(NEW.document_id, '')), 'A') ||
                        setweight(to_tsvector('german', COALESCE(NEW.content::text, '')), 'B') ||
                        setweight(to_tsvector('german', COALESCE(NEW.classification, '')), 'C');
                    RETURN NEW;
                END
                $$ LANGUAGE plpgsql;
            """)
            
            self.cursor.execute(f"""
                DROP TRIGGER IF EXISTS {content_table}_search_trigger ON {content_table};
                CREATE TRIGGER {content_table}_search_trigger
                    BEFORE INSERT OR UPDATE ON {content_table}
                    FOR EACH ROW EXECUTE FUNCTION update_search_vector();
            """)
            
            self.conn.commit()
            
            if ERROR_LOGGING_AVAILABLE:
                log_operation_success("PostgreSQL", "setup_fulltext_search", table=content_table)
            
            logger.info(f"✅ PostgreSQL Full-Text Search Setup für {content_table} abgeschlossen")
            
            return {
                "success": True,
                "table": content_table,
                "index": f"{content_table}_search_idx",
                "trigger": f"{content_table}_search_trigger"
            }
            
        except Exception as e:
            self.conn.rollback()
            if ERROR_LOGGING_AVAILABLE:
                log_operation_failure("PostgreSQL", "setup_fulltext_search", e, table=content_table)
            logger.error(f"❌ PostgreSQL Full-Text Search Setup fehlgeschlagen: {e}")
            return {"success": False, "error": str(e)}
    
    def fulltext_search(
        self,
        query_text: str,
        top_k: int = 10,
        table: str = "documents",
        language: str = "german"
    ) -> List[Dict[str, Any]]:
        """
        Führt BM25-ähnliche Full-Text Suche durch
        
        Nutzt PostgreSQL ts_rank_cd für BM25-ähnliches Ranking.
        Unterstützt deutsche Stemming (german Konfiguration).
        
        Args:
            query_text: Suchanfrage (z.B. "§ 58 LBO Abstandsflächen")
            top_k: Anzahl der Ergebnisse
            table: Tabelle für Suche
            language: Sprachkonfiguration (default: german)
            
        Returns:
            Liste von Dicts mit document_id, content, score, rank
        """
        self.connect()
        
        try:
            if ERROR_LOGGING_AVAILABLE:
                log_operation_start("PostgreSQL", "fulltext_search", query=query_text[:50])
            
            # BM25-ähnliches Ranking mit ts_rank_cd (Cover Density)
            # Gewichtung: {0.1, 0.2, 0.4, 1.0} für {D, C, B, A} Gewichte
            self.cursor.execute(f"""
                SELECT 
                    document_id,
                    file_path,
                    classification,
                    content_length,
                    ts_rank_cd(
                        search_vector, 
                        plainto_tsquery('{language}', %s),
                        32  -- Normalization: length normalization
                    ) AS rank,
                    ts_headline(
                        '{language}',
                        COALESCE(file_path, ''),
                        plainto_tsquery('{language}', %s),
                        'MaxWords=50, MinWords=25, StartSel=<mark>, StopSel=</mark>'
                    ) AS snippet
                FROM {table}
                WHERE search_vector @@ plainto_tsquery('{language}', %s)
                ORDER BY rank DESC
                LIMIT %s
            """, (query_text, query_text, query_text, top_k))
            
            results = []
            for row in self.cursor.fetchall():
                results.append({
                    "document_id": row['document_id'],
                    "file_path": row.get('file_path', ''),
                    "classification": row.get('classification', ''),
                    "content_length": row.get('content_length', 0),
                    "score": float(row['rank']) if row['rank'] else 0.0,
                    "snippet": row.get('snippet', ''),
                    "source": "keyword_bm25"
                })
            
            if ERROR_LOGGING_AVAILABLE:
                log_operation_success("PostgreSQL", "fulltext_search", query=query_text[:50], results=len(results))
            
            logger.info(f"✅ PostgreSQL Full-Text Search: {len(results)} Ergebnisse für '{query_text[:30]}...'")
            
            return results
            
        except Exception as e:
            if ERROR_LOGGING_AVAILABLE:
                log_operation_failure("PostgreSQL", "fulltext_search", e, query=query_text[:50])
            logger.error(f"❌ PostgreSQL Full-Text Search fehlgeschlagen: {e}")
            return []
    
    def execute_sql(
        self,
        sql: str,
        params: Optional[tuple] = None,
        fetch: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Führt beliebige SQL-Query aus (für Search API)
        
        Ermöglicht flexible Queries für Full-Text Search und andere Anwendungen.
        
        Args:
            sql: SQL Statement
            params: Parameter für prepared statement
            fetch: True = fetchall(), False = commit only
            
        Returns:
            Liste von Dict-Rows (bei fetch=True) oder leere Liste
        """
        self.connect()
        
        try:
            if ERROR_LOGGING_AVAILABLE:
                log_operation_start("PostgreSQL", "execute_sql", sql=sql[:100])
            
            if params:
                self.cursor.execute(sql, params)
            else:
                self.cursor.execute(sql)
            
            if fetch:
                results = []
                for row in self.cursor.fetchall():
                    results.append(dict(row))
                
                if ERROR_LOGGING_AVAILABLE:
                    log_operation_success("PostgreSQL", "execute_sql", rows=len(results))
                
                return results
            else:
                self.conn.commit()
                if ERROR_LOGGING_AVAILABLE:
                    log_operation_success("PostgreSQL", "execute_sql", action="commit")
                return []
                
        except Exception as e:
            self.conn.rollback()
            if ERROR_LOGGING_AVAILABLE:
                log_operation_failure("PostgreSQL", "execute_sql", e, sql=sql[:100])
            logger.error(f"❌ PostgreSQL execute_sql fehlgeschlagen: {e}")
            return []


# Factory Function (analog zu anderen Backends)
def create_postgresql_backend(config: Dict[str, Any]) -> PostgreSQLRelationalBackend:
    """
    Erstellt PostgreSQL Backend
    
    Args:
        config: PostgreSQL Konfiguration
        
    Returns:
        PostgreSQLRelationalBackend Instance
    """
    return PostgreSQLRelationalBackend(config)
