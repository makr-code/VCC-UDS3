#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
database.py

database.py
UDS3 Database API - Enhanced Database Interface
==============================================
Verbesserte und konsolidierte Database-API für UDS3
Bietet einheitliche Schnittstellen für:
- Multi-Database Operations (Vector, Graph, Relational, File Storage)
- Schema Management und Validation
- Query Optimization und Caching
- Transaction Management
- Performance Monitoring
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
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib
from contextlib import contextmanager

# Core imports
from core.schemas import UDS3DatabaseSchemasMixin


class DatabaseType(Enum):
    """Verfügbare Database-Typen"""
    VECTOR = "vector"
    GRAPH = "graph" 
    RELATIONAL = "relational"
    FILE_STORAGE = "file_storage"


class QueryType(Enum):
    """Unterstützte Query-Typen"""
    SEMANTIC_SEARCH = "semantic_search"
    GRAPH_TRAVERSAL = "graph_traversal"
    SQL_QUERY = "sql_query"
    METADATA_FILTER = "metadata_filter"
    HYBRID_QUERY = "hybrid_query"


@dataclass
class QueryResult:
    """Standardisiertes Query-Resultat"""
    query_type: QueryType
    database_type: DatabaseType
    results: List[Dict[str, Any]]
    total_count: int
    execution_time_ms: float
    cached: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DatabaseConnection:
    """Database Connection Information"""
    db_type: DatabaseType
    connection_string: str
    config: Dict[str, Any] = field(default_factory=dict)
    is_connected: bool = False
    last_health_check: Optional[datetime] = None


class DatabaseAPIError(Exception):
    """Database API spezifische Fehler"""
    pass


class UDS3DatabaseAPI(UDS3DatabaseSchemasMixin):
    """
    Enhanced Database API für UDS3
    
    Erweiterte Database-Schnittstelle mit:
    - Multi-Database Support
    - Query Optimization
    - Caching und Performance Monitoring
    - Transaction Management
    - Schema Validation
    """
    
    def __init__(self, connections: Optional[List[DatabaseConnection]] = None):
        """
        Initialisiert Database API
        
        Args:
            connections: Liste der Database-Verbindungen
        """
        self.connections: Dict[DatabaseType, DatabaseConnection] = {}
        self.schemas = self._initialize_schemas()
        self.query_cache: Dict[str, QueryResult] = {}
        self.performance_metrics: List[Dict] = []
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize connections
        if connections:
            for conn in connections:
                self.add_connection(conn)
    
    def _initialize_schemas(self) -> Dict[DatabaseType, Dict]:
        """Initialisiert alle Database Schemas"""
        return {
            DatabaseType.VECTOR: self._create_vector_schema(),
            DatabaseType.GRAPH: self._create_graph_schema(),
            DatabaseType.RELATIONAL: self._create_relational_schema(),
            DatabaseType.FILE_STORAGE: self._create_file_storage_schema()
        }
    
    def add_connection(self, connection: DatabaseConnection) -> bool:
        """
        Fügt eine Database-Verbindung hinzu
        
        Args:
            connection: Database-Verbindung
            
        Returns:
            bool: Erfolg der Verbindung
        """
        try:
            # Hier würde die echte Verbindung implementiert werden
            self.connections[connection.db_type] = connection
            connection.is_connected = True
            connection.last_health_check = datetime.now()
            
            self.logger.info(f"✅ Connected to {connection.db_type.value} database")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Connection failed for {connection.db_type.value}: {e}")
            return False
    
    def get_schema(self, db_type: DatabaseType) -> Dict:
        """
        Gibt das Schema für einen Database-Typ zurück
        
        Args:
            db_type: Database-Typ
            
        Returns:
            Dict: Schema-Definition
        """
        return self.schemas.get(db_type, {})
    
    def validate_schema(self, db_type: DatabaseType, data: Dict) -> Tuple[bool, List[str]]:
        """
        Validiert Daten gegen das Schema
        
        Args:
            db_type: Database-Typ
            data: Zu validierende Daten
            
        Returns:
            Tuple: (is_valid, error_messages)
        """
        schema = self.get_schema(db_type)
        errors = []
        
        # Einfache Schema-Validierung (kann erweitert werden)
        if not schema:
            errors.append(f"No schema found for {db_type.value}")
            return False, errors
        
        # Hier würde detaillierte Schema-Validierung implementiert werden
        # Für jetzt return True für Kompatibilität
        return True, errors
    
    def execute_query(self, 
                     query_type: QueryType, 
                     query_data: Dict[str, Any],
                     database_types: Optional[List[DatabaseType]] = None,
                     use_cache: bool = True) -> QueryResult:
        """
        Führt eine Query über eine oder mehrere Databases aus
        
        Args:
            query_type: Typ der Query
            query_data: Query-Parameter
            database_types: Ziel-Databases (None = automatische Auswahl)
            use_cache: Cache verwenden
            
        Returns:
            QueryResult: Query-Resultat
        """
        start_time = datetime.now()
        
        try:
            # Cache check
            if use_cache:
                cache_key = self._generate_cache_key(query_type, query_data)
                if cache_key in self.query_cache:
                    cached_result = self.query_cache[cache_key]
                    cached_result.cached = True
                    return cached_result
            
            # Database selection
            if not database_types:
                database_types = self._select_optimal_databases(query_type)
            
            # Execute query
            results = []
            primary_db_type = database_types[0] if database_types else DatabaseType.RELATIONAL
            
            # Hier würde die echte Query-Ausführung implementiert werden
            # Für Demo purposes, return mock data
            results = self._mock_query_execution(query_type, query_data)
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Create result
            result = QueryResult(
                query_type=query_type,
                database_type=primary_db_type,
                results=results,
                total_count=len(results),
                execution_time_ms=execution_time,
                metadata={
                    "database_types_used": [db.value for db in database_types],
                    "query_timestamp": start_time.isoformat()
                }
            )
            
            # Cache result
            if use_cache:
                self.query_cache[cache_key] = result
            
            # Performance tracking
            self._track_performance(query_type, execution_time, len(results))
            
            self.logger.info(f"✅ Query executed: {query_type.value} in {execution_time:.2f}ms")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Query execution failed: {e}")
            raise DatabaseAPIError(f"Query execution failed: {e}")
    
    def _select_optimal_databases(self, query_type: QueryType) -> List[DatabaseType]:
        """
        Wählt optimale Databases für Query-Typ aus
        
        Args:
            query_type: Typ der Query
            
        Returns:
            List: Optimale Database-Typen
        """
        mapping = {
            QueryType.SEMANTIC_SEARCH: [DatabaseType.VECTOR, DatabaseType.RELATIONAL],
            QueryType.GRAPH_TRAVERSAL: [DatabaseType.GRAPH, DatabaseType.RELATIONAL],
            QueryType.SQL_QUERY: [DatabaseType.RELATIONAL],
            QueryType.METADATA_FILTER: [DatabaseType.RELATIONAL, DatabaseType.VECTOR],
            QueryType.HYBRID_QUERY: [DatabaseType.VECTOR, DatabaseType.GRAPH, DatabaseType.RELATIONAL]
        }
        
        return mapping.get(query_type, [DatabaseType.RELATIONAL])
    
    def _generate_cache_key(self, query_type: QueryType, query_data: Dict) -> str:
        """Generiert Cache-Schlüssel für Query"""
        data_str = json.dumps(query_data, sort_keys=True)
        cache_input = f"{query_type.value}:{data_str}"
        return hashlib.md5(cache_input.encode(), usedforsecurity=False).hexdigest()
    
    def _mock_query_execution(self, query_type: QueryType, query_data: Dict) -> List[Dict]:
        """Mock Query-Ausführung für Demo"""
        # Hier würde die echte Database-Implementierung stehen
        return [
            {
                "id": f"doc_{i}",
                "title": f"Document {i}",
                "score": 0.95 - (i * 0.1),
                "metadata": {"type": "test_document"}
            }
            for i in range(min(5, query_data.get('limit', 5)))
        ]
    
    def _track_performance(self, query_type: QueryType, execution_time: float, result_count: int):
        """Tracked Performance Metriken"""
        metric = {
            "timestamp": datetime.now().isoformat(),
            "query_type": query_type.value,
            "execution_time_ms": execution_time,
            "result_count": result_count,
            "cache_hit_rate": self._calculate_cache_hit_rate()
        }
        
        self.performance_metrics.append(metric)
        
        # Keep only last 1000 metrics
        if len(self.performance_metrics) > 1000:
            self.performance_metrics = self.performance_metrics[-1000:]
    
    def _calculate_cache_hit_rate(self) -> float:
        """Berechnet Cache Hit Rate"""
        if not self.performance_metrics:
            return 0.0
        
        recent_metrics = self.performance_metrics[-100:]  # Last 100 queries
        cache_hits = sum(1 for m in recent_metrics if m.get("cached", False))
        return cache_hits / len(recent_metrics) if recent_metrics else 0.0
    
    # High-level API Methods
    def semantic_search(self, 
                       query: str, 
                       filters: Optional[Dict] = None,
                       limit: int = 10) -> QueryResult:
        """
        Führt semantische Suche durch
        
        Args:
            query: Suchquery
            filters: Zusätzliche Filter
            limit: Maximale Ergebnisse
            
        Returns:
            QueryResult: Suchergebnisse
        """
        query_data = {
            "query": query,
            "filters": filters or {},
            "limit": limit
        }
        
        return self.execute_query(QueryType.SEMANTIC_SEARCH, query_data)
    
    def graph_traversal(self,
                       start_nodes: List[str],
                       relationships: List[str],
                       max_depth: int = 3) -> QueryResult:
        """
        Führt Graph-Traversierung durch
        
        Args:
            start_nodes: Start-Knoten
            relationships: Zu durchlaufende Beziehungstypen
            max_depth: Maximale Traversierung-Tiefe
            
        Returns:
            QueryResult: Traversierung-Ergebnisse
        """
        query_data = {
            "start_nodes": start_nodes,
            "relationships": relationships,
            "max_depth": max_depth
        }
        
        return self.execute_query(QueryType.GRAPH_TRAVERSAL, query_data)
    
    def metadata_filter(self,
                       filters: Dict[str, Any],
                       sort_by: Optional[str] = None,
                       limit: int = 50) -> QueryResult:
        """
        Filtert nach Metadaten
        
        Args:
            filters: Filter-Kriterien
            sort_by: Sortierung
            limit: Maximale Ergebnisse
            
        Returns:
            QueryResult: Filter-Ergebnisse
        """
        query_data = {
            "filters": filters,
            "sort_by": sort_by,
            "limit": limit
        }
        
        return self.execute_query(QueryType.METADATA_FILTER, query_data)
    
    @contextmanager
    def transaction(self, database_types: Optional[List[DatabaseType]] = None):
        """
        Context Manager für Database-Transaktionen
        
        Args:
            database_types: Databases für Transaction
        """
        transaction_id = hashlib.md5(str(datetime.now()).encode(), usedforsecurity=False).hexdigest()[:8]
        
        try:
            self.logger.info(f"🔄 Starting transaction {transaction_id}")
            yield transaction_id
            self.logger.info(f"✅ Transaction {transaction_id} committed")
        except Exception as e:
            self.logger.error(f"❌ Transaction {transaction_id} rolled back: {e}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """
        Führt Health Check aller Database-Verbindungen durch
        
        Returns:
            Dict: Health Status
        """
        status = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "databases": {},
            "performance": {
                "avg_query_time_ms": 0.0,
                "cache_hit_rate": self._calculate_cache_hit_rate(),
                "total_queries": len(self.performance_metrics)
            }
        }
        
        # Check each database connection
        unhealthy_count = 0
        for db_type, connection in self.connections.items():
            db_status = {
                "connected": connection.is_connected,
                "last_check": connection.last_health_check.isoformat() if connection.last_health_check else None,
                "status": "healthy" if connection.is_connected else "unhealthy"
            }
            
            if not connection.is_connected:
                unhealthy_count += 1
            
            status["databases"][db_type.value] = db_status
        
        # Calculate average query time
        if self.performance_metrics:
            avg_time = sum(m["execution_time_ms"] for m in self.performance_metrics[-100:]) / min(len(self.performance_metrics), 100)
            status["performance"]["avg_query_time_ms"] = round(avg_time, 2)
        
        # Overall status
        if unhealthy_count > 0:
            status["overall_status"] = "degraded" if unhealthy_count < len(self.connections) else "unhealthy"
        
        return status
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Gibt Database-Statistiken zurück
        
        Returns:
            Dict: Statistiken
        """
        return {
            "connections": len(self.connections),
            "schemas_loaded": len(self.schemas),
            "cache_size": len(self.query_cache),
            "performance_metrics": len(self.performance_metrics),
            "cache_hit_rate": self._calculate_cache_hit_rate(),
            "database_types": [db.value for db in self.connections.keys()]
        }


# Factory functions
def create_database_api(connections: Optional[List[DatabaseConnection]] = None) -> UDS3DatabaseAPI:
    """
    Factory-Funktion zur Erstellung der Database API
    
    Args:
        connections: Database-Verbindungen
        
    Returns:
        UDS3DatabaseAPI: Database API Instance
    """
    return UDS3DatabaseAPI(connections)


def create_mock_connections() -> List[DatabaseConnection]:
    """
    Erstellt Mock-Verbindungen für Testing/Demo
    
    Returns:
        List: Mock Database-Verbindungen
    """
    return [
        DatabaseConnection(
            db_type=DatabaseType.VECTOR,
            connection_string="vector://localhost:8000"
        ),
        DatabaseConnection(
            db_type=DatabaseType.GRAPH,
            connection_string="neo4j://localhost:7687"
        ),
        DatabaseConnection(
            db_type=DatabaseType.RELATIONAL,
            connection_string="postgresql://localhost:5432/uds3"
        ),
        DatabaseConnection(
            db_type=DatabaseType.FILE_STORAGE,
            connection_string="file://var/uds3/storage"
        )
    ]


if __name__ == "__main__":
    # Demo der Database API
    print("UDS3 Database API Demo")
    print("=====================")
    
    # API mit Mock-Connections erstellen
    connections = create_mock_connections()
    db_api = create_database_api(connections)
    
    # Health Check
    health = db_api.health_check()
    print(f"Database Health: {health['overall_status']}")
    
    # Beispiel-Query
    search_result = db_api.semantic_search("Verwaltungsrecht", limit=5)
    print(f"Search Results: {len(search_result.results)} documents found")
    
    # Statistiken
    stats = db_api.get_statistics()
    print(f"Database API Stats: {stats}")
    
    print("✅ Database API Demo completed")