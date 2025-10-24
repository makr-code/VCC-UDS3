"""
UDS3 Core Module - Kernkomponenten
==================================

Reorganisiert: 24. Oktober 2025
Kernkomponenten mit verkürzten Namen:
- database.py: Hauptdatabase-Strategie (ehemals uds3_core.py)
- schemas.py: Database-Schemas (ehemals uds3_database_schemas.py)
- relations.py: Relations-Core (ehemals uds3_relations_core.py)
- framework.py: Relations-Framework (ehemals uds3_relations_data_framework.py)
- cache.py: Single-Record-Cache (ehemals uds3_single_record_cache.py)
"""

# Core Database Components (neue Struktur) 
__all__ = []
CORE_DATABASE_AVAILABLE = False

try:
    from .database import UnifiedDatabaseStrategy
    from .schemas import UDS3DatabaseSchemasMixin
    CORE_DATABASE_AVAILABLE = True
    __all__.extend(["UnifiedDatabaseStrategy", "UDS3DatabaseSchemasMixin"])
except ImportError as e:
    pass

# Erweiterte Core-Komponenten (optional)
try:
    from .relations import UDS3RelationsCore
    from .framework import UDS3RelationsDataFramework
    from .cache import SingleRecordCache
    __all__.extend(["UDS3RelationsCore", "UDS3RelationsDataFramework", "SingleRecordCache"])
except ImportError:
    pass

# Legacy Exports (für Rückwärtskompatibilität)
LEGACY_CORE_AVAILABLE = False
try:
    from .polyglot_manager import UDS3PolyglotManager
    from .embeddings import UDS3GermanEmbeddings, create_german_embeddings
    from .llm_ollama import OllamaClient
    from .rag_pipeline import UDS3GenericRAG, QueryType, RAGContext
    from .rag_cache import RAGCache, PersistentRAGCache, CachedRAGResult
    from .rag_async import UDS3AsyncRAG, AsyncRAGResult, create_async_rag, batch_answer_queries
    LEGACY_CORE_AVAILABLE = True
    __all__.extend([
        "UDS3PolyglotManager", "UDS3GermanEmbeddings", "create_german_embeddings",
        "OllamaClient", "UDS3GenericRAG", "QueryType", "RAGContext", 
        "RAGCache", "PersistentRAGCache", "CachedRAGResult",
        "UDS3AsyncRAG", "AsyncRAGResult", "create_async_rag", "batch_answer_queries"
    ])
except ImportError:
    pass

# Verfügbarkeits-Flags
__all__.extend(["CORE_DATABASE_AVAILABLE", "LEGACY_CORE_AVAILABLE"])

__all__ = [
    # Neue Core Database Components
    "UnifiedDatabaseStrategy",
    "UDS3DatabaseSchemasMixin", 
    "RelationsCore",
    "RelationsDataFramework",
    "SingleRecordCache",
    
    # Legacy Core Manager (Rückwärtskompatibilität)
    "UDS3PolyglotManager",
    # Embeddings
    "UDS3GermanEmbeddings",
    "create_german_embeddings",
    # LLM
    "OllamaClient",
    # RAG Pipeline
    "UDS3GenericRAG",
    "QueryType",
    "RAGContext",
    # RAG Cache
    "RAGCache",
    "PersistentRAGCache",
    "CachedRAGResult",
    # RAG Async
    "UDS3AsyncRAG",
    "AsyncRAGResult",
    "create_async_rag",
    "batch_answer_queries",
]

__module_name__ = "core"
__version__ = "2.0.0"
