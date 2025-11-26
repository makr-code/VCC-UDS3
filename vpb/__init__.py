#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
__init__.py

UDS3 VPB Module
Dieses Modul ist Teil der UDS3 Polyglot Persistence Architecture.
VPB = Verwaltungsprozessbeschreibung

Part of UDS3 (Unified Database Strategy v3)
Author: Martin Krüger (ma.krueger@outlook.com)
License: MIT with Government Partnership Commons Clause
Repository: https://github.com/makr-code/VCC-UDS3
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

# v2.0.0: Process-Aware Queries
from .process_aware_query import (
    ProcessAwareQuery,
    ProcessContext,
    ProcessAwareSearchResult,
    ProcessStepType,
    ProcessStatus,
    create_process_aware_query,
)

__module_name__ = "vpb"
__version__ = "2.2.0"  # Updated for v2.0.0 features

__all__ = [
    "VPBAdapter",
    "create_vpb_adapter",
    "VPBRAGDataMiner",
    "create_vpb_dataminer",
    "ProcessKnowledgeNode",
    "ProcessKnowledgeGraph",
    "DataMiningResult",
    # v2.0.0: Process-Aware Queries
    "ProcessAwareQuery",
    "ProcessContext",
    "ProcessAwareSearchResult",
    "ProcessStepType",
    "ProcessStatus",
    "create_process_aware_query",
]
