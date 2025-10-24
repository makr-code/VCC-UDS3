#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
manager.py

manager.py
UDS3 API Manager - Unified API Interface
========================================
Konsolidierte API-Schnittstelle für alle UDS3-Komponenten
Dieses Modul bietet eine einheitliche API-Schnittstelle für:
- Database Operations (Vector, Graph, Relational, File Storage)
- CRUD Operations (Basic, Advanced, Batch)
- Streaming Operations
- Archive Operations
- SAGA Pattern Implementation
- Query & Filter Systems
Author: UDS3 Team
Date: 24. Oktober 2025
Version: 3.1.0
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
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

# Core imports
from core.schemas import UDS3DatabaseSchemasMixin

# Operational imports
try:
    from api.crud import AdvancedCRUDManager
    from manager.streaming import StreamingManager
    from manager.archive import ArchiveManager
    from manager.saga import SagaOrchestrator
    ADVANCED_OPERATIONS_AVAILABLE = True
except ImportError:
    ADVANCED_OPERATIONS_AVAILABLE = False


@dataclass
class APIConfiguration:
    """Konfiguration für UDS3 API"""
    enable_streaming: bool = True
    enable_archive: bool = True
    enable_saga: bool = True
    enable_advanced_crud: bool = True
    log_level: str = "INFO"
    max_concurrent_operations: int = 10
    default_timeout: int = 30


class UDS3APIError(Exception):
    """Base exception für UDS3 API Fehler"""
    pass


class UDS3APIManager:
    """
    Unified API Manager für UDS3
    
    Zentraler Zugriffspunkt für alle UDS3-Funktionalitäten mit:
    - Einheitliche Fehlerbehandlung
    - Logging und Monitoring
    - Configuration Management
    - Operation Orchestration
    """
    
    def __init__(self, config: Optional[APIConfiguration] = None):
        """
        Initialisiert den UDS3 API Manager
        
        Args:
            config: API-Konfiguration (optional)
        """
        self.config = config or APIConfiguration()
        self._setup_logging()
        
        # Core components
        self.database_strategy = None
        self.crud_manager = None
        self.streaming_manager = None
        self.archive_manager = None
        self.saga_orchestrator = None
        
        # Initialize components
        self._initialize_components()
    
    def _setup_logging(self):
        """Konfiguriert Logging für API Manager"""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(getattr(logging, self.config.log_level))
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def _initialize_components(self):
        """Initialisiert alle verfügbaren Komponenten"""
        try:
            # Core database strategy (lazy import to avoid circular imports)
            from core.database import UnifiedDatabaseStrategy
            self.database_strategy = UnifiedDatabaseStrategy()
            self.logger.info("✅ Database strategy initialized")
            
            # Advanced operations
            if ADVANCED_OPERATIONS_AVAILABLE:
                if self.config.enable_advanced_crud:
                    self.crud_manager = AdvancedCRUDManager(self.database_strategy)
                    
                if self.config.enable_streaming:
                    self.streaming_manager = StreamingManager(self.database_strategy)
                    
                if self.config.enable_archive:
                    self.archive_manager = ArchiveManager(self.database_strategy)
                    
                if self.config.enable_saga:
                    self.saga_orchestrator = SagaOrchestrator()
                
                self.logger.info("✅ Advanced operations initialized")
            else:
                self.logger.warning("⚠️ Advanced operations not available")
                
        except Exception as e:
            self.logger.error(f"❌ Component initialization failed: {e}")
            raise UDS3APIError(f"Failed to initialize components: {e}")
    
    # Database Operations API
    def create_document(self, document: Dict[str, Any]) -> str:
        """
        Erstellt ein neues Dokument in der Datenbank
        
        Args:
            document: Dokument-Daten
            
        Returns:
            str: Dokument-ID
        """
        try:
            if not self.database_strategy:
                raise UDS3APIError("Database strategy not initialized")
            
            result = self.database_strategy.store_document(document)
            self.logger.info(f"✅ Document created: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Document creation failed: {e}")
            raise UDS3APIError(f"Document creation failed: {e}")
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Ruft ein Dokument aus der Datenbank ab
        
        Args:
            document_id: ID des Dokuments
            
        Returns:
            Dict: Dokument-Daten oder None
        """
        try:
            if not self.database_strategy:
                raise UDS3APIError("Database strategy not initialized")
            
            result = self.database_strategy.get_document(document_id)
            self.logger.info(f"✅ Document retrieved: {document_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Document retrieval failed: {e}")
            raise UDS3APIError(f"Document retrieval failed: {e}")
    
    def search_documents(self, query: str, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Durchsucht Dokumente in der Datenbank
        
        Args:
            query: Suchquery
            filters: Zusätzliche Filter
            
        Returns:
            List: Suchergebnisse
        """
        try:
            if not self.database_strategy:
                raise UDS3APIError("Database strategy not initialized")
            
            result = self.database_strategy.search_documents(query, filters or {})
            self.logger.info(f"✅ Search completed: {len(result)} results")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Search failed: {e}")
            raise UDS3APIError(f"Search failed: {e}")
    
    # Advanced CRUD Operations API
    def batch_create(self, documents: List[Dict]) -> List[str]:
        """
        Erstellt mehrere Dokumente in einem Batch
        
        Args:
            documents: Liste von Dokumenten
            
        Returns:
            List: Liste der Dokument-IDs
        """
        if not self.crud_manager:
            raise UDS3APIError("Advanced CRUD not available")
        
        try:
            result = self.crud_manager.batch_create(documents)
            self.logger.info(f"✅ Batch create completed: {len(result)} documents")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Batch create failed: {e}")
            raise UDS3APIError(f"Batch create failed: {e}")
    
    # Streaming Operations API
    def stream_upload(self, file_path: str, metadata: Optional[Dict] = None) -> str:
        """
        Lädt eine große Datei über Streaming hoch
        
        Args:
            file_path: Pfad zur Datei
            metadata: Zusätzliche Metadaten
            
        Returns:
            str: Upload-ID
        """
        if not self.streaming_manager:
            raise UDS3APIError("Streaming operations not available")
        
        try:
            result = self.streaming_manager.stream_upload(file_path, metadata or {})
            self.logger.info(f"✅ Stream upload started: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Stream upload failed: {e}")
            raise UDS3APIError(f"Stream upload failed: {e}")
    
    # Archive Operations API
    def archive_document(self, document_id: str, retention_days: Optional[int] = None) -> bool:
        """
        Archiviert ein Dokument
        
        Args:
            document_id: ID des Dokuments
            retention_days: Aufbewahrungsdauer in Tagen
            
        Returns:
            bool: Erfolg der Archivierung
        """
        if not self.archive_manager:
            raise UDS3APIError("Archive operations not available")
        
        try:
            result = self.archive_manager.archive_document(document_id, retention_days)
            self.logger.info(f"✅ Document archived: {document_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Archive failed: {e}")
            raise UDS3APIError(f"Archive failed: {e}")
    
    # Health Check & Status
    def health_check(self) -> Dict[str, Any]:
        """
        Führt einen Health Check aller Komponenten durch
        
        Returns:
            Dict: Status aller Komponenten
        """
        status = {
            "timestamp": datetime.now().isoformat(),
            "api_version": "3.1.0",
            "components": {}
        }
        
        # Database strategy
        status["components"]["database"] = {
            "available": self.database_strategy is not None,
            "status": "healthy" if self.database_strategy else "unavailable"
        }
        
        # Advanced operations
        status["components"]["advanced_crud"] = {
            "available": self.crud_manager is not None,
            "status": "healthy" if self.crud_manager else "unavailable"
        }
        
        status["components"]["streaming"] = {
            "available": self.streaming_manager is not None,
            "status": "healthy" if self.streaming_manager else "unavailable"
        }
        
        status["components"]["archive"] = {
            "available": self.archive_manager is not None,
            "status": "healthy" if self.archive_manager else "unavailable"
        }
        
        status["components"]["saga"] = {
            "available": self.saga_orchestrator is not None,
            "status": "healthy" if self.saga_orchestrator else "unavailable"
        }
        
        # Overall status
        all_critical_healthy = (
            status["components"]["database"]["available"]
        )
        
        status["overall_status"] = "healthy" if all_critical_healthy else "degraded"
        
        return status
    
    def get_api_info(self) -> Dict[str, Any]:
        """
        Gibt Informationen über die verfügbare API zurück
        
        Returns:
            Dict: API-Informationen
        """
        return {
            "name": "UDS3 Unified API",
            "version": "3.1.0",
            "description": "Unified Database Strategy v3 API",
            "endpoints": {
                "database": {
                    "create_document": "Erstellt neues Dokument",
                    "get_document": "Ruft Dokument ab",
                    "search_documents": "Durchsucht Dokumente"
                },
                "advanced_crud": {
                    "batch_create": "Batch-Erstellung von Dokumenten",
                    "batch_update": "Batch-Update von Dokumenten",
                    "conditional_update": "Bedingte Updates"
                },
                "streaming": {
                    "stream_upload": "Streaming-Upload großer Dateien",
                    "stream_download": "Streaming-Download"
                },
                "archive": {
                    "archive_document": "Dokument archivieren",
                    "restore_document": "Dokument wiederherstellen"
                }
            },
            "configuration": {
                "streaming_enabled": self.config.enable_streaming,
                "archive_enabled": self.config.enable_archive,
                "saga_enabled": self.config.enable_saga,
                "advanced_crud_enabled": self.config.enable_advanced_crud
            }
        }


# Factory function für einfache Nutzung
def create_uds3_api(config: Optional[APIConfiguration] = None) -> UDS3APIManager:
    """
    Factory-Funktion zur Erstellung eines UDS3 API Managers
    
    Args:
        config: Optional API-Konfiguration
        
    Returns:
        UDS3APIManager: Initialisierte API-Instanz
    """
    return UDS3APIManager(config)


# Default API instance für direkten Import
default_api = None

def get_default_api() -> UDS3APIManager:
    """
    Gibt die Standard-API-Instanz zurück
    
    Returns:
        UDS3APIManager: Standard API-Instanz
    """
    global default_api
    if default_api is None:
        default_api = create_uds3_api()
    return default_api


if __name__ == "__main__":
    # Demo der API
    print("UDS3 API Manager Demo")
    print("====================")
    
    # API erstellen
    api = create_uds3_api()
    
    # Health Check
    health = api.health_check()
    print(f"Health Status: {health['overall_status']}")
    
    # API Info
    info = api.get_api_info()
    print(f"API Version: {info['version']}")
    
    print("✅ API Demo completed")