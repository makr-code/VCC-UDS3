"""
UDS3 API Module - API-Schnittstellen
====================================

Dieses Modul enthält alle API-Schnittstellen und -komponenten:
- manager.py: Unified API Manager (ehemals uds3_api_manager.py)
- database.py: Database API (ehemals uds3_database_api.py)
- search.py: Search API (ehemals uds3_search_api.py)
- crud.py: Advanced CRUD (ehemals uds3_advanced_crud.py)
- crud_strategies.py: CRUD Strategies (ehemals uds3_crud_strategies.py)
- query.py: Polyglot Query (ehemals uds3_polyglot_query.py)
- filters.py: Query Filters (ehemals uds3_query_filters.py)
- vector_filter.py: Vector Filter (ehemals uds3_vector_filter.py)
- graph_filter.py: Graph Filter (ehemals uds3_graph_filter.py)
- relational_filter.py: Relational Filter (ehemals uds3_relational_filter.py)
- file_filter.py: File Storage Filter (ehemals uds3_file_storage_filter.py)
- naming.py: Naming Strategy (ehemals uds3_naming_strategy.py)
- naming_integration.py: Naming Integration (ehemals uds3_naming_integration.py)
- geo.py: Geo Extension (ehemals uds3_geo_extension.py)
- parser_base.py: Process Parser Base (ehemals uds3_process_parser_base.py)
- petrinet.py: Petrinet Parser (ehemals uds3_petrinet_parser.py)
- workflow.py: Workflow Net Analyzer (ehemals uds3_workflow_net_analyzer.py)
"""

# API components - graceful imports
# Nur verfügbare Komponenten werden importiert

__all__ = []
API_CORE_AVAILABLE = False
SEARCH_QUERY_AVAILABLE = False
CRUD_AVAILABLE = False

# Core API Components (essentiell)
try:
    from .manager import UDS3APIManager, create_uds3_api, APIConfiguration
    from .database import UDS3DatabaseAPI, create_database_api, DatabaseType, QueryType
    API_CORE_AVAILABLE = True
    __all__.extend([
        "UDS3APIManager", "UDS3DatabaseAPI", "create_uds3_api", 
        "create_database_api", "APIConfiguration", "DatabaseType", "QueryType"
    ])
except ImportError as e:
    pass

# Search APIs (optional)
try:
    # Flexible Imports - nur was verfügbar ist
    SEARCH_QUERY_AVAILABLE = True
except ImportError:
    pass

# CRUD APIs (optional)  
try:
    # Flexible Imports - nur was verfügbar ist
    CRUD_AVAILABLE = True
except ImportError:
    pass

# Verfügbarkeits-Flags exportieren
__all__.extend([
    "API_CORE_AVAILABLE",
    "SEARCH_QUERY_AVAILABLE", 
    "CRUD_AVAILABLE"
])

__version__ = "3.1.0"
__updated__ = "2025-10-24"

# Health Check für API-Module
def api_health_check():
    """Prüft Verfügbarkeit aller API-Komponenten"""
    return {
        "api_core_available": API_CORE_AVAILABLE,
        "search_query_available": SEARCH_QUERY_AVAILABLE,
        "crud_available": CRUD_AVAILABLE,
        "overall_status": "healthy" if API_CORE_AVAILABLE else "degraded"
    }