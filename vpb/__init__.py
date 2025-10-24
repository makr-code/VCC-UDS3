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
