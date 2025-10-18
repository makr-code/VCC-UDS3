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

__all__ = [
    "UDS3PolyglotManager",
    "UDS3GermanEmbeddings",
    "create_german_embeddings",
    "OllamaClient",
    "UDS3GenericRAG",
    "QueryType",
    "RAGContext",
]

__module_name__ = "core"
__version__ = "2.0.0"
