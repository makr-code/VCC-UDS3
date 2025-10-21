"""
UDS3 Lokale Konfiguration (überschreibt config.py)

Diese Datei wird automatisch von config.py geladen und überschreibt
die Standard-Konfigurationswerte.

WICHTIG: Diese Datei wird NICHT ins Git committed (in .gitignore).
Sie enthält lokale/produktive Verbindungsdetails.
"""

from typing import Dict, Any

# Überschreibe DATABASES aus config.py mit Remote-Konfiguration
DATABASES: Dict[str, Dict[str, Any]] = {
    "postgis": {
        "host": "192.168.178.94",  # Remote PostgreSQL/PostGIS Server
        "port": 5432,
        "database": "uds3_geo",
        "user": "postgres",
        "password": "postgres",  # TODO: Aus Umgebungsvariable laden
        "connect_timeout": 10,
    },
    "vector": {
        "provider": "chromadb",
        "endpoint": "http://localhost:8000",  # ChromaDB läuft lokal
        "api_key": "",
    },
    "graph": {
        "provider": "neo4j",
        "uri": "bolt://192.168.178.94:7687",  # Remote Neo4j Server
        "user": "neo4j",
        "password": "neo4jneo4j",  # TODO: Aus Umgebungsvariable laden
    },
    "relational": {
        "provider": "postgresql",
        "host": "192.168.178.94",  # Remote PostgreSQL Server
        "port": 5432,
        "database": "veritas_db",
        "user": "postgres",
        "password": "postgres",  # TODO: Aus Umgebungsvariable laden
    },
    "couchdb": {
        "host": "192.168.178.94",  # Remote CouchDB Server
        "port": 5984,
        "database": "veritas_files",
        "user": "admin",
        "password": "admin",  # TODO: Aus Umgebungsvariable laden
    },
}

# Feature Flags
FEATURES: Dict[str, Any] = {
    "expect_uds3_backend": True,  # UDS3 läuft als produktives Backend
}

# Optimization Settings
OPTIMIZATION: Dict[str, Any] = {
    "batch_size": 1000,  # Größere Batches für Remote-DB
    "vector_batch_size": 200,
}
