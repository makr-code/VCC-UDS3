"""
UDS3 Core Module

Dieses Modul ist Teil der UDS3 Polyglot Persistence Architecture.

Auto-generiert von generate_init_files.py
"""

# Exports für Backwards Compatibility
from .polyglot_manager import UDS3PolyglotManager
from .embeddings import UDS3GermanEmbeddings, create_german_embeddings
from .llm_ollama import OllamaClient
from .rag_pipeline import UDS3GenericRAG, QueryType, RAGContext
from .rag_cache import RAGCache, PersistentRAGCache, CachedRAGResult
from .rag_async import UDS3AsyncRAG, AsyncRAGResult, create_async_rag, batch_answer_queries

__all__ = [
    # Core Manager
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
