"""Zentrale Konfigurationsdatei für das UDS3 Projekt.

Diese Datei enthält Basis-Konfigurationsklassen und Factory-Pattern für alle 
Adapter (Datenbanken, Geo, Identity, Security, Quality, Batch-Optimierungen etc.).

Design Pattern:
- Basiskonfigurationen als Dataclasses/Factories
- config_local.py erbt/implementiert davon für produktive Umgebungen
- Keine Umgebungsvariablen direkt im Code
- Overrides durch Vererbung in config_local.py
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

@dataclass
class DatabaseConfig:
    """Basis-Datenbankkonfiguration für lokale/Stub-Umgebungen."""
    host: str
    port: int
    user: str
    password: str
    database: str = ""
    provider: str = ""
    uri: str = ""
    api_key: str = ""
    connect_timeout: int = 10
    
    def __post_init__(self):
        """Generiere URI falls nicht gesetzt."""
        if not self.uri and self.provider:
            if self.provider == "neo4j":
                self.uri = f"bolt://{self.host}:{self.port}"
            elif self.provider == "postgresql":
                self.uri = f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
            elif self.provider == "couchdb":
                self.uri = f"http://{self.host}:{self.port}"
            elif self.provider == "chromadb":
                self.uri = f"http://{self.host}:{self.port}"

@dataclass 
class PolyglotPersistenceConfig:
    """Factory für Polyglot Persistence Konfiguration."""
    postgis: DatabaseConfig = field(default_factory=lambda: DatabaseConfig(
        host="localhost", port=5432, user="postgres", password="test",
        database="uds3_geo_local", provider="postgresql"
    ))
    
    vector: DatabaseConfig = field(default_factory=lambda: DatabaseConfig(
        host="localhost", port=8000, user="local", password="test",
        provider="chromadb"
    ))
    
    graph: DatabaseConfig = field(default_factory=lambda: DatabaseConfig(
        host="localhost", port=7687, user="neo4j", password="test", 
        database="neo4j", provider="neo4j"
    ))
    
    relational: DatabaseConfig = field(default_factory=lambda: DatabaseConfig(
        host="localhost", port=5432, user="postgres", password="test",
        database="uds3_local", provider="postgresql"
    ))
    
    file: DatabaseConfig = field(default_factory=lambda: DatabaseConfig(
        host="localhost", port=5984, user="admin", password="test",
        provider="couchdb"
    ))
    
    def to_legacy_dict(self) -> Dict[str, Dict[str, Any]]:
        """Konvertiert zu Legacy-Dictionary Format für Abwärtskompatibilität."""
        return {
            "postgis": {
                "host": self.postgis.host,
                "port": self.postgis.port,
                "database": self.postgis.database,
                "user": self.postgis.user,
                "password": self.postgis.password,
                "connect_timeout": self.postgis.connect_timeout,
            },
            "vector": {
                "provider": self.vector.provider,
                "host": self.vector.host,
                "port": self.vector.port,
                "uri": self.vector.uri,
                "api_key": self.vector.api_key,
                "user": self.vector.user,
                "password": self.vector.password
            },
            "graph": {
                "provider": self.graph.provider,
                "host": self.graph.host,
                "port": self.graph.port,
                "uri": self.graph.uri,
                "user": self.graph.user,
                "password": self.graph.password,
            },
            "relational": {
                "provider": self.relational.provider,
                "host": self.relational.host,
                "port": self.relational.port,
                "uri": self.relational.uri,
                "database": self.relational.database,
                "user": self.relational.user,
                "password": self.relational.password,
            },
            "file": {
                "provider": self.file.provider,
                "host": self.file.host,
                "port": self.file.port,
                "uri": self.file.uri,
                "user": self.file.user,
                "password": self.file.password
            }
        }

@dataclass
class FeatureConfig:
    """Basis Feature-Flags für lokale Entwicklungsumgebung."""
    expect_uds3_backend: bool = False  # Local development mode
    debug_mode: bool = True           # Enable debug features for local development
    use_stubs: bool = True           # Use stub implementations for testing
    enable_logging: bool = True      # Enable detailed logging
    auto_fallback: bool = True       # Enable automatic fallbacks

@dataclass
class OptimizationConfig:
    """Basis-Optimierungseinstellungen für lokale Umgebung."""
    batch_size: int = 500
    vector_batch_size: int = 100
    connection_pool_size: int = 5    # Kleinere Pools für lokale Entwicklung
    query_timeout: int = 30          # Timeout in Sekunden
    cache_ttl: int = 300            # Cache TTL in Sekunden

@dataclass 
class GeoConfig:
    """Basis-Geo-Einstellungen."""
    auto_extract: bool = True
    quality_threshold: float = 0.5
    default_srid: int = 4326
    enable_spatial_index: bool = True


class UDS3ConfigFactory:
    """Factory für UDS3 Konfigurationsobjekte mit lokaler Override-Unterstützung."""
    
    def __init__(self):
        self._polyglot_config = None
        self._feature_config = None
        self._optimization_config = None
        self._geo_config = None
        self._load_configs()
    
    def _load_configs(self):
        """Lädt Basis-Configs und versucht lokale Overrides zu laden."""
        # Basis-Konfigurationen laden
        self._polyglot_config = PolyglotPersistenceConfig()
        self._feature_config = FeatureConfig()
        self._optimization_config = OptimizationConfig() 
        self._geo_config = GeoConfig()
        
        # Versuche lokale Overrides zu laden
        try:
            from . import config_local
            if hasattr(config_local, 'get_polyglot_config'):
                self._polyglot_config = config_local.get_polyglot_config()
            if hasattr(config_local, 'get_feature_config'):
                self._feature_config = config_local.get_feature_config()
            if hasattr(config_local, 'get_optimization_config'):
                self._optimization_config = config_local.get_optimization_config()
            if hasattr(config_local, 'get_geo_config'):
                self._geo_config = config_local.get_geo_config()
        except ImportError:
            # config_local.py nicht vorhanden - verwende Standard-Konfiguration
            pass
    
    @property
    def polyglot(self) -> PolyglotPersistenceConfig:
        """Zugriff auf Polyglot Persistence Konfiguration."""
        return self._polyglot_config
    
    @property  
    def features(self) -> FeatureConfig:
        """Zugriff auf Feature-Konfiguration."""
        return self._feature_config
    
    @property
    def optimization(self) -> OptimizationConfig:
        """Zugriff auf Optimierungs-Konfiguration."""
        return self._optimization_config
    
    @property
    def geo(self) -> GeoConfig:
        """Zugriff auf Geo-Konfiguration."""
        return self._geo_config

# Globale Konfigurationsinstanz
config_factory = UDS3ConfigFactory()

# Legacy-Kompatibilität: Exportiere Dictionary-Versionen
DATABASES = config_factory.polyglot.to_legacy_dict()
FEATURES = {
    "expect_uds3_backend": config_factory.features.expect_uds3_backend,
    "debug_mode": config_factory.features.debug_mode,
    "use_stubs": config_factory.features.use_stubs,
    "enable_logging": config_factory.features.enable_logging,
    "auto_fallback": config_factory.features.auto_fallback,
}
OPTIMIZATION = {
    "batch_size": config_factory.optimization.batch_size,
    "vector_batch_size": config_factory.optimization.vector_batch_size,
    "connection_pool_size": config_factory.optimization.connection_pool_size,
    "query_timeout": config_factory.optimization.query_timeout,
    "cache_ttl": config_factory.optimization.cache_ttl,
}
GEO_SETTINGS = {
    "auto_extract": config_factory.geo.auto_extract,
    "quality_threshold": config_factory.geo.quality_threshold,
    "default_srid": config_factory.geo.default_srid,
    "enable_spatial_index": config_factory.geo.enable_spatial_index,
}
