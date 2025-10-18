"""
UDS3 VPB Module

Dieses Modul ist Teil der UDS3 Polyglot Persistence Architecture.
VPB = Verwaltungsprozessbeschreibung
"""

# Core Adapter
from .adapter import VPBAdapter, create_vpb_adapter

# RAG DataMiner
from .rag_dataminer import (
    VPBRAGDataMiner,
    create_vpb_dataminer,
    ProcessKnowledgeNode,
    ProcessKnowledgeGraph,
    DataMiningResult
)

__module_name__ = "vpb"
__version__ = "2.1.0"

__all__ = [
    "VPBAdapter",
    "create_vpb_adapter",
    "VPBRAGDataMiner",
    "create_vpb_dataminer",
    "ProcessKnowledgeNode",
    "ProcessKnowledgeGraph",
    "DataMiningResult",
]
