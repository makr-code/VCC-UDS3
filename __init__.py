"""
UDS3 - Unified Data Strategy 3.0
Clean Modular Architecture

Reorganisiert: 24. Oktober 2025
Neue Struktur: core/, manager/, api/, docs/
Verkürzte Dateinamen, klare Trennung
"""

# Core Components (neue Struktur)
try:
    from .core.database import UnifiedDatabaseStrategy
    from .core.schemas import UDS3DatabaseSchemasMixin
    from .core.relations import UDS3RelationsCore
    from .core.framework import UDS3RelationsDataFramework
    from .core.cache import SingleRecordCache
    CORE_AVAILABLE = True
except ImportError as e:
    CORE_AVAILABLE = False
    print(f"Warning: Core components not available: {e}")

# API Components (neue Struktur)
try:
    from .api.manager import UDS3APIManager, create_uds3_api, APIConfiguration
    from .api.database import UDS3DatabaseAPI, create_database_api, DatabaseType, QueryType
    from .api.search import UDS3SearchAPI
    from .api.crud import AdvancedCRUDManager
    API_AVAILABLE = True
except ImportError as e:
    API_AVAILABLE = False
    print(f"Warning: API components not available: {e}")

# Manager Components (neue Struktur)
try:
    from .manager.saga import UDS3SagaOrchestrator
    from .manager.streaming import StreamingManager
    from .manager.archive import ArchiveManager
    MANAGER_AVAILABLE = True
except ImportError as e:
    MANAGER_AVAILABLE = False
    print(f"Warning: Manager components not available: {e}")

# Legacy Support (for backward compatibility)
try:
    from legacy.core import LegacyCore
    LEGACY_SUPPORT_AVAILABLE = True
except ImportError:
    LEGACY_SUPPORT_AVAILABLE = False

# Version Info
__version__ = "3.1.0"
__author__ = "UDS3 Team"
__updated__ = "2025-10-24"

# Main Exports (neue modulare Struktur)
__all__ = [
    # Core Components
    "UnifiedDatabaseStrategy",
    "UDS3DatabaseSchemasMixin",
    "RelationsCore",
    "RelationsDataFramework", 
    "SingleRecordCache",
    
    # API Components
    "UDS3APIManager",
    "UDS3DatabaseAPI", 
    "UDS3SearchAPI",
    "AdvancedCRUDManager",
    "create_uds3_api",
    "create_database_api",
    
    # Manager Components
    "SagaOrchestrator",
    "StreamingManager",
    "ArchiveManager",
    
    # Configuration & Types
    "APIConfiguration",
    "DatabaseType", 
    "QueryType",
]

# Module Discovery (neue Struktur)
__modules__ = [
    "core",           # Kernkomponenten (database, schemas, relations, framework, cache)
    "api",            # API-Schnittstellen (manager, database, search, crud, filters, etc.)
    "manager",        # Management & Orchestrierung (saga, streaming, archive, delete, etc.)
    "doku",           # Dokumentation
    "archive",        # Archivierte Legacy-Dateien
    "legacy",         # Rückwärtskompatibilität 
    "vpb",            # VPB-Submodule
    # Bestehende Untermodule
    "compliance",
    "integration", 
    "operations",
    "query",
    "domain",
    "saga",
    "relations", 
    "performance",
    "search",
    "security",
]

# Archivierte Module (verschoben nach /archive)
__archived_modules__ = [
    "examples",           # /archive/examples/ 
    "legacy_components",  # /archive/legacy_components/
    "deprecated_apis",    # /archive/deprecated_apis/
    "utilities",          # /archive/utilities/
]

# Health Check Function
def health_check() -> dict:
    """
    Führt Health Check aller verfügbaren Module durch
    
    Returns:
        dict: Status aller Komponenten
    """
    status = {
        "version": __version__,
        "updated": __updated__,
        "structure": "modular",
        "core_available": CORE_AVAILABLE,
        "api_available": API_AVAILABLE,  
        "manager_available": MANAGER_AVAILABLE,
        "legacy_support": LEGACY_SUPPORT_AVAILABLE,
        "active_modules": __modules__,
        "archived_modules": __archived_modules__
    }
    
    # Detailed API health checks
    if API_AVAILABLE:
        try:
            api = create_uds3_api()
            api_health = api.health_check()
            status["api_manager_status"] = api_health["overall_status"]
        except Exception as e:
            status["api_manager_status"] = f"error: {e}"
    
    # Module-specific health checks
    try:
        from .core import CORE_DATABASE_AVAILABLE
        status["core_database_available"] = CORE_DATABASE_AVAILABLE
    except ImportError:
        pass
        
    try:
        from .manager import manager_health_check
        status["manager_health"] = manager_health_check()
    except ImportError:
        pass
        
    try:
        from .api import api_health_check  
        status["api_health"] = api_health_check()
    except ImportError:
        pass
    
    return status

# Convenience Functions
def get_api() -> 'UDS3APIManager':
    """
    Gibt Standard API Manager zurück
    
    Returns:
        UDS3APIManager: Standard API-Instanz
    """
    if not API_AVAILABLE:
        raise ImportError("API components not available")
    
    return create_uds3_api()

def get_database_api() -> 'UDS3DatabaseAPI':
    """
    Gibt Database API zurück
    
    Returns:
        UDS3DatabaseAPI: Database API-Instanz  
    """
    if not API_AVAILABLE:
        raise ImportError("API components not available")
    
    return create_database_api()

def get_core() -> dict:
    """
    Gibt alle Core-Komponenten zurück
    
    Returns:
        dict: Core-Komponenten
    """
    if not CORE_AVAILABLE:
        raise ImportError("Core components not available")
    
    return {
        "database_strategy": UnifiedDatabaseStrategy,
        "schemas": UDS3DatabaseSchemasMixin,
        "relations": UDS3RelationsCore,
        "framework": UDS3RelationsDataFramework,
        "cache": SingleRecordCache
    }

# Add convenience functions to exports
__all__.extend([
    "health_check",
    "get_api", 
    "get_database_api",
    "get_core",
    "main"
])

def main():
    """Main CLI entry point for UDS3 package"""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="UDS3 - Unified Database Strategy v3")
    parser.add_argument("--version", action="version", version=f"UDS3 {__version__}")
    parser.add_argument("--health", action="store_true", help="Run health check")
    parser.add_argument("--info", action="store_true", help="Show system info")
    
    args = parser.parse_args()
    
    if args.health:
        health_status = health_check()
        print("🔍 UDS3 Health Check:")
        for component, status in health_status.items():
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {component}: {'Available' if status else 'Not Available'}")
        sys.exit(0 if all(health_status.values()) else 1)
    
    if args.info:
        print(f"🚀 UDS3 v{__version__}")
        print(f"📦 Package Location: {__file__}")
        print(f"🐍 Python: {sys.version}")
        
        print("\n📊 Available Components:")
        components = {
            "Core": CORE_AVAILABLE,
            "API": API_AVAILABLE, 
            "Manager": MANAGER_AVAILABLE,
            "Legacy": LEGACY_SUPPORT_AVAILABLE
        }
        for name, available in components.items():
            status = "✅ Available" if available else "❌ Not Available"
            print(f"  {name}: {status}")
        sys.exit(0)
    
    # Default: show help
    parser.print_help()
    sys.exit(0)
