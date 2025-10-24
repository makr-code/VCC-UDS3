"""
UDS3 Lokale Konfiguration (erbt von config.py Base Classes)

Diese Datei implementiert/erbt von den Basis-Konfigurationsklassen aus config.py
und überschreibt diese mit produktiven Remote-Verbindungsdaten.

WICHTIG: Diese Datei wird NICHT ins Git committed (in .gitignore).
Sie enthält lokale/produktive Verbindungsdetails.

Design Pattern: Factory/Dataclass Inheritance
"""

from config import PolyglotPersistenceConfig, DatabaseConfig, FeatureConfig, OptimizationConfig, GeoConfig

def get_polyglot_config() -> PolyglotPersistenceConfig:
    """Erstellt produktive Polyglot Persistence Konfiguration."""
    return PolyglotPersistenceConfig(
        # PostgreSQL/PostGIS Remote Server  
        postgis=DatabaseConfig(
            host="192.168.178.94",
            port=5432,
            user="postgres", 
            password="postgres",  # ECHTES Passwort
            database="uds3_geo",
            provider="postgresql"
        ),
        
        # ChromaDB Remote Server
        vector=DatabaseConfig(
            host="192.168.178.94",
            port=8000,
            user="chroma",
            password="",  # ChromaDB meist ohne Auth
            provider="chromadb"
        ),
        
        # Neo4j Remote Server
        graph=DatabaseConfig(
            host="192.168.178.94",
            port=7687,
            user="neo4j",
            password="neo4jneo4j",  # ECHTES Neo4j Passwort
            database="neo4j",
            provider="neo4j"
        ),
        
        # PostgreSQL Relational Remote
        relational=DatabaseConfig(
            host="192.168.178.94",
            port=5432,
            user="postgres",
            password="postgres",  # ECHTES Passwort
            database="veritas_db",
            provider="postgresql"
        ),
        
        # CouchDB Remote Server (Docker Port Forwarding)
        file=DatabaseConfig(
            host="192.168.178.94",
            port=32770,  # Docker: 32770 → 5984/TCP
            user="admin",
            password="admin",  # ECHTES CouchDB Passwort  
            provider="couchdb"
        )
    )

def get_feature_config() -> FeatureConfig:
    """Erstellt produktive Feature-Konfiguration."""
    return FeatureConfig(
        expect_uds3_backend=True,  # Produktives Backend
        debug_mode=False,          # Debug deaktiviert in Produktion
        use_stubs=False,           # Echte Implementierungen
        enable_logging=True,       # Logging aktiviert
        auto_fallback=True         # Fallback aktiviert
    )

def get_optimization_config() -> OptimizationConfig:
    """Erstellt produktive Optimierungs-Konfiguration."""
    return OptimizationConfig(
        batch_size=1000,              # Größere Batches für Remote
        vector_batch_size=200,        # Optimiert für Remote Vector DB
        connection_pool_size=20,      # Größere Pools für Produktion
        query_timeout=60,             # Längere Timeouts für Remote
        cache_ttl=600                 # Längere Cache-Zeit
    )

def get_geo_config() -> GeoConfig:
    """Erstellt produktive Geo-Konfiguration."""
    return GeoConfig(
        auto_extract=True,
        quality_threshold=0.7,        # Höhere Qualitätsschwelle
        default_srid=4326,
        enable_spatial_index=True
    )

# Legacy Compatibility - falls alte imports vorhanden sind
DATABASES_LEGACY = {
    "postgis": {
        "host": "192.168.178.94",
        "port": 5432,
        "database": "uds3_geo", 
        "user": "postgres",
        "password": "postgres",
        "connect_timeout": 10,
    },
    "vector": {
        "provider": "chromadb",
        "host": "192.168.178.94",
        "port": 8000,
        "uri": "http://192.168.178.94:8000",
        "api_key": "",
        "user": "chroma",
        "password": ""
    },
    "graph": {
        "provider": "neo4j",
        "host": "192.168.178.94", 
        "port": 7687,
        "uri": "bolt://192.168.178.94:7687",
        "user": "neo4j",
        "password": "neo4jneo4j",
    },
    "relational": {
        "provider": "postgresql",
        "host": "192.168.178.94",
        "port": 5432,
        "uri": "192.168.178.94:5432", 
        "database": "veritas_db",
        "user": "postgres",
        "password": "postgres",
    },
    "file": {
        "provider": "couchdb",
        "host": "192.168.178.94",
        "port": 32770,  # Docker Port Forwarding: 32770 → 5984/TCP
        "uri": "http://192.168.178.94:32770",
        "user": "admin", 
        "password": "admin"
    }
}
