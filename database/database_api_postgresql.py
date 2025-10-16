"""
PostgreSQL Relational Backend für UDS3

Implementiert PostgreSQL-Backend analog zu SQLiteRelationalBackend.
Verwendet für Corvina Backend die migrierte PostgreSQL-Datenbank.

Error-Handling:
- Connection Pool Management (Auto-Reconnect)
- Deadlock Detection + Retry
- Transaction Rollback bei Failures
- Structured Error Logging
"""

import logging
import psycopg2
import psycopg2.extras
import psycopg2.errors
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
    """PostgreSQL Backend für relationale Daten (Dokument-Metadaten)"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialisiert PostgreSQL Backend
        
        Args:
            config: PostgreSQL Konfiguration mit:
                - host: PostgreSQL Host (e.g., '192.168.178.94')
                - port: PostgreSQL Port (default: 5432)
                - user: Database User (e.g., 'postgres')
                - password: Database Password
                - database: Database Name (e.g., 'postgres')
                - schema: Schema Name (default: 'public')
        """
        self.config = config
        self.host = config.get('host', '192.168.178.94')
        self.port = config.get('port', 5432)
        self.user = config.get('user', 'postgres')
        self.password = config.get('password', 'postgres')
        self.database = config.get('database', 'postgres')
        self.schema = config.get('schema', 'public')
        
        self.conn = None
        self.cursor = None
        
        logger.info(f"PostgreSQL Backend initialisiert: {self.host}:{self.port}/{self.database}")
    
    
    def connect(self):
        """
        Verbindet zu PostgreSQL-Datenbank mit Error-Handling
        
        Features:
        - Auto-Reconnect bei Connection Loss
        - Retry-Logic (3 Versuche)
        - Structured Error Logging
        
        Returns:
            bool: True wenn erfolgreich verbunden
        
        Raises:
            Exception: Nach allen Retry-Versuchen
        """
        if self.conn is not None and not self.conn.closed:
            return True  # Bereits verbunden
        
        max_retries = 3
        base_delay = 1.0
        
        for retry in range(max_retries):
            try:
                if ERROR_LOGGING_AVAILABLE:
                    log_operation_start("PostgreSQL", "connect", host=self.host, port=self.port)
                
                self.conn = psycopg2.connect(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    connect_timeout=10  # 10s Timeout
                )
                self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                
                if ERROR_LOGGING_AVAILABLE:
                    log_operation_success("PostgreSQL", "connect", host=self.host, port=self.port)
                else:
                    logger.info(f"✅ PostgreSQL Verbindung hergestellt: {self.host}:{self.port}")
                
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
        """Schließt PostgreSQL-Verbindung"""
        try:
            if self.cursor:
                self.cursor.close()
                self.cursor = None
        except Exception as e:
            logger.warning(f"Warnung beim Schließen des Cursors: {e}")
        
        try:
            if self.conn and not self.conn.closed:
                self.conn.close()
                self.conn = None
            logger.debug("PostgreSQL Verbindung geschlossen")
        except Exception as e:
            logger.warning(f"Warnung beim Schließen der Verbindung: {e}")
    
    
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
