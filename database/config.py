#!/usr/bin/env python3

import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

class DatabaseType(Enum):
    """Database-Typen für modulares System"""
    VECTOR = "vector"
    GRAPH = "graph"
    RELATIONAL = "relational"
    FILE = "file"
    KEY_VALUE = "key_value"

class DatabaseBackend(Enum):
    """Verfügbare Database-Backends"""
    # Vector Databases
    CHROMADB = "chromadb"
    PINECONE = "pinecone"
    WEAVIATE = "weaviate"
    
    # Graph Databases
    NEO4J = "neo4j"
    ARANGODB = "arangodb"
    
    # Relational Databases
    POSTGRESQL = "postgresql"
    MONGODB = "mongodb"
    
    # Key-Value Databases
    REDIS = "redis"
    
    # File-based Backends
    COUCHDB = "couchdb"
    S3 = "s3"

@dataclass
class DatabaseConnection:
    """Einheitliche Database-Verbindungsparameter"""
    db_type: DatabaseType
    backend: DatabaseBackend
    enabled: bool = True
    
    # Standard Verbindungsparameter
    host: str = "localhost"
    port: int = 0
    username: str = ""
    password: str = ""
    database: str = ""
    
    # Dateipfad-basierte Backends
    path: str = ""
    
    # Zusätzliche Backend-spezifische Parameter
    settings: Dict[str, Any] = field(default_factory=dict)
    
    # Performance & Caching
    connection_pool_size: int = 10
    query_timeout: int = 30
    cache_ttl: int = 300
    
    def __post_init__(self):
        """Setze Standard-Ports basierend auf Backend"""
        if self.port == 0:
            self.port = self._get_default_port()
    
    def _get_default_port(self) -> int:
        """Standard-Ports für verschiedene Backends"""
        port_mapping = {
            DatabaseBackend.CHROMADB: 8000,
            DatabaseBackend.NEO4J: 7687,
            DatabaseBackend.POSTGRESQL: 5432,
            DatabaseBackend.MONGODB: 27017,
            DatabaseBackend.REDIS: 6379,
            DatabaseBackend.ARANGODB: 8529,
            DatabaseBackend.COUCHDB: 5984,
            DatabaseBackend.WEAVIATE: 8080,
            DatabaseBackend.PINECONE: 443,
        }
        return port_mapping.get(self.backend, 0)
    
    def get_connection_string(self) -> str:
        """Generiere Verbindungsstring für Backend"""
        if self.backend == DatabaseBackend.NEO4J:
            return f"bolt://{self.host}:{self.port}"
        elif self.backend == DatabaseBackend.POSTGRESQL:
            return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        elif self.backend == DatabaseBackend.MONGODB:
            return f"mongodb://{self.host}:{self.port}/{self.database}"
        elif self.backend == DatabaseBackend.REDIS:
            return f"redis://{self.host}:{self.port}/{self.settings.get('db', 0)}"
        else:
            return f"http://{self.host}:{self.port}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiere zu Dictionary für Legacy-Kompatibilität"""
        return {
            'enabled': self.enabled,
            'backend': self.backend.value,
            'host': self.host,
            'port': self.port,
            'username': self.username,
            'user': self.username,
            'password': self.password,
            'database': self.database,
            'path': self.path,
            'settings': self.settings,
            'connection_pool_size': self.connection_pool_size,
            'query_timeout': self.query_timeout,
            'cache_ttl': self.cache_ttl,
            'connection_string': self.get_connection_string()
        }

class BaseDatabaseManager(ABC):
    """Abstrakte Basis-Klasse für Database-Manager."""
    
    @abstractmethod
    def get_databases(self) -> List[DatabaseConnection]:
        """Abstrakte Methode für Database-Liste."""
        pass

class StubDatabaseManager(BaseDatabaseManager):
    """Stub/Localhost Database Manager für Entwicklungsumgebung."""
    
    def get_databases(self) -> List[DatabaseConnection]:
        """Liefert Localhost/Stub-Datenbank-Konfigurationen."""
        return [
            # Vector Database - ChromaDB LOCALHOST
            DatabaseConnection(
                db_type=DatabaseType.VECTOR,
                backend=DatabaseBackend.CHROMADB,
                host="localhost",
                port=8000,
                path="./chroma/uds3_vector_dev.db",
                settings={
                    'mode': 'persistent',
                    'similarity_threshold': 0.3,
                    'default_k': 5,
                }
            ),
            
            # Graph Database - Neo4j LOCALHOST  
            DatabaseConnection(
                db_type=DatabaseType.GRAPH,
                backend=DatabaseBackend.NEO4J,
                host="localhost",
                port=7687,
                username="neo4j",
                password="test",  # STUB-Passwort
                database="neo4j",
            ),
            
            # PostgreSQL LOCALHOST
            DatabaseConnection(
                db_type=DatabaseType.RELATIONAL,
                backend=DatabaseBackend.POSTGRESQL,
                host="localhost",
                port=5432,
                username="postgres",
                password="test",  # STUB-Passwort
                database="uds3_local",
            ),
            
            # CouchDB LOCALHOST
            DatabaseConnection(
                db_type=DatabaseType.FILE,
                backend=DatabaseBackend.COUCHDB,
                host="localhost",
                port=5984,
                username="admin",
                password="test",  # STUB-Passwort
                database="uds3_files_local",
            ),
            
            # Key-Value via PostgreSQL LOCALHOST
            DatabaseConnection(
                db_type=DatabaseType.KEY_VALUE,
                backend=DatabaseBackend.POSTGRESQL,
                host="localhost",
                port=5432,
                username="postgres",
                password="test",  # STUB-Passwort
                database="uds3_local",
                settings={'table': 'kv_store'}
            ),
        ]

class DatabaseManager:
    """Manager für Database-Konfigurationen mit Factory-Pattern."""
    
    def __init__(self, manager: BaseDatabaseManager = None):
        if manager is None:
            # Versuche lokale Database-Manager zu laden
            try:
                from . import database_config_local
                if hasattr(database_config_local, 'get_database_manager'):
                    self._manager = database_config_local.get_database_manager()
                else:
                    self._manager = StubDatabaseManager()
            except ImportError:
                # Fallback auf Stub-Manager
                self._manager = StubDatabaseManager()
        else:
            self._manager = manager
        
        self.databases: List[DatabaseConnection] = self._manager.get_databases()

    def get_database_backend_dict(self) -> Dict[str, Any]:
        """Legacy helper: Liefert ein dict mit Backend-Konfigurationen."""
        backend_map: Dict[str, Any] = {}
        for conn in self.databases:
            key = conn.db_type.value
            item = conn.to_dict()
            existing = backend_map.get(key)

            # Bevorzuge aktivierte Einträge
            if existing is None:
                backend_map[key] = item
            elif not existing.get('enabled', True) and item.get('enabled', True):
                backend_map[key] = item
        return backend_map
    
    def get_databases_by_type(self, db_type: DatabaseType) -> List[DatabaseConnection]:
        """Hole alle Datenbanken eines bestimmten Typs"""
        return [db for db in self.databases if db.db_type == db_type and db.enabled]
    
    def get_primary_database(self, db_type: DatabaseType) -> Optional[DatabaseConnection]:
        """Hole primäre Datenbank eines Typs (erste aktivierte)"""
        databases = self.get_databases_by_type(db_type)
        return databases[0] if databases else None
    
    def list_databases(self) -> str:
        """Erstelle lesbare Liste aller Datenbanken"""
        output = []
        for db_type in DatabaseType:
            databases = self.get_databases_by_type(db_type)
            output.append(f"\n{db_type.value.upper()} DATABASES:")
            if databases:
                for db in databases:
                    status = "✅ AKTIV" if db.enabled else "❌ DEAKTIVIERT"
                    output.append(f"  - {db.backend.value}: {status}")
                    output.append(f"    Connection: {db.get_connection_string()}")
            else:
                output.append("  - Keine Datenbanken konfiguriert")
        
        return "\n".join(output)

def get_database_backend_dict() -> Dict[str, Any]:
    """Module-level helper für Abwärtskompatibilität."""
    mgr = DatabaseManager()
    return mgr.get_database_backend_dict()

# Globale Instanz für einfache Verwendung
database_manager = DatabaseManager()

if __name__ == "__main__":
    # Test der neuen Konfiguration
    print("=== UDS3 DATABASE CONFIGURATION (STUB MODE) ===")
    print(database_manager.list_databases())
    
    print("\n=== LEGACY-KOMPATIBLE KONFIGURATION ===")
    legacy_config = get_database_backend_dict()
    for key, value in legacy_config.items():
        if isinstance(value, dict) and 'backend' in value:
            print(f"{key.upper()}: {value['backend']} ({value.get('connection_string', 'N/A')})")